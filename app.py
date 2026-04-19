"""
Streamlit Web UI - Giao dien tao slide AI.
Workflow: Input -> Outline -> Research -> Speaker Doc -> Slide -> PPTX
"""

import os
import sys

import streamlit as st

# Them project root vao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import THEMES, suggest_theme, get_llm_config, LLM_PROVIDERS
from crew import (
    run_phase1,
    run_phase2_doc,
    run_phase3,
    revise_outline_with_human_feedback,
    use_user_outline,
    _save_final_assets,
)


st.set_page_config(
    page_title="Tao Slide AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles():
    """CSS nhe de giao dien ro rang hon."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        .app-hero {
            padding: 1.25rem 1.5rem;
            border: 1px solid rgba(49, 51, 63, 0.15);
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(14, 116, 144, 0.08), rgba(245, 158, 11, 0.08));
            margin-bottom: 1rem;
        }
        .app-hero h1 {
            margin: 0 0 0.4rem 0;
            font-size: 2rem;
        }
        .app-hero p {
            margin: 0;
            color: #475569;
        }
        .metric-card {
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            background: rgba(255,255,255,0.7);
        }
        .section-card {
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 18px;
            padding: 1rem 1rem 0.75rem 1rem;
            background: rgba(255,255,255,0.72);
            margin-bottom: 1rem;
        }
        .muted {
            color: #64748b;
            font-size: 0.95rem;
        }
        .small-gap {
            margin-top: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state():
    """Khoi tao session state."""
    defaults = {
        "phase": "input",
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
        "user_outline": "",
        "zai_base_url": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_app():
    """Reset toan bo state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def render_hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="app-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(items):
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="muted">{label}</div>
                    <div><strong>{value}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def phase_label(phase: str) -> str:
    mapping = {
        "input": "Nhap yeu cau",
        "processing": "Dang xu ly",
        "review_outline": "Duyet outline",
        "done": "Hoan thanh",
        "error": "Co loi",
    }
    return mapping.get(phase, phase)


def render_sidebar():
    """Sidebar cau hinh."""
    with st.sidebar:
        st.title("Dieu khien")
        st.caption("Chinh cau hinh truoc khi chay pipeline.")

        st.subheader("LLM")
        provider = st.selectbox(
            "Provider",
            options=list(LLM_PROVIDERS.keys()),
            index=list(LLM_PROVIDERS.keys()).index(st.session_state.provider),
            key="provider_select",
        )
        st.session_state.provider = provider

        llm_config = get_llm_config(provider)
        st.info(f"Model dang dung: `{llm_config['model']}`")

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
            zai_base_url = st.text_input(
                "Base URL (Z AI)",
                value=st.session_state.get("zai_base_url", "") or default_base_url,
                key="zai_base_url_input",
            )
            if zai_base_url:
                os.environ[base_url_env] = zai_base_url
                st.session_state.zai_base_url = zai_base_url
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

        st.subheader("Review")
        review_mode = st.radio(
            "Che do",
            options=["agent", "human"],
            format_func=lambda v: "Agent review tu dong" if v == "agent" else "Human duyet outline truoc",
            index=0 if st.session_state.review_mode == "agent" else 1,
            help="Human mode se dung lai sau buoc outline de ban xem va chinh sua truoc khi research.",
        )
        st.session_state.review_mode = review_mode

        st.divider()

        st.subheader("Theme")
        suggested = suggest_theme(st.session_state.topic) if st.session_state.topic else "corporate"
        theme_options = list(THEMES.keys())
        theme_labels = [f"{THEMES[t]['name']} - {THEMES[t]['description']}" for t in theme_options]
        current_theme = st.session_state.theme_name if st.session_state.phase != "input" else suggested
        selected_idx = st.selectbox(
            "Chon style slide",
            options=range(len(theme_options)),
            format_func=lambda i: theme_labels[i],
            index=theme_options.index(current_theme if current_theme in theme_options else "corporate"),
            key="theme_select",
        )
        st.session_state.theme_name = theme_options[selected_idx]

        theme = THEMES[st.session_state.theme_name]
        cols = st.columns(4)
        color_labels = ["BG", "Title", "Text", "Accent"]
        color_keys = ["bg_color", "title_color", "text_color", "accent_color"]
        for col, label, key in zip(cols, color_labels, color_keys):
            with col:
                st.color_picker(label, f"#{theme[key]}", disabled=True, key=f"color_{key}")

        st.divider()

        st.subheader("So luong slide")
        st.session_state.num_slides = st.slider(
            "Target slides",
            min_value=5,
            max_value=20,
            value=st.session_state.num_slides,
            key="num_slides_slider",
        )

        st.divider()

        st.subheader("Trang thai")
        st.caption(f"Pha hien tai: {phase_label(st.session_state.phase)}")
        if st.session_state.phase == "input":
            st.success("San sang nhan de bai.")
        elif st.session_state.phase == "processing":
            st.warning("Pipeline dang chay.")
        elif st.session_state.phase == "review_outline":
            st.info("Dang cho ban duyet outline.")
        elif st.session_state.phase == "done":
            st.success("Da tao xong bo san pham.")
        elif st.session_state.phase == "error":
            st.error("Can xu ly loi.")

        st.divider()
        if st.button("Bat dau lai", use_container_width=True):
            reset_app()


def render_input_phase():
    """Trang nhap yeu cau."""
    render_hero(
        "Tao Slide Thuyet Trinh Bang AI",
        "Workflow moi: tao outline truoc, sau do research, viet speaker doc co nguon ro rang, roi moi tao slide va PowerPoint.",
    )

    render_metric_cards(
        [
            ("Workflow", "Outline -> Research -> Speaker Doc"),
            ("Review mode", "Agent" if st.session_state.review_mode == "agent" else "Human"),
            ("Theme", THEMES[st.session_state.theme_name]["name"]),
        ]
    )

    left, right = st.columns([1.35, 1], gap="large")

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("1. Chu de bai thuyet trinh")
        st.caption("Nhap mot chu de ro rang. He thong se suy ra theme va tao outline phu hop.")
        topic = st.text_input(
            "Chu de",
            value=st.session_state.topic,
            placeholder="Vi du: Chuyen doi so cho doanh nghiep vua va nho",
            key="topic_input",
        )
        st.session_state.topic = topic

        st.markdown('<div class="small-gap"></div>', unsafe_allow_html=True)
        st.subheader("2. Outline co san (tuy chon)")
        st.caption("Ban co the bo qua de AI tao outline, hoac dan outline san o dang JSON hay text/markdown.")
        user_outline = st.text_area(
            "Outline dau vao",
            value=st.session_state.user_outline,
            height=250,
            placeholder="""Vi du JSON:
{
  "presentation_title": "Tieu de bai thuyet trinh",
  "slides": [
    {"type": "title", "title": "Tieu de chinh", "subtitle": "Phu de"},
    {"type": "content", "title": "Hien trang", "bullet_points": ["Diem 1", "Diem 2"]},
    {"type": "summary", "title": "Tom tat", "bullet_points": ["Y chinh"]}
  ]
}

Hoac dang text:
# Tieu de bai thuyet trinh
## Mo dau
- Y chinh 1
- Y chinh 2
## Hien trang
- Y chinh 1
- Y chinh 2
## Ket luan
- Tom tat""",
            key="user_outline_input",
        )
        st.session_state.user_outline = user_outline

        if st.button("Bat dau tao", type="primary", use_container_width=True, disabled=not topic.strip()):
            st.session_state.phase = "processing"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Tom tat workflow")
        if st.session_state.user_outline.strip():
            st.success("Outline san duoc uu tien. He thong se chuan hoa outline truoc khi research.")
            workflow_items = [
                "Validate/chuan hoa outline dau vao",
                "Research chi tiet theo tung slide",
                "Writer agent viet speaker doc co nguon",
                "Tao slide + review",
                "Xuat PowerPoint",
            ]
        else:
            st.info("Khong co outline san. Agent se tao outline truoc.")
            workflow_items = [
                "Tao outline tu chu de",
                "Review outline",
                "Research chi tiet theo outline da duyet",
                "Writer agent viet speaker doc co nguon",
                "Tao slide + review + xuat PowerPoint",
            ]
        for idx, item in enumerate(workflow_items, start=1):
            st.markdown(f"**{idx}.** {item}")

        st.markdown("---")
        st.subheader("Cach dung tot nhat")
        st.markdown(
            """
            - Dung `human review` neu ban muon duyet outline truoc khi di xa hon.
            - Outline san nen ngan gon, tap trung vao ten slide va y chinh.
            - Speaker doc se chi tiet va co nguon, phu hop cho nguoi thuyet trinh.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)


def render_processing_phase():
    """Trang xu ly."""
    render_hero(
        "Pipeline Dang Chay",
        f"Chu de: {st.session_state.topic} | Theme: {THEMES[st.session_state.theme_name]['name']}",
    )

    progress = st.progress(0, text="Dang khoi tao...")
    user_outline = st.session_state.user_outline.strip()
    auto_review = st.session_state.review_mode == "agent"

    if st.session_state.review_mode == "human":
        if user_outline:
            progress.progress(30, text="Dang validate outline san...")
            result = use_user_outline(user_outline)
            if result["error"]:
                st.session_state.errors = [result["error"]]
                st.session_state.failed_phase = "outline"
                st.session_state.phase = "error"
                st.rerun()
            st.session_state.outline_json = result["outline_json"]
            st.session_state.outline_display = result["outline_display"]
            st.session_state.review_logs = result.get("review_logs", [])
            st.session_state.phase = "review_outline"
            st.rerun()

        progress.progress(20, text="Dang tao outline...")
        phase1 = run_phase1(
            topic=st.session_state.topic,
            provider=st.session_state.provider,
            api_key=st.session_state.api_key if st.session_state.api_key else None,
            num_slides=st.session_state.num_slides,
            auto_review=False,
        )
        st.session_state.review_logs = phase1.get("review_logs", [])

        if phase1["error"]:
            st.session_state.errors = [phase1["error"]]
            st.session_state.failed_phase = "outline"
            st.session_state.phase = "error"
            st.rerun()

        st.session_state.outline_json = phase1["outline_json"]
        st.session_state.outline_display = phase1["outline_display"]
        st.session_state.phase = "review_outline"
        st.rerun()

    progress.progress(10, text="Dang khoi tao pipeline...")

    if user_outline:
        progress.progress(20, text="Dang validate outline san...")
        phase1 = use_user_outline(user_outline)
    else:
        progress.progress(20, text="Dang tao outline...")
        phase1 = run_phase1(
            topic=st.session_state.topic,
            provider=st.session_state.provider,
            api_key=st.session_state.api_key if st.session_state.api_key else None,
            num_slides=st.session_state.num_slides,
            auto_review=auto_review,
        )

    st.session_state.review_logs = phase1.get("review_logs", [])

    if phase1["error"]:
        st.session_state.errors = [phase1["error"]]
        st.session_state.failed_phase = "outline"
        st.session_state.phase = "error"
        st.rerun()

    st.session_state.outline_json = phase1["outline_json"]
    st.session_state.outline_display = phase1["outline_display"]

    progress.progress(45, text="Dang research va viet speaker doc...")
    phase2 = run_phase2_doc(
        approved_outline=phase1["outline_json"],
        topic=st.session_state.topic,
        provider=st.session_state.provider,
        api_key=st.session_state.api_key if st.session_state.api_key else None,
        auto_review=auto_review,
    )
    st.session_state.review_logs.extend(phase2.get("review_logs", []))

    if phase2["error"]:
        st.session_state.errors = [phase2["error"]]
        st.session_state.failed_phase = "doc"
        st.session_state.phase = "error"
        st.rerun()

    progress.progress(75, text="Dang tao slide va PowerPoint...")
    phase3 = run_phase3(
        approved_outline=phase1["outline_json"],
        approved_doc=phase2["doc_content"],
        theme_name=st.session_state.theme_name,
        provider=st.session_state.provider,
        api_key=st.session_state.api_key if st.session_state.api_key else None,
        auto_review=auto_review,
    )
    st.session_state.review_logs.extend(phase3.get("review_logs", []))

    if phase3["error"]:
        st.session_state.doc_content = phase2["doc_content"]
        st.session_state.errors = [phase3["error"]]
        st.session_state.failed_phase = "slide"
        st.session_state.phase = "error"
        st.rerun()

    progress.progress(90, text="Dang luu san pham...")
    asset_paths = _save_final_assets(
        topic=st.session_state.topic,
        doc_content=phase2["doc_content"],
        slide_json=phase3["slide_json"],
        pptx_filepath=phase3["filepath"],
    )

    st.session_state.doc_content = phase2["doc_content"]
    st.session_state.slide_json = phase3["slide_json"]
    st.session_state.review_result = phase3["review_result"]
    st.session_state.filepath = phase3["filepath"]
    st.session_state.doc_filepath = asset_paths["doc_filepath"]
    st.session_state.slide_filepath = asset_paths["slide_filepath"]
    st.session_state.phase = "done"

    progress.progress(100, text="Hoan thanh!")
    st.rerun()


def render_review_outline_phase():
    """Trang duyet outline."""
    render_hero(
        "Duyet Outline",
        "Ban co the chap nhan outline hien tai, chinh sua bang feedback, hoac quay lai de doi de bai.",
    )

    render_metric_cards(
        [
            ("Chu de", st.session_state.topic or "-"),
            ("Theme", THEMES[st.session_state.theme_name]["name"]),
            ("Review mode", "Human"),
        ]
    )

    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Outline da tao")
        if st.session_state.outline_display:
            st.text(st.session_state.outline_display)
        else:
            st.info("Chua co outline.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Feedback cho outline")
        feedback = st.text_area(
            "Nhap gop y neu muon sua",
            value=st.session_state.human_outline_feedback,
            height=220,
            placeholder="Vi du: Them slide ve xu huong tuong lai, rut gon phan mo dau, tach phan case study thanh 2 slide...",
            key="outline_feedback_input",
        )
        st.session_state.human_outline_feedback = feedback

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Chap nhan & tiep tuc", type="primary", use_container_width=True):
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

                asset_paths = _save_final_assets(
                    topic=st.session_state.topic,
                    doc_content=phase2["doc_content"],
                    slide_json=phase3["slide_json"],
                    pptx_filepath=phase3["filepath"],
                )
                st.session_state.doc_content = phase2["doc_content"]
                st.session_state.slide_json = phase3["slide_json"]
                st.session_state.review_result = phase3["review_result"]
                st.session_state.filepath = phase3["filepath"]
                st.session_state.doc_filepath = asset_paths["doc_filepath"]
                st.session_state.slide_filepath = asset_paths["slide_filepath"]
                st.session_state.phase = "done"
                st.rerun()

        with col2:
            if st.button("Sua outline", use_container_width=True):
                if feedback.strip():
                    result = revise_outline_with_human_feedback(
                        current_outline=st.session_state.outline_json,
                        feedback=feedback,
                        topic=st.session_state.topic,
                        provider=st.session_state.provider,
                        api_key=st.session_state.api_key if st.session_state.api_key else None,
                    )
                    if result["error"]:
                        st.error(f"Loi sua outline: {result['error']}")
                    else:
                        st.session_state.outline_json = result["outline_json"]
                        st.session_state.outline_display = result["outline_display"]
                        st.session_state.review_logs.extend(result.get("review_logs", []))
                        st.session_state.human_outline_feedback = ""
                        st.success("Da cap nhat outline.")
                        st.rerun()
                else:
                    st.warning("Vui long nhap feedback truoc khi sua.")

        with col3:
            if st.button("Quay lai", use_container_width=True):
                reset_app()
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Xem outline JSON"):
            if st.session_state.outline_json:
                st.code(st.session_state.outline_json, language="json")


def render_review_logs(logs):
    """Hien thi logs co nhom mau."""
    if not logs:
        st.info("Chua co review log.")
        return

    for idx, log in enumerate(logs, start=1):
        label = f"Log {idx}"
        if "DAT" in log.upper():
            st.success(log)
        elif "CAN SUA" in log.upper() or "Loi" in log:
            st.warning(log)
        elif "Review" in log or "review" in log:
            with st.expander(label, expanded=False):
                st.text(log)
        else:
            st.markdown(log)


def render_done_phase():
    """Trang ket qua."""
    render_hero(
        "Bo San Pham Da San Sang",
        "Ban co the tai xuong PowerPoint, xem speaker doc, slide JSON va log review trong cung mot man hinh.",
    )

    render_metric_cards(
        [
            ("Chu de", st.session_state.topic or "-"),
            ("Theme", THEMES[st.session_state.theme_name]["name"]),
            ("Review logs", str(len(st.session_state.get("review_logs", [])))),
            ("Trang thai", "Done"),
        ]
    )

    col1, col2, col3 = st.columns(3)

    doc_filepath = st.session_state.get("doc_filepath")
    if doc_filepath and os.path.exists(doc_filepath):
        with open(doc_filepath, "rb") as f:
            doc_data = f.read()
        with col1:
            st.download_button(
                label="Tai speaker doc",
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
                label="Tai slide JSON",
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
                label="Tai PowerPoint",
                data=file_data,
                file_name=os.path.basename(filepath),
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
    else:
        with col3:
            st.warning("Khong tim thay file PowerPoint.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Speaker Doc", "Slide JSON", "Danh gia slide", "Review logs"]
    )

    with tab1:
        if st.session_state.doc_content:
            st.markdown(st.session_state.doc_content)
        else:
            st.info("Khong co speaker doc.")

    with tab2:
        if st.session_state.get("slide_json"):
            st.code(st.session_state.get("slide_json", "{}"), language="json")
        else:
            st.info("Khong co slide JSON.")

    with tab3:
        if st.session_state.review_result:
            st.text(st.session_state.review_result)
        else:
            st.info("Khong co ket qua review slide.")

    with tab4:
        render_review_logs(st.session_state.get("review_logs", []))

    st.markdown("---")
    if st.button("Tao de bai moi", use_container_width=True):
        reset_app()


def render_error_phase():
    """Trang loi."""
    render_hero(
        "Pipeline Gap Loi",
        "He thong dung lai o mot pha trong workflow. Ban co the xem log, san pham tam thoi va thu lai.",
    )

    failed_phase = st.session_state.get("failed_phase", "unknown")
    phase_names = {
        "outline": "Tao/validate outline",
        "doc": "Research + speaker doc",
        "slide": "Tao slide",
    }
    st.error(f"Loi o giai doan: {phase_names.get(failed_phase, failed_phase)}")

    for err in st.session_state.errors:
        st.error(err)

    left, right = st.columns([1.1, 1], gap="large")

    with left:
        if st.session_state.outline_display:
            with st.expander("Outline da tao", expanded=True):
                st.text(st.session_state.outline_display)

        if st.session_state.doc_content:
            with st.expander("Speaker doc tam thoi"):
                st.markdown(st.session_state.doc_content)

    with right:
        with st.expander("Review logs", expanded=True):
            render_review_logs(st.session_state.get("review_logs", []))

        st.subheader("Goi y khac phuc")
        st.markdown(
            """
            1. Kiem tra API key va provider dang chon.
            2. Thu doi review mode neu ban muon kiem soat outline thu cong.
            3. Rut gon chu de neu de bai qua rong.
            4. Thu lai sau va cap nhat feedback neu can.
            """
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Thu lai", use_container_width=True):
            st.session_state.errors = []
            st.session_state.phase = "processing"
            st.rerun()
    with col2:
        if st.button("Bat dau lai", use_container_width=True):
            reset_app()


def main():
    inject_styles()
    init_session_state()
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
