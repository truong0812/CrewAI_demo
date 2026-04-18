"""
Slide Designer Agent - Tạo file PowerPoint từ outline đã approve.
"""

from crewai import Agent, LLM
from config import get_llm_config


def create_slide_designer(provider: str = None, api_key: str = None) -> Agent:
    """Tạo Slide Designer Agent."""
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
        role="Chuyên gia Thiết kế Slide PowerPoint",
        goal="Chuyển đổi outline nội dung thành file PowerPoint chuyên nghiệp với format và theme phù hợp",
        backstory="""Bạn là chuyên gia thiết kế PowerPoint với nhiều năm kinh nghiệm tạo các bài thuyết trình 
        chuyên nghiệp. Bạn có khả năng:
        - Chuyển đổi nội dung text thành JSON structure chuẩn xác
        - Xác định đúng type cho mỗi slide (title, content, summary)
        - Tổ chức bullet points rõ ràng, súc tích
        - Thêm speaker notes hữu ích cho người thuyết trình
        - Đảm bảo format nhất quán trên tất cả slide
        
        QUAN TRỌNG: Bạn phải xuất kết quả theo đúng JSON format sau:
        {
            "presentation_title": "Tiêu đề bài thuyết trình",
            "slides": [
                {
                    "type": "title",
                    "title": "Tiêu đề chính",
                    "subtitle": "Phụ đề hoặc mô tả ngắn",
                    "notes": "Lời khuyên cho người thuyết trình"
                },
                {
                    "type": "content",
                    "title": "Tiêu đề slide",
                    "bullet_points": ["Điểm 1", "Điểm 2"],
                    "notes": "Speaker notes"
                },
                {
                    "type": "summary",
                    "title": "Tóm tắt / Cảm ơn",
                    "bullet_points": ["Tóm tắt 1"]
                }
            ]
        }
        Bạn phản hồi bằng tiếng Việt.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )