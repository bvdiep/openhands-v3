# Đánh giá và Kế hoạch Cải thiện Ứng dụng OpenHands

## 1. Đánh giá Lộ trình và Tính Khả thi

Dưới đây là đánh giá về lộ trình bạn đề xuất, bao gồm mức độ ưu tiên và tính khả thi của từng hạng mục dựa trên tài liệu OpenHands SDK:

1. **Chuyển giao diện hiện tại thành giao diện chat (Không đóng conversation)**
   - **Đánh giá:** Rất hợp lý và khả thi. Đây là tính năng cốt lõi của một trợ lý AI. OpenHands SDK hỗ trợ việc duy trì một `Conversation` thông qua luồng sự kiện (event stream). Việc không đóng conversation hoàn toàn khả thi bằng cách giữ instance của agent chạy ngầm hoặc kết nối lại với cùng một ID conversation.
   - **Ưu tiên:** Cao (Nền tảng cho các tính năng khác).

2. **Chuyển model thành dropdown list cho phép chọn nhiều models**
   - **Đánh giá:** Rất khả thi. OpenHands SDK cho phép cấu hình `LLMConfig` linh hoạt. Bạn có thể dễ dàng thay đổi model thông qua giao diện và truyền cấu hình mới vào SDK khi khởi tạo hoặc cập nhật agent.
   - **Ưu tiên:** Cao (Cải thiện trải nghiệm người dùng ngay lập tức).

3. **Tích hợp các MCP servers có sẵn (từ `/home/dd/work/diep/mcp-servers`)**
   - **Đánh giá:** Khả thi. OpenHands hỗ trợ Model Context Protocol (MCP). Bạn có thể đọc danh sách các thư mục/cấu hình từ đường dẫn trên, hiển thị lên UI dưới dạng checkbox, và truyền danh sách các MCP được chọn vào cấu hình của OpenHands khi khởi tạo.
   - **Ưu tiên:** Trung bình - Cao (Mở rộng khả năng của agent rất tốt).

4. **Hủy nhiệm vụ đang làm của OpenHands**
   - **Đánh giá:** Khả thi. OpenHands SDK cung cấp các cơ chế để dừng (stop) hoặc đóng (close) một agent/conversation đang chạy.
   - **Ưu tiên:** Cao (Rất cần thiết khi agent đi sai hướng hoặc tốn quá nhiều thời gian).

5. **Can thiệp vào nhiệm vụ đang làm (chỉ dẫn thêm)**
   - **Đánh giá:** Khả thi. Trong lúc agent đang chạy, bạn có thể gửi thêm các sự kiện `MessageAction` vào luồng sự kiện của conversation. Agent sẽ nhận được thông điệp mới và điều chỉnh hành vi của mình.
   - **Ưu tiên:** Cao (Tăng tính tương tác và kiểm soát).

6. **Bổ sung khái niệm "Skill" vào hệ thống**
   - **Đánh giá:** Khả thi. OpenHands có hỗ trợ việc thêm các kỹ năng (skills) thông qua việc cung cấp các công cụ (tools) tùy chỉnh hoặc tiêm (inject) kiến thức vào system prompt. Bạn có thể tạo một thư viện các đoạn mã Python/Bash hoặc các hướng dẫn cụ thể và cho phép người dùng chọn để "trang bị" cho agent.
   - **Ưu tiên:** Trung bình (Tính năng nâng cao).

7. **Tối ưu, chạy parallel, chạy sub-agent**
   - **Đánh giá:** Khả thi nhưng phức tạp. OpenHands SDK cho phép khởi tạo nhiều instance của `OpenHands` cùng lúc. Bạn có thể thiết kế một kiến trúc trong đó một "Main Agent" phân chia công việc cho các "Sub-Agents" chạy song song và tổng hợp kết quả.
   - **Ưu tiên:** Thấp (Nên làm sau khi các tính năng cơ bản đã ổn định).

---

## 2. Kế hoạch Triển khai Chi tiết

