"""
CLI Entry Point - Chay tao slide tu command line (fallback khi khong dung Streamlit).
Pipeline tu dong: Outline -> Research -> Speaker Doc -> Slide -> PPTX
Co the cung cap outline san qua --outline.
Usage: python main.py "Chu de slide cua ban"
       python main.py "Chu de" --outline outline.json
"""

import os
import sys
import argparse
import json

# Them project root vao path
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
        description="🎨 Tao Slide Thuyet trinh bang AI (CrewAI) - Tu dong toan bo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python main.py "Gioi thieu Machine Learning"
  python main.py "Chuyen doi so cho SME" --slides 12 --theme technical
  python main.py "AI trong y te" --provider anthropic --api-key sk-ant-xxx
  python main.py "AI trong giao duc" --outline my_outline.json

Themes: corporate, creative, academic, technical, nature
Providers: openai, anthropic, gemini, ollama

Workflow tu dong:
  1. Tao Outline (hoac dung outline san tu --outline)
  2. Auto-Review Outline (Agent tu sua neu can)
  3. Research chi tiet dua tren outline
  4. Writer agent viet speaker doc chi tiet cho nguoi thuyet trinh (voi nguon tham khao)
  5. Auto-Review Doc
  6. Tao & Auto-Review Slide
  7. Generate PowerPoint
        """,
    )
    parser.add_argument("topic", help="Chu de thuyet trinh")
    parser.add_argument("--slides", type=int, default=10, help="So luong slide (mac dinh: 10)")
    parser.add_argument("--theme", default=None, help="Ten theme (mac dinh: tu dong)")
    parser.add_argument("--provider", default=None, help="LLM provider")
    parser.add_argument("--api-key", default=None, help="API key")
    parser.add_argument("--outline", default=None, help="Duong dan den file outline (JSON hoac text/markdown) de skip buoc tao outline")
    parser.add_argument("--output", default=None, help="Ten file output")

    args = parser.parse_args()

    topic = args.topic
    num_slides = args.slides
    theme_name = args.theme or suggest_theme(topic)
    provider = args.provider
    api_key = args.api_key

    # Doc outline tu file neu co
    user_outline = None
    if args.outline:
        try:
            with open(args.outline, "r", encoding="utf-8") as f:
                user_outline = f.read()
            print(f"📋 Da doc outline tu file: {args.outline}")
        except Exception as e:
            print(f"❌ Khong the doc file outline: {e}")
            sys.exit(1)

    # Hien thi thong tin
    print_header("🎨 TAO SLIDE THUYET TRINH BANG AI (TU DONG)")
    print(f"  Chu de: {topic}")
    print(f"  So slide: {num_slides}")
    print(f"  Theme: {theme_name} - {THEMES[theme_name]['name']}")
    llm_config = get_llm_config(provider)
    print(f"  LLM: {llm_config['provider']} / {llm_config['model']}")
    if user_outline:
        print(f"  Outline: Su dung outline san tu {args.outline}")
    else:
        print(f"  Outline: AI tu tao")
    print_separator()
    print("\n⏳ Bat dau pipeline tu dong...")
    if user_outline:
        print("   Agent se tu dong: Validate Outline -> Research -> Viet Doc -> Review -> Slide -> Review -> PPTX")
    else:
        print("   Agent se tu dong: Outline -> Review -> Research -> Viet Doc -> Review -> Slide -> Review -> PPTX")

    # ============================================
    # Run Full Pipeline (tu dong)
    # ============================================
    result = run_full_pipeline(
        topic=topic,
        theme_name=theme_name,
        num_slides=num_slides,
        provider=provider,
        api_key=api_key,
        user_outline=user_outline,
    )

    # ============================================
    # Hien thi Review Logs
    # ============================================
    review_logs = result.get("review_logs", [])
    if review_logs:
        print_step("🔍", "QUA TRINH AUTO-REVIEW")
        for log in review_logs:
            print(f"  {log}")

    # ============================================
    # Kiem tra ket qua
    # ============================================
    errors = result.get("errors", [])
    if errors:
        print_step("⚠️", "CANH BAO")
        for err in errors:
            print(f"  ❌ {err}")

    if result["phase"] != "done":
        print(f"\n❌ Pipeline that bai o giai doan: {result['phase']}")

        # Hien thi nhung gi da tao duoc
        if result.get("outline_display"):
            print_step("📋", "OUTLINE DA TAO (buoc cuoi dat duoc):")
            print(result["outline_display"])

        if result.get("doc_content"):
            print_step("📄", "TAI LIEU DA TAO (buoc cuoi dat duoc):")
            print_separator("-")
            print(result["doc_content"][:500] + "..." if len(result.get("doc_content", "")) > 500 else result.get("doc_content", ""))

        sys.exit(1)

    # ============================================
    # Ket qua thanh cong
    # ============================================
    print_header("✅ HOAN THANH!")

    # Hien thi outline
    if result.get("outline_display"):
        print_step("📋", "OUTLINE:")
        print(result["outline_display"])

    # Hien thi tai lieu
    if result.get("doc_content"):
        print_step("📄", "TAI LIEU CHI TIET CHO NGUOI THUYET TRINH:")
        print_separator("-")
        print(result["doc_content"])
        print_separator("-")

    # Hien thi danh gia
    if result.get("review_result"):
        print_step("📝", "DANH GIA CHAT LUONG SLIDE:")
        print(result["review_result"])

    # File output
    print_separator()
    print(f"  📄 File tai lieu: {result.get('doc_filepath')}")
    print(f"  🧩 File slide JSON: {result.get('slide_filepath')}")
    print(f"  📁 File PowerPoint: {result['filepath']}")
    print(f"  📊 Theme: {theme_name}")
    print(f"  📋 Tong so review loops: {len([l for l in review_logs if l.startswith('🔄')])}")
    print_separator()

    print(f"\n🎉 Bo san pham cuoi da duoc luu trong thu muc output.")
    print("💡 Ban co the dung tai lieu Markdown de duyet noi dung, slide JSON de tich hop tiep, va PowerPoint de trinh chieu.")


if __name__ == "__main__":
    main()
