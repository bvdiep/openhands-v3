# TÀI LIỆU NGHIỆP VỤ: QUẢN LÝ VÒNG ĐỜI VÀ ĐA PHIÊN AGENT (MULTI-SESSION & LIFECYCLE MANAGEMENT)

## 1. Định nghĩa trạng thái (Status) của Agent
Hệ thống quản lý vòng đời Agent qua các trạng thái:
- **running**: Đang thực thi tác vụ.
- **waiting_for_input**: Đang tạm dừng ở hàng đợi đầu vào, chờ người dùng đưa thêm chỉ thị. (Có thể Resume).
- **completed**: Đã kết thúc do hoàn thành hoặc bị người dùng ép dừng (Stop). Tài nguyên đã giải phóng, không thể Resume.
- **timeout**: Đã hết thời gian chờ ngầm (ví dụ 3600s). Tài nguyên đã giải phóng, không thể Resume.

## 2. Giao diện Lịch sử (History UI)
- Mỗi bản ghi lịch sử hiển thị trạng thái của Agent thông qua mã màu (Color-coding):
  - **Màu Xanh lá/Xanh dương:** Trạng thái `waiting_for_input` (Active / Đang chờ lệnh).
  - **Màu Xám/Nhạt:** Trạng thái `completed`, `timeout`, `error` (Đã đóng).
- Các nút thao tác gắn trên từng dòng lịch sử:
  - Nút **Resume/Continue**: Chỉ hiển thị hoặc kích hoạt khi trạng thái là `waiting_for_input`.
  - Nút **Stop**: Chỉ hiển thị hoặc kích hoạt khi trạng thái là `running` hoặc `waiting_for_input`.

## 3. Thao tác điều khiển cốt lõi (Control Actions)

**3.1. Stop Agent (Dừng đơn lẻ)**
- Cho phép dừng bất kỳ Agent nào (từ danh sách History hoặc Agent đang active ở ô chat).
- **Quy trình UI:** Nếu Stop Agent đang hiện diện ở ô chat, Frontend gán `current_exec_id = null`, xóa trắng toàn bộ nội dung DOM của ô chat (reset form). Hệ thống fetch lại History để hiển thị Agent vừa Stop thành trạng thái `completed`.
- **Quy trình API:** Gọi `POST /api/execute/{exec_id}/stop`, đẩy tín hiệu `__STOP__` vào queue.

**3.2. Stop All (Dừng tất cả)**
- Giao diện cung cấp nút "Stop All".
- **Quy trình API:** Gửi yêu cầu dừng tất cả Agent đang ở trạng thái hoạt động, **loại trừ** (exclude) Agent đang active ở ô chat (`current_exec_id`). Backend quét mảng queue nội bộ và đẩy tín hiệu `__STOP__` vào các queue phù hợp.

**3.3. Resume / Continue (Chạy tiếp Agent)**
- Người dùng chọn một Agent màu xanh từ History.
- **Quy trình UI:**
  1. Nếu có một Agent khác đang active ở ô chat, Agent cũ đó bị đẩy xuống History (nhưng vẫn giữ nguyên trạng thái nội tại của nó ở Backend).
  2. Frontend gọi API lấy toàn bộ tin nhắn (`/api/execute/{exec_id}/messages`) của Agent được chọn.
  3. Render lại cuộc hội thoại lên màn hình và gán `current_exec_id = new_id`.
  4. Mở khóa ô chat để người dùng tiếp tục nhập lệnh. Tin nhắn gửi đi sẽ đi vào queue của phiên bản Resume.

**3.4. Xử lý Timeout (Hết hạn)**
- Xử lý hoàn toàn ở Backend. Khi vòng lặp hàng đợi (`in_q.get(block=True, timeout=3600)`) tung ra ngoại lệ `queue.Empty`, hệ thống tự động:
  1. Gán trạng thái thành `timeout` trong Database.
  2. Đóng session LLM, xóa biến tạm trên RAM, dọn dẹp luồng.
- Frontend trong lần poll tiếp theo sẽ thấy trạng thái `timeout`, tự động đổi màu nhãn thành xám và vô hiệu hóa nút Resume.

## 4. Yêu cầu kỹ thuật triển khai

**Backend (`routes/api.py`, `services/execution.py`):**
1. Bổ sung API `POST /api/execute/stop-all` với tham số `exclude_id`.
2. Chỉnh sửa logic xử lý exception timeout trong `services/execution.py` để gọi `update_execution_status(exec_id, "timeout")` thay vì `completed`.
3. Đảm bảo API trả về danh sách History cập nhật đủ các field status cho Frontend.

**Frontend (`static/app.js`, `routes/web.py`):**
1. Duy trì state `window.current_exec_id` để biết Agent nào đang kiểm soát DOM chat.
2. Viết hàm `loadExecution(exec_id)` xử lý dọn dẹp DOM và render lại từ dữ liệu tin nhắn.
3. Cập nhật logic Polling History để đồng bộ hóa mã màu thẻ DOM dựa trên status trả về.