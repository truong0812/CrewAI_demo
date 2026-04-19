"""
CrewAI Crew orchestration - Tu dong hoa toan bo pipeline:
Outline (hoac user cung cap) -> Research -> Viet Doc chi tiet -> Slide -> PPTX
Human co the cung cap outline san hoac de AI tao.
"""

import json
import os
import re

from crewai import Crew, Process

from agents import (
    create_researcher, create_content_strategist,
    create_speaker_doc_writer, create_slide_designer,
    create_reviewer, create_outline_reviewer, create_doc_reviewer,
)
from tasks import (
    create_research_task,
    create_content_task, create_revise_content_task,
    create_doc_task, create_revise_doc_task,
    create_slide_task,
    create_review_task, create_outline_review_task, create_doc_review_task,
)
from tools.pptx_generator import PPTXGenerator

# So lan toi da cho auto-review loop
MAX_REVIEW_ITERATIONS = 2


def _clean_outline_line(line: str) -> str:
    """Loai bo ky tu danh dau de parse outline text de dang hon."""
    return re.sub(r"^\s*(?:[-*+•]+|\d+[.)]|#{1,6})\s*", "", line).strip()


def _infer_slide_type(index: int, title: str, total_slides: int) -> str:
    """Suy ra loai slide tu vi tri va tieu de."""
    normalized = title.lower()
    if index == 0 or any(keyword in normalized for keyword in ["mở đầu", "mo dau", "giới thiệu", "gioi thieu", "title"]):
        return "title"
    if index == total_slides - 1 or any(keyword in normalized for keyword in ["kết luận", "ket luan", "tóm tắt", "tom tat", "cảm ơn", "cam on", "q&a"]):
        return "summary"
    return "content"


def parse_outline_text(outline_text: str) -> dict:
    """Chuyen outline dang van ban/markdown thanh JSON outline noi bo."""
    raw_lines = [line.rstrip() for line in outline_text.splitlines() if line.strip()]
    if not raw_lines:
        raise ValueError("Outline rong")

    title = "Bai thuyet trinh"
    slides = []
    current_slide = None

    for line in raw_lines:
        stripped = line.strip()
        cleaned = _clean_outline_line(stripped)
        lower = cleaned.lower()

        if stripped.startswith("# "):
            title = cleaned or title
            continue

        is_slide_header = (
            stripped.startswith("##")
            or re.match(r"^\s*slide\s*\d+\s*[:.-]", stripped, flags=re.IGNORECASE)
            or re.match(r"^\s*\d+\s*[.)]\s+\S+", stripped)
        )

        if is_slide_header:
            if current_slide:
                slides.append(current_slide)
            slide_title = re.sub(r"^\s*slide\s*\d+\s*[:.-]\s*", "", cleaned, flags=re.IGNORECASE)
            current_slide = {
                "type": "content",
                "title": slide_title or f"Slide {len(slides) + 1}",
                "bullet_points": [],
            }
            continue

        if lower.startswith(("notes:", "note:", "ghi chu:", "ghi chú:")):
            if not current_slide:
                current_slide = {"type": "content", "title": f"Slide {len(slides) + 1}", "bullet_points": []}
            current_slide["notes"] = cleaned.split(":", 1)[1].strip() if ":" in cleaned else cleaned
            continue

        if stripped.startswith(("-", "*", "+", "•")):
            if not current_slide:
                current_slide = {"type": "content", "title": f"Slide {len(slides) + 1}", "bullet_points": []}
            current_slide.setdefault("bullet_points", []).append(cleaned)
            continue

        if not current_slide:
            current_slide = {"type": "content", "title": cleaned, "bullet_points": []}
        elif current_slide.get("title", "").startswith("Slide "):
            current_slide["title"] = cleaned
        else:
            current_slide.setdefault("bullet_points", []).append(cleaned)

    if current_slide:
        slides.append(current_slide)

    if not slides:
        raise ValueError("Khong tim thay slide nao trong outline")

    for index, slide in enumerate(slides):
        slide["type"] = _infer_slide_type(index, slide.get("title", ""), len(slides))
        if slide["type"] == "title":
            slide.pop("bullet_points", None)
            slide.setdefault("subtitle", "Tong quan noi dung bai thuyet trinh")
        elif not slide.get("bullet_points"):
            slide["bullet_points"] = ["Noi dung se duoc bo sung trong buoc research"]

    return {
        "presentation_title": title if title != "Bai thuyet trinh" else slides[0].get("title", title),
        "slides": slides,
    }


