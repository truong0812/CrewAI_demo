# Project Documentation

## 1. Tổng quan

Project này xây dựng một hệ thống tạo bài thuyết trình bằng multi-agent pipeline trên CrewAI.

Thay vì sinh trực tiếp PowerPoint từ một prompt ngắn, hệ thống chia công việc thành nhiều phase:
- nghiên cứu chủ đề
- tạo outline
- viết tài liệu chi tiết
- chuyển thành slide JSON
- xuất file trình chiếu

Cách chia phase này giúp:
- nội dung có cấu trúc hơn
- dễ kiểm soát chất lượng ở từng bước
- dễ chèn human review checkpoint
- dễ thay provider/model

## 2. Mục tiêu thiết kế

Các mục tiêu chính:
- tách biệt concern giữa research, writing, reviewing, exporting
- cho phép vừa chạy full-auto, vừa cho phép human review ở checkpoint
- chuẩn hóa đầu ra trung gian thành JSON để tái sử dụng
- giữ phần PowerPoint generation tách khỏi LLM logic

## 3. Kiến trúc module

### `config.py`

Chứa:
- mapping provider -> env var
- default model cho từng provider
- theme registry
- logic gợi ý theme

### `agents/`

Định nghĩa vai trò và backstory cho từng agent. Các agent chỉ chịu trách nhiệm về năng lực chuyên môn của mình, không orchestration.

Danh sách:
- `researcher.py` — Agent nghiên cứu nội dung
- `content_strategist.py` — Agent tạo và sửa outline
- `speaker_doc_writer.py` — Agent viết speaker doc chi tiết (agent chính cho Phase 2)
- `doc_writer.py` — Agent viết tài liệu (backup, hiện không dùng trong pipeline chính)
- `slide_designer.py` — Agent tạo slide JSON
- `reviewer.py` — 3 reviewer agents: outline, doc, slide

Tất cả agent sử dụng chung helper `create_llm_instance()` từ `config.py` để tạo LLM, tránh code duplication.

### `tasks/`

Mỗi file trong `tasks/` chứa prompt template cho một nhóm nhiệm vụ:
- research
- outline generation / outline revision
- document generation / document revision
- slide generation
- review

Điểm quan trọng: project đang encode gần như toàn bộ business rules vào prompt task.

### `crew.py`

Đây là orchestration layer thực tế.

Vai trò:
- gọi agent đúng thứ tự
- parse / validate JSON
- quản lý auto-review loop
- điều phối human feedback
- lưu final assets

Các function chính:
- `run_phase1`
- `run_phase2_doc`
- `run_phase3`
- `run_full_pipeline`
- `revise_outline_with_human_feedback`
- `_save_final_assets`

### `app.py`

UI layer chạy bằng Streamlit.

Chức năng:
- thu input người dùng
- lưu state của workflow
- hiển thị outline checkpoint
- nhận human feedback
- kích hoạt phase tiếp theo
- hiển thị và download final assets

### `main.py`

CLI đơn giản để chạy pipeline mà không cần UI.

Hiện phù hợp cho:
- local run
- smoke test thủ công
- debugging nhanh

### `tools/pptx_generator.py`

Đây là module non-LLM.

Nó đọc JSON đã được chuẩn hóa rồi chuyển thành file `.pptx`.
Ưu điểm của thiết kế này là:
- dễ thay đổi layout mà không đụng orchestration
- có thể thay nguồn JSON bằng pipeline khác trong tương lai

## 4. Data flow

### 4.1 Phase 1

Input:
- topic
- provider
- api_key
- num_slides

Output:
- `research_result`
- `outline_json`
- `outline_display`

Nếu `auto_review=True`:
- outline reviewer sẽ đánh giá
- nếu chưa đạt thì strategist sửa
- lặp tối đa `MAX_REVIEW_ITERATIONS`

### 4.2 Human review checkpoint

Chỉ dùng khi `review_mode=human`.

Người dùng có thể:
- đọc outline dễ hiểu qua `outline_display`
- xem `outline_json`
- nhập feedback text
- yêu cầu agent sửa outline
- approve để chạy tiếp

Checkpoint này có giá trị lớn vì:
- cắt bớt token burn ở các phase sau
- giúp phát hiện sớm sai hướng nội dung
- giảm xác suất rate limit khi provider hạn chế TPM

