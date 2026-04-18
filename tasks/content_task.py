"""
Content Tasks - Nhiệm vụ tạo outline và chỉnh sửa outline từ góp ý.
"""

from crewai import Task


def create_content_task(agent, research_result: str, topic: str, num_slides: int = 10) -> Task:
    """Tạo task thiết kế outline slide từ kết quả nghiên cứu."""
    return Task(
        description=f"""
        Dựa trên kết quả nghiên cứu dưới đây, hãy tạo outline chi tiết cho bài thuyết trình về: "{topic}"
        
        === KẾT QUẢ NGHIÊN CỨU ===
        {research_result}
        === HẾT KẾT QUẢ NGHIÊN CỨU ===
        
        Yêu cầu về outline:
        1. Số lượng slide: {num_slides} slide (có thể linh hoạt ±2)
        2. Slide đầu tiên phải là slide tiêu đề (type: "title")
        3. Slide cuối cùng phải là slide tóm tắt/cảm ơn (type: "summary")
        4. Các slide ở giữa là slide nội dung (type: "content")
        5. Mỗi slide nội dung có tối đa 5-6 bullet points
        6. Tiêu đề slide phải ngắn gọn (< 50 ký tự)
        7. Mỗi bullet point phải súc tích (< 100 ký tự)
        8. Thêm speaker notes cho mỗi slide để hướng dẫn người thuyết trình
        
        QUAN TRỌNG - Xuất kết quả theo ĐÚNG JSON format sau:
        ```json
        {{
            "presentation_title": "Tiêu đề bài thuyết trình",
            "slides": [
                {{
                    "type": "title",
                    "title": "Tiêu đề chính",
                    "subtitle": "Phụ đề hoặc mô tả ngắn",
                    "notes": "Hướng dẫn cho người thuyết trình"
                }},
                {{
                    "type": "content",
                    "title": "Tiêu đề slide nội dung",
                    "bullet_points": [
                        "Điểm chính 1",
                        "Điểm chính 2",
                        "Điểm chính 3"
                    ],
                    "notes": "Speaker notes chi tiết"
                }},
                {{
                    "type": "summary",
                    "title": "Tóm tắt & Cảm ơn",
                    "bullet_points": [
                        "Tóm tắt điểm 1",
                        "Tóm tắt điểm 2"
                    ]
                }}
            ]
        }}
        ```
        
        Toàn bộ nội dung phải bằng tiếng Việt. Chỉ xuất JSON, không thêm giải thích.
        """,
        agent=agent,
        expected_output='JSON string theo đúng format yêu cầu, chứa presentation_title và danh sách slides. Mỗi slide có type, title, bullet_points (với content/summary), notes. Toàn bộ tiếng Việt.',
    )


def create_revise_content_task(agent, current_outline: str, feedback: str, topic: str) -> Task:
    """Tạo task chỉnh sửa outline dựa trên góp ý của người dùng."""
    return Task(
        description=f"""
        Bạn cần chỉnh sửa outline bài thuyết trình về "{topic}" dựa trên góp ý của người dùng.
        
        === OUTLINE HIỆN TẠI ===
        {current_outline}
        === HẾT OUTLINE HIỆN TẠI ===
        
        === GÓP Ý CỦA NGƯỜI DÙNG ===
        {feedback}
        === HẾT GÓP Ý ===
        
        Yêu cầu:
        1. Giữ nguyên JSON format như outline hiện tại
        2. Áp dụng các thay đổi theo góp ý của người dùng
        3. Đảm bảo vẫn tuân thủ nguyên tắc: mỗi slide 1 ý chính, tối đa 5-6 bullet points
        4. Giữ nguyên slide tiêu đề (type: "title") và slide cuối (type: "summary") nếu không cần sửa
        5. Đảm bảo luồng thông tin vẫn logic sau khi chỉnh sửa
        
        QUAN TRỌNG - Xuất kết quả theo ĐÚNG JSON format:
        ```json
        {{
            "presentation_title": "Tiêu đề bài thuyết trình",
            "slides": [
                {{
                    "type": "title",
                    "title": "Tiêu đề chính",
                    "subtitle": "Phụ đề",
                    "notes": "Hướng dẫn cho người thuyết trình"
                }},
                {{
                    "type": "content",
                    "title": "Tiêu đề slide",
                    "bullet_points": ["Điểm 1", "Điểm 2"],
                    "notes": "Speaker notes"
                }},
                {{
                    "type": "summary",
                    "title": "Tóm tắt & Cảm ơn",
                    "bullet_points": ["Tóm tắt 1"]
                }}
            ]
        }}
        ```
        
        Toàn bộ nội dung phải bằng tiếng Việt. Chỉ xuất JSON, không thêm giải thích.
        """,
        agent=agent,
        expected_output='JSON string đã chỉnh sửa theo đúng format yêu cầu, áp dụng các góp ý của người dùng. Toàn bộ tiếng Việt.',
    )