"""
CrewAI Crew orchestration - Tự động hóa toàn bộ pipeline:
Research → Auto-Review Outline → Doc → Auto-Review Doc → Slide → Auto-Review Slide → Final Assets
Human chỉ tương tác với sản phẩm cuối (Doc + Slide + PPTX).
"""

import json
import os
import re

from crewai import Crew, Process

from agents import (
    create_researcher, create_content_strategist,
    create_doc_writer, create_slide_designer,
    create_reviewer, create_outline_reviewer, create_doc_reviewer,
)
from tasks import (
    create_research_task, create_content_task, create_revise_content_task,
    create_doc_task, create_revise_doc_task,
    create_slide_task,
    create_review_task, create_outline_review_task, create_doc_review_task,
)
from tools.pptx_generator import PPTXGenerator

# Số lần tối đa cho auto-review loop
MAX_REVIEW_ITERATIONS = 2


def _slugify_filename(text: str, fallback: str = "presentation") -> str:
    """Tạo tên file an toàn từ tiêu đề."""
    cleaned = "".join(c if c.isalnum() or c in " -_" else "_" for c in text).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return (cleaned[:60] or fallback).strip("._")


def _save_final_assets(topic: str, doc_content: str, slide_json: str, pptx_filepath: str) -> dict:
    """Lưu doc và slide JSON để human chỉ làm việc với bộ sản phẩm cuối."""
    output_dir = os.path.dirname(pptx_filepath) if pptx_filepath else "output"
    os.makedirs(output_dir, exist_ok=True)

    base_name = _slugify_filename(topic)
    doc_path = os.path.join(output_dir, f"{base_name}.md")
    slide_path = os.path.join(output_dir, f"{base_name}.json")

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(doc_content or "")

    with open(slide_path, "w", encoding="utf-8") as f:
        f.write(slide_json or "")

    return {
        "doc_filepath": doc_path,
        "slide_filepath": slide_path,
    }


def _extract_json(text: str) -> str:
    """Trích xuất JSON từ text có thể chứa markdown code blocks."""
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()

    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return text[start:end]

    return text


def _is_approved(review_text: str) -> bool:
    """Kiểm tra xem review kết luận là ĐẠT hay CẦN SỬA."""
    text = review_text.upper()
    # Tìm dòng có KẾT LUẬN
    conclusion_patterns = [
        r"KẾT\s*LUẬN\s*:\s*ĐẠT",
        r"KẾT\s*LUẬN\s*:\s*CẦN\s*SỬA",
    ]
    for pattern in conclusion_patterns:
        match = re.search(pattern, text)
        if match:
            return "ĐẠT" in match.group()

    # Fallback: nếu có "ĐẠT" xuất hiện sau "KẾT LUẬN" hoặc ở cuối
    if "KẾT LUẬN" in text:
        idx = text.index("KẾT LUẬN")
        conclusion_part = text[idx:]
        if "ĐẠT" in conclusion_part and "CẦN SỬA" not in conclusion_part:
            return True
        return False

    # Nếu không tìm thấy KẾT LUẬN, mặc định là ĐẠT (tin tưởng agent)
    return True


def _extract_review_feedback(review_text: str) -> str:
    """Trích xuất phần vấn đề + đề xuất từ review để dùng làm feedback cho lần revise."""
    lines = review_text.split("\n")
    feedback_lines = []
    capturing = False
    for line in lines:
        lower = line.strip().lower()
        if any(kw in lower for kw in ["vấn đề", "cần sửa", "đề xuất", "cải thiện"]):
            capturing = True
        if capturing:
            feedback_lines.append(line)
        if "kết luận" in lower:
            capturing = False
    return "\n".join(feedback_lines) if feedback_lines else review_text


def validate_outline_json(json_str: str) -> dict:
    """Validate và parse outline JSON. Trả về dict hoặc raise exception."""
    clean_json = _extract_json(json_str)
    outline = json.loads(clean_json)

    if "slides" not in outline:
        raise ValueError("JSON thiếu trường 'slides'")

    if not isinstance(outline["slides"], list):
        raise ValueError("'slides' phải là một list")

    if len(outline["slides"]) == 0:
        raise ValueError("'slides' không được rỗng")

    for i, slide in enumerate(outline["slides"]):
        if "type" not in slide:
            raise ValueError(f"Slide {i} thiếu 'type'")
        if "title" not in slide:
            raise ValueError(f"Slide {i} thiếu 'title'")
        if slide["type"] not in ["title", "content", "summary"]:
            raise ValueError(f"Slide {i} có type không hợp lệ: {slide['type']}")

    return outline


