"""
Review Tasks - Nhiệm vụ kiểm tra chất lượng outline, tài liệu và slide.
"""

from crewai import Task


def create_outline_review_task(agent, outline_json: str, topic: str) -> Task:
    """Tạo task kiểm tra chất lượng outline bài thuyết trình."""
    return Task(
        description=f"""
        Hãy kiểm tra và đánh giá chất lượng của outline bài thuyết trình sau:
        
        Chủ đề yêu cầu: {topic}
        
        === OUTLINE BÀI THUYẾT TRÌNH ===
        {outline_json}
        === HẾT OUTLINE ===
        
        Tiêu chí đánh giá:
        1. ĐỘ PHỦ: Outline có bao quát đủ chủ đề "{topic}" không?
        2. CẤU TRÚC: Có luồng logic (mở bài → thân bài → kết bài) không?
        3. SỐ LƯỢNG SLIDE: Phù hợp với độ phức tạp của chủ đề không?
        4. TIÊU ĐỀ: Ngắn gọn, thu hút, phản ánh đúng nội dung không?
        5. BULLET POINTS: Súc tích, không trùng lặp, có phân cấp rõ ràng không?
        6. NHẤT QUÁN: Format đồng nhất giữa các slide không?
        7. TÍNH ỨNG DỤNG: Có thể phát triển thành bài thuyết trình thực tế không?
        
        QUAN TRỌNG: 
        - Chỉ đánh giá "CẦN SỬA" nếu có vấn đề NGHIÊM TRỌNG
        - Nếu outline cơ bản tốt → "ĐẠT"
        
        Định dạng kết quả BẮT BUỘC:
        - Đánh giá tổng thể: [1-2 câu]
        - Điểm tốt: [liệt kê]
        - Vấn đề (nếu có): [liệt kê cụ thể]
        - Đề xuất cải thiện: [liệt kê]
        - KẾT LUẬN: ĐẠT hoặc CẦN SỬA
        """,
        agent=agent,
        expected_output="Báo cáo đánh giá chất lượng outline bằng tiếng Việt. KẾT LUẬN phải là 'ĐẠT' hoặc 'CẦN SỬA'.",
    )


def create_doc_review_task(agent, doc_content: str, topic: str) -> Task:
    """Tạo task kiểm tra chất lượng tài liệu chi tiết."""
    return Task(
        description=f"""
        Hãy kiểm tra và đánh giá chất lượng của tài liệu chi tiết sau:
        
        Chủ đề: {topic}
        
        === TÀI LIỆU CHI TIẾT ===
        {doc_content}
        === HẾT TÀI LIỆU ===
        
        Tiêu chí đánh giá:
        1. NỘI DUNG: Chính xác, đầy đủ, có chiều sâu không?
        2. CẤU TRÚC: Heading rõ ràng, luồng logic không?
        3. NGÔN NGỮ: Tiếng Việt đúng ngữ pháp, chính tả, tự nhiên không?
        4. TÍNH ỨNG DỤNG: Có thể chuyển thành slide dễ dàng không?
        5. VÍ DỤ & SỐ LIỆU: Có đủ minh chứng không?
        6. ĐỘ DÀI: Phù hợp, không quá dài hoặc quá ngắn?
        
        QUAN TRỌNG:
        - Chỉ đánh giá "CẦN SỬA" nếu có vấn đề NGHIÊM TRỌNG
        - Nếu tài liệu cơ bản tốt → "ĐẠT"
        
        Định dạng kết quả BẮT BUỘC:
        - Đánh giá tổng thể: [1-2 câu]
        - Điểm tốt: [liệt kê]
        - Vấn đề (nếu có): [liệt kê cụ thể]
        - Đề xuất cải thiện: [liệt kê]
        - KẾT LUẬN: ĐẠT hoặc CẦN SỬA
        """,
        agent=agent,
        expected_output="Báo cáo đánh giá chất lượng tài liệu bằng tiếng Việt. KẾT LUẬN phải là 'ĐẠT' hoặc 'CẦN SỬA'.",
    )


def create_review_task(agent, slide_json: str) -> Task:
    """Tạo task kiểm tra chất lượng bài thuyết trình (slide JSON)."""
    return Task(
        description=f"""
        Hãy kiểm tra và đánh giá chất lượng của bài thuyết trình sau:
        
        === NỘI DUNG BÀI THUYẾT TRÌNH ===
        {slide_json}
        === HẾT NỘI DUNG ===
        
        Tiêu chí đánh giá:
        1. NỘI DUNG: Thông tin có chính xác, đầy đủ và phù hợp không?
        2. CẤU TRÚC: Luồng thông tin có logic không? Slide có sắp xếp hợp lý không?
        3. ĐỘ DÀI: Số lượng slide và bullet points có phù hợp không?
        4. TIÊU ĐỀ: Các tiêu đề có ngắn gọn, thu hút và phản ánh đúng nội dung không?
        5. BULLET POINTS: Có súc tích, dễ đọc và không quá dài không?
        6. NHẤT QUÁN: Format và phong cách có nhất quán giữa các slide không?
        7. NGÔN NGỮ: Tiếng Việt có đúng ngữ pháp và chính tả không?
        
        QUAN TRỌNG:
        - Chỉ đánh giá "CẦN SỬA" nếu có vấn đề NGHIÊM TRỌNG
        - Nếu slide cơ bản tốt → "ĐẠT"
        
        Định dạng kết quả BẮT BUỘC:
        - Đánh giá tổng thể: [1-2 câu]
        - Điểm tốt: [liệt kê]
        - Vấn đề (nếu có): [liệt kê cụ thể]
        - Đề xuất cải thiện: [liệt kê]
        - KẾT LUẬN: ĐẠT hoặc CẦN SỬA
        """,
        agent=agent,
        expected_output="Báo cáo đánh giá chất lượng bằng tiếng Việt. KẾT LUẬN phải là 'ĐẠT' hoặc 'CẦN SỬA'.",
    )