### 4.3 Phase 2

Input:
- approved outline

Output:
- markdown document

Tài liệu này đóng vai trò:
- nguồn nội dung giàu ngữ cảnh cho slide
- artifact đọc được cho con người

### 4.4 Phase 3

Input:
- approved outline
- approved document
- theme

Output:
- slide JSON
- review result
- `.pptx`

Nếu bật auto review:
- slide reviewer đánh giá
- slide designer sửa theo feedback

## 5. Review modes

### Agent review mode

Ưu điểm:
- full-auto
- không cần con người can thiệp giữa pipeline
- phù hợp batch generation

Nhược điểm:
- nhiều lượt gọi model hơn
- dễ chạm rate limit hơn
- khó kiểm soát sớm khi outline sai hướng

### Human review mode

Ưu điểm:
- có checkpoint thật sự
- giảm token usage ở phase sau
- thực tế hơn cho môi trường có rate limit

Nhược điểm:
- phải có thao tác người dùng
- không còn end-to-end automation tuyệt đối

## 6. Các artifact

Project tạo ba loại artifact cuối:

### Markdown document

Mục đích:
- tài liệu đọc cho con người
- nguồn để kiểm tra nội dung
- đầu vào giàu ngữ cảnh cho phase slide

### Slide JSON

Mục đích:
- representation trung gian, có cấu trúc
- thuận tiện cho debug
- có thể dùng cho các exporter khác ngoài PPTX

### PowerPoint

Mục đích:
- đầu ra trình chiếu cuối cùng cho user

## 7. Xử lý lỗi

### Lỗi phổ biến

1. Sai hoặc thiếu API key
2. Provider trả lỗi rate limit
3. LLM trả JSON sai format
4. Model trả nội dung không đúng schema kỳ vọng

### Trạng thái hiện tại

Project đã có:
- parse validation cho outline/slide JSON
- fallback nhất định khi parse lỗi
- error phase trong Streamlit UI

Project chưa có:
- retry/backoff chuẩn
- error classification rõ ràng
- telemetry

## 8. Rate limit

Vấn đề rate limit nổi bật ở provider như Groq khi:
- prompt dài
- tài liệu phase 2 sinh ra lớn
- thêm auto-review loop

Mitigation hiện tại:
- human review mode
- giảm số vòng auto-review
- chọn provider/model khác

Mitigation nên làm tiếp:
- retry với sleep theo thông tin `Please try again in ...`
- cắt prompt nếu tài liệu quá dài
- chunking document generation

## 9. Điểm mạnh của thiết kế hiện tại

- Orchestration rõ ràng
- UI và core logic tách tương đối sạch
- Có intermediate artifacts dễ debug
- Hỗ trợ nhiều provider ngay từ đầu
- Dễ mở rộng thêm review checkpoint

## 10. Điểm yếu hiện tại

- Chưa có test suite tự động
- Prompt đang dài và lặp nhiều giữa task/agent
- Coupling khá lớn giữa UI và orchestration function
- Một số helper nội bộ như `_save_final_assets` đang được import trực tiếp từ UI
- Chưa có retry/backoff cho rate limit
- Chưa có persistence cho session workflow ngoài Streamlit session state
- CLI chưa expose `human review mode`

## 11. Đề xuất refactor

### Ngắn hạn

- thêm retry/backoff cho rate limit
- thêm `groq` vào `.env.example`
- expose human review mode ở CLI
- gom error handling thành utility riêng

### Trung hạn

- tạo schema riêng cho slide JSON
- thêm tests cho `validate_outline_json`, `_extract_json`, `_save_final_assets`
- tách service layer khỏi `crew.py`

### Dài hạn

- lưu workflow/job state vào DB hoặc filesystem bền vững
- hỗ trợ queue job bất đồng bộ
- hỗ trợ nhiều output renderer hơn ngoài PPTX

## 12. Quy trình làm việc đề xuất cho team

### Khi phát triển tính năng mới

1. sửa orchestration ở `crew.py`
2. cập nhật prompt ở `tasks/` nếu cần
3. cập nhật UI ở `app.py` nếu user-facing
4. cập nhật README và doc kỹ thuật

