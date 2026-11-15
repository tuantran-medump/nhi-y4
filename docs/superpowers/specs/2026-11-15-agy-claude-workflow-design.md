# Workflow agy + Claude cho giai đoạn B (soạn từng bài)

Ngày: 2026-11-15. Áp dụng từ lô Tiêu hóa - Dinh dưỡng (G2-B01 đến G2-B12).

## Ý định

Người dùng hết lượt Claude quá nhanh khi chạy một lô. Mục tiêu là chuyển phần đọc nặng sang Antigravity (`agy`, gói Google AI Pro), để Claude Code chỉ điều phối, kiểm tra bằng script và quyết phần y khoa khó (mâu thuẫn, dòng ⭐). Chất lượng sản phẩm và mọi quy định trong `toolbox/PLAYBOOK.md` giữ nguyên.

## Mục tiêu

- Lượt Claude cho mỗi bài giảm rõ so với lô Thận - Nội tiết. Phần đọc bằng chứng, rút thẻ, sửa OCR, xếp cấp dòng và soạn nháp Phần B do `agy` làm.
- Sản phẩm vẫn qua đủ `check_lesson.py`, so từng từ với sách (`verify_words`), checklist mục 9 playbook.
- Mỗi bước giao `agy` chạy lại được, có log, bị ngắt thì làm tiếp đúng chỗ (sổ tiến độ).

## Không làm

- Không dùng Codex/GPT trong giai đoạn B. Bài thử ngày 2026-11-15 (bài HCTH, nguồn S088 và S091, 59 chú thích chuẩn): Hydrogen medium trùng 44/59 trong 67 giây, Argon medium 42/59 trong 196 giây, Sonnet 5.5 qua agy 47/59, gpt-6.1-sol medium 37/59 và báo thừa mâu thuẫn, Flash 33/59. Codex chỉ có thể nhận việc hình ảnh ngoài luồng chính (xem cuối).
- Không dùng API key Gemini, chỉ dùng gói đăng ký qua `agy`.
- Không dùng harness, không dùng NotebookLM trong luồng tự động.

## Phải tránh (dù chạy được vẫn coi là hỏng)

- Thân bài bị model diễn đạt lại. Thân bài vẫn do script chép từ kho, mọi đầu ra của `agy` chỉ là chỗ sửa, bảng hoặc chú thích, và phải qua script kiểm tra.
- Kết luận mâu thuẫn do model khác quyết mà Claude không soát.
- `agy` ghi đè file trong repo hoặc `kho/`.

## Ràng buộc

- Quy tắc agy trong CLAUDE.md của người dùng: việc ghi file phải chạy trong worktree, nhánh `agy/<task>`; không dùng cờ bỏ qua quyền; Claude Code và agy không sửa cùng một file; agy lỗi hoặc hết quota thì dừng job đó và báo người dùng; không tự merge.
- `toolbox/kho/` bị gitignore, worktree không thấy dữ liệu bài.
- Gói Google AI Pro có giới hạn lượt theo thời gian. Mỗi bài cần chia việc cho vừa.

## Cách đã cân nhắc

| Cách | Mô tả | Đánh giá |
|---|---|---|
| **A (người dùng chọn)** | Claude điều phối và kiểm tra, model khác đọc nặng | Bớt lượt nhiều, Claude vẫn giữ khâu kết luận y khoa |
| B | Giao trọn bài cho model khác, Claude chỉ chạy check | Tiết kiệm nhất nhưng kết luận y khoa không được Claude soát |
| C | Ba model đối chiếu độc lập, Claude phân xử | Chính xác nhất nhưng tổng lượt tăng, không giải quyết vấn đề |

Ban đầu A chia giữa Codex và agy. Sau bài thử, người dùng chuyển sang chỉ agy + Claude.

## Thiết kế

### Cách gọi agy: chỉ đọc, in kết quả ra stdout

`agy` chạy ở thư mục repo chính với `-p --mode plan` (không sửa file), `--add-dir` tới thư mục bài, `--model <id>`, `--print-timeout`. `agy` không ghi file nào: nó đọc file đầu vào rồi in một đối tượng JSON. Script của toolbox lưu stdout vào `kho/lessons/<bài>/agy/<bước>_<n>.json`. Cách này giữ đúng quy tắc "không ghi file ngoài worktree" vì agy không ghi gì, và giải quyết chuyện worktree không thấy `kho/`.

