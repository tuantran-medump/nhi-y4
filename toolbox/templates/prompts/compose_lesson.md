# Tổng hợp chú thích và Phần B cho một bài (model mạnh)

Đọc: `toolbox/PLAYBOOK.md` mục 2.1 đến 2.7 và mục 6; các file thẻ `kho/lessons/<bài>/cards_*.json`; `kho/lessons/<bài>/body_numbered.txt` theo từng đoạn (offset/limit, mỗi lần khoảng 120 dòng). Hiệp hội ưu tiên của bài ghi trong `data/lessons.csv`. Không mở lại file nguồn gốc trừ khi cần xác minh một con số.

Ghi:

1. `kho/lessons/<bài>/notes.json`: mảng `{"line": n, "note": "(...)"}`. Gộp notes từ các file thẻ, bỏ trùng, bỏ mục sách đã nói, bỏ mục ngoài trẻ em, tối đa 1-2 chú thích mỗi dòng. Chú thích trong đúng một cặp ngoặc đơn, không ngoặc lồng, có mã S/C/N/R, mở đầu bằng tên người tạo nguồn nếu biết (`Giảng viên:`, `Ghi chú lớp:`, `Slide BS X:`). Dòng thuộc bảng hoặc khối không chèn được thì chuyển lên dòng tên bảng.

2. `kho/lessons/<bài>/extra.json`, giá trị là Markdown dùng `-`, `+`:
- `summary`: Tóm tắt không quá 1 trang A4 (350-450 từ), chỉ tóm từ thân bài, có mã `[G1:pN]` cho số liệu, liều (N lấy từ dấu `<<pN>>` gần nhất phía trên dòng).
- `approach`, `experience`, `exam`: gộp từ thẻ thành mạch logic, giữ mã nguồn.
- `conflicts`: mỗi điểm có tiêu đề in đậm, các dòng `- Sách: ...`, `- Nguồn: ...`, `- Kết luận theo <tên guideline năm>: ...`. Loại điểm không phải mâu thuẫn thật (lỡ lời, khác đối tượng, khác cách diễn đạt). Kết luận ưu tiên hiệp hội trong `lessons.csv`; không có thì dùng guideline uy tín khác và ghi rõ tên. Được tra web hoặc PubMed chỉ cho các điểm này, ghi nguồn vào `data/external_sources.csv` (code,title,url) với mã E tiếp theo số lớn nhất đang có, trích `[E7:p1]`. Không tìm được thì ghi "Chưa thấy có nguồn hiệp hội/guideline xác nhận". Không suy đoán.
- `missing`: chỗ thiếu, chỗ sách in lỗi, trang scan hỏng đã biết.

Không thêm kiến thức ngoài nguồn trừ mục conflicts. Không đổi số, liều. Thẻ có vẻ sai thì bỏ.

Kiểm tra từ thư mục repo:
`python toolbox/scripts/b5_annotate.py <bài> apply toolbox/kho/lessons/<bài>/notes.json` rồi `python toolbox/scripts/check_lesson.py <bài>`. Phải trả về `[]`. Lỗi `uncited_fact` hoặc `block_number` thuộc thân bài thì báo lại, đừng sửa thân bài.
