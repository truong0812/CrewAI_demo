"""
Doc Tasks - Nhiệm vụ tạo tài liệu chi tiết và chỉnh sửa từ góp ý.
"""

from crewai import Task


def create_doc_task(agent, approved_outline: str, topic: str) -> Task:
    """Tạo task viết tài liệu chi tiết (Markdown) từ outline đã duyệt."""
    return Task(
        description=f"""
        Dựa trên outline bài thuyết trình đã được duyệt dưới đây, hãy viết một tài liệu chi tiết bằng Markdown.

        === OUTLINE ĐÃ DUYỆT ===
        {approved_outline}
        === HẾT OUTLINE ===

        Chủ đề: "{topic}"

        Yêu cầu về tài liệu:
        1. Mỗi slide trong outline tương ứng với một phần (## heading) trong tài liệu
        2. Mỗi phần phải có:
           - Nội dung chi tiết, giải thích rõ ràng các bullet points trong outline
           - Ví dụ thực tế, số liệu, case study (nếu phù hợp)
           - Bullet points súc tích (tối đa 5-6 điểm) để đưa lên slide
           - Speaker notes chi tiết hướng dẫn người thuyết trình
        3. Giữ nguyên cấu trúc: slide tiêu đề → các slide nội dung → slide tóm tắt
        4. Ngôn ngữ tiếng Việt, văn phong chuyên nghiệp

        Định dạng Markdown yêu cầu:
        ```markdown
        # [Tiêu đề bài thuyết trình]

        ## Slide 1: [Tiêu đề slide]
        **Loại:** title
        **Nội dung chi tiết:**
        [Mô tả chi tiết về nội dung slide này]

        **Bullet points cho slide:**
        - Điểm chính 1
        - Điểm chính 2

        **Speaker notes:**
        [Hướng dẫn chi tiết cho người thuyết trình]

        ---

        ## Slide 2: [Tiêu đề slide]
        **Loại:** content
        **Nội dung chi tiết:**
        [Giải thích chi tiết từng bullet point, bổ sung ví dụ và số liệu]

        **Bullet points cho slide:**
        - Điểm chính 1
        - Điểm chính 2

        **Speaker notes:**
        [Hướng dẫn chi tiết cho người thuyết trình]

        ---
        ... (tiếp tục cho tất cả slide)
        ```

        QUAN TRỌNG:
        - Viết đầy đủ, chi tiết nhưng súc tích
        - Mỗi phần "Nội dung chi tiết" phải có đủ thông tin để người đọc hiểu sâu
        - Bullet points phải ngắn gọn (< 100 ký tự mỗi điểm)
        - Speaker notes phải hữu ích cho người thuyết trình
        - Toàn bộ bằng tiếng Việt
        """,
        agent=agent,
        expected_output="Tài liệu Markdown chi tiết bằng tiếng Việt, bao gồm nội dung mở rộng cho từng slide, bullet points súc tích, và speaker notes. Mỗi slide trong outline tương ứng một phần trong tài liệu.",
    )


def create_revise_doc_task(agent, current_doc: str, feedback: str, topic: str) -> Task:
    """Tạo task chỉnh sửa tài liệu dựa trên góp ý của người dùng."""
    return Task(
        description=f"""
        Bạn cần chỉnh sửa tài liệu thuyết trình về "{topic}" dựa trên góp ý của người dùng.

        === TÀI LIỆU HIỆN TẠI ===
        {current_doc}
        === HẾT TÀI LIỆU ===

        === GÓP Ý CỦA NGƯỜI DÙNG ===
        {feedback}
        === HẾT GÓP Ý ===

        Yêu cầu:
        1. Giữ nguyên cấu trúc Markdown của tài liệu hiện tại
        2. Áp dụng các thay đổi theo góp ý của người dùng
        3. Đảm bảo nội dung vẫn phong phú, chi tiết
        4. Giữ nguyên bullet points súc tích (< 100 ký tự mỗi điểm)
        5. Cập nhật speaker notes nếu cần thiết
        6. Đảm bảo luồng thông tin vẫn logic sau khi chỉnh sửa

        QUAN TRỌNG:
        - Chỉ xuất tài liệu Markdown đã chỉnh sửa, không thêm giải thích
        - Toàn bộ bằng tiếng Việt
        """,
        agent=agent,
        expected_output="Tài liệu Markdown đã chỉnh sửa theo góp ý, giữ nguyên cấu trúc. Toàn bộ tiếng Việt.",
    )