def normalize_outline_input(outline_input: str) -> dict:
    """Chap nhan outline dang JSON hoac van ban/Markdown."""
    try:
        return validate_outline_json(outline_input)
    except Exception:
        return validate_outline_json(json.dumps(parse_outline_text(outline_input), ensure_ascii=False))


def _slugify_filename(text: str, fallback: str = "presentation") -> str:
    """Tao ten file an toan tu tieu de."""
    cleaned = "".join(c if c.isalnum() or c in " -_" else "_" for c in text).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return (cleaned[:60] or fallback).strip("._")


def _save_final_assets(topic: str, doc_content: str, slide_json: str, pptx_filepath: str) -> dict:
    """Luu doc va slide JSON de human chi lam viec voi bo san pham cuoi."""
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
    """Trich xuat JSON tu text co the chua markdown code blocks."""
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
    """Kiem tra xem review ket luan la DAT hay CAN SUA."""
    text = review_text.upper()

    # Kiem tra pattern Unicode da bieu thuc (co dau)
    conclusion_patterns = [
        r"KẾT\s*LUẬN\s*:\s*ĐẠT",
        r"KẾT\s*LUẬN\s*:\s*CẦN\s*SỬA",
    ]
    for pattern in conclusion_patterns:
        match = re.search(pattern, text)
        if match:
            return "ĐẠT" in match.group()

    if "KẾT LUẬN" in text:
        idx = text.index("KẾT LUẬN")
        conclusion_part = text[idx:]
        if "ĐẠT" in conclusion_part and "CẦN SỬA" not in conclusion_part:
            return True
        return False

    # Fallback: Kiem tra khong dau
    text_no_accent = (
        text.replace("Ế", "E").replace("Ậ", "A").replace("Ầ", "A").replace("Ử", "U")
    )
    if "KET LUAN" in text_no_accent:
        idx = text_no_accent.index("KET LUAN")
        conclusion_part = text_no_accent[idx:]
        if "DAT" in conclusion_part and "CAN SUA" not in conclusion_part:
            return True
        return False

    # WARNING: Khong tim thay ket luan ro rang -> mac dinh CAN SUA (an toan hon)
    print("⚠️ WARNING: Khong tim thay 'KET LUAN' trong review text, mac dinh la CAN SUA")
    return False


def _extract_review_feedback(review_text: str) -> str:
    """Trich xuat phan van de + de xuat tu review de dung lam feedback cho lan revise."""
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
    """Validate va parse outline JSON. Tra ve dict hoac raise exception."""
    clean_json = _extract_json(json_str)
    outline = json.loads(clean_json)

    if "slides" not in outline:
        raise ValueError("JSON thieu truong 'slides'")

    if not isinstance(outline["slides"], list):
        raise ValueError("'slides' phai la mot list")

    if len(outline["slides"]) == 0:
        raise ValueError("'slides' khong duoc rong")

    for i, slide in enumerate(outline["slides"]):
        if "type" not in slide:
            raise ValueError(f"Slide {i} thieu 'type'")
        if "title" not in slide:
            raise ValueError(f"Slide {i} thieu 'title'")
        if slide["type"] not in ["title", "content", "summary"]:
            raise ValueError(f"Slide {i} co type khong hop le: {slide['type']}")

    return outline


def format_outline_display(outline: dict) -> str:
    """Format outline thanh text de doc de hien thi cho nguoi dung."""
    lines = []
    title = outline.get("presentation_title", "Khong co tieu de")
    lines.append(f"📋 Tieu de bai thuyet trinh: {title}")
    lines.append(f"📊 Tong so slide: {len(outline.get('slides', []))}")
    lines.append("")

    for i, slide in enumerate(outline.get("slides", [])):
        slide_type = slide.get("type", "content")
        emoji = {"title": "🎬", "content": "📄", "summary": "🏁"}.get(slide_type, "📄")
        lines.append(f"{emoji} Slide {i+1} [{slide_type.upper()}]: {slide.get('title', 'Khong co tieu de')}")

        if slide.get("subtitle"):
            lines.append(f"   Phu de: {slide['subtitle']}")

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
# Phase 1: Tao Outline (with auto-review)
# ============================================

