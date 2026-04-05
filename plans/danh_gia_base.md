# Đánh giá Tổng thể Codebase — OpenHands-v3

**Ngày đánh giá:** 2026-04-05  
**Phiên bản:** Branch `api_expose_and_upgrade` (HEAD: e54b1f9)  
**Tổng LOC:** ~2,013 dòng Python/JS/CSS (không tính plans, docs)

---

## 1. Tổng quan Kiến trúc

### Mô tả
OpenHands-v3 là một **FastHTML web application** cho phép người dùng gửi prompt đến AI agent (OpenHands SDK), theo dõi quá trình thực thi real-time qua SSE (Server-Sent Events), và quản lý lịch sử execution trong SQLite.

### Cấu trúc thư mục hiện tại

```
openhands-v3/
├── main.py                  # Entry point (~50 LOC) — slim, chỉ khởi tạo app
├── engine/
│   ├── config.py            # Cấu hình LLM, MCP servers, ProjectConfig (~232 LOC)
│   └── runner.py            # TaskRunner — wrapper OpenHands SDK (~306 LOC)
├── db/
│   └── queries.py           # SQLite queries, init_db, CRUD (~220 LOC)
├── services/
│   └── execution.py         # Thread-safe execution logic, QueueWriter (~202 LOC)
├── middleware/
│   ├── auth.py              # Authentication middleware (~46 LOC)
│   └── rate_limit.py        # In-memory rate limiter (~29 LOC)
├── routes/
│   ├── auth.py              # Login/logout routes (~61 LOC)
│   ├── stream.py            # SSE streaming endpoint (~37 LOC)
│   ├── api.py               # REST API endpoints (~112 LOC)
│   └── web.py               # UI routes + HTML generation (~544 LOC)
├── static/
│   ├── app.js               # Client-side utilities (~35 LOC)
│   └── style.css            # Styles (~130 LOC)
├── skills/hello-world/      # Skill mẫu
├── plans/                   # Tài liệu kế hoạch
├── requirements.txt         # Dependencies
└── ecosystem.config.json    # PM2 deployment config
```

### Điểm mạnh kiến trúc
- ✅ **Modular hóa tốt**: Code đã được tách từ monolith (~1159 LOC) thành 8+ modules rõ ràng
- ✅ **Separation of Concerns**: DB, services, middleware, routes tách biệt
- ✅ **Entry point sạch**: `main.py` chỉ 50 dòng — dễ hiểu flow ngay lập tức
- ✅ **Pattern nhất quán**: Mỗi route module có `register(app)` function

### Điểm yếu kiến trúc
- ⚠️ `routes/web.py` vẫn quá lớn (544 LOC) — mix HTML generation + JS inline + business logic
- ⚠️ Inline JavaScript trong f-string Python rất khó maintain và debug
- ⚠️ Không có layer abstraction giữa routes và DB (routes gọi thẳng `db.queries`)

---

## 2. Đánh giá theo Module

### 2.1 `engine/config.py` — ⭐⭐⭐ Khá

| Tiêu chí | Đánh giá |
|-----------|----------|
| Security | ✅ `get_api_key()` đọc từ env, fail fast nếu thiếu |
| Flexibility | ✅ `_get_llm_config()` hỗ trợ cả direct API và proxy |
| MCP Config | ✅ `get_mcp_config()` filter đúng format SDK |
| Vấn đề | ⚠️ `ProjectConfig` phức tạp nhưng không thấy dùng ở đâu trong app |
| Vấn đề | ⚠️ `AVAILABLE_MCP_SERVERS` hardcode absolute paths (`/home/dd/...`) |
| Vấn đề | ⚠️ Global mutable state `_current_project_config` — thread-unsafe |

### 2.2 `engine/runner.py` — ⭐⭐⭐⭐ Tốt

| Tiêu chí | Đánh giá |
|-----------|----------|
| Design | ✅ Clean wrapper cho OpenHands SDK |
| Event handling | ✅ `_on_event()` xử lý tốt nhiều loại event phức tạp |
| Thought extraction | ✅ `_extract_thought_metadata()` robust, nhiều fallback |
| Metrics | ✅ Thu thập đầy đủ token usage, cost, latency |
| Multi-turn | ✅ `start_session()` + `send_task()` hỗ trợ conversation liên tục |
| Vấn đề | ⚠️ `_on_event()` có bare `except Exception: pass` — nuốt mọi lỗi |
| Vấn đề | ⚠️ Thiếu logging structured — chỉ dùng `print()` |

### 2.3 `db/queries.py` — ⭐⭐⭐ Khá