Script mới `toolbox/scripts/agy_run.py <bài> <bước> [--model ...] [--part n/N]`:
1. Dựng prompt từ `toolbox/templates/prompts/<bước>.md` cùng đường dẫn file đầu vào (đã có từ luồng cũ).
2. Gọi `agy`, lưu stdout và log, ghi thời gian chạy.
3. Tách JSON, kiểm tra cấu trúc (ví dụ `NOTE_OK` của `b5_annotate.py`, `line` trỏ dòng có nội dung). Sai thì gọi lại đúng một lần kèm thông báo lỗi. Sai lần hai thì dừng và báo.
4. Gặp lỗi quota hoặc lỗi agy thì dừng bài đó, ghi vào sổ tiến độ, báo người dùng. Không tự chuyển sang Claude.

### Chia việc theo bước của playbook

| Bước | Việc | Ai làm | Model |
|---|---|---|---|
| B1 | Cắt bài, dựng khung | Script | |
| B2 | Soát từng trang OCR cạnh ảnh | agy | Hydrogen medium |
| B2a | Vá cặp từ nghi sai dấu | agy | Hydrogen medium |
| B2b | Bảng cấp dòng, điểm tách | agy | Hydrogen medium |
| B3 | Chốt nguồn tham khảo và phần viết tay cần đọc | agy | Hydrogen medium |
| B4 | Đọc ảnh viết tay có chọn lọc | agy | Hydrogen medium |
| B5a | Rút thẻ bằng chứng (`cards.md`), chia đều số phần bằng chứng | agy | một nửa Hydrogen medium, một nửa Claude Sonnet 5.5 qua agy |
| B5b | Soạn nháp `notes.json` và Phần B (`compose_lesson.md`, `compose_extra.md`) | agy | Claude Opus 5.5 qua agy |
| B6 | Quyết mâu thuẫn, viết `resolve` cho dòng ⭐ | **Claude Code** | phiên chính |
| B7 | Kiểm tra, dựng PDF cả 2 bản, gắn link | Script, Claude chỉ mở dòng bị báo | |

"Chia đều" ở B5a là chia giữa hai model trong gói Google, để không dồn hết lượt vào một model. Cả hai đều tính vào hạn mức Google, không tính vào gói Claude.

### Claude Code làm gì

1. Chạy `agy_run.py` từng bước, đọc phần tóm tắt do script in ra, không đọc toàn bộ JSON.
2. Chạy script kiểm tra sau mỗi bước. Chỉ mở đúng dòng bị báo.
3. B6: đọc toàn bộ nháp chú thích cùng dòng sách (xem "Mâu thuẫn" ở dưới), quyết theo hiệp hội trong `lessons.csv`, viết `resolve`.
4. Soát nhanh nháp Phần B: mỗi câu có mã nguồn, không có kiến thức ngoài (playbook 2.5).
5. Cổng duyệt giai đoạn C giữ nguyên: xong cả lô thì người dùng duyệt.

### Sổ tiến độ

`toolbox/data/progress.json` thêm trạng thái theo bước cho từng bài (ví dụ `B5a: 3/4`), để chạy tiếp được khi bị ngắt hoặc hết quota.

### Việc ngoài luồng cho Codex (tùy chọn)

Codex có thể nhận việc hình ảnh không đụng thân bài: sơ đồ mermaid (`kho/.../diagrams/*.mmd`) và CSS của bản mẫu B14 (`toolbox/templates/b14.css`). Làm theo quy tắc agy/worktree thông thường (nhánh riêng, người dùng duyệt). Việc này tách khỏi thiết kế này và cần người dùng đồng ý riêng.

## Chi tiết đã chốt

