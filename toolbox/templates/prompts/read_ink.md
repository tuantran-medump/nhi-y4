# Đọc viết tay và trang scan (model nhỏ)

Đầu vào: `kho/ink/<bài>/tasks.json` và các ảnh trong cùng thư mục, danh sách id được giao.

Với mỗi task, mở ảnh và ghi `kho/ink/<bài>/results/<id>.json` dạng `{"1": "nội dung", "2": "..."}`, đủ mọi nhãn trong `items`.

- `kind: ink`: mỗi vùng có nhãn đỏ `[n]`, chỉ chép nét viết tay.
- `kind: page`: chép cả trang thành Markdown, bảng dùng pipe table, nhãn là `1`.
- Chỉ chép những gì nhìn thấy, không suy diễn, không sửa kiến thức.
- Chữ không chắc: `[?chữ?]`. Không đọc được: `[không đọc được]`. Vùng vô nghĩa: `""`.
- Giữ nguyên viết tắt y khoa và mũi tên `→ ↑ ↓`.
