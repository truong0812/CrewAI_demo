# CrewAI Presentation Pipeline

Hệ thống tạo bài thuyết trình tự động bằng multi-agent workflow trên CrewAI.

Người dùng nhập một chủ đề, hệ thống sẽ:
- nghiên cứu nội dung
- tạo outline
- viết tài liệu chi tiết
- sinh slide JSON
- xuất PowerPoint `.pptx`

Project hiện hỗ trợ 2 kiểu review:
- `Agent review`: agent tự review và tự sửa qua từng phase
- `Human review`: dừng sau outline để con người góp ý trước khi chạy tiếp

Sản phẩm cuối cùng gồm:
- file tài liệu Markdown
- file slide JSON
- file PowerPoint `.pptx`

## Mục tiêu

Project này phù hợp khi bạn cần một pipeline tạo slide có cấu trúc, có khả năng thay provider LLM, và đủ linh hoạt để:
- chạy hoàn toàn tự động
- chèn human checkpoint ở giữa workflow
- xuất ra nhiều dạng artifact để dùng tiếp trong các hệ thống khác

## Tính năng chính

- Multi-agent orchestration với CrewAI
- Tách pha rõ ràng: research, outline, document, slide, export
- Hỗ trợ nhiều provider: `openai`, `anthropic`, `gemini`, `ollama`, `groq`, `z_ai`
- Có `human review mode` để giảm chi phí và rủi ro rate limit ở các phase sau
- Lưu artifact cuối vào thư mục `output/`
- Có giao diện Streamlit và CLI
- Hỗ trợ speaker notes cho từng slide

## Kiến trúc tổng quan

```text
Input Topic
  |
  v
Phase 1: Research + Outline
  - Researcher
  - Content Strategist
  - Outline Reviewer (optional if agent review mode)
  |
  v
Human Review Checkpoint (optional)
  - User xem outline
  - User nhập feedback
  - Agent sửa outline theo feedback
  |
  v
Phase 2: Document Generation
  - Doc Writer
  - Doc Reviewer (optional if agent review mode)
  |
  v
Phase 3: Slide Generation
  - Slide Designer
  - Slide Reviewer (optional if agent review mode)
  |
  v
PowerPoint Export
  - PPTXGenerator
  |
  v
Final Assets
  - .md
  - .json
  - .pptx
```

## Cấu trúc thư mục

```text
CrewAI/
├── .env
├── .env.example
├── README.md
├── app.py
├── config.py
├── crew.py
├── main.py
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── content_strategist.py
│   ├── doc_writer.py
│   ├── researcher.py
│   ├── reviewer.py
│   └── slide_designer.py
├── tasks/
│   ├── __init__.py
│   ├── content_task.py
│   ├── doc_task.py
│   ├── research_task.py
│   ├── review_task.py
│   └── slide_task.py
├── tools/
│   ├── __init__.py
│   └── pptx_generator.py
├── docs/
│   └── PROJECT_DOC.md
└── output/
```

## Các thành phần chính

### 1. `app.py`

Giao diện Streamlit cho người dùng cuối.

Chức năng chính:
- cấu hình provider, API key, theme, số slide
- chọn review mode
- chạy pipeline
- duyệt outline trong human review mode
- tải artifact cuối

### 2. `crew.py`

Đây là file orchestration trung tâm.

Các hàm quan trọng:
- `run_phase1(...)`: research + outline
- `run_phase2_doc(...)`: tạo tài liệu chi tiết
- `run_phase3(...)`: sinh slide JSON + xuất PPTX
- `run_full_pipeline(...)`: chạy end-to-end
- `revise_outline_with_human_feedback(...)`: sửa outline theo feedback người dùng
- `_save_final_assets(...)`: lưu `.md`, `.json`, `.pptx`

### 3. `config.py`

Quản lý:
- provider/model
- API key và base URL
- theme cho slide
- cơ chế gợi ý theme theo topic

### 4. `agents/`

Khai báo các agent:
- `Researcher`
- `Content Strategist`
- `Doc Writer`
- `Slide Designer`
- `Outline Reviewer`
- `Doc Reviewer`
- `Slide Reviewer`

### 5. `tasks/`

Định nghĩa prompt/task tương ứng cho từng agent.

### 6. `tools/pptx_generator.py`

Chịu trách nhiệm:
- đọc slide JSON
- dựng layout PowerPoint
- apply theme
- ghi file `.pptx`

