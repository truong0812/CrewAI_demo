"""
Researcher Agent - Nghiên cứu và thu thập thông tin về chủ đề.
"""

from crewai import Agent, LLM
from config import get_llm_config


def create_researcher(provider: str = None, api_key: str = None) -> Agent:
    """Tạo Researcher Agent."""
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
        role="Chuyên gia Nghiên cứu Nội dung",
        goal="Nghiên cứu sâu và thu thập thông tin toàn diện về chủ đề được yêu cầu để tạo bài thuyết trình chất lượng cao",
        backstory="""Bạn là một chuyên gia nghiên cứu nội dung dày dặn kinh nghiệm với khả năng 
        phân tích và tổng hợp thông tin từ nhiều nguồn. Bạn có kỹ năng đặc biệt trong việc:
        - Xác định các khía cạnh quan trọng của bất kỳ chủ đề nào
        - Tìm kiếm và tổ chức thông tin một cách logic
        - Đánh giá độ tin cậy và mức độ liên quan của thông tin
        - Trình bày thông tin phức tạp một cách dễ hiểu
        Bạn luôn đảm bảo thông tin được nghiên cứu đầy đủ, chính xác và có cấu trúc rõ ràng.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )