# Xếp cấp dòng (model nhỏ)

Đầu vào: kết quả `b2b_layout.py <bài> units` (dòng đánh số).

Chỉ phát bảng JSON cho các dòng khác mặc định, không chép lại văn bản:
`[{"line":3,"level":2,"marker":"+","split":["gồm:",","]},{"line":9,"join_prev":true}]`

- Mặc định mỗi dòng là cấp 1, ký hiệu `-`. Đề mục số của sách được nhận tự động.
- Cấp 1 `-`, cấp 2 `+`, cấp 3 `*`. Danh sách đếm được dùng `1.`, nhóm lớn dùng `I.`
- `split`: phần tử đầu kết thúc dòng dẫn, phần tử sau là dấu ngăn các ý con.
- `join_prev`: nối câu bị ngắt qua trang vào dòng trước.
- Không đổi từ ngữ. Script sẽ so khớp từng từ và từ chối nếu sai.
