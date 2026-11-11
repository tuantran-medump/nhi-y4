# Sửa lỗi OCR (model nhỏ)

Đầu vào: kết quả `b2_ocr_fix.py <bài> suspects`, ảnh trang gốc khi cần đối chiếu.

Chỉ phát file JSON bản vá, không chép lại văn bản:
`[{"line": 12, "old": "phồi", "new": "phổi", "learn": true}]`

- Chỉ sửa lỗi nhận dạng. Không đổi từ, số, đơn vị theo suy đoán.
- Số, liều, đơn vị nghi sai: đối chiếu ảnh trang gốc. Vẫn không chắc thì đổi thành `[?chữ?]`.
- Sửa chữ số (ví dụ `5OO` thành `500`): bắt buộc đã xem ảnh gốc và ghi `"verified": true`, nếu không script từ chối.
- `learn: true` chỉ cho lỗi chữ lặp lại chắc chắn đúng ở mọi ngữ cảnh. Từ điển không nhận mục có chữ số.
- Bảng, lưu đồ: bọc phần OCR bằng dòng `<<block:t1>>` và `<<endblock>>` qua bản vá, rồi gõ lại ở `kho/lessons/<bài>/blocks/t1.md`.
