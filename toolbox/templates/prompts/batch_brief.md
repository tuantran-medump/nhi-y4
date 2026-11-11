# Brief giao lô cho harness

Mục tiêu: hoàn tất các bài `<danh sách mã bài>` của lô `<chuyên khoa>` theo `toolbox/PLAYBOOK.md`.

Bối cảnh: toolbox đã có sẵn, xem mục 8 của playbook. Bài mẫu đã duyệt là `G1-B08`, dùng làm chuẩn.

Được sửa: `toolbox/kho/lessons/<mã bài>/`, `toolbox/data/progress.json`, `toolbox/data/cards/`, `toolbox/data/ocr_dict.tsv`.

Không được sửa: `toolbox/scripts`, `toolbox/lib`, `toolbox/templates`, `toolbox/PLAYBOOK.md`, thư mục `Tài liệu`.

Điều kiện hoàn thành: mỗi bài `python toolbox/scripts/check_lesson.py <mã bài>` trả về rỗng, `python toolbox/scripts/progress.py <mã bài>` báo đã xong.

Báo cáo: danh sách bài xong, bài dừng, số `[?chữ?]`, các mâu thuẫn chờ người dùng quyết.
