"""
Slide Task - Nhiệm vụ tạo JSON structure cho PowerPoint từ outline và tài liệu đã approve.
"""

from crewai import Task


def create_slide_task(agent, approved_outline: str, theme_name: str, doc_content: str = None, additional_instructions: str = None) -> Task:
    """Tạo task chuyển outline + tài liệu thành JSON structure chuẩn cho PPTX generator."""

    doc_section = ""
    if doc_content:
        doc_section = f"""
        === TÀI LIỆU CHI TIẾT ĐÃ DUYỆT ===
        {doc_content}
        === HẾT TÀI LIỆU ===
        """

    extra_section = ""
    if additional_instructions:
        extra_section = f"""
        === HƯỚNG DẪN BỔ SUNG ===
        {additional_instructions}
        === HẾT HƯỚNG DẪN BỔ SUNG ===
        """

    return Task(
        description=f"""
        Chuyển đổi outline và tài liệu chi tiết đã được duyệt thành JSON structure chuẩn để tạo file PowerPoint.

        === OUTLINE ĐÃ DUYỆT ===
        {approved_outline}
        === HẾT OUTLINE ===

        {doc_section}
        Theme được chọn: {theme_name}

        {extra_section}

        Nhiệm vụ của bạn:
        1. Sử dụng outline làm cấu trúc chính (số lượng slide, type, title)
        2. Sử dụng tài liệu chi tiết để làm phong phú nội dung bullet points và speaker notes
        3. Đảm bảo JSON structure hoàn toàn hợp lệ (không lỗi cú pháp)
        4. Mỗi slide phải có đúng "type" (title/content/summary)
        5. Slide "title" phải có: title, subtitle (optional), notes (optional)
        6. Slide "content" phải có: title, bullet_points (list of strings), notes (optional)
        7. Slide "summary" phải có: title, bullet_points (optional)
        8. Đảm bảo presentation_title có mặt ở root level
        9. Bullet points phải súc tích (< 100 ký tự), lấy từ tài liệu chi tiết
        10. Speaker notes phải chi tiết, hữu ích cho người thuyết trình
        11. Kiểm tra lại toàn bộ nội dung bằng tiếng Việt

        Xuất kết quả cuối cùng là JSON string hợp lệ, KHÔNG có markdown code block wrapper.
        """,
        agent=agent,
        expected_output="JSON string hợp lệ (không có markdown wrapper) chứa presentation_title và slides array. Mỗi slide có type, title, bullet_points (nếu là content/summary), notes. Nội dung phong phú từ tài liệu chi tiết.",
    )