def format_outline_display(outline: dict) -> str:
    """Format outline thành text dễ đọc để hiển thị cho người dùng."""
    lines = []
    title = outline.get("presentation_title", "Không có tiêu đề")
    lines.append(f"📋 Tiêu đề bài thuyết trình: {title}")
    lines.append(f"📊 Tổng số slide: {len(outline.get('slides', []))}")
    lines.append("")

    for i, slide in enumerate(outline.get("slides", [])):
        slide_type = slide.get("type", "content")
        emoji = {"title": "🎬", "content": "📄", "summary": "🏁"}.get(slide_type, "📄")
        lines.append(f"{emoji} Slide {i+1} [{slide_type.upper()}]: {slide.get('title', 'Không có tiêu đề')}")

        if slide.get("subtitle"):
            lines.append(f"   Phụ đề: {slide['subtitle']}")

        bullets = slide.get("bullet_points", [])
        if bullets:
            for bp in bullets:
                if isinstance(bp, dict):
                    indent = "     " if bp.get("level", 0) > 0 else "   • "
                    lines.append(f"{indent}{bp.get('text', '')}")
                else:
                    lines.append(f"   • {bp}")

        if slide.get("notes"):
            lines.append(f"   📝 Notes: {slide['notes'][:100]}...")

        lines.append("")

    return "\n".join(lines)


# ============================================
# Phase 1: Research & Outline (with auto-review)
# ============================================

def run_phase1(topic: str, provider: str = None, api_key: str = None, num_slides: int = 10,
               auto_review: bool = True) -> dict:
    """
    Chạy Phase 1: Research → Tạo Outline → Auto-Review Outline.
    Nếu reviewer yêu cầu sửa → tự động revise (max MAX_REVIEW_ITERATIONS lần).
    Trả về dict với keys: research_result, outline_json, outline_display, review_logs, error
    """
    review_logs = []

    try:
        # Tạo agents
        researcher = create_researcher(provider=provider, api_key=api_key)
        strategist = create_content_strategist(provider=provider, api_key=api_key)
        outline_reviewer = create_outline_reviewer(provider=provider, api_key=api_key)

        # Step 1: Research
        research_task = create_research_task(researcher, topic)
        crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True,
        )
        result = crew.kickoff()
        research_result = str(result)

        # Step 2: Tạo outline từ kết quả research
        content_task = create_content_task(strategist, research_result, topic, num_slides)
        outline_crew = Crew(
            agents=[strategist],
            tasks=[content_task],
            process=Process.sequential,
            verbose=True,
        )
        outline_result = outline_crew.kickoff()
        outline_raw = str(outline_result)

        # Parse và validate
        try:
            outline = validate_outline_json(outline_raw)
            outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, ValueError) as e:
            review_logs.append(f"⚠️ Lỗi parse JSON outline ban đầu: {e}")
            return {
                "research_result": research_result,
                "outline_json": outline_raw,
                "outline_display": f"⚠️ Không thể parse JSON: {e}\n\n{outline_raw}",
                "outline_dict": None,
                "review_logs": review_logs,
                "error": f"Lỗi parse JSON: {e}",
            }

        # Step 3: Auto-review loop
        current_outline = outline_json
        if not auto_review:
            review_logs.append("⏸️ Bỏ qua auto-review outline vì đang dùng human review mode")
        else:
            for iteration in range(MAX_REVIEW_ITERATIONS):
                review_logs.append(f"🔄 Review outline - lần {iteration + 1}")

                # Review outline
                review_task = create_outline_review_task(outline_reviewer, current_outline, topic)
                review_crew = Crew(
                    agents=[outline_reviewer],
                    tasks=[review_task],
                    process=Process.sequential,
                    verbose=True,
                )
                review_result = str(review_crew.kickoff())
                review_logs.append(f"📝 Kết quả review outline (lần {iteration + 1}):\n{review_result}")

                if _is_approved(review_result):
                    review_logs.append(f"✅ Outline ĐẠT ở lần review {iteration + 1}")
                    break
                else:
                    review_logs.append(f"⚠️ Outline CẦN SỬA ở lần review {iteration + 1}")
                    # Extract feedback và revise
                    feedback = _extract_review_feedback(review_result)
                    revise_task = create_revise_content_task(strategist, current_outline, feedback, topic)
                    revise_crew = Crew(
                        agents=[strategist],
                        tasks=[revise_task],
                        process=Process.sequential,
                        verbose=True,
                    )
                    revise_result = revise_crew.kickoff()
                    revised_raw = str(revise_result)

                    # Parse revised outline
                    try:
                        outline = validate_outline_json(revised_raw)
                        current_outline = json.dumps(outline, ensure_ascii=False, indent=2)
                        review_logs.append(f"✅ Đã sửa outline theo feedback (lần {iteration + 1})")
                    except (json.JSONDecodeError, ValueError) as e:
                        review_logs.append(f"⚠️ Lỗi parse revised outline: {e}, giữ nguyên outline cũ")
            else:
                review_logs.append(f"ℹ️ Đã hết số lần review tối đa ({MAX_REVIEW_ITERATIONS}), sử dụng outline hiện tại")

        # Final parse
        outline_display = format_outline_display(outline)

        return {
            "research_result": research_result,
            "outline_json": current_outline,
            "outline_display": outline_display,
            "outline_dict": outline,
            "review_logs": review_logs,
            "error": None,
        }

    except Exception as e:
        return {
            "research_result": None,
            "outline_json": None,
            "outline_display": None,
            "outline_dict": None,
            "review_logs": review_logs,
            "error": f"Lỗi Phase 1: {e}",
        }


