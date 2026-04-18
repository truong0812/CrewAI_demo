"""
Content Strategist Agent - Thiết kế cấu trúc và nội dung slide.
"""

from crewai import Agent, LLM
from config import get_llm_config


def create_content_strategist(provider: str = None, api_key: str = None) -> Agent:
    """Tạo Content Strategist Agent."""
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
        role="Chuyên gia Chiến lược Nội dung Thuyết trình",
        goal="Tổ chức nội dung thành cấu trúc slide logic, hấp dẫn và dễ hiểu, đảm bảo truyền tải thông điệp hiệu quả",
        backstory="""Bạn là một chuyên gia thiết kế nội dung thuyết trình hàng đầu với hơn 15 năm kinh nghiệm.
        Bạn có khả năng đặc biệt trong việc:
        - Tổ chức thông tin phức tạp thành cấu trúc slide rõ ràng, logic
        - Xác định số lượng slide phù hợp (thường 8-15 slide cho một bài thuyết trình)
        - Viết tiêu đề ngắn gọn, thu hút
        - Tạo bullet points súc tích, dễ đọc
        - Đảm bảo luồng thông tin liền mạch giữa các slide
        - Thêm speaker notes chi tiết cho người thuyết trình
        Bạn luôn tuân thủ nguyên tắc: mỗi slide chỉ chứa 1 ý chính, tối đa 5-6 bullet points.
        Bạn phản hồi bằng tiếng Việt.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )