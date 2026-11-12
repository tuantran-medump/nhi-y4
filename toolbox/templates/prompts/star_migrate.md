# Chuyển chú thích mâu thuẫn của một bài đã làm sang kiểu dòng ⭐

Chỉ dùng file sản phẩm trong `toolbox/kho/lessons/<bài>/`: `extra.json` (khóa `conflicts`), `notes.json`, `body_numbered.txt` (đọc theo đoạn bằng offset/limit hoặc grep, không đọc cả file). Không mở tài liệu gốc, thẻ, evidence hay web.

Việc:
1. Với mỗi điểm trong `conflicts`, tìm dòng thân bài tương ứng trong `body_numbered.txt` (số dòng = khóa `line` của notes). Thường đã có chú thích ở dòng đó nhắc "Mâu thuẫn nguồn" hoặc cùng nội dung.
2. Thêm khóa `resolve` cho chú thích ở dòng đó: một câu ngắn (tối đa khoảng 40 từ) bắt đầu `Kết luận theo <tên guideline năm>: ...`, giữ đúng nội dung và mã nguồn (`[E..]`, `[R..]`, ...) của dòng kết luận trong `conflicts`. Điểm không có kết luận thì `Kết luận: Chưa thấy có nguồn hiệp hội/guideline xác nhận`. Không thêm ý mới.
3. Dòng chưa có chú thích thì tạo chú thích mới `{"line": n, "note": "(<người tạo nguồn>: <nguồn nói gì> [mã:p])", "resolve": ...}` lấy từ dòng `Nguồn:` của điểm đó. Dòng thuộc bảng/khối thì dùng dòng tên bảng. Mỗi dòng chỉ một chú thích có `resolve`; nhiều điểm cùng một dòng thì gộp kết luận.
4. Bỏ cụm "xem Mâu thuẫn nguồn" trong các chú thích đã có `resolve`. Không sửa chú thích khác, không đổi `extra.json`.

Ghi `notes.json` bằng script python (công cụ Write rồi chạy, script tạm để trong `tmp_star/` của bài, không dùng heredoc). Kiểm tra từ thư mục repo:
`python toolbox/scripts/b5_annotate.py <bài> apply toolbox/kho/lessons/<bài>/notes.json` rồi `python toolbox/scripts/check_lesson.py <bài>`, phải ra `[]`.

Báo lại ngắn: số điểm mâu thuẫn, số chú thích có `resolve`, điểm nào không tìm được dòng.