### Khi debug lỗi chất lượng nội dung

1. xem `outline_json`
2. xem log review
3. xác định lỗi xuất phát từ phase nào
4. sửa prompt/task trước khi sửa exporter

### Khi debug lỗi format slide

1. xem `slide_json`
2. validate schema
3. kiểm tra `pptx_generator.py`

## 13. Hướng dẫn sử dụng human review mode

Trong Streamlit:
1. chọn `Human review trước Phase 2`
2. chạy phase 1
3. đọc outline
4. nhập feedback vào ô review
5. nhấn nút sửa outline nếu cần
6. khi ổn, approve để tạo sản phẩm cuối

Đây là mode phù hợp nhất khi:
- outline cần được business owner duyệt
- provider có quota thấp
- cần hạn chế token burn không cần thiết

## 14. Kết luận

Project đã có nền tảng tốt cho một AI presentation pipeline thực dụng:
- có multi-agent orchestration
- có review mode linh hoạt
- có output rõ ràng
- đủ dễ hiểu để mở rộng tiếp

Việc nên ưu tiên tiếp theo là:
- tăng độ ổn định với retry/backoff
- thêm test
- chuẩn hóa schema và tài liệu để giảm drift giữa code và docs

---

## 15. Changelog

### v1.1 — Bug fixes & refactoring (2026-04-19)

#### 🔧 Refactoring: Shared LLM creation helper

**Vấn đề:** Mỗi agent file (`researcher.py`, `content_strategist.py`, `slide_designer.py`, `doc_writer.py`, `speaker_doc_writer.py`, `reviewer.py`) đều lặp cùng đoạn code ~8 dòng để tạo LLM instance.

**Giải pháp:** Thêm hàm `create_llm_instance(provider, api_key, base_url_override)` vào `config.py`. Tất cả agent giờ dùng chung helper này.

**Lợi ích:**
- Giảm code duplication từ ~48 dòng xuống 6 dòng import
- Dễ bảo trì: thay đổi logic tạo LLM chỉ cần sửa 1 chỗ
- Hỗ trợ `base_url_override` cho provider cần config runtime

#### 🐛 Fix: Z AI base_url không được truyền từ UI

**Vấn đề:** Streamlit UI (`app.py`) cho người dùng nhập Base URL cho Z AI provider, nhưng giá trị này không bao giờ được truyền vào pipeline. Base URL chỉ đọc từ env var trong `config.py`.

**Giải pháp:** Khi user nhập Z AI base URL trong UI, giá trị được lưu vào cả `session_state` lẫn `os.environ` để `config.py` đọc được.

#### 🐛 Fix: `_is_approved()` default trả về `True`

**Vấn đề:** Hàm `_is_approved()` trong `crew.py` mặc định trả về `True` nếu không tìm thấy "KẾT LUẬN" trong review text. Điều này có nghĩa là nếu LLM trả lời bằng format khác (tiếng Anh, structure khác), pipeline tự động coi là ĐẠT.

**Giải pháp:**
- Đổi default thành `False` (an toàn hơn)
- Thêm warning log khi không tìm thấy kết luận
- Thêm fallback hỗ trợ cả tiếng Việt không dấu

#### 🧹 Dead code: `doc_writer` import

**Vấn đề:** `agents/__init__.py` import `create_doc_writer` từ `doc_writer.py`, nhưng hàm này không được gọi ở bất kỳ đâu trong dự án. Pipeline thực tế dùng `create_speaker_doc_writer`.

**Giải pháp:** Xóa import `create_doc_writer` khỏi `agents/__init__.py`. File `doc_writer.py` được giữ lại làm backup.

#### 📝 Cập nhật `.env.example`

**Thay đổi:**
- Thêm block cấu hình Groq (trước đây thiếu)
- Sửa Gemini model từ `gemini/gemini-1.5-pro` thành `gemini/gemini-2.0-flash` (đồng bộ với `config.py` default)

#### 📝 Cập nhật documentation

**Thay đổi:**
- `docs/PROJECT_DOC.md`: Cập nhật danh sách agents cho chính xác, thêm mô tả từng agent
- `docs/PROJECT_DOC.md`: Cập nhật section điểm yếu
- `docs/PROJECT_DOC.md`: Thêm section changelog này