| Tiêu chí | Đánh giá |
|-----------|----------|
| Context manager | ✅ `get_db()` đúng pattern, auto-close |
| Schema migration | ✅ `init_db()` check columns trước khi ALTER — backward compatible |
| Queries | ✅ Parameterized queries — chống SQL injection |
| Vấn đề | ⚠️ Mỗi query mở/đóng connection riêng — không connection pooling |
| Vấn đề | ⚠️ `update_turn_status()` build SQL dynamic bằng string format — dễ bug |
| Vấn đề | ⚠️ Không có index trên `execution_turns.execution_id` |
| Vấn đề | ⚠️ `DB_FILE` hardcode — khó test và deploy nhiều instance |

### 2.4 `services/execution.py` — ⭐⭐⭐⭐ Tốt

| Tiêu chí | Đánh giá |
|-----------|----------|
| Thread safety | ✅ `_lock` bảo vệ shared state |
| ThreadSafeStdout | ✅ Giải pháp sáng tạo để redirect stdout per-thread |
| QueueWriter | ✅ Bridge tốt giữa sync thread và async event loop |
| Cleanup | ✅ `cleanup_execution()` trong finally block |
| Vấn đề | ⚠️ `start_execution_thread()` quá dài (~80 LOC trong nested function) |
| Vấn đề | ⚠️ Timeout 3600s hardcode — nên configurable |
| Vấn đề | ⚠️ Không giới hạn số execution đồng thời |

### 2.5 `middleware/auth.py` — ⭐⭐⭐ Khá

| Tiêu chí | Đánh giá |
|-----------|----------|
| Auth flow | ✅ Dual auth: session cho web, API key cho REST |
| Rate limiting | ✅ Tích hợp rate limiter |
| IP detection | ✅ Hỗ trợ X-Forwarded-For |
| Vấn đề | ⚠️ `API_KEY` chỉ warning khi thiếu, không fail fast |
| Vấn đề | ⚠️ Plaintext password comparison — thiếu hashing |
| Vấn đề | ⚠️ Session auth dùng cookie không có CSRF protection |

### 2.6 `middleware/rate_limit.py` — ⭐⭐⭐⭐ Tốt

| Tiêu chí | Đánh giá |
|-----------|----------|
| Implementation | ✅ Sliding window, thread-safe, đơn giản hiệu quả |
| Vấn đề | ⚠️ In-memory only — reset khi restart |
| Vấn đề | ⚠️ Không cleanup old entries — memory leak tiềm ẩn |

### 2.7 `routes/web.py` — ⭐⭐ Trung bình

| Tiêu chí | Đánh giá |
|-----------|----------|
| UI functional | ✅ Đầy đủ features: form, history, pagination, modal |
| Real-time | ✅ SSE integration cho live logs + agent thoughts |
| Conversation view | ✅ Chain of thought visualization |
| Vấn đề | 🔴 544 LOC — quá lớn, cần tách |
| Vấn đề | 🔴 Inline JS trong f-string — nightmare để debug |
| Vấn đề | 🔴 HTML/CSS/JS mix trong Python — vi phạm separation of concerns |
| Vấn đề | ⚠️ Unicode escapes (`\u{1F916}`) trong f-string gây syntax issues |
| Vấn đề | ⚠️ Không có error handling trong route functions |
| Vấn đề | ⚠️ `post_execute()` có thể tạo unlimited concurrent executions |

### 2.8 `routes/api.py` — ⭐⭐⭐⭐ Tốt

| Tiêu chí | Đánh giá |
|-----------|----------|
| REST design | ✅ Clean, RESTful endpoints |
| Error handling | ✅ Proper JSON error responses |
| Documentation | ✅ Có API_USAGE.md đầy đủ |
| Vấn đề | ⚠️ Thiếu input validation (workspace path traversal) |
| Vấn đề | ⚠️ Không validate model name |

### 2.9 `routes/stream.py` — ⭐⭐⭐⭐ Tốt

| Tiêu chí | Đánh giá |
|-----------|----------|
| Implementation | ✅ Đơn giản, đúng SSE spec |
| Heartbeat | ✅ 15s keepalive |
| Vấn đề | ⚠️ Không auth — bất kỳ ai biết exec_id đều xem được |

### 2.10 `static/` — ⭐⭐⭐ Khá

| Tiêu chí | Đánh giá |
|-----------|----------|
| XSS protection | ✅ DOMPurify + marked.js cho markdown |
| CSS | ✅ Responsive, clean design |
| Vấn đề | ⚠️ `app.js` quá nhỏ (35 LOC) — phần lớn JS nằm inline trong Python |

---

## 3. Đánh giá Chéo (Cross-cutting Concerns)

### 3.1 Security — ⭐⭐⭐ Khá

