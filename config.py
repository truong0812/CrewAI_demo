"""
Cấu hình hệ thống - Hỗ trợ nhiều LLM provider, có thể chỉnh sửa lúc runtime.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================
# LLM Provider Configuration
# ============================================
LLM_PROVIDERS = {
    "openai": {
        "model_env": "OPENAI_MODEL_NAME",
        "default_model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "model_env": "ANTHROPIC_MODEL_NAME",
        "default_model": "claude-sonnet-4-20250514",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "gemini": {
        "model_env": "GEMINI_MODEL_NAME",
        "default_model": "gemini/gemini-2.0-flash",
        "api_key_env": "GEMINI_API_KEY",
    },
    "ollama": {
        "model_env": "OLLAMA_MODEL_NAME",
        "default_model": "ollama/llama3",
        "base_url_env": "OLLAMA_BASE_URL",
        "default_base_url": "http://localhost:11434",
    },
    "groq": {
        "model_env": "GROQ_MODEL_NAME",
        "default_model": "groq/llama-3.3-70b-versatile",
        "api_key_env": "GROQ_API_KEY",
    },
    "z_ai": {
        "model_env": "ZAI_MODEL_NAME",
        "default_model": "openai/glm-5",
        "api_key_env": "ZAI_API_KEY",
        "base_url_env": "ZAI_BASE_URL",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4/",
    },
}


def get_llm_config(provider: str = None) -> dict:
    """Lấy cấu hình LLM dựa trên provider."""
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider not in LLM_PROVIDERS:
        raise ValueError(
            f"Provider '{provider}' không được hỗ trợ. "
            f"Các provider có sẵn: {list(LLM_PROVIDERS.keys())}"
        )

    config = LLM_PROVIDERS[provider]
    model = os.getenv(config["model_env"], config["default_model"])

    result = {"model": model, "provider": provider}

    if "api_key_env" in config:
        api_key = os.getenv(config["api_key_env"], "")
        result["api_key"] = api_key

    if "base_url_env" in config:
        base_url = os.getenv(config["base_url_env"], config.get("default_base_url", ""))
        result["base_url"] = base_url

    return result


def build_llm_string(provider: str = None, model_override: str = None) -> str:
    """
    Tạo chuỗi LLM cho CrewAI.
    Ví dụ: 'openai/gpt-4o', 'anthropic/claude-sonnet-4-20250514'
    """
    config = get_llm_config(provider)
    if model_override:
        return model_override
    return config["model"]


# ============================================
# Slide Themes
# ============================================
THEMES = {
    "corporate": {
        "name": "Doanh nghiệp",
        "description": "Trang trọng, chuyên nghiệp - phù hợp báo cáo kinh doanh",
        "bg_color": "FFFFFF",
        "title_color": "1B3A5C",
        "text_color": "333333",
        "accent_color": "2E86AB",
    },
    "creative": {
        "name": "Sáng tạo",
        "description": "Màu sắc tươi sáng, hiện đại - phù hợp thuyết trình sáng tạo",
        "bg_color": "F8F9FA",
        "title_color": "6C3483",
        "text_color": "2C3E50",
        "accent_color": "E74C3C",
    },
    "academic": {
        "name": "Học thuật",
        "description": "Tối giản, rõ ràng - phù hợp bài giảng, nghiên cứu",
        "bg_color": "FFFFFF",
        "title_color": "1A5276",
        "text_color": "333333",
        "accent_color": "2E86C1",
    },
    "technical": {
        "name": "Công nghệ",
        "description": "Tone tối, hiện đại - phù hợp demo kỹ thuật",
        "bg_color": "2C3E50",
        "title_color": "ECF0F1",
        "text_color": "BDC3C7",
        "accent_color": "3498DB",
    },
    "nature": {
        "name": "Thiên nhiên",
        "description": "Tone xanh lá, nhẹ nhàng - phù hợp môi trường, sức khỏe",
        "bg_color": "F0FFF0",
        "title_color": "2E7D32",
        "text_color": "333333",
        "accent_color": "4CAF50",
    },
}


def get_theme(theme_name: str) -> dict:
    """Lấy cấu hình theme theo tên."""
    if theme_name not in THEMES:
        return THEMES["corporate"]
    return THEMES[theme_name]


def suggest_theme(topic: str) -> str:
    """
    Gợi ý theme dựa trên chủ đề (đơn giản - dùng keyword matching).
    """
    topic_lower = topic.lower()

    corporate_keywords = [
        "kinh doanh", "doanh nghiệp", "báo cáo", "chiến lược",
        "marketing", "tài chính", "quản lý", "business", "startup",
    ]
    creative_keywords = [
        "sáng tạo", "thiết kế", "nghệ thuật", "creative", "design",
        "thương hiệu", "brand",
    ]
    academic_keywords = [
        "giáo dục", "nghiên cứu", "học tập", "đại học", "khoa học",
        "academic", "research", "luận án", "luận văn",
    ]
    technical_keywords = [
        "công nghệ", "lập trình", "ai", "machine learning", "deep learning",
        "software", "programming", "api", "cloud", "devops", "blockchain",
        "technical", "dữ liệu", "data",
    ]
    nature_keywords = [
        "môi trường", "sinh học", "sức khỏe", "y tế", "thiên nhiên",
        "nature", "health", "green", "biología",
    ]

    for kw in technical_keywords:
        if kw in topic_lower:
            return "technical"
    for kw in corporate_keywords:
        if kw in topic_lower:
            return "corporate"
    for kw in academic_keywords:
        if kw in topic_lower:
            return "academic"
    for kw in creative_keywords:
        if kw in topic_lower:
            return "creative"
    for kw in nature_keywords:
        if kw in topic_lower:
            return "nature"

    return "corporate"