# ============================================
# Phase 2: Document Generation (with auto-review)
# ============================================

def run_phase2_doc(approved_outline: str, topic: str, provider: str = None, api_key: str = None,
                   auto_review: bool = True) -> dict:
    """
    Chạy Phase 2: Tạo tài liệu chi tiết → Auto-Review → Auto-Revise nếu cần.
    Trả về dict với keys: doc_content, review_logs, error
    """
    review_logs = []

    try:
        doc_writer = create_doc_writer(provider=provider, api_key=api_key)
        doc_reviewer = create_doc_reviewer(provider=provider, api_key=api_key)

        # Step 1: Tạo tài liệu
        doc_task = create_doc_task(doc_writer, approved_outline, topic)
        crew = Crew(
            agents=[doc_writer],
            tasks=[doc_task],
            process=Process.sequential,
            verbose=True,
        )
        result = crew.kickoff()
        current_doc = str(result)

        # Step 2: Auto-review loop
        if not auto_review:
            review_logs.append("⏸️ Bỏ qua auto-review tài liệu vì đang dùng human review mode")
        else:
            for iteration in range(MAX_REVIEW_ITERATIONS):
                review_logs.append(f"🔄 Review tài liệu - lần {iteration + 1}")

                review_task = create_doc_review_task(doc_reviewer, current_doc, topic)
                review_crew = Crew(
                    agents=[doc_reviewer],
                    tasks=[review_task],
                    process=Process.sequential,
                    verbose=True,
                )
                review_result = str(review_crew.kickoff())
                review_logs.append(f"📝 Kết quả review tài liệu (lần {iteration + 1}):\n{review_result}")

                if _is_approved(review_result):
                    review_logs.append(f"✅ Tài liệu ĐẠT ở lần review {iteration + 1}")
                    break
                else:
                    review_logs.append(f"⚠️ Tài liệu CẦN SỬA ở lần review {iteration + 1}")
                    feedback = _extract_review_feedback(review_result)
                    revise_task = create_revise_doc_task(doc_writer, current_doc, feedback, topic)
                    revise_crew = Crew(
                        agents=[doc_writer],
                        tasks=[revise_task],
                        process=Process.sequential,
                        verbose=True,
                    )
                    revise_result = revise_crew.kickoff()
                    current_doc = str(revise_result)
                    review_logs.append(f"✅ Đã sửa tài liệu theo feedback (lần {iteration + 1})")
            else:
                review_logs.append(f"ℹ️ Đã hết số lần review tối đa ({MAX_REVIEW_ITERATIONS}), sử dụng tài liệu hiện tại")

        return {
            "doc_content": current_doc,
            "review_logs": review_logs,
            "error": None,
        }

    except Exception as e:
        return {
            "doc_content": None,
            "review_logs": review_logs,
            "error": f"Lỗi Phase 2 (Doc): {e}",
        }