## Workflow chi tiết

### Agent review mode

Phù hợp khi:
- muốn chạy tự động hoàn toàn
- chấp nhận nhiều lượt gọi model hơn
- muốn hệ thống tự refinement nội bộ

Luồng:
1. Research topic
2. Tạo outline
3. Agent review outline
4. Tạo document
5. Agent review document
6. Tạo slide JSON
7. Agent review slide
8. Xuất `.pptx`
9. Lưu final assets

### Human review mode

Phù hợp khi:
- muốn giảm token usage
- muốn chèn quyết định của con người trước Phase 2
- muốn hạn chế lỗi rate limit ở provider như Groq

Luồng:
1. Research topic
2. Tạo outline
3. Dừng tại checkpoint
4. Người dùng xem outline
5. Người dùng nhập feedback nếu cần
6. Agent sửa outline theo feedback
7. Khi người dùng approve, hệ thống mới chạy Phase 2 và Phase 3
8. Bỏ auto-review tài liệu và slide để giảm số lượt gọi model

## Cài đặt

### Yêu cầu

- Python 3.10+
- Kết nối internet nếu dùng provider cloud
- API key hợp lệ cho provider tương ứng

### Cài dependency

```bash
pip install -r requirements.txt
```

### Cấu hình môi trường

Tạo file `.env` từ mẫu:

```bash
copy .env.example .env
```

Ví dụ cấu hình:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL_NAME=gpt-4o
```

### Provider currently supported

| Provider | API key env | Model env | Ghi chú |
|---|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL_NAME` | Mặc định `gpt-4o` |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL_NAME` | Claude Sonnet |
| Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL_NAME` | Google Gemini |
| Ollama | không bắt buộc | `OLLAMA_MODEL_NAME` | chạy local |
| Groq | `GROQ_API_KEY` | `GROQ_MODEL_NAME` | dễ chạm rate limit TPM |
| Z AI | `ZAI_API_KEY` | `ZAI_MODEL_NAME` | cần `ZAI_BASE_URL` |

Lưu ý: `config.py` có hỗ trợ `groq`, nhưng mẫu `.env.example` hiện chưa có block Groq. Nếu dùng Groq, hãy tự thêm:

```env
GROQ_API_KEY=your-groq-key
GROQ_MODEL_NAME=groq/llama-3.3-70b-versatile
```

## Chạy project

### Streamlit UI

```bash
streamlit run app.py
```

Sau khi mở app:
1. nhập topic
2. chọn provider
3. chọn theme
4. chọn `Agent review` hoặc `Human review`
5. chạy pipeline

### CLI

```bash
python main.py "Giới thiệu về Machine Learning"
```

Ví dụ thêm tham số:

```bash
python main.py "Chuyển đổi số cho SME" --slides 12 --theme technical --provider anthropic --api-key your-key
```

## Output

Sau khi chạy thành công, project lưu artifact vào `output/`:

- `*.md`: tài liệu chi tiết
- `*.json`: slide JSON cuối
- `*.pptx`: file PowerPoint

## Rate limit và chi phí

Một số provider có TPM/RPM chặt, đặc biệt với prompt dài ở Phase 2.

Khuyến nghị:
- dùng `Human review mode` nếu provider dễ rate limit
- giảm độ dài topic đầu vào nếu không cần quá nhiều chiều sâu
- chọn model nhanh/nhẹ hơn nếu phù hợp
- thêm retry/backoff trong tương lai nếu triển khai production

## Hạn chế hiện tại

- Chưa có retry/backoff tự động cho lỗi rate limit
- Chưa có persistence cho session workflow ngoài Streamlit session state
- Chưa có test suite tự động
- CLI hiện chưa expose `human review mode`
- Mẫu `.env.example` chưa đồng bộ đầy đủ với tất cả provider trong `config.py`

## Hướng phát triển đề xuất

- thêm retry và exponential backoff cho lỗi rate limit
- thêm logging chuẩn thay cho text log trong session
- thêm test cho parser JSON và asset saver
- expose `human review mode` trong CLI
- thêm export DOCX/PDF
- thêm storage backend để lưu lịch sử job

## Tài liệu bổ sung

Xem tài liệu kỹ thuật chi tiết tại [docs/PROJECT_DOC.md](D:\CrewAI\docs\PROJECT_DOC.md).

## License

MIT
