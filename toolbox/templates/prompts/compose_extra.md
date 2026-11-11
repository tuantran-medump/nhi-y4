# Chú thích và Phần B (model mạnh)

Đầu vào: `body.md`, `novel_<mã>.jsonl`, `p*.ink.txt`, thẻ từ `cards.py <bài>`. Không mở file gốc nếu đã có các file này.

1. Thêm mã nguồn cuối ý vào `body.md`: số liệu, liều, tiêu chuẩn, chỉ định, ý quan trọng. Số trang là số trang của file PDF, với sách lấy từ dấu `<<pN>>`.
2. Với câu `changed_fact` hoặc nguồn khác có chỉnh sửa: giữ câu sách, thêm ngay sau ý `(Nguồn năm: nội dung [S12:p4])`.
3. Mâu thuẫn thật: ghi vào `conflicts` điểm lệch, từng nguồn nói gì, kết luận của hiệp hội ưu tiên trong `lessons.csv`. Không tìm được thì dùng hiệp hội uy tín khác và ghi rõ tên. Guideline ngoài thư mục được tra riêng cho điểm đó, thêm vào `data/external_sources.csv` với mã `E`.
4. Ghi `extra.json` với khóa `summary`, `approach`, `experience`, `exam`, `conflicts`, `missing`. Mục không có nội dung để chuỗi rỗng.
5. Ghi thẻ cho ý dùng lại được: `cards.add(mã, bài, ý, trang)`.
6. Không thêm kiến thức ngoài nguồn. Thiếu thì ghi vào `missing`.
