# Soát OCR từng trang (model nhỏ)

Đầu vào: `kho/lessons/<bài>/review/tasks.json`, danh sách id được giao. Mỗi task có ảnh trang (`image`) và chữ OCR có số dòng (`text`).

Với mỗi task, xem ảnh, so với từng dòng chữ, rồi ghi `kho/lessons/<bài>/review/results/<id>.json`. Không có lỗi thì ghi `[]`. Không chép lại văn bản:
`[{"line": 12, "old": "phôi", "new": "phổi"}]`

- Soát kỹ dấu tiếng Việt. Lỗi hay gặp vẫn ra từ có nghĩa: tiêu/tiểu, thê/thể, phôi/phổi, đây/đầy, yêu/yếu, tô/tố, âm/ẩm.
- Tiêu đề in hoa cũng phải soát dấu (MỤC TIÊU, VIÊM PHỔI). Ký hiệu khí: `SpO,` là `SpO2`, `FiO,` là `FiO2`, `CO,` là `CO2`, ghi `"verified": true`.
- `old` chỉ gồm đoạn đủ ngắn nhưng phải có trong dòng đó. Mỗi dòng có nhiều lỗi thì ghi nhiều mục, theo thứ tự trái sang phải.
- Chỉ sửa cho khớp ảnh. Không đổi từ, số, đơn vị theo suy đoán, không sửa kiến thức.
- Sửa chữ số: phải nhìn rõ trên ảnh và ghi `"verified": true`. Không chắc thì đổi đoạn đó thành `[?chữ?]`.
- Thiếu một dòng so với ảnh: thêm vào cuối dòng trước bằng mục sửa, `new` là nội dung cũ cộng xuống dòng cộng dòng thiếu.
- Bảng, lưu đồ: bọc phần OCR bằng dòng `<<block:t1>>` trước dòng đầu và `<<endblock>>` sau dòng cuối qua mục sửa, tên khối là `p` + mã trang của task + chữ cái, ví dụ task `p0128` có khối `p0128a`, `p0128b`, để không trùng giữa các trang. Không cần sửa chữ bên trong khối.
- Hình minh họa (giải phẫu, X-quang, biểu đồ): bọc phần OCR rác của hình thành khối tên `p<mã trang>f` (nhiều hình thì `f1`, `f2` đều kết thúc bằng chữ số thì đặt `p0088af`, `p0088bf`, luôn tận cùng bằng `f`). Tên hình "Hình x.y ..." ở ngoài khối, vẫn soát chữ bình thường. Nếu OCR không sinh ra chữ nào trong hình thì chèn khối rỗng ở dòng ngay trước tên hình.
- `learn: true` chỉ cho lỗi chữ không có từ nào đúng trùng dạng đó, ví dụ `phdi`. Không dùng cho `phôi`, `tiêu`, `thê`.