Dưới đây là kế hoạch triển khai từng bước cho các hạng mục trên:

### Giai đoạn 1: Nền tảng Giao diện và Cấu hình Cơ bản (Mục 1 & 2)
- **Bước 1.1: Xây dựng UI Chat:**
  - Thiết kế lại giao diện frontend: Thêm ô nhập liệu (input box), khu vực hiển thị tin nhắn (message list) phân biệt giữa User và Agent.
  - Tích hợp Markdown/Code highlighting cho tin nhắn của Agent.
- **Bước 1.2: Quản lý State của Conversation:**
  - Cập nhật backend để duy trì kết nối với OpenHands SDK (ví dụ: sử dụng WebSockets hoặc Server-Sent Events để stream log/tin nhắn theo thời gian thực).
  - Lưu trữ lịch sử chat vào database hoặc file để có thể tải lại khi người dùng mở lại ứng dụng (sử dụng Conversation ID).
- **Bước 1.3: Cấu hình Model Động:**
  - Thêm dropdown list trên UI chứa danh sách các model được hỗ trợ (ví dụ: `gpt-4o`, `claude-3-5-sonnet`, v.v.).
  - Khi người dùng chọn model và bắt đầu chat, backend sẽ khởi tạo `LLMConfig` tương ứng và truyền vào OpenHands.

### Giai đoạn 2: Mở rộng Khả năng và Kiểm soát (Mục 3, 4 & 5)
- **Bước 2.1: Tích hợp MCP Servers:**
  - Backend: Viết API quét thư mục `/home/dd/work/diep/mcp-servers` để lấy danh sách các MCP hiện có.
  - Frontend: Hiển thị danh sách này dưới dạng checkbox.
  - Tích hợp SDK: Khi khởi tạo OpenHands, đọc các checkbox được chọn và cấu hình tham số `mcp_servers` (hoặc tương đương trong SDK) để agent có thể sử dụng các công cụ này.
- **Bước 2.2: Tính năng Hủy (Cancel):**
  - Thêm nút "Stop/Cancel" trên UI khi agent đang xử lý.
  - Backend: Gọi phương thức `close()` hoặc `stop()` của instance OpenHands đang chạy để ngắt tiến trình.
- **Bước 2.3: Tính năng Can thiệp (Intervene):**
  - Cho phép ô nhập liệu vẫn hoạt động khi agent đang chạy.
  - Khi người dùng gửi tin nhắn mới, backend sẽ đẩy một `MessageAction` vào event stream của conversation hiện tại. Agent sẽ đọc được tin nhắn này ở bước tiếp theo của vòng lặp suy luận (reasoning loop) và phản hồi.

### Giai đoạn 3: Tính năng Nâng cao (Mục 6 & 7)
- **Bước 3.1: Triển khai Hệ thống "Skill":**
  - Định nghĩa cấu trúc của một "Skill" (có thể là một file JSON/YAML chứa mô tả, system prompt bổ sung, hoặc các custom tools).
  - Tạo UI để quản lý và chọn Skills.
  - Tích hợp: Khi khởi tạo agent, nối (append) nội dung của các Skills được chọn vào `system_prompt` hoặc đăng ký các custom tools tương ứng với SDK.
- **Bước 3.2: Nghiên cứu và Triển khai Sub-agents / Parallel Execution:**
  - Thiết kế kiến trúc: Tạo một "Orchestrator Agent" có nhiệm vụ nhận yêu cầu lớn, chia nhỏ thành các sub-tasks.
  - Triển khai: Sử dụng Python `asyncio` để khởi tạo nhiều instance `OpenHands` chạy song song cho từng sub-task.
  - Tổng hợp: Orchestrator Agent sẽ đợi các sub-agents hoàn thành, thu thập kết quả và đưa ra câu trả lời cuối cùng cho người dùng.

---
*Lưu ý: Kế hoạch này được lưu trữ tại `plans/improvement_plan.md` để làm tài liệu tham khảo cho quá trình phát triển tiếp theo.*