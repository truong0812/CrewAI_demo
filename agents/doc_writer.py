"""
Doc Writer Agent - Viết tài liệu chi tiết (Markdown) từ outline đã duyệt.
"""

from crewai import Agent, LLM
from config import get_llm_config


def create_doc_writer(provider: str = None, api_key: str = None) -> Agent:
    """Tạo Doc Writer Agent."""
    llm_config = get_llm_config(provider)

    llm_kwargs = {"model": llm_config["model"]}
    if api_key:
        llm_kwargs["api_key"] = api_key
    elif "api_key" in llm_config and llm_config["api_key"]:
        llm_kwargs["api_key"] = llm_config["api_key"]
    if "base_url" in llm_config:
        llm_kwargs["base_url"] = llm_config["base_url"]

    llm = LLM(**llm_kwargs)

    return Agent(
        role="Chuyên gia Viết Tài liệu Thuyết trình",
        goal="Viết tài liệu chi tiết bằng Markdown từ outline slide, đảm bảo nội dung phong phú, chính xác và sẵn sàng để tạo slide PowerPoint",
        backstory="""Bạn là một chuyên gia viết tài liệu thuyết trình với hơn 10 năm kinh nghiệm.
        Bạn có khả năng đặc biệt trong việc:
        - Mở rộng outline thành tài liệu chi tiết, đầy đủ nội dung
        - Viết nội dung rõ ràng, mạch lạc, dễ hiểu
        - Bổ sung ví dụ thực tế, số liệu, và giải thích chi tiết
        - Tổ chức thông tin theo cấu trúc Markdown dễ đọc
        - Đảm bảo mỗi phần có đủ thông tin để tạo slide chất lượng cao
        - Viết speaker notes chi tiết hướng dẫn người thuyết trình
        
        Bạn luôn tuân thủ nguyên tắc:
        - Nội dung phải phong phú nhưng súc tích
        - Mỗi mục tương ứng với một slide trong outline
        - Có bullet points rõ ràng và giải thích chi tiết
        - Bổ sung ví dụ, case study khi cần thiết
        Bạn phản hồi bằng tiếng Việt.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )