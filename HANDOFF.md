# HANDOFF – nhi-y4

Sổ tay quy trình: `toolbox/PLAYBOOK.md`. Quy tắc agy: chỉ tự chạy `toolbox/scripts/agy_run.py`, từng lệnh một, dừng khi 402/403/429/quota (mã thoát 3).

## Trạng thái đang làm dở (cập nhật 2026-11-24)

- **Giai đoạn 2 hoctap (kb-y4 + bộ sản phẩm học tập): Task 1-8 xong, người dùng duyệt 2026-11-24.** Nhánh `claude/hoc-tap-giai-doan-2` (worktree `C:/Users/Admin/orca/nhi-y4-hoctap`, chưa push, chưa merge main). Kế hoạch và spec ở bản `main` của nhi-y4 (`docs/superpowers/plans/2026-11-24-kb-y4-giai-doan-2.md`, `specs/2026-11-24-hoc-tap-kb-design.md`, chưa theo dõi), KB ở `C:/Users/Admin/orca/kb-y4`. Mã ở `toolbox/hoctap/` (đọc `CONTRACT.md` và `README.md` ở đó): `boxes.py`, `build_cheatsheet.py --style warm|clean|screen [--pdf]` (dấu `{rong}` cho mục rộng cả trang), `html_to_md.py`, `check_fonts.py`, `check_sources.py`, `check_roundtrip.py`, `kb_flow.py` + `check_diagram.py` (lưu đồ và markmap từ kb-y4), `build_typst.py` (thử), `excalidraw/entry.js` (thử). CSS `styles/*.css`; agy chỉnh `clean.css` và `screen.css` (3440d4a; agy chạy được với `--mode accept-edits`, lệnh shell bị từ chối). **Nội dung giáo trình không vào git**: `toolbox/hoctap/content/` (HCTH.md đã gắn nguồn, 0 ý `[?]`, Opus quyết; dòng 125 giữ mã cũ, dòng 45 `[G1:p209]` còn nghi sai; SO-SANH-HCTH-VCTC.md) và `out/` (PDF, ảnh, `duyet-gd2.html`). Codex bị sandbox chặn chạy exe (typst, mmdc, markmap, Edge) nên Claude tự chạy bước dựng; test của Codex từng khẳng định lỗi, luôn chạy lại thật. **Chờ người dùng quyết:** giữ HTML hay đổi sang Typst (Typst 0,25 giây so với 1,3 giây nhưng dòng chồng nhau, thiếu font viết tay); Excalidraw mới thử chuyển đổi (39 phần tử), chưa mở file trong giao diện; KB thiếu nhánh (VCTC `la_the_cua`, phân biệt HCTH/Cushing, VCTC/IgA, VCTC/MPGN); push hoặc merge. Việc kế: giai đoạn 3 (đóng gói `agent-kit/addons/research`, bàn giao).

- **Thử model qua OpenRouter (chưa bắt đầu, chờ người dùng có key).** Model: Qwen 3.6 27B, Qwen 3.6 35B-A3B, Gemma 4 31B, gpt-oss-120b và **DeepSeek V4.1 Flash** (thay V4 Flash: DeepSeek đã khai tử V4 Flash, tên cũ chỉ tạm chuyển hướng sang V4.1; V4.1 Flash nhận ảnh, nên cho chạy cả phần ảnh G1-B04 `review`/`ink`; chưa rõ có mở trọng số không). Phiên 2026-11-21 chưa có `OPENROUTER_API_KEY`. Không có skill nào gọi OpenRouter; `toolbox/kho/bakeoff/run.sh` chỉ gọi agy/codex. Đề xuất đang chờ người dùng gật: viết `toolbox/kho/bakeoff/or_run.py` (đọc biến môi trường, dự phòng file `~/.openrouter_key` ngoài repo), ghi kết quả vào `out/` để `score.py` chấm. `compare_review.py` mà mục dưới nhắc không có trong `bench_neon/G1-B04/`: tìm trong repo hoặc viết lại phần so sánh. Đề:
  - Soạn chú thích: `toolbox/kho/bakeoff/` (task.md, body_numbered.txt, evidence_chunk.md), chấm bằng `score.py`, đáp án 56 chú thích. Mốc: Sonnet 46, Hydrogen 41, Haiku ~30, Qwen3.5-9B 0 (chặt)/19 (nới).
  - OCR: bài G1-B04, kết quả Hydrogen và Neon cùng các dòng đã đối chiếu ảnh ở `toolbox/kho/bench_neon/G1-B04/` (`review_diff.json`, `ink_diff.json`, `compare_review.py`).
  - Script đọc key từ biến môi trường `OPENROUTER_API_KEY`. Người dùng nhắn "chạy bài thử API" mới được gửi nội dung giáo trình ra ngoài. Không tạo tài khoản, không nạp tiền.
  - Kết quả quyết định mua máy: ≥35/56 mới đáng mua; chỉ đạt OCR thì Mac Mini M5 Pro 48GB (~63,5tr, Phúc Anh); DeepSeek V4 Flash gần Hydrogen thì cân nhắc 2× Strix Halo / Gorgon Halo 192GB. Tóm tắt nghiên cứu phần cứng nằm trong memory `local-model-purchase-eval`.
- **Chọn model agy (xong, 2026-11-19).** `review` và `ink` dùng Neon (`gemini-4-neon-medium`, commit 6c3d163). `blocks`, `cards`, `compose`, `layout` giữ Hydrogen (người dùng: "giữ Hydrogen đi"). Luật mới trong `toolbox/templates/prompts/read_ink.md` (chép đủ ghi chú tay ở vùng có chữ in) chưa chạy thử lại trên ảnh t018 của G1-B04.
- **Cheatsheet HCTH và VCTC (xong).** Nguồn `toolbox/kho/cheatsheet/` (HTML + style.css, in bằng Edge headless), PDF ở `NHI_Y4_SAP_XEP/Cheatsheet/` trên OneDrive, đã đẩy repo riêng `nhi-y4-bai-hoc` (commit 80ab7b7). VCTC đã có mục nguyên nhân và biến chứng. Gợi ý chưa làm: cheatsheet Viêm mạch máu IgA.
- **Người dùng đang review lô Dinh dưỡng và Huyết học.** Chờ họ báo chỗ sửa.
- **Đề xuất chưa quyết:**
  - Thêm luật ô gộp nhiều cột vào `toolbox/templates/prompts/blocks.md`.
  - Thử DeepSeek-OCR 3B trên máy bàn (RX 6600) so với Qwen3.5-9B.
  - Các mục "Cần bổ sung" còn lại đều cần bịa nội dung sách (danh sách tham khảo, mục rỗng G1-B11 8.3, G2-B11 1.1, ô bảng trống G1-B04/G2-B08…), để nguyên trừ khi người dùng muốn bổ sung có trích nguồn.

## Chờ người dùng quyết

- Repo công khai `nhi-y4`: 53 commit chưa push (tính cả commit bàn giao này là 54). Chỉ push khi được yêu cầu.
- `toolbox/data/ocr_dict.tsv` đang sửa dở từ trước, cùng các file chưa theo dõi (`debug.log`, `extra_data.py`, `ocr-qwen-test.png`, `on-tap/`, `toolbox/data/*.csv|json`): chưa rõ giữ hay bỏ.