def run_phase1(topic: str, provider: str = None, api_key: str = None, num_slides: int = 10,
               auto_review: bool = True) -> dict:
    """
    Chay Phase 1: Tao Outline tu topic -> Auto-Review Outline.
    KHONG research truoc - chi tao outline.
    Neu reviewer yeu cau sua -> tu dong revise (max MAX_REVIEW_ITERATIONS lan).
    Tra ve dict voi keys: outline_json, outline_display, review_logs, error
    """
    review_logs = []

    try:
        # Tao agents
        strategist = create_content_strategist(provider=provider, api_key=api_key)
        outline_reviewer = create_outline_reviewer(provider=provider, api_key=api_key)

        # Step 1: Tao outline tu topic
        content_task = create_content_task(strategist, topic, num_slides)
        outline_crew = Crew(
            agents=[strategist],
            tasks=[content_task],
            process=Process.sequential,
            verbose=True,
        )
        outline_result = outline_crew.kickoff()
        outline_raw = str(outline_result)

        # Parse va validate
        try:
            outline = validate_outline_json(outline_raw)
            outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, ValueError) as e:
            review_logs.append(f"⚠️ Loi parse JSON outline ban dau: {e}")
            return {
                "outline_json": outline_raw,
                "outline_display": f"⚠️ Khong the parse JSON: {e}\n\n{outline_raw}",
                "outline_dict": None,
                "review_logs": review_logs,
                "error": f"Loi parse JSON: {e}",
            }

        # Step 2: Auto-review loop
        current_outline = outline_json
        if not auto_review:
            review_logs.append("⏸️ Bo qua auto-review outline vi dang dung human review mode")
        else:
            for iteration in range(MAX_REVIEW_ITERATIONS):
                review_logs.append(f"🔄 Review outline - lan {iteration + 1}")

                review_task = create_outline_review_task(outline_reviewer, current_outline, topic)
                review_crew = Crew(
                    agents=[outline_reviewer],
                    tasks=[review_task],
                    process=Process.sequential,
                    verbose=True,
                )
                review_result = str(review_crew.kickoff())
                review_logs.append(f"📝 Ket qua review outline (lan {iteration + 1}):\n{review_result}")

                if _is_approved(review_result):
                    review_logs.append(f"✅ Outline DAT o lan review {iteration + 1}")
                    break
                else:
                    review_logs.append(f"⚠️ Outline CAN SUA o lan review {iteration + 1}")
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

                    try:
                        outline = validate_outline_json(revised_raw)
                        current_outline = json.dumps(outline, ensure_ascii=False, indent=2)
                        review_logs.append(f"✅ Da sua outline theo feedback (lan {iteration + 1})")
                    except (json.JSONDecodeError, ValueError):
                        review_logs.append(f"⚠️ Loi parse revised outline JSON, giu nguyen outline cu")
            else:
                review_logs.append(f"ℹ️ Da het so lan review toi da ({MAX_REVIEW_ITERATIONS}), su dung outline hien tai")

        return {
            "outline_json": current_outline,
            "outline_display": format_outline_display(outline),
            "outline_dict": outline,
            "review_logs": review_logs,
            "error": None,
        }

    except Exception as e:
        return {
            "outline_json": None,
            "outline_display": None,
            "outline_dict": None,
            "review_logs": review_logs,
            "error": f"Loi Phase 1: {e}",
        }


