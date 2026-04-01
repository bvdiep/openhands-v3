# Kiến trúc hệ thống FastHTML Task Runner

## Tổng quan
FastHTML Task Runner là một ứng dụng web độc lập (standalone) được xây dựng bằng FastHTML, cho phép người dùng nhập yêu cầu từ giao diện web. Các yêu cầu này sau đó được chuyển xuống OpenHands (thông qua `TaskRunner`) để thực thi. Quá trình thực thi có thể lặp lại trong một cuộc hội thoại (conversation) mà không mất ngữ cảnh, và trạng thái hội thoại được lưu trữ trên ổ đĩa.

## Cấu trúc thư mục
Sau khi được tách ra thành một ứng dụng độc lập, cấu trúc thư mục đã được làm sạch và tối ưu hóa:

```
/home/dd/work/diep/openhands-v3/
├── main.py                 # Điểm vào chính của ứng dụng FastHTML, quản lý giao diện và API
├── requirements.txt        # Danh sách TẤT CẢ các thư viện phụ thuộc của dự án
├── .env                    # File cấu hình biến môi trường DUY NHẤT của dự án
├── ecosystem.config.json   # Cấu hình PM2 để chạy ứng dụng trong môi trường production
├── executor.db             # Cơ sở dữ liệu SQLite lưu trữ lịch sử các execution và turns
├── engine/                 # Thư mục chứa logic giao tiếp với OpenHands SDK
│   ├── __init__.py
│   ├── config.py           # Cấu hình LLM và các thiết lập chung cho OpenHands
│   └── runner.py           # Lớp TaskRunner, khởi tạo Agent, LLM và quản lý vòng đời thực thi
└── plans/
    └── architecture.md     # Tài liệu kiến trúc này
```

## Tại sao trước đây lại có hai file `requirements.txt` và hai file `.env`?

Trong cấu trúc cũ, thư mục `engine/` được thiết kế như một module dùng chung (shared module) cho nhiều dự án khác nhau (ví dụ: các script tự động hóa, pipeline, v.v.). Do đó:
- `engine/requirements.txt` chứa các thư viện cốt lõi mà bản thân engine cần (như `openhands`, `python-dotenv`).
- `engine/.env` chứa các API keys (như `LITELLM_KEY`, `GEMINI_API_KEY`) dùng riêng cho engine.
- Thư mục gốc (`fasthtml_task_runner`) lại có `requirements.txt` và `.env` riêng phục vụ cho giao diện web (FastHTML, Uvicorn, thông tin đăng nhập web).

**Hiện tại:**
Vì chúng ta đã tách ứng dụng này thành một hệ thống **standalone** (độc lập hoàn toàn), việc duy trì hai file cấu hình và hai file dependencies là không cần thiết và dễ gây nhầm lẫn. 

**Giải pháp đã thực hiện:**
1. **Gộp `.env`**: Đã chuyển các API keys từ `engine/.env` sang file `.env` ở thư mục gốc. Bây giờ chỉ có một file `.env` duy nhất chứa cả thông tin đăng nhập web (`LOGIN_USER`, `LOGIN_PASS`) và API keys (`LITELLM_KEY`, `GEMINI_API_KEY`).
2. **Gộp `requirements.txt`**: Đã thêm `openhands` và các dependencies của engine vào `requirements.txt` ở thư mục gốc.
3. **Xóa file thừa**: Đã xóa `engine/.env` và `engine/requirements.txt`.
4. **Làm sạch `engine/`**: Đã xóa các file không được sử dụng bởi FastHTML Task Runner như `base_step.py`, `pipeline.py`, và `README.md` cũ của engine, chỉ giữ lại `runner.py` và `config.py` là những thành phần thực sự cần thiết.

## Luồng hoạt động (Workflow)
1. **Giao diện người dùng (UI)**: Người dùng truy cập web (FastHTML), nhập prompt và chọn model.
2. **Lưu trữ (Database)**: `main.py` lưu yêu cầu vào `executor.db` (bảng `executions` và `execution_turns`).
3. **Thực thi (Execution)**: 
   - Một luồng (thread) nền lấy yêu cầu từ hàng đợi (queue).
   - Khởi tạo `TaskRunner` (từ `engine/runner.py`).
   - `TaskRunner` thiết lập OpenHands Agent với các công cụ (Terminal, FileEditor, Browser) và cấu hình LLM từ `engine/config.py`.
   - Agent thực thi nhiệm vụ, logs được stream ngược lại UI thông qua Server-Sent Events (SSE).
4. **Lưu trạng thái**: Ngữ cảnh của conversation được lưu xuống đĩa để có thể tiếp tục trong các turn tiếp theo.