| Vấn đề | Mức độ | Chi tiết |
|---------|--------|----------|
| ✅ API key auth | — | Dual auth (session + API key) |
| ✅ Rate limiting | — | Login (5/min) + API (30/min) |
| ✅ XSS protection | — | DOMPurify sanitization |
| ✅ SQL injection | — | Parameterized queries |
| ⚠️ Plaintext password | Medium | `LOGIN_USER`/`LOGIN_PASS` so sánh trực tiếp |
| ⚠️ No CSRF | Medium | Session-based auth không có CSRF token |
| ⚠️ Path traversal | Medium | `workspace` không validated — có thể truy cập `/etc/` |
| ⚠️ SSE unauthenticated | Low | `/stream/{id}` không yêu cầu auth |
| ⚠️ MCP paths hardcoded | Low | Absolute paths lộ cấu trúc server |

### 3.2 Error Handling — ⭐⭐ Trung bình

- `engine/runner.py` `_on_event()` nuốt mọi exception
- Routes thiếu try/except — unhandled error trả 500 HTML cho API clients
- Không có global error handler
- Không có structured logging

### 3.3 Testing — ⭐ Yếu

- **Không có test nào** — zero unit tests, zero integration tests
- Không có test infrastructure (pytest, fixtures, etc.)
- Không có CI/CD pipeline

### 3.4 Performance — ⭐⭐⭐ Khá

- ✅ SSE streaming hiệu quả (không polling)
- ✅ Thread-based execution — non-blocking
- ⚠️ SQLite không connection pooling
- ⚠️ Không giới hạn concurrent executions
- ⚠️ Rate limiter in-memory — không persist, memory leak potential

### 3.5 Maintainability — ⭐⭐⭐ Khá

- ✅ Modular structure sau refactor
- ✅ README + API_USAGE.md documentation
- ⚠️ `routes/web.py` vẫn quá phức tạp
- ⚠️ Inline JS trong Python f-strings
- ⚠️ Thiếu type hints ở nhiều chỗ
- ⚠️ Không có linting/formatting configuration

---

## 4. Điểm Tổng và Xếp hạng

| Tiêu chí | Điểm (1-5) | Ghi chú |
|-----------|-------------|---------|
| Kiến trúc | ⭐⭐⭐⭐ (4/5) | Modular tốt sau refactor |
| Security | ⭐⭐⭐ (3/5) | Cơ bản ổn, thiếu CSRF + password hashing |
| Code Quality | ⭐⭐⭐ (3/5) | Runner tốt, web.py cần refactor tiếp |
| Error Handling | ⭐⭐ (2/5) | Thiếu structured error handling |
| Testing | ⭐ (1/5) | Không có test |
| Documentation | ⭐⭐⭐⭐ (4/5) | README + API docs + plans đầy đủ |
| Performance | ⭐⭐⭐ (3/5) | SSE tốt, thiếu concurrency limits |
| Maintainability | ⭐⭐⭐ (3/5) | Cấu trúc tốt nhưng inline JS là debt |

### **Điểm tổng: 23/40 — Khá (Functional nhưng cần cải thiện)**

---

## 5. Khuyến nghị Ưu tiên

### Ưu tiên cao (Nên làm ngay)

1. **Tách inline JS ra file riêng** — Di chuyển `_sse_live_script()`, `_sse_detail_script()` sang `static/` hoặc template files
2. **Thêm input validation cho workspace** — Chống path traversal: whitelist hoặc sandbox
3. **Thêm authentication cho SSE endpoint** — Kiểm tra session/API key
4. **Giới hạn concurrent executions** — Semaphore hoặc queue system
5. **Thêm basic tests** — Ít nhất unit test cho `db/queries.py` và `middleware/`

### Ưu tiên trung bình

6. **Tách `routes/web.py`** — Chia thành `web_index.py`, `web_execution.py`, `web_conversation.py`
7. **Structured logging** — Thay `print()` bằng `logging` module
8. **Password hashing** — Dùng `bcrypt` hoặc `passlib` cho login credentials
9. **CSRF protection** — Thêm CSRF token cho form submissions
10. **Database connection pooling** — Hoặc dùng WAL mode cho SQLite

### Ưu tiên thấp (Nice to have)

11. **CI/CD pipeline** — GitHub Actions cho lint + test
12. **Type hints** — Thêm type annotations đầy đủ
13. **Configuration management** — MCP paths từ env thay vì hardcode
14. **Health check endpoint** — `/api/health` cho monitoring
15. **Graceful shutdown** — Cleanup running executions khi app stop

---

## 6. Trạng thái Git

- **Branch hiện tại:** `api_expose_and_upgrade`
- **Files đã modified nhưng chưa commit:** `main.py`, `engine/config.py`, `AGENTS.md`
- **Files mới chưa tracked:** `db/`, `services/`, `middleware/`, `routes/`, `static/`, `.env.example`
- ⚠️ **Cần commit** các module mới để không mất code

---

*Đánh giá bởi OpenHands Agent — 2026-04-05*
