# Sửa lỗi OCR (model nhỏ)

Đầu vào: kết quả `b2_ocr_fix.py <bài> suspects`, ảnh trang gốc khi cần đối chiếu.

Chỉ phát file JSON bản vá, không chép lại văn bản:
`[{"line": 12, "old": "phồi", "new": "phổi", "learn": true}]`

- Chỉ sửa lỗi nhận dạng. Không đổi từ, số, đơn vị theo suy đoán.
- Số, liều, đơn vị nghi sai: đối chiếu ảnh trang gốc. Vẫn không chắc thì đổi thành `[?chữ?]`.
- `learn: true` chỉ cho lỗi lặp lại chắc chắn đúng ở mọi ngữ cảnh.
