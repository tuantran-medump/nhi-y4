# Rút thẻ bằng chứng (model nhỏ)

Đầu vào: `kho/lessons/<bài>/body_numbered.txt` (đọc theo đoạn, mỗi lần khoảng 120 dòng) và một đoạn dòng của `kho/lessons/<bài>/evidence.md` được giao (đọc theo đoạn).

Trong bằng chứng, mỗi dòng có mã nguồn như `[S061:p12]`; dòng `(viết tay)` là ghi chú tay; `!KHÁC SÁCH` là câu gần giống sách nhưng khác.

Ghi file JSON UTF-8 được giao với các khóa:
- `notes`: mảng `{"line": số dòng trong body_numbered, "note": "(Nguồn, năm nếu có: nội dung [S061:p12])"}`. Chỉ khi nguồn cập nhật, làm rõ, bổ sung chi tiết cụ thể hoặc khác với đúng ý ở dòng đó của sách. Không ghi điều sách đã nói. `note` nằm trong một cặp ngoặc đơn, bên trong không có ngoặc đơn khác, có ít nhất một mã S, C, N hoặc R. Mở đầu bằng tên người tạo nguồn nếu biết: Giảng viên, Ghi chú lớp, Tài liệu ôn, Slide BS X.
- `conflicts`: mảng `{"line", "point", "book", "source", "cite"}`. Chỉ khi hai bên không thể cùng đúng về chỉ định, liều, ngưỡng, tiêu chuẩn.
- `approach`: mảng chuỗi, bước tiếp cận và biện luận lâm sàng về bệnh của bài, kết thúc bằng mã nguồn.
- `experience`: mảng chuỗi, kinh nghiệm lâm sàng, mẹo của giảng viên, kết thúc bằng mã nguồn.
- `exam`: mảng chuỗi, câu hỏi thi hoặc điểm hay ra thi, kết thúc bằng mã nguồn.

Quy tắc:
- Chỉ dùng điều có trong bằng chứng. Không thêm kiến thức ngoài. Không sửa số, liều.
- Chỉ lấy nội dung về bệnh của bài ở trẻ em. Bỏ bệnh khác, câu cụt, chữ rác, tiêu đề slide.
- Bỏ mọi câu chứa `[?...?]` hoặc `[không đọc được]`.
- Súc tích, tiếng Việt, giữ thuật ngữ tiếng Anh.
- Kiểm tra JSON hợp lệ bằng python trước khi xong.
