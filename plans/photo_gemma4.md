Nhiệm vụ của bạn là sử dụng Gemma 4 để sinh mô tả ảnh của các ảnh trong một thư mục ảnh.

Bạn được cung cấp các thông tin sau:
- Tài liệu để gọi model tại đây: https://marketplace.fptcloud.com/en/models/gemma-4-31b-it
- API key: sk-PN_R9sCjReZSfgbu7oUlJm6xI4c4Ebdp90QpWSKvbx8=
- Hãy sử dụng model gemma-4-31B-it
- Thư mục ảnh: /home/dd/Desktop/BSM/test

Nhiệm vụ của bạn là sử dụng model để trích xuất ra mô tả của tất cả các ảnh trong thư mục được cho. Chú ý là chỉ xử lý ảnh, không xử lý video.

Kết quả cần được lưu vào file plans/photobsm_motaanh.json với định dạng:
{
  "photo": "path_to_photo.jpg",
  "description": "mô tả của ảnh"
}