- **Cờ agy đã kiểm bằng `agy --help` và `agy models` ngày 2026-11-15:** có `-p`, `--mode plan`, `--add-dir`, `--model`, `--print-timeout`. ID model: `gemini-4-hydrogen-medium`, `claude-sonnet-5-5-medium`, `claude-opus-5-5-medium`.
- **Bộ áp dụng giữ nguyên:** agy chỉ thay chỗ subagent ở khâu sinh JSON. `agy_run.py` ghi JSON đã kiểm vào đúng file và đúng định dạng mà subagent cũ ghi (ví dụ `cards_<n>.json`, `notes.json`, `extra.json`). Các script áp dụng hiện có (`b2_ocr_fix.py`, `b2b_layout.py`, `b5_annotate.py apply`...) không đổi. Bước nào hiện chưa có bộ áp dụng nhận JSON thì người dựng ghi lại và viết thêm.
- **Kiểm tra theo bước:** dùng đúng script mà luồng cũ đã chạy sau bước đó: so từng từ (`verify_words`) sau B2, B2a, B2b; `NOTE_OK` và dòng hợp lệ sau B5a; `check_lesson.py` sau B5b, B6 (mã nguồn, câu không trích dẫn, dòng ⭐). `agy_run.py` chỉ thêm phần kiểm cấu trúc JSON.
- **Mâu thuẫn (B6):** khóa `conflicts` do B5a sinh ra (đã có trong `cards.md`), B5b gộp vào `extra.json` như hiện nay. Người dùng chọn (2026-11-15): Claude đọc **toàn bộ nháp `notes.json`** của bài cùng dòng sách tương ứng (`body_numbered.txt`, chỉ các dòng có chú thích), không đọc tài liệu gốc. Claude vừa xét các điểm agy gắn cờ, vừa bắt mâu thuẫn agy bỏ sót (cả mâu thuẫn không dính số liệu như chỉ định, lựa chọn thuốc), rồi viết `resolve`. Script in sẵn từng cặp "dòng sách, chú thích" để Claude không phải mở file theo đoạn.
- **Hai bản PDF ở B7:** `b7_render.py` (bản sao ⭐) và `b8_render_b14.py` (bản mẫu B14). Bản B14 phụ thuộc việc commit phần mẫu B14 đang chờ người dùng duyệt.
- **Quota:** chưa biết hạn mức cụ thể. Nhận biết lỗi bằng mã thoát khác 0 hoặc stdout không có JSON. Việc đầu tiên của kế hoạch là một lần chạy thăm dò để ghi lại dạng lỗi thật.
- **Sổ tiến độ:** chỉ thêm khóa mới vào `progress.json`, không đổi khóa cũ. Người dựng kiểm tra những script đang đọc file này.
- **Mốc so sánh:** lô Thận không ghi số lượt Claude. Mốc là chất lượng so với G1-B15 (cùng cỡ) và cảm nhận hạn mức của người dùng (`/usage` trước và sau bài thử).
- **Kết quả thăm dò agy (2026-11-15, Hydrogen medium, `--mode plan`):**
  - Đọc file trong `kho/` qua `--add-dir`: được, chép đúng dòng.
  - Đọc ảnh trang: được (`VISION_OK = True`), 3 dòng đầu trang p0203 khớp `fixed.txt`. Điều kiện: prompt phải mở đầu bằng "Đây là câu hỏi chỉ đọc, KHÔNG lập kế hoạch, KHÔNG chờ duyệt". Thiếu câu này thì ở chế độ plan agy viết kế hoạch vào thư mục riêng của nó (`~/.gemini/antigravity-cli/brain/`) rồi chờ duyệt, không trả lời.
  - Model sai tên: mã thoát 1, stderr `error: invalid model selection ...`.
  - Quá `--print-timeout`: mã thoát 3, stderr có dòng `AGY_ERROR: {"status":"DEADLINE_EXCEEDED","reason":"print_timeout",...}`, và stdout vẫn có **phần trả lời dở**. Vì vậy phải xét mã thoát trước, không được tách JSON từ stdout khi mã thoát khác 0.
  - Lỗi hết hạn mức (gặp thật ngày 2026-11-15, bài G1-B13 phần 6/9, model Sonnet 5.5 qua agy, sau khoảng 8 phút gọi liên tục trong ngày): mã thoát 3, stderr `error: Individual quota reached ... Resets in 3h33m28s.` và `AGY_ERROR: {"status":"RESOURCE_EXHAUSTED","error_code":429,"retryable":true,...}`. `agy_run.py` dừng đúng như thiết kế.

## Để người dựng quyết

- `agy` có đọc được ảnh trang ở chế độ `-p --mode plan` hay không (cần cho B2, B4). Nếu không, B2 và B4 giữ như cũ (subagent Claude) và ghi lại.
- Cách tách phần bằng chứng cho B5a (theo nguồn hay theo số dòng), miễn mỗi phần vừa một lần gọi.
- Định dạng log và tên file trong `kho/lessons/<bài>/agy/`.
- Prompt hiện có viết cho subagent Claude (đọc theo đoạn bằng công cụ). Có thể cần chỉnh nhẹ cho agy, nhưng giữ nguyên quy tắc nội dung.

## Kiểm chứng

- Test đơn vị cho `agy_run.py`: tách JSON từ stdout có chữ thừa, gọi lại một lần khi JSON sai, dừng khi lỗi quota (giả lập lệnh agy bằng script giả).
- Chạy thử trọn một bài mới đầu lô Tiêu hóa, so số lần gọi Claude và chất lượng (check_lesson ra `[]`, số chú thích, số mâu thuẫn) với một bài lô Thận cùng cỡ. Người dùng xem bài đó trước khi chạy cả lô.