def revise_outline_with_human_feedback(current_outline: str, topic: str, feedback: str,
                                       provider: str = None, api_key: str = None) -> dict:
    """
    Cho phép human review mode gửi góp ý để agent sửa outline trước khi sang Phase 2.
    """
    review_logs = []

    try:
        strategist = create_content_strategist(provider=provider, api_key=api_key)
        revise_task = create_revise_content_task(strategist, current_outline, feedback, topic)
        revise_crew = Crew(
            agents=[strategist],
            tasks=[revise_task],
            process=Process.sequential,
            verbose=True,
        )
        revise_result = revise_crew.kickoff()
        revised_raw = str(revise_result)

        outline = validate_outline_json(revised_raw)
        outline_json = json.dumps(outline, ensure_ascii=False, indent=2)

        review_logs.append("✅ Đã cập nhật outline theo góp ý của người dùng")

        return {
            "outline_json": outline_json,
            "outline_display": format_outline_display(outline),
            "outline_dict": outline,
            "review_logs": review_logs,
            "error": None,
        }
    except Exception as e:
        return {
            "outline_json": current_outline,
            "outline_display": None,
            "outline_dict": None,
            "review_logs": review_logs,
            "error": f"Lỗi sửa outline theo góp ý: {e}",
        }


# ============================================
# Phase 3: Generate Slide & Review (with auto-review)
# ============================================

def run_phase3(approved_outline: str, approved_doc: str, theme_name: str, provider: str = None,
               api_key: str = None, auto_review: bool = True) -> dict:
    """
    Chạy Phase 3: Slide Design → Auto-Review → Auto-Revise nếu cần → Generate PPTX.
    Trả về dict với keys: slide_json, review_result, filepath, review_logs, error
    """
    review_logs = []

    try:
        designer = create_slide_designer(provider=provider, api_key=api_key)
        slide_reviewer = create_reviewer(provider=provider, api_key=api_key)

        # Step 1: Slide Design
        slide_task = create_slide_task(designer, approved_outline, theme_name, doc_content=approved_doc)
        design_crew = Crew(
            agents=[designer],
            tasks=[slide_task],
            process=Process.sequential,
            verbose=True,
        )
        design_result = design_crew.kickoff()
        slide_json_raw = str(design_result)

        # Parse JSON
        try:
            slide_data = validate_outline_json(slide_json_raw)
            current_slide_json = json.dumps(slide_data, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, ValueError):
            current_slide_json = approved_outline
            slide_data = json.loads(approved_outline)
            review_logs.append("⚠️ Không parse được slide JSON từ designer, dùng outline gốc")

        final_review_result = ""
        if not auto_review:
            review_logs.append("⏸️ Bỏ qua auto-review slide vì đang dùng human review mode")
        else:
            # Step 2: Auto-review loop
            for iteration in range(MAX_REVIEW_ITERATIONS):
                review_logs.append(f"🔄 Review slide - lần {iteration + 1}")

                review_task = create_review_task(slide_reviewer, current_slide_json)
                review_crew = Crew(
                    agents=[slide_reviewer],
                    tasks=[review_task],
                    process=Process.sequential,
                    verbose=True,
                )
                review_result = str(review_crew.kickoff())
                final_review_result = review_result
                review_logs.append(f"📝 Kết quả review slide (lần {iteration + 1}):\n{review_result}")

                if _is_approved(review_result):
                    review_logs.append(f"✅ Slide ĐẠT ở lần review {iteration + 1}")
                    break
                else:
                    review_logs.append(f"⚠️ Slide CẦN SỬA ở lần review {iteration + 1}")
                    # Re-design slide with review feedback
                    feedback = _extract_review_feedback(review_result)
                    revise_task = create_slide_task(
                        designer, approved_outline, theme_name,
                        doc_content=approved_doc,
                        additional_instructions=f"""
                        LƯU Ý: Slide trước đó đã bị review yêu cầu sửa. Hãy cải thiện theo feedback sau:
                        {feedback}
                        
                        Hãy đảm bảo output JSON được cải thiện theo các điểm trên.
                        """,
                    )
                    revise_crew = Crew(
                        agents=[designer],
                        tasks=[revise_task],
                        process=Process.sequential,
                        verbose=True,
                    )
                    revise_result = revise_crew.kickoff()
                    revised_raw = str(revise_result)

                    try:
                        slide_data = validate_outline_json(revised_raw)
                        current_slide_json = json.dumps(slide_data, ensure_ascii=False, indent=2)
                        review_logs.append(f"✅ Đã sửa slide theo feedback (lần {iteration + 1})")
                    except (json.JSONDecodeError, ValueError):
                        review_logs.append(f"⚠️ Lỗi parse revised slide JSON, giữ nguyên slide cũ")
            else:
                review_logs.append(f"ℹ️ Đã hết số lần review tối đa ({MAX_REVIEW_ITERATIONS}), sử dụng slide hiện tại")

        # Generate PPTX
        generator = PPTXGenerator()
        filepath = generator.generate(current_slide_json, theme_name=theme_name)

        return {
            "slide_json": current_slide_json,
            "review_result": final_review_result,
            "filepath": filepath,
            "review_logs": review_logs,
            "error": None,
        }

    except Exception as e:
        return {
            "slide_json": None,
            "review_result": None,
            "filepath": None,
            "review_logs": review_logs,
            "error": f"Lỗi Phase 3: {e}",
        }


