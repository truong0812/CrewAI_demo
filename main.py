"""
CLI Entry Point - Chạy tạo slide từ command line (fallback khi không dùng Streamlit).
Toàn bộ pipeline tự động: Research → Outline → Doc → Slide → PPTX
Human chỉ xem sản phẩm cuối.
Usage: python main.py "Chủ đề slide của bạn"
"""

import os
import sys
import argparse

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import THEMES, suggest_theme, get_llm_config
from crew import run_full_pipeline, format_outline_display


def print_separator(char="=", length=60):
    print(char * length)


def print_header(title: str):
    print_separator()
    print(f"  {title}")
    print_separator()


def print_step(step: str, message: str):
    print(f"\n{step} {message}")
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="🎨 Tạo Slide Thuyết trình bằng AI (CrewAI) - Tự động toàn bộ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python main.py "Giới thiệu Machine Learning"
  python main.py "Chuyển đổi số cho SME" --slides 12 --theme technical
  python main.py "AI trong y tế" --provider anthropic --api-key sk-ant-xxx

Themes: corporate, creative, academic, technical, nature
Providers: openai, anthropic, gemini, ollama

Workflow tự động:
  1. Nghiên cứu chủ đề
  2. Tạo & Auto-Review Outline (Agent tự sửa nếu cần)
  3. Viết & Auto-Review Tài liệu (Agent tự sửa nếu cần)
  4. Tạo & Auto-Review Slide (Agent tự sửa nếu cần)
  5. Generate PowerPoint
  6. Human xem sản phẩm cuối (Doc + Slide JSON + PPTX)
        """,
    )
    parser.add_argument("topic", help="Chủ đề thuyết trình")
    parser.add_argument("--slides", type=int, default=10, help="Số lượng slide (mặc định: 10)")
    parser.add_argument("--theme", default=None, help="Tên theme (mặc định: tự động)")
    parser.add_argument("--provider", default=None, help="LLM provider")
    parser.add_argument("--api-key", default=None, help="API key")
    parser.add_argument("--output", default=None, help="Tên file output")

    args = parser.parse_args()

    topic = args.topic
    num_slides = args.slides
    theme_name = args.theme or suggest_theme(topic)
    provider = args.provider
    api_key = args.api_key

    # Hiển thị thông tin
    print_header("🎨 TẠO SLIDE THUYẾT TRÌNH BẰNG AI (TỰ ĐỘNG)")
    print(f"  Chủ đề: {topic}")
    print(f"  Số slide: {num_slides}")
    print(f"  Theme: {theme_name} - {THEMES[theme_name]['name']}")
    llm_config = get_llm_config(provider)
    print(f"  LLM: {llm_config['provider']} / {llm_config['model']}")
    print_separator()
    print("\n⏳ Bắt đầu pipeline tự động...")
    print("   Agent sẽ tự động: Research → Outline → Review → Doc → Review → Slide → Review → PPTX")

    # ============================================
    # Run Full Pipeline (tự động)
    # ============================================
    result = run_full_pipeline(
        topic=topic,
        theme_name=theme_name,
        num_slides=num_slides,
        provider=provider,
        api_key=api_key,
    )

    # ============================================
    # Hiển thị Review Logs
    # ============================================
    review_logs = result.get("review_logs", [])
    if review_logs:
        print_step("🔍", "QUÁ TRÌNH AUTO-REVIEW")
        for log in review_logs:
            print(f"  {log}")

    # ============================================
    # Kiểm tra kết quả
    # ============================================
    errors = result.get("errors", [])
    if errors:
        print_step("⚠️", "CẢNH BÁO")
        for err in errors:
            print(f"  ❌ {err}")

    if result["phase"] != "done":
        print(f"\n❌ Pipeline thất bại ở giai đoạn: {result['phase']}")

        # Hiển thị những gì đã tạo được
        if result.get("outline_display"):
            print_step("📋", "OUTLINE ĐÃ TẠO (bước cuối đạt được):")
            print(result["outline_display"])

        if result.get("doc_content"):
            print_step("📄", "TÀI LIỆU ĐÃ TẠO (bước cuối đạt được):")
            print_separator("-")
            print(result["doc_content"][:500] + "..." if len(result.get("doc_content", "")) > 500 else result.get("doc_content", ""))

        sys.exit(1)

    # ============================================
    # Kết quả thành công
    # ============================================
    print_header("✅ HOÀN THÀNH!")

    # Hiển thị outline
    if result.get("outline_display"):
        print_step("📋", "OUTLINE:")
        print(result["outline_display"])

    # Hiển thị tài liệu
    if result.get("doc_content"):
        print_step("📄", "TÀI LIỆU CHI TIẾT:")
        print_separator("-")
        print(result["doc_content"])
        print_separator("-")

    # Hiển thị đánh giá
    if result.get("review_result"):
        print_step("📝", "ĐÁNH GIÁ CHẤT LƯỢNG SLIDE:")
        print(result["review_result"])

    # File output
    print_separator()
    print(f"  📄 File tài liệu: {result.get('doc_filepath')}")
    print(f"  🧩 File slide JSON: {result.get('slide_filepath')}")
    print(f"  📁 File PowerPoint: {result['filepath']}")
    print(f"  📊 Theme: {theme_name}")
    print(f"  📋 Tổng số review loops: {len([l for l in review_logs if l.startswith('🔄')])}")
    print_separator()

    print(f"\n🎉 Bộ sản phẩm cuối đã được lưu trong thư mục output.")
    print("💡 Bạn có thể dùng tài liệu Markdown để duyệt nội dung, slide JSON để tích hợp tiếp, và PowerPoint để trình chiếu.")


if __name__ == "__main__":
    main()
