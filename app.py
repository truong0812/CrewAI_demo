"""
Streamlit Web UI - Giao diện tương tác với hệ thống tạo Slide AI.
Workflow: Input → Auto Pipeline (Research → Outline → Doc → Slide → PPTX) → Done
Human chỉ tương tác với sản phẩm cuối (Doc + Slide + PPTX).
Chạy: streamlit run app.py
"""

import os
import sys
import json

import streamlit as st

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import THEMES, suggest_theme, get_llm_config, LLM_PROVIDERS
from crew import (
    run_full_pipeline,
    run_phase1,
    run_phase2_doc,
    run_phase3,
    revise_outline_with_human_feedback,
    _save_final_assets,
    format_outline_display,
)


# ============================================
# Page Config
# ============================================
st.set_page_config(
    page_title="🎨 Tạo Slide AI",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# Session State Init
# ============================================
def init_session_state():
    """Khởi tạo session state variables."""
    defaults = {
        "phase": "input",  # input -> processing -> done -> error
        "topic": "",
        "theme_name": "corporate",
        "num_slides": 10,
        "provider": "openai",
        "api_key": "",
        "review_mode": "agent",
        "doc_content": None,
        "slide_json": None,
        "outline_display": None,
        "outline_json": None,
        "review_result": None,
        "filepath": None,
        "doc_filepath": None,
        "slide_filepath": None,
        "research_result": None,
        "failed_phase": None,
        "human_outline_feedback": "",
        "review_logs": [],
        "errors": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# ============================================
# Sidebar - Cấu hình
# ============================================
def render_sidebar():
    """Render sidebar với cấu hình LLM và theme."""
    with st.sidebar:
        st.title("⚙️ Cấu hình")

        # --- LLM Provider ---
        st.subheader("🤖 LLM Provider")
        provider = st.selectbox(
            "Chọn Provider",
            options=list(LLM_PROVIDERS.keys()),
            index=list(LLM_PROVIDERS.keys()).index(st.session_state.provider),
            key="provider_select",
            help="Chọn nhà cung cấp LLM",
        )
        st.session_state.provider = provider

        # Hiển thị model tương ứng
        llm_config = get_llm_config(provider)
        st.info(f"📌 Model: `{llm_config['model']}`")

        # API Key input
        api_key_label = f"API Key ({provider.upper()})"
        if provider == "ollama":
            api_key = st.text_input(
                "Base URL (Ollama)",
                value=st.session_state.get("api_key", "") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                key="api_key_input",
            )
        elif provider == "z_ai":
            env_key = LLM_PROVIDERS[provider].get("api_key_env", "")
            default_key = os.getenv(env_key, "")
            api_key = st.text_input(
                api_key_label,
                value=st.session_state.get("api_key", "") or default_key,
                type="password",
                key="api_key_input",
            )
            base_url_env = LLM_PROVIDERS[provider].get("base_url_env", "")
            default_base_url = os.getenv(base_url_env, LLM_PROVIDERS[provider].get("default_base_url", ""))
            st.text_input(
                "Base URL (Z AI)",
                value=st.session_state.get("zai_base_url", "") or default_base_url,
                key="zai_base_url_input",
            )
        else:
            env_key = LLM_PROVIDERS[provider].get("api_key_env", "")
            default_key = os.getenv(env_key, "")
            api_key = st.text_input(
                api_key_label,
                value=st.session_state.get("api_key", "") or default_key,
                type="password",
                key="api_key_input",
            )
        st.session_state.api_key = api_key

        st.divider()

        st.subheader("🧭 Review Mode")
        review_mode = st.radio(
            "Chọn chế độ review",
            options=["agent", "human"],
            format_func=lambda v: "Agent review tự động" if v == "agent" else "Human review trước Phase 2",
            index=0 if st.session_state.review_mode == "agent" else 1,
            help="Human review mode sẽ dừng sau outline để bạn duyệt trước khi tạo tài liệu và slide.",
        )
        st.session_state.review_mode = review_mode

        st.divider()

        # --- Slide Style ---
        st.subheader("🎨 Slide Style")
        suggested = suggest_theme(st.session_state.topic) if st.session_state.topic else "corporate"

        theme_options = list(THEMES.keys())
        theme_labels = [f"{THEMES[t]['name']} - {THEMES[t]['description']}" for t in theme_options]

        suggested_idx = theme_options.index(suggested) if suggested in theme_options else 0

        selected_idx = st.selectbox(
            "Chọn Theme",
            options=range(len(theme_options)),
            format_func=lambda i: theme_labels[i],
            index=suggested_idx if st.session_state.phase == "input" else theme_options.index(st.session_state.theme_name),
            key="theme_select",
        )
        st.session_state.theme_name = theme_options[selected_idx]

        # Preview theme colors
        theme = THEMES[st.session_state.theme_name]
        cols = st.columns(4)
        color_labels = ["Background", "Title", "Text", "Accent"]
        color_keys = ["bg_color", "title_color", "text_color", "accent_color"]
        for i, (label, key) in enumerate(zip(color_labels, color_keys)):
            with cols[i]:
                hex_color = theme[key]
                st.color_picker(label, f"#{hex_color}", disabled=True, key=f"color_{key}")

        st.divider()

        # --- Số lượng slide ---
        st.subheader("📊 Số lượng Slide")
        num_slides = st.slider(
            "Số slide",
            min_value=5,
            max_value=20,
            value=st.session_state.num_slides,
            key="num_slides_slider",
        )
        st.session_state.num_slides = num_slides

        st.divider()

        # --- Workflow Progress ---
        st.subheader("📊 Tiến trình")
        phase = st.session_state.phase
        if phase == "input":
            st.info("💡 Nhập chủ đề và nhấn **Bắt đầu tạo**")
        elif phase == "processing":
            st.warning("⏳ Đang xử lý tự động...")
        elif phase == "review_outline":
            st.info("👀 Đang chờ bạn duyệt outline")
        elif phase == "done":
            st.success("✅ Hoàn thành!")
        elif phase == "error":
            st.error("❌ Có lỗi xảy ra")

        st.divider()

        # --- Reset ---
        if st.button("🔄 Bắt đầu lại", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ============================================
# Main Content - Các Phase
# ============================================

def render_input_phase():
    """Phase: Nhập topic và bắt đầu."""
    st.title("🎨 Tạo Slide Thuyết trình bằng AI")
    st.markdown("---")

    st.markdown("### 📝 Nhập chủ đề thuyết trình")
    st.markdown("Mô tả chủ đề bạn muốn tạo slide. Hệ thống sẽ **tự động** nghiên cứu, tạo outline, viết tài liệu, review chất lượng và tạo file PowerPoint.")

    topic = st.text_area(
        "Chủ đề thuyết trình",
        placeholder="Ví dụ: Giới thiệu về Machine Learning và ứng dụng trong kinh doanh\n\nHoặc chi tiết hơn: Bài thuyết trình về chuyển đổi số cho doanh nghiệp SME, bao gồm các bước triển khai, công cụ cần thiết và case study thực tế",
        height=150,
        key="topic_input",
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🚀 Bắt đầu tạo", type="primary", use_container_width=True, disabled=not topic.strip()):
            if topic.strip():
                st.session_state.topic = topic.strip()
                st.session_state.phase = "processing"
                st.rerun()

    # Hiển thị hướng dẫn
    with st.expander("💡 Hướng dẫn sử dụng"):
        st.markdown("""
        ### Workflow tự động:
        1. **Nhập chủ đề** - Mô tả chủ đề slide bạn muốn tạo
        2. **Cấu hình** (sidebar) - Chọn LLM provider, API key, theme
        3. **Tự động xử lý** - Hệ thống sẽ tự động:
           - 🔍 Nghiên cứu chủ đề
           - 📋 Tạo & review outline (Agent tự review, tự sửa nếu cần)
           - 📝 Viết & review tài liệu chi tiết (Agent tự review, tự sửa nếu cần)
           - 🎨 Tạo & review slide JSON (Agent tự review, tự sửa nếu cần)
           - 📊 Generate file PowerPoint
        4. **Nhận sản phẩm** - Xem tài liệu, slide JSON và tải PowerPoint

        **Mẹo:** Chủ đề càng chi tiết, slide càng chính xác!
        
        **Lưu ý:** Toàn bộ quá trình review được thực hiện bởi AI Agent.
        Bạn chỉ làm việc với bộ sản phẩm cuối cùng: tài liệu, slide JSON và file trình chiếu.
        """)


def render_processing_phase():
    """Phase: Đang xử lý tự động toàn bộ pipeline."""
    st.title("⏳ Đang xử lý tự động...")
    st.markdown(f"**Chủ đề:** {st.session_state.topic}")
    st.markdown(f"**Theme:** {THEMES[st.session_state.theme_name]['name']}")
    st.markdown("---")

    # Progress steps
    steps = [
        "🔍 Đang nghiên cứu chủ đề...",
        "📋 Đang tạo & review outline...",
        "📝 Đang viết & review tài liệu chi tiết...",
        "🎨 Đang tạo & review slide...",
        "📊 Đang generate file PowerPoint...",
    ]

    progress_bar = st.progress(0, text=steps[0])

    with st.spinner("🤖 Các Agent đang làm việc tự động... Quá trình này có thể mất 5-15 phút tùy thuộc vào chủ đề."):
        if st.session_state.review_mode == "human":
            result = run_phase1(
                topic=st.session_state.topic,
                num_slides=st.session_state.num_slides,
                provider=st.session_state.provider,
                api_key=st.session_state.api_key if st.session_state.api_key else None,
                auto_review=False,
            )
        else:
            result = run_full_pipeline(
                topic=st.session_state.topic,
                theme_name=st.session_state.theme_name,
                num_slides=st.session_state.num_slides,
                provider=st.session_state.provider,
                api_key=st.session_state.api_key if st.session_state.api_key else None,
                auto_review=True,
            )

    progress_bar.progress(100, text="✅ Hoàn thành!")

    # Lưu kết quả vào session state
    st.session_state.review_logs = result.get("review_logs", [])
    st.session_state.errors = result.get("errors", [])

    if st.session_state.review_mode == "human":
        if result["error"] is None:
            st.session_state.research_result = result.get("research_result")
            st.session_state.outline_json = result.get("outline_json")
            st.session_state.outline_display = result.get("outline_display")
            st.session_state.phase = "review_outline"
        else:
            st.session_state.failed_phase = "research"
            st.session_state.phase = "error"
    elif result["phase"] == "done":
        st.session_state.outline_display = result.get("outline_display")
        st.session_state.outline_json = result.get("outline_json")
        st.session_state.doc_content = result.get("doc_content")
        st.session_state.review_result = result.get("review_result")
        st.session_state.slide_json = result.get("slide_json")
        st.session_state.filepath = result.get("filepath")
        st.session_state.doc_filepath = result.get("doc_filepath")
        st.session_state.slide_filepath = result.get("slide_filepath")
        st.session_state.phase = "done"
    else:
        # Có lỗi ở một phase nào đó
        st.session_state.outline_display = result.get("outline_display")
        st.session_state.doc_content = result.get("doc_content")
        st.session_state.failed_phase = result["phase"]
        st.session_state.phase = "error"

    st.rerun()


def render_review_outline_phase():
    """Phase: Human review outline trước khi tạo doc và slide."""
    st.title("👀 Duyệt Outline Trước Phase 2")
    st.markdown(f"**Chủ đề:** {st.session_state.topic}")
    st.markdown("Chế độ này giúp giảm số lần gọi model ở Phase 2 và Phase 3 bằng cách để bạn duyệt outline trước.")
    st.markdown("---")

    if st.session_state.get("outline_display"):
        st.subheader("📋 Outline hiện tại")
        st.text(st.session_state.outline_display)
    else:
        st.warning("⚠️ Không có outline để duyệt")

    with st.expander("🔧 Xem outline JSON", expanded=False):
        st.code(st.session_state.get("outline_json", "{}"), language="json")

    st.markdown("---")
    st.subheader("💬 Góp ý cho outline")
    feedback = st.text_area(
        "Nhập góp ý để agent sửa outline",
        value=st.session_state.get("human_outline_feedback", ""),
        placeholder="Ví dụ: thêm 1 slide về rủi ro triển khai, rút gọn phần mở đầu, đổi thứ tự case study lên trước phần kết luận...",
        height=140,
        key="human_outline_feedback_input",
    )
    st.session_state.human_outline_feedback = feedback

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🛠️ Sửa outline theo góp ý", use_container_width=True, disabled=not feedback.strip()):
            with st.spinner("🤖 Đang cập nhật outline theo góp ý của bạn..."):
                revised = revise_outline_with_human_feedback(
                    current_outline=st.session_state.outline_json,
                    topic=st.session_state.topic,
                    feedback=feedback.strip(),
                    provider=st.session_state.provider,
                    api_key=st.session_state.api_key if st.session_state.api_key else None,
                )

                st.session_state.review_logs.extend(revised.get("review_logs", []))

                if revised["error"]:
                    st.session_state.errors = [revised["error"]]
                    st.session_state.failed_phase = "research"
                    st.session_state.phase = "error"
                    st.rerun()

                st.session_state.outline_json = revised["outline_json"]
                st.session_state.outline_display = revised["outline_display"]
                st.session_state.human_outline_feedback = ""
                st.rerun()

    with col2:
        if st.button("✅ Duyệt outline và tạo sản phẩm cuối", type="primary", use_container_width=True):
            with st.spinner("🤖 Đang tạo tài liệu, slide và PowerPoint từ outline đã duyệt..."):
                phase2 = run_phase2_doc(
                    approved_outline=st.session_state.outline_json,
                    topic=st.session_state.topic,
                    provider=st.session_state.provider,
                    api_key=st.session_state.api_key if st.session_state.api_key else None,
                    auto_review=False,
                )

                st.session_state.review_logs.extend(phase2.get("review_logs", []))

                if phase2["error"]:
                    st.session_state.errors = [phase2["error"]]
                    st.session_state.failed_phase = "doc"
                    st.session_state.phase = "error"
                    st.rerun()

                phase3 = run_phase3(
                    approved_outline=st.session_state.outline_json,
                    approved_doc=phase2["doc_content"],
                    theme_name=st.session_state.theme_name,
                    provider=st.session_state.provider,
                    api_key=st.session_state.api_key if st.session_state.api_key else None,
                    auto_review=False,
                )

                st.session_state.review_logs.extend(phase3.get("review_logs", []))

                if phase3["error"]:
                    st.session_state.doc_content = phase2["doc_content"]
                    st.session_state.errors = [phase3["error"]]
                    st.session_state.failed_phase = "slide"
                    st.session_state.phase = "error"
                    st.rerun()

                result = {
                    "phase": "done",
                    "outline_display": st.session_state.outline_display,
                    "outline_json": st.session_state.outline_json,
                    "doc_content": phase2["doc_content"],
                    "slide_json": phase3["slide_json"],
                    "review_result": phase3["review_result"],
                    "filepath": phase3["filepath"],
                }

                asset_paths = _save_final_assets(
                    topic=st.session_state.topic,
                    doc_content=phase2["doc_content"],
                    slide_json=phase3["slide_json"],
                    pptx_filepath=phase3["filepath"],
                )

                st.session_state.doc_content = result["doc_content"]
                st.session_state.slide_json = result["slide_json"]
                st.session_state.review_result = result["review_result"]
                st.session_state.filepath = result["filepath"]
                st.session_state.doc_filepath = asset_paths["doc_filepath"]
                st.session_state.slide_filepath = asset_paths["slide_filepath"]
                st.session_state.phase = "done"
                st.rerun()

    with col3:
        if st.button("🔄 Quay lại nhập chủ đề", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def render_done_phase():
    """Phase: Hoàn thành - Hiển thị bộ sản phẩm cuối cho người dùng."""
    st.title("✅ Hoàn thành!")
    st.markdown(f"**Chủ đề:** {st.session_state.topic}")
    st.markdown(f"**Theme:** {THEMES[st.session_state.theme_name]['name']}")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    doc_filepath = st.session_state.get("doc_filepath")
    if doc_filepath and os.path.exists(doc_filepath):
        with open(doc_filepath, "rb") as f:
            doc_data = f.read()
        with col1:
            st.download_button(
                label="📥 Download Doc",
                data=doc_data,
                file_name=os.path.basename(doc_filepath),
                mime="text/markdown",
                use_container_width=True,
            )

    slide_filepath = st.session_state.get("slide_filepath")
    if slide_filepath and os.path.exists(slide_filepath):
        with open(slide_filepath, "rb") as f:
            slide_data = f.read()
        with col2:
            st.download_button(
                label="📥 Download Slide JSON",
                data=slide_data,
                file_name=os.path.basename(slide_filepath),
                mime="application/json",
                use_container_width=True,
            )

    filepath = st.session_state.filepath
    if filepath and os.path.exists(filepath):
        with open(filepath, "rb") as f:
            file_data = f.read()
        with col3:
            st.download_button(
                label="📥 Download PowerPoint",
                data=file_data,
                file_name=os.path.basename(filepath),
                mime="application/vnd.openxmlformats-offencedocument.presentationml.presentation",
                use_container_width=True,
            )
    else:
        st.warning("⚠️ Không tìm thấy file PowerPoint")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Tài liệu Chi tiết",
        "🧩 Slide JSON",
        "📝 Đánh giá chất lượng",
        "🔍 Review Logs",
    ])

    with tab1:
        st.subheader("📖 Tài liệu chi tiết")
        if st.session_state.doc_content:
            st.markdown(st.session_state.doc_content)

        else:
            st.info("Không có tài liệu")

    with tab2:
        st.subheader("🧩 Slide JSON cuối cùng")
        if st.session_state.get("slide_json"):
            st.code(st.session_state.get("slide_json", "{}"), language="json")
        else:
            st.info("Không có slide JSON")

    with tab3:
        st.subheader("📝 Đánh giá chất lượng Slide")
        if st.session_state.review_result:
            st.text(st.session_state.review_result)
        else:
            st.info("Không có đánh giá")

    with tab4:
        st.subheader("🔍 Chi tiết quá trình Auto-Review")
        st.markdown("Dưới đây là log chi tiết các vòng auto-review mà Agent đã thực hiện:")
        for log in st.session_state.get("review_logs", []):
            if log.startswith("✅"):
                st.success(log)
            elif log.startswith("⚠️"):
                st.warning(log)
            elif log.startswith("🔄"):
                st.info(log)
            elif log.startswith("📝"):
                with st.expander("📋 Chi tiết review", expanded=False):
                    st.text(log.replace(f"📝 Kết quả review", "Kết quả review"))
            else:
                st.markdown(log)

    # Nút bắt đầu lại
    st.markdown("---")
    if st.button("🔄 Tạo slide mới", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def render_error_phase():
    """Phase: Lỗi."""
    st.title("❌ Có lỗi xảy ra")
    st.markdown(f"**Chủ đề:** {st.session_state.topic}")
    st.markdown("---")

    failed_phase = st.session_state.get("failed_phase", "unknown")
    phase_names = {
        "research": "Nghiên cứu (Phase 1)",
        "doc": "Tạo tài liệu (Phase 2)",
        "slide": "Tạo slide (Phase 3)",
    }
    st.error(f"⚠️ Lỗi ở giai đoạn: **{phase_names.get(failed_phase, failed_phase)}**")

    for err in st.session_state.errors:
        st.error(f"⚠️ {err}")

    # Hiển thị review logs nếu có
    if st.session_state.get("review_logs"):
        with st.expander("🔍 Review Logs"):
            for log in st.session_state.review_logs:
                st.markdown(log)

    # Hiển thị sản phẩm đã tạo được (nếu có)
    if st.session_state.doc_content:
        with st.expander("📄 Tài liệu đã tạo (có thể xem)"):
            st.markdown(st.session_state.doc_content)

    if st.session_state.outline_display:
        with st.expander("📋 Outline đã tạo"):
            st.text(st.session_state.outline_display)

    st.markdown("### 💡 Gợi ý khắc phục:")
    st.markdown("""
    1. **Kiểm tra API Key** - Đảm bảo API key đúng và còn hạn
    2. **Kiểm tra Provider** - Đảm bảo chọn đúng LLM provider
    3. **Thử lại** - Đôi khi LLM trả về lỗi tạm thời
    4. **Đơn giản hóa chủ đề** - Thử chủ đề ngắn gọn hơn
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Thử lại", use_container_width=True):
            st.session_state.errors = []
            st.session_state.phase = "processing"
            st.rerun()

    with col2:
        if st.button("🏠 Bắt đầu lại", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ============================================
# Main Render
# ============================================
def main():
    render_sidebar()

    phase = st.session_state.phase

    if phase == "input":
        render_input_phase()
    elif phase == "processing":
        render_processing_phase()
    elif phase == "review_outline":
        render_review_outline_phase()
    elif phase == "done":
        render_done_phase()
    elif phase == "error":
        render_error_phase()
    else:
        render_input_phase()


if __name__ == "__main__":
    main()
