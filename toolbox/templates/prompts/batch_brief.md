# Brief chạy một lô

Mục tiêu: hoàn tất các bài `<danh sách mã bài>` của lô `<chuyên khoa>` theo `toolbox/PLAYBOOK.md`.

Bối cảnh: toolbox đã có sẵn, xem mục 8 của playbook. Bài mẫu đã duyệt là `G1-B08`, dùng làm chuẩn.

Luồng mỗi bài (chi tiết ở bảng giai đoạn B và "Quy tắc agy" trong playbook):
1. `progress.py <bài>` để biết bước kế tiếp. B1 bằng script.
2. B2: `b2_review.py <bài> tasks`, `agy_run.py <bài> review`, `b2_review.py <bài> apply`, rồi `agy_run.py <bài> blocks` (gõ lại bảng, lưu đồ; hình thì script tự cắt). B2a (`b2_ocr_fix.py <bài> diacritics`) do Claude làm: chỉ xem ảnh khi ngữ cảnh không đủ để quyết.
3. B2b: `b2b_layout.py <bài> units > kho/lessons/<bài>/units.txt`, `agy_run.py <bài> layout`, rồi `b2b_layout.py <bài> apply kho/lessons/<bài>/layout.json` (so khớp từng từ).
4. B3: `b3_novel.py <bài>`, Claude chốt nguồn từ `data/lesson_sources.csv`. Bài không có nguồn thì chỉ có Phần A, bỏ qua B4 và `cards`. B4: `b4_ink.py <bài> tasks`, `agy_run.py <bài> ink`, rồi `b4_ink.py <bài> merge`.
5. B5: `b5_evidence.py <bài>`, `b5_annotate.py <bài> number` (tạo `body_numbered.txt`), rồi `agy_run.py <bài> cards`, rồi `agy_run.py <bài> compose`.
6. B6: `b6_pairs.py <bài>`, Claude đọc hết, viết `resolve` vào `notes.json`, sửa kết luận trong `extra.json`. Cuối bản in có mục "Trang bằng chứng chưa có trong thẻ" (tối đa 40 trang nhiều số liệu, chỉ định, tiên lượng nhất mà bài chưa dùng): ý đáng giữ thì thêm chú thích, còn lại bỏ qua. Mục `missing` chỉ giữ trang hoặc nội dung thiếu, bỏ lỗi chính tả của sách mà agy ghi vào.
7. B7: `b5_annotate.py <bài> apply ...`, `check_lesson.py <bài>` phải ra `[]`, dựng `b7_render.py` và `b8_render_b14.py`. Lỗi `block_number` thường do OCR đọc rác thành số: so từng số với bảng gõ lại (và ảnh khi cần), đúng thì chép khối đã gõ vào `fixed.txt`.
Claude không chạy `agy_run.py` (gọi agy là vi phạm chính sách của Google). Đến mỗi lệnh `agy_run.py` ở trên, Claude dừng, đưa người dùng đúng lệnh cần chạy, chờ người dùng báo xong rồi mới chạy bước áp và kiểm tra. `agy_run.py` thoát mã 1 thì dừng bài đó, không tự làm thay bằng Claude.
`agy_run.py` không ghi sổ tiến độ. Chỉ chạy `progress.py <bài> <bước> "ghi chú"` sau khi bước đó đã áp và qua script kiểm tra. Bị ngắt giữa chừng thì xem `kho/lessons/<bài>/agy/log.jsonl` để biết phần nào agy đã làm.

Được sửa: `toolbox/kho/lessons/<mã bài>/`, `toolbox/kho/ink/<mã bài>/`, `toolbox/data/progress.json`, `toolbox/data/cards/`, `toolbox/data/ocr_dict.tsv`, `toolbox/data/external_sources.csv`.

Không được sửa: `toolbox/scripts`, `toolbox/lib`, `toolbox/templates`, `toolbox/PLAYBOOK.md`, thư mục `Tài liệu`.

Điều kiện hoàn thành: mỗi bài `python toolbox/scripts/check_lesson.py <mã bài>` trả về rỗng, `python toolbox/scripts/progress.py <mã bài>` báo đã xong.

Báo cáo: danh sách bài xong, bài dừng (kèm dòng lỗi trong `agy/log.jsonl`), số lượt gọi agy theo model, số `[?chữ?]`, các mâu thuẫn chờ người dùng quyết.