def use_user_outline(outline_json_str: str) -> dict:
    """
    Su dung outline do nguoi dung cung cap.
    Validate va tra ve dict giong run_phase1.
    """
    review_logs = []
    try:
        outline = normalize_outline_input(outline_json_str)
        current_outline = json.dumps(outline, ensure_ascii=False, indent=2)
        review_logs.append("✅ Da cap nhat outline theo gop y cua nguoi dung")

        return {
            "outline_json": current_outline,
            "outline_display": format_outline_display(outline),
            "outline_dict": outline,
            "review_logs": review_logs,
            "error": None,
        }
    except Exception as e:
        return {
            "outline_json": outline_json_str,
            "outline_display": None,
            "outline_dict": None,
            "review_logs": review_logs,
            "error": f"Loi validate user outline: {e}",
        }


# ============================================
# Phase 2: Research + Viet Doc (with auto-review)
# ============================================

def run_phase2_doc(approved_outline: str, topic: str, provider: str = None,
                   api_key: str = None, auto_review: bool = True) -> dict:
    """
    Chay Phase 2: Research (dựa trên outline) -> Viet Doc chi tiet -> Auto-Review Doc.
    Doc danh cho nguoi thuyet trinh voi nguon tham khao ro rang.
    """
    review_logs = []

    try:
        # Tao agents
        researcher = create_researcher(provider=provider, api_key=api_key)
        writer = create_speaker_doc_writer(provider=provider, api_key=api_key)
        doc_reviewer_agent = create_doc_reviewer(provider=provider, api_key=api_key)

        # Step 1: Research chi tiet dua tren outline
        review_logs.append("🔍 Bat dau nghien cuu chi tiet dua tren outline...")
        research_task = create_research_task(researcher, topic, outline=approved_outline)
        research_crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True,
        )
        research_result = str(research_crew.kickoff())
        review_logs.append("✅ Hoan thanh nghien cuu")

        # Step 2: Viet doc chi tiet cho nguoi thuyet trinh
        review_logs.append("✍️ Bat dau viet tai lieu chi tiet cho nguoi thuyet trinh...")
        doc_task = create_doc_task(writer, approved_outline, research_result, topic)
        doc_crew = Crew(
            agents=[writer],
            tasks=[doc_task],
            process=Process.sequential,
            verbose=True,
        )
        doc_result = doc_crew.kickoff()
        current_doc = str(doc_result)
        review_logs.append("✅ Hoan thanh viet tai lieu")

        # Step 3: Auto-review doc loop
        final_review_result = ""
        if not auto_review:
            review_logs.append("⏸️ Bo qua auto-review doc vi dang dung human review mode")
        else:
            for iteration in range(MAX_REVIEW_ITERATIONS):
                review_logs.append(f"🔄 Review doc - lan {iteration + 1}")

                review_task = create_doc_review_task(doc_reviewer_agent, current_doc, topic)
                review_crew = Crew(
                    agents=[doc_reviewer_agent],
                    tasks=[review_task],
                    process=Process.sequential,
                    verbose=True,
                )
                review_result = str(review_crew.kickoff())
                final_review_result = review_result
                review_logs.append(f"📝 Ket qua review doc (lan {iteration + 1}):\n{review_result}")

                if _is_approved(review_result):
                    review_logs.append(f"✅ Doc DAT o lan review {iteration + 1}")
                    break
                else:
                    review_logs.append(f"⚠️ Doc CAN SUA o lan review {iteration + 1}")
                    feedback = _extract_review_feedback(review_result)
                    revise_task = create_revise_doc_task(writer, current_doc, feedback, topic)
                    revise_crew = Crew(
                        agents=[writer],
                        tasks=[revise_task],
                        process=Process.sequential,
                        verbose=True,
                    )
                    revise_result = revise_crew.kickoff()
                    current_doc = str(revise_result)
                    review_logs.append(f"✅ Da sua doc theo feedback (lan {iteration + 1})")
            else:
                review_logs.append(f"ℹ️ Da het so lan review toi da ({MAX_REVIEW_ITERATIONS}), su dung doc hien tai")

        return {
            "research_result": research_result,
            "doc_content": current_doc,
            "review_result": final_review_result,
            "review_logs": review_logs,
            "error": None,
        }

    except Exception as e:
        return {
            "research_result": None,
            "doc_content": None,
            "review_result": None,
            "review_logs": review_logs,
            "error": f"Loi Phase 2: {e}",
        }


# ============================================
# Phase 3: Generate Slide & Review (with auto-review)
# ============================================