# ============================================
# Full Pipeline: Chạy toàn bộ tự động
# ============================================

def run_full_pipeline(topic: str, theme_name: str = "corporate", num_slides: int = 10,
                      provider: str = None, api_key: str = None, auto_review: bool = True) -> dict:
    """
    Chạy toàn bộ pipeline tự động: Research → Outline → Doc → Slide → PPTX.
    Mỗi phase có auto-review loop riêng.
    Trả về dict với tất cả kết quả và review_logs.
    """
    all_review_logs = []
    all_errors = []

    # Phase 1: Research + Outline
    phase1 = run_phase1(
        topic=topic, provider=provider, api_key=api_key, num_slides=num_slides, auto_review=auto_review,
    )
    all_review_logs.extend(phase1.get("review_logs", []))

    if phase1["error"]:
        all_errors.append(phase1["error"])
        return {
            "phase": "research",
            "outline_json": None,
            "outline_display": None,
            "doc_content": None,
            "slide_json": None,
            "review_result": None,
            "filepath": None,
            "review_logs": all_review_logs,
            "errors": all_errors,
        }

    # Phase 2: Doc
    phase2 = run_phase2_doc(
        approved_outline=phase1["outline_json"],
        topic=topic, provider=provider, api_key=api_key, auto_review=auto_review,
    )
    all_review_logs.extend(phase2.get("review_logs", []))

    if phase2["error"]:
        all_errors.append(phase2["error"])
        return {
            "phase": "doc",
            "outline_json": phase1["outline_json"],
            "outline_display": phase1["outline_display"],
            "doc_content": None,
            "slide_json": None,
            "review_result": None,
            "filepath": None,
            "review_logs": all_review_logs,
            "errors": all_errors,
        }

    # Phase 3: Slide + PPTX
    phase3 = run_phase3(
        approved_outline=phase1["outline_json"],
        approved_doc=phase2["doc_content"],
        theme_name=theme_name,
        provider=provider, api_key=api_key, auto_review=auto_review,
    )

    all_review_logs.extend(phase3.get("review_logs", []))

    if phase3["error"]:
        all_errors.append(phase3["error"])
        return {
            "phase": "slide",
            "outline_json": phase1["outline_json"],
            "outline_display": phase1["outline_display"],
            "doc_content": phase2["doc_content"],
            "slide_json": None,
            "review_result": None,
            "filepath": None,
            "doc_filepath": None,
            "slide_filepath": None,
            "review_logs": all_review_logs,
            "errors": all_errors,
        }

    asset_paths = _save_final_assets(
        topic=topic,
        doc_content=phase2["doc_content"],
        slide_json=phase3["slide_json"],
        pptx_filepath=phase3["filepath"],
    )

    return {
        "phase": "done",
        "outline_json": phase1["outline_json"],
        "outline_display": phase1["outline_display"],
        "doc_content": phase2["doc_content"],
        "slide_json": phase3["slide_json"],
        "review_result": phase3["review_result"],
        "filepath": phase3["filepath"],
        "doc_filepath": asset_paths["doc_filepath"],
        "slide_filepath": asset_paths["slide_filepath"],
        "review_logs": all_review_logs,
        "errors": all_errors,
    }
