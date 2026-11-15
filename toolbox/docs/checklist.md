# Checklist sản phẩm hoàn thiện

Dùng cho mỗi bài. Quy định gốc nằm ở `toolbox/PLAYBOOK.md`, số trong ngoặc là mục tương ứng.

Mã bài: ________  Ngày kiểm: ________

## 1. Tự động

- [ ] `python toolbox/scripts/check_lesson.py <mã bài>` trả về rỗng (7)
- [ ] `python toolbox/scripts/progress.py <mã bài>` báo đã xong mọi bước (5)

## 2. Nguồn

- [ ] Mọi ý truy được về file và trang trong `Tài liệu`, không có kiến thức ngoài (2.5)
- [ ] Thân bài bài trong sách chỉ lấy từ Nhi Khoa Tập 1, 2 (2.1)
- [ ] Bài ngoài sách có nhãn "Ngoài giáo trình" và viết từ slide giảng viên mới nhất (2.2)
- [ ] Chỉ đối chiếu file cùng chuyên khoa và file tổng hợp (2.1)
- [ ] Không dùng bản đã đánh dấu trùng (A2)
- [ ] Không có file nào trong `Tài liệu` bị sửa, đổi tên, xóa (2.8)

## 3. Thân bài

- [ ] Đề mục đúng số và đúng thứ tự của sách (2.2)
- [ ] Câu chữ khớp sách, chỉ sửa lỗi OCR (2.2)
- [ ] Đã đối chiếu ảnh trang gốc cho mọi số, liều, đơn vị nghi lỗi (2.2)
- [ ] Không còn `[?chữ?]` chưa xử lý (2.2)
- [ ] Mỗi ý một dòng, thụt lề đúng quan hệ cha con (2.2)
- [ ] Ký hiệu đúng quy ước: `-`, `+`, `*`, số thường, số La Mã (2.2)
- [ ] Có đủ Mục tiêu học tập, Câu hỏi tự lượng giá, Đáp án, Tài liệu tham khảo của sách (6)
- [ ] Đối chiếu ngẫu nhiên 3 trang trong bài với ảnh sách gốc: không thiếu đoạn, không sai số

## 4. Chú thích, trích dẫn, mâu thuẫn

- [ ] Số liệu, liều, tiêu chuẩn, chỉ định đều có mã nguồn (2.6)
- [ ] Số trang trong mã nguồn là số trang của file PDF, kể cả giáo trình (2.6)
- [ ] Mã nguồn ở cuối câu, nhiều trang cùng nguồn đã gộp (2.6)
- [ ] Mọi chỉnh sửa từ nguồn khác nằm trong ngoặc đơn ngay sau ý, có mã nguồn (2.3)
- [ ] Mâu thuẫn có đủ: điểm lệch, từng nguồn nói gì, kết luận của hiệp hội ưu tiên, hoặc hiệp hội uy tín khác nếu không tìm được, có ghi tên (2.4)
- [ ] Thân bài vẫn giữ theo sách ở điểm mâu thuẫn (2.4)
- [ ] Mỗi điểm mâu thuẫn có 2 dòng ⭐ thụt vào ngay dưới ý trong thân bài: chú thích nguồn và kết luận theo guideline, khớp với mục "Mâu thuẫn nguồn" (2.4)
- [ ] Nguồn ngoài chỉ dùng cho điểm mâu thuẫn, có mã `E` trong danh mục (2.4)
- [ ] Điểm không có nguồn giải quyết ghi "Chưa thấy có nguồn hiệp hội/guideline xác nhận" (2.4)

## 5. Hình và bảng

- [ ] Bảng và lưu đồ có chữ đã gõ lại, đủ hàng cột so với gốc (2.7)
- [ ] Hình gốc đặt đúng chỗ, giữ số hình và chú thích (2.7)
- [ ] Tên bảng, tên hình in nghiêng, không gạch đầu dòng (2.7)

## 6. Cấu trúc và Phần B

- [ ] Đầu file có tên bài, mã bài, hiệp hội trọng tài, ngày dựng (6)
- [ ] Tóm tắt 1 trang nằm đầu bài, có mã nguồn, không quá 1 trang (6)
- [ ] Đủ 6 mục Phần B theo đúng thứ tự (6)
- [ ] Mục không có nội dung ghi "Không có trong nguồn" (6)
- [ ] "Cần bổ sung" liệt kê trang thiếu trong bản scan và chỗ thiếu nội dung (A4, 2.5)
- [ ] Danh mục nguồn đủ mọi mã đã dùng (6)

## 7. File PDF

- [ ] Đúng vị trí `NHI_Y4_SAP_XEP\Bài học\<Chuyên khoa>\<Tên bài>.pdf`, mỗi bài đúng 1 file (1)
- [ ] Khổ A4, có mục lục, bookmark, số trang (6)
- [ ] Dấu tiếng Việt hiển thị đúng, tìm kiếm chữ được (6)
- [ ] Mở xem từng trang: không tràn lề, không vỡ bảng, không trang trắng
- [ ] Sau khi có link Drive: mọi mã nguồn bấm được, mở đúng file (2.6)

## 7b. Bước giao agy

- [ ] Mọi bước agy chạy qua `agy_run.py`, kết quả đã qua script kiểm tra, `agy/log.jsonl` không còn dòng lỗi chưa xử lý (4)
- [ ] B6: đã đọc hết đầu ra `b6_pairs.py`, không chỉ các dòng ⚑ (4)
- [ ] Đã dựng cả `b7_render.py` và `b8_render_b14.py` (4)

## 8. Báo cáo cho người dùng

- [ ] Nêu rõ bước nào chưa chạy hoặc chưa kiểm chứng (7)
- [ ] Liệt kê trang thiếu, mâu thuẫn chờ quyết, mục "Cần bổ sung" (7)
- [ ] Quyết định mới của người dùng đã ghi vào playbook (7)
