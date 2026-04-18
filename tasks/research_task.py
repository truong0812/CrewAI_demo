"""
Research Task - Nhiệm vụ nghiên cứu chủ đề.
"""

from crewai import Task


def create_research_task(agent, topic: str) -> Task:
    """Tạo task nghiên cứu chủ đề."""
    return Task(
        description=f"""
        Nghiên cứu chủ đề sau một cách toàn diện và chi tiết: "{topic}"
        
        Yêu cầu:
        1. Tìm hiểu các khía cạnh chính của chủ đề
        2. Thu thập thông tin quan trọng, số liệu, ví dụ thực tế
        3. Xác định các điểm then chốt cần đưa vào bài thuyết trình
        4. Tổ chức thông tin theo thứ tự logic:
           - Giới thiệu / Tổng quan
           - Các nội dung chính (3-7 phần)
           - Kết luận / Tóm tắt
        5. Mỗi phần cần có thông tin chi tiết đủ để tạo slide
        
        Chủ đề: {topic}
        
        Hãy nghiên cứu sâu và trình bày kết quả một cách có cấu trúc rõ ràng bằng tiếng Việt.
        """,
        agent=agent,
        expected_output="Một báo cáo nghiên cứu chi tiết bằng tiếng Việt, có cấu trúc rõ ràng với các phần: Giới thiệu, Nội dung chính (3-7 phần), Kết luận. Mỗi phần có thông tin cụ thể, ví dụ và số liệu (nếu có).",
    )