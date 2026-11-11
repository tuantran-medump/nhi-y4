# Xếp cấp dòng (model nhỏ)

Đầu vào: `kho/lessons/<bài>/units.txt`, mỗi dòng dạng `số<TAB>nội dung`.

Ghi file JSON `kho/lessons/<bài>/layout.json`, chỉ gồm các dòng khác mặc định, không chép lại văn bản:
`[{"line":3,"level":2,"marker":"+","split":["gồm:",","]},{"line":9,"join_prev":true}]`

- Mặc định mỗi dòng là cấp 1, ký hiệu `-`. Đề mục có số của sách (`1.`, `2.1.`) được nhận tự động, không cần ghi.
- Đề mục không số (Bài, MỤC TIÊU HỌC TẬP, CÂU HỎI TỰ LƯỢNG GIÁ, ĐÁP ÁN, TÀI LIỆU THAM KHẢO): ghi `"marker":"##"`.
- Mỗi ý một dòng, thụt theo quan hệ cha con: cấp 1 `-`, cấp 2 `+`, cấp 3 `*`. Dòng con ghi `level` và `marker`.
- Dòng dẫn kết thúc bằng dấu hai chấm thì các ý liệt kê ngay sau nó xuống một cấp.
- Danh sách đếm được dùng `1.`, nhóm lớn dùng `I.`. Dòng đã có sẵn số của sách thì ghi đúng số đó làm `marker`.
- `split`: câu liệt kê nhiều ý trong một dòng. Phần tử đầu là chuỗi kết thúc dòng dẫn, phần tử sau là dấu ngăn các ý con. Chỉ dùng khi tách không làm đổi nghĩa, không tách số thập phân.
- `join_prev`: câu bị ngắt qua trang hoặc bị tách sai, nối vào dòng trước.
- Không đổi từ ngữ. Script so khớp từng từ và từ chối nếu sai.
