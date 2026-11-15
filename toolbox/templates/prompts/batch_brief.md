# Brief chạy một lô

Mục tiêu: hoàn tất các bài `<danh sách mã bài>` của lô `<chuyên khoa>` theo `toolbox/PLAYBOOK.md`.

Bối cảnh: toolbox đã có sẵn, xem mục 8 của playbook. Bài mẫu đã duyệt là `G1-B08`, dùng làm chuẩn.

Luồng mỗi bài (chi tiết ở bảng giai đoạn B và "Quy tắc agy" trong playbook):
1. `progress.py <bài>` để biết bước kế tiếp. B1 bằng script.
2. B2: `b2_review.py <bài> tasks`, `agy_run.py <bài> review`, rồi `b2_review.py <bài> apply`. B2a do Claude làm.
3. B2b: `agy_run.py <bài> layout`, rồi `b2b_layout.py` so khớp từng từ.
4. B3 do Claude làm. B4: `b4_ink.py <bài> tasks`, `agy_run.py <bài> ink`, rồi `b4_ink.py <bài> merge`.
5. B5: `b5_evidence.py`, rồi `agy_run.py <bài> cards`, rồi `agy_run.py <bài> compose`.
6. B6: `b6_pairs.py <bài>`, Claude đọc hết, viết `resolve` vào `notes.json`, sửa kết luận trong `extra.json`.
7. B7: `b5_annotate.py <bài> apply ...`, `check_lesson.py <bài>` phải ra `[]`, dựng `b7_render.py` và `b8_render_b14.py`.
`agy_run.py` thoát mã 1 thì dừng bài đó và báo người dùng, không tự làm thay bằng Claude.

Được sửa: `toolbox/kho/lessons/<mã bài>/`, `toolbox/kho/ink/<mã bài>/`, `toolbox/data/progress.json`, `toolbox/data/cards/`, `toolbox/data/ocr_dict.tsv`, `toolbox/data/external_sources.csv`.

Không được sửa: `toolbox/scripts`, `toolbox/lib`, `toolbox/templates`, `toolbox/PLAYBOOK.md`, thư mục `Tài liệu`.

Điều kiện hoàn thành: mỗi bài `python toolbox/scripts/check_lesson.py <mã bài>` trả về rỗng, `python toolbox/scripts/progress.py <mã bài>` báo đã xong.

Báo cáo: danh sách bài xong, bài dừng (kèm dòng lỗi trong `agy/log.jsonl`), số lượt gọi agy theo model, số `[?chữ?]`, các mâu thuẫn chờ người dùng quyết.