def run_phase3(approved_outline: str, approved_doc: str, theme_name: str, provider: str = None,
               api_key: str = None, auto_review: bool = True) -> dict:
    """
    Chay Phase 3: Slide Design -> Auto-Review -> Auto-Revise neu can -> Generate PPTX.
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
            review_logs.append("⚠️ Khong parse duoc slide JSON tu designer, dung outline goc")

        final_review_result = ""
        if not auto_review:
            review_logs.append("⏸️ Bo qua auto-review slide vi dang dung human review mode")
        else:
            for iteration in range(MAX_REVIEW_ITERATIONS):
                review_logs.append(f"🔄 Review slide - lan {iteration + 1}")

                review_task = create_review_task(slide_reviewer, current_slide_json)
                review_crew = Crew(
                    agents=[slide_reviewer],
                    tasks=[review_task],
                    process=Process.sequential,
                    verbose=True,
                )
                review_result = str(review_crew.kickoff())
                final_review_result = review_result
                review_logs.append(f"📝 Ket qua review slide (lan {iteration + 1}):\n{review_result}")

                if _is_approved(review_result):
                    review_logs.append(f"✅ Slide DAT o lan review {iteration + 1}")
                    break
                else:
                    review_logs.append(f"⚠️ Slide CAN SUA o lan review {iteration + 1}")
                    feedback = _extract_review_feedback(review_result)
                    revise_task = create_slide_task(
                        designer, approved_outline, theme_name,
                        doc_content=approved_doc,
                        additional_instructions=f"""
                        LUU Y: Slide truoc do da bi review yeu cau sua. Hay cai thien theo feedback sau:
                        {feedback}

                        Hay dam bao output JSON duoc cai thien theo cac diem tren.
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
                        review_logs.append(f"✅ Da sua slide theo feedback (lan {iteration + 1})")
                    except (json.JSONDecodeError, ValueError):
                        review_logs.append(f"⚠️ Loi parse revised slide JSON, giu nguyen slide cu")
            else:
                review_logs.append(f"ℹ️ Da het so lan review toi da ({MAX_REVIEW_ITERATIONS}), su dung slide hien tai")

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
            "error": f"Loi Phase 3: {e}",
        }


# ============================================
# revise_outline_with_human_feedback
# ============================================

def revise_outline_with_human_feedback(current_outline: str, feedback: str, topic: str,
                                        provider: str = None, api_key: str = None) -> dict:
    """Chinh sua outline dua tren gop y cua nguoi dung."""
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
        result = revise_crew.kickoff()
        outline_raw = str(result)

        outline = validate_outline_json(outline_raw)
        outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
        review_logs.append("✅ Da cap nhat outline theo gop y cua nguoi dung")

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
            "error": f"Loi sua outline theo gop y: {e}",
        }


# ============================================
# Full Pipeline: Chay toan bo tu dong
# ============================================

def run_full_pipeline(topic: str, theme_name: str = "corporate", num_slides: int = 10,
                      provider: str = None, api_key: str = None, auto_review: bool = True,
                      user_outline: str = None) -> dict:
    """
    Chay toan bo pipeline tu dong.
    Neu co user_outline -> skip Phase 1, dung outline san.
    Nguoc lai -> Tao outline tu topic.
    Research -> Viet Doc -> Slide -> PPTX.
    """
    all_review_logs = []
    all_errors = []

    # Phase 1: Tao Outline hoac dung user outline
    if user_outline:
        phase1 = use_user_outline(user_outline)
        all_review_logs.append("📋 Su dung outline do nguoi dung cung cap")
    else:
        phase1 = run_phase1(
            topic=topic, provider=provider, api_key=api_key,
            num_slides=num_slides, auto_review=auto_review,
        )
    all_review_logs.extend(phase1.get("review_logs", []))

    if phase1["error"]:
        all_errors.append(phase1["error"])
        return {
            "phase": "outline",
            "outline_json": None,
            "outline_display": None,
            "doc_content": None,
            "slide_json": None,
            "review_result": None,
            "filepath": None,
            "review_logs": all_review_logs,
            "errors": all_errors,
        }

    # Phase 2: Research + Viet Doc
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
