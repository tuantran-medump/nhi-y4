# Workflow agy + Claude — Implementation Plan

> **Cập nhật 2026-11-18:** Claude lại tự chạy `agy_run.py`, lần lượt từng lệnh, dừng hẳn khi hết quota hoặc bị chặn (402/403). Giai đoạn 2026-11-16 đến 2026-11-18 người dùng tự chạy. Xem "Quy tắc agy" trong `toolbox/PLAYBOOK.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Các bước đọc nặng của giai đoạn B chạy qua `agy` ở chế độ chỉ đọc. Claude Code chỉ điều phối, kiểm tra bằng script và quyết mâu thuẫn (B6).

**Architecture:** Script mới `toolbox/scripts/agy_run.py` dựng prompt từ các prompt có sẵn trong `toolbox/templates/prompts/`. Script gọi `agy -p --mode plan`, tách và kiểm JSON trong stdout, rồi ghi vào đúng file mà luồng subagent cũ vẫn ghi, nên các bộ áp dụng hiện có giữ nguyên. Script `b6_pairs.py` in từng cặp "dòng sách, chú thích" để Claude đọc trọn trong một lần.

**Tech Stack:** Python 3.15, unittest, subprocess, CLI `agy` (gói Google AI Pro).

**Spec:** `docs/superpowers/specs/2026-11-15-agy-claude-workflow-design.md`

## Global Constraints

- `agy` không bao giờ ghi file. Luôn gọi `agy -p "<prompt>" --mode plan --model <id> --add-dir <thư mục bài> --print-timeout <n>s`. Không dùng `--dangerously-skip-permissions`.
- ID model: `HYDROGEN = "gemini-4-hydrogen-medium"`, `SONNET = "claude-sonnet-5-5-medium"`, `OPUS = "claude-opus-5-5-medium"`.
- Lỗi agy (mã thoát khác 0, quá thời gian, stdout không có JSON hai lần liền) thì dừng bước đó, ghi log, báo người dùng. Không tự chuyển sang Claude.
- JSON sai cấu trúc thì gọi lại đúng 1 lần, kèm danh sách lỗi.
- Thân bài không bao giờ do model viết lại. Kết quả của agy chỉ là chỗ sửa, bảng hoặc chú thích, và phải qua script kiểm tra hiện có.
- `resolve` và tra guideline ngoài (mã E) chỉ do Claude Code làm ở B6. Nếu agy trả về `resolve` thì coi là sai cấu trúc.
- Không đổi cấu trúc `toolbox/data/progress.json`. Chỉ ghi ghi chú qua `progress.set(lesson, step, note)` có sẵn.
- Test chạy bằng: `python -m unittest discover -s toolbox/tests` (đang có 258 test OK).
- Commit dùng `git -c user.name="Claude Code" -c user.email=noreply@anthropic.com commit`, cuối message có `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Làm trên nhánh `feat/agy-workflow`. Không merge, không push khi người dùng chưa đồng ý.
- **Quyết định của plan:** B2a (vá dấu) và B3 (chốt nguồn) hiện chưa có định dạng JSON để áp dụng, nên tạm vẫn do Claude làm. Ghi vào PLAYBOOK là việc làm sau.

## Review Focus

1. agy bọc JSON trong ```` ```json ```` hoặc thêm lời dẫn trước, sau: vẫn tách được (test ở Task 2).
2. agy treo hoặc quá thời gian: báo `AgyError`, không ghi file kết quả dở (test ở Task 2).
3. Chạy lại sau khi bị ngắt giữa chừng: bỏ qua phần đã có file kết quả hợp lệ, trừ khi có `--force` (test ở Task 3).
4. Chú thích trỏ vào dòng trống, dòng `<<...>>` hoặc dòng bảng `|`: bị loại và đưa vào lượt gọi lại (test ở Task 3).
5. Một nguồn có số dòng bằng chứng lớn hơn `max_lines`: vẫn tách, cắt ở ranh giới dòng (test ở Task 3).

---

### Task 1: Thăm dò agy (không viết code)

**Files:**
- Modify: `docs/superpowers/specs/2026-11-15-agy-claude-workflow-design.md` (mục "Chi tiết đã chốt")

- [ ] **Step 1: Thử đọc ảnh.** Chạy từ repo:
  `agy -p "Mở ảnh toolbox/kho/lessons/G1-B13/review/<một file p*.png có thật> và chép 3 dòng đầu. Không ghi file." --mode plan --model gemini-4-hydrogen-medium --add-dir toolbox/kho/lessons/G1-B13 --print-timeout 300s`
  Expected: in ra chữ khớp ảnh, hoặc báo không đọc được ảnh.
- [ ] **Step 2: Thử đọc file trong `kho/`** bằng cách tương tự với `body_numbered.txt`. Expected: chép đúng dòng 1–3.
- [ ] **Step 3: Ghi dạng lỗi thật.** Chạy với `--model khong-co-model` và với `--print-timeout 1s`. Ghi lại mã thoát và chữ trong stderr.
- [ ] **Step 4:** Ghi kết quả vào spec: `VISION_OK = True/False`, dạng lỗi. Commit `docs: record agy probe results`.

### Task 2: Lõi gọi agy

**Files:**
- Create: `toolbox/scripts/agy_run.py`
- Create: `toolbox/tests/fake_agy.py` (agy giả: đọc biến môi trường `FAKE_AGY_OUT` là danh sách đầu ra theo lượt, `FAKE_AGY_EXIT`, `FAKE_AGY_SLEEP`; đếm lượt bằng file trong `FAKE_AGY_STATE`)
- Test: `toolbox/tests/test_agy_run.py`

**Interfaces:**
- Produces:
  - `class AgyError(RuntimeError)`
  - `extract_json(text: str) -> object`: lấy đối tượng hoặc mảng JSON ngoài cùng trong stdout. Không có thì `ValueError`.
  - `call(prompt: str, model: str, add_dirs: list[str], timeout_s: int = 1200) -> str`: lệnh lấy từ biến môi trường `AGY_CMD` (tách bằng `shlex`, mặc định `agy`). Mã thoát khác 0 hoặc `subprocess.TimeoutExpired` thì `AgyError`, kèm 500 ký tự cuối của stderr.
  - `ask_json(prompt: str, model: str, add_dirs: list[str], validate: Callable[[object], list[str]], timeout_s: int = 1200) -> object`: gọi, tách, kiểm. Lỗi thì gọi lại 1 lần, prompt nối thêm `"\n\nLần trước sai:\n- " + "\n- ".join(errors)`. Lần hai vẫn lỗi thì `AgyError`.

- [ ] **Step 1: Viết test hỏng.**
  - `test_extract_json_from_fenced_and_prose`: `extract_json('Đây:\n```json\n{"a": [1]}\n```\nXong')` trả `{"a": [1]}`.
  - `test_extract_json_none_raises`: `ValueError` với `"không có"`.
  - `test_call_nonzero_exit_raises`: `FAKE_AGY_EXIT=3` thì `AgyError`.
  - `test_call_timeout_raises`: `FAKE_AGY_SLEEP=5`, `timeout_s=1` thì `AgyError`.
  - `test_ask_json_retries_once_then_ok`: lượt 1 in `{"x":1}`, validate báo lỗi khi thiếu `"y"`, lượt 2 in `{"y":2}`. Kết quả `{"y":2}`, agy giả ghi nhận 2 lượt và prompt lượt 2 có chữ `"Lần trước sai"`.
  - `test_ask_json_fails_twice_raises`: cả hai lượt in chữ không phải JSON thì `AgyError`.
- [ ] **Step 2:** `python -m unittest toolbox/tests/test_agy_run.py`. Expected: FAIL (`ModuleNotFoundError: scripts.agy_run`).
- [ ] **Step 3:** Viết code theo Interfaces. Lệnh dựng như Global Constraints.
- [ ] **Step 4:** Chạy lại. Expected: PASS. Chạy toàn bộ: OK.
- [ ] **Step 5:** Commit `feat(toolbox): read-only agy caller with JSON retry`.

### Task 3: Các bước giao agy và dòng lệnh

**Files:**
- Modify: `toolbox/scripts/agy_run.py`
- Test: `toolbox/tests/test_agy_run.py`

**Interfaces:**
- Consumes: `ask_json`, `AgyError` (Task 2); `b5_annotate.NOTE_OK`; `common.kho_path`, `common.read_json`, `common.write_json`; `progress.set`.
- Produces:
  - `split_evidence(text: str, max_lines: int = 400) -> list[str]`: nhóm các dòng liền nhau theo mã nguồn ở đầu dòng (`[S088:`). Dòng không có mã thì theo nhóm trước nó. Không cắt một nguồn ra nhiều phần, trừ khi riêng nguồn đó đã quá `max_lines`.
  - `valid_note_errors(note: dict, body_lines: list[str]) -> list[str]`: kiểm `NOTE_OK`; `line` phải trỏ dòng có nội dung, không bắt đầu bằng `<<` hay `|`; không có khóa `resolve`.
  - `STEPS: dict[str, Step]`, trong đó `Step` là dataclass gồm `b_step: str`, `prompt_file: str`, `parts(lesson) -> list[Part]`, `validate(data, lesson, part) -> list[str]`, `write(lesson, part, data) -> None`.
  - CLI: `python toolbox/scripts/agy_run.py <bài> <bước> [--part i] [--model m] [--force]`. Log mỗi lượt gọi vào `kho/lessons/<bài>/agy/log.jsonl` dạng `{step, part, model, seconds, status}`. Xong thì `progress.set(bài, b_step, "agy <bước> k/N")`.

Các bước (prompt luôn là: "Làm theo quy tắc nội dung trong `<prompt_file>`. Không ghi file nào. Thay vì ghi file, in một JSON dạng ..." cộng đường dẫn đầu vào của phần đó):

| Bước | b_step | prompt_file | Phần | Model | Kết quả ghi vào | Kiểm |
|---|---|---|---|---|---|---|
| `cards` | B5 | `cards.md` | `split_evidence(evidence.md)`, mỗi phần lưu `agy/evidence_<i>.md` | phần lẻ HYDROGEN, phần chẵn SONNET | `cards_<i>.json` | đủ 5 khóa `notes, conflicts, approach, experience, exam` là mảng; mỗi note qua `valid_note_errors` |
| `compose` | B5 | `compose_lesson.md` | 1 | OPUS | `{"notes", "extra"}` tách ra `notes.json`, `extra.json` | note như trên; `extra` có đủ `summary, approach, experience, exam, conflicts, missing` là chuỗi. Prompt dặn: không `resolve`, không tra web, dòng kết luận trong `conflicts` ghi `Kết luận: (Claude quyết ở B6)` |
| `layout` | B2b | `layout.md` | 1 | HYDROGEN | `layout.json` | mảng các dict có `line` là số nguyên |
| `review` | B2 | `ocr_fix.md` | lô 6 id từ `review/tasks.json` | HYDROGEN | `review/results/<id>.json` | khóa nằm trong lô, giá trị là mảng. Chỉ bật khi `VISION_OK` |
| `ink` | B4 | `read_ink.md` | lô 6 id từ `kho/ink/<bài>/tasks.json` | HYDROGEN | `kho/ink/<bài>/results/<id>.json` | khóa nằm trong lô, giá trị là dict có đủ nhãn của `items`. Chỉ bật khi `VISION_OK` |

- [ ] **Step 1: Viết test hỏng** (dùng thư mục tạm làm `kho`, agy giả từ Task 2):
  - `test_split_evidence_groups_by_source`: 3 nguồn × 150 dòng, `max_lines=400`, ra 2 phần, không nguồn nào bị cắt.
  - `test_split_evidence_oversize_source_splits_at_line`: 1 nguồn 900 dòng ra 3 phần, ghép lại đúng bằng đầu vào.
  - `test_note_on_blank_marker_or_table_line_rejected`: 3 trường hợp, mỗi trường hợp có lỗi; note hợp lệ không có lỗi.
  - `test_note_with_resolve_rejected`.
  - `test_cards_part_models_alternate`: phần 1 dùng HYDROGEN, phần 2 dùng SONNET (đọc từ log.jsonl).
  - `test_rerun_skips_valid_existing_part`: đã có `cards_1.json` hợp lệ thì chạy lại không gọi agy cho phần 1; có `--force` thì gọi.
  - `test_compose_writes_notes_and_extra`.
  - `test_agy_error_writes_nothing_and_logs`: agy giả thoát mã 1 thì không có `cards_1.json`, log có `status: "error"`, thoát khác 0.
- [ ] **Step 2:** Chạy, Expected FAIL.
- [ ] **Step 3:** Viết code theo bảng và Interfaces.
- [ ] **Step 4:** Chạy, Expected PASS. Toàn bộ OK.
- [ ] **Step 5:** Commit `feat(toolbox): agy steps for cards, compose, layout, review, ink`.

### Task 4: Cặp dòng sách và chú thích cho B6

**Files:**
- Create: `toolbox/scripts/b6_pairs.py`
- Test: `toolbox/tests/test_b6_pairs.py`

**Interfaces:**
- Produces: `pairs(body_numbered: str, notes: list[dict], conflict_lines: set[int]) -> str`. Mỗi dòng sách có chú thích in một khối: `L<n> [⚑ nếu n thuộc conflict_lines] <chữ sách>`, dưới đó mỗi chú thích là một dòng `  → <note>`. Xếp theo số dòng. CLI: `python toolbox/scripts/b6_pairs.py <bài>` đọc `body_numbered.txt`, `notes.json`, và số dòng từ `cards_*.json` → `conflicts[].line`.

- [ ] **Step 1: Viết test hỏng.**
  - `test_pairs_groups_notes_under_book_line`: 2 note cùng dòng 5 và 1 note dòng 9 ra 2 khối theo thứ tự, mỗi note có `→`.
  - `test_conflict_line_flagged`: dòng 9 thuộc `conflict_lines` thì có `⚑`.
- [ ] **Step 2:** Chạy, FAIL. **Step 3:** Viết code. **Step 4:** Chạy, PASS, toàn bộ OK.
- [ ] **Step 5:** Commit `feat(toolbox): book-line and note pairs for conflict review`.

### Task 5: Test cho bản mẫu B14

**Files:**
- Test: `toolbox/tests/test_b8.py`

**Interfaces:**
- Consumes: `b8_render_b14.swap_diagrams(md, lesson)`, `gradient_title(text)`; các hàm b7 mà b8 dùng: `assemble`, `md_to_html`, `_load_links`, `_nav`, `finish_pdf`.

- [ ] **Step 1: Viết test.**
  - `test_b7_functions_used_by_b8_exist`: mỗi tên kể trên `callable(getattr(b7_render, name))`.
  - `test_swap_diagrams_replaces_only_blocks_with_mmd`: với `kho` tạm có `diagrams/p1a.mmd`, khối `p1a` thành `@@DIAGRAM:p1a@@`, khối `p2b` giữ nguyên.
  - `test_gradient_title_keeps_text`: bỏ thẻ span thì còn đúng chữ gốc, ký tự đầu màu `#c9413a`.
- [ ] **Step 2:** Chạy, PASS. Test này khóa phụ thuộc vào b7, nên PASS ngay từ đầu là đúng. Thử tạm đổi tên `_nav` trong b7 để thấy test FAIL, rồi trả lại.
- [ ] **Step 3:** Commit `test(toolbox): pin b8 renderer dependencies on b7`.

### Task 6: Playbook và prompt

**Files:**
- Modify: `toolbox/PLAYBOOK.md` (mục 4 bảng giai đoạn B cột "Người làm"; mục 5 thay điểm 12–13; mục 8 thêm `agy_run.py`, `b6_pairs.py`, `b8_render_b14.py`; B7 ghi "dựng cả 2 bản")
- Modify: `toolbox/docs/checklist.md` (thêm: mọi kết quả agy đã qua script kiểm tra; B6 đã đọc hết `b6_pairs.py`)
- Modify: `toolbox/templates/prompts/batch_brief.md` (luồng mỗi bài: lệnh `agy_run.py` theo thứ tự, rồi B6 bằng `b6_pairs.py`)

- [ ] **Step 1:** Sửa theo spec: bảng chia việc, quy tắc agy chỉ đọc, dừng khi lỗi, B2a và B3 tạm do Claude, kết quả bài thử ngày 2026-11-15 (một dòng).
- [ ] **Step 2:** Kiểm lại với playbook mục 7.1 (sản phẩm khớp playbook). Toàn bộ test OK.
- [ ] **Step 3:** Commit `docs(toolbox): playbook for agy + Claude stage B`.

### Task 7: Chạy thử bài G2-B01 (dừng chờ người dùng duyệt)

- [ ] **Step 1:** Chạy B1 bằng script như cũ. Chạy B2/B4 qua agy nếu `VISION_OK`, nếu không thì như cũ. Rồi lần lượt: `agy_run.py G2-B01 layout`, `cards`, `compose`.
- [ ] **Step 2:** B6: `b6_pairs.py G2-B01`. Claude đọc hết, viết `resolve` vào `notes.json`, tra guideline nếu cần (mã E), cập nhật `extra.json` phần kết luận.
- [ ] **Step 3:** `b5_annotate.py G2-B01 apply ...` rồi `check_lesson.py G2-B01`. Expected `[]`. Dựng cả `b7_render.py` và `b8_render_b14.py`.
- [ ] **Step 4:** Báo người dùng: số lượt gọi agy theo model, thời gian, số chú thích, số mâu thuẫn, so với G1-B15. Nhắc người dùng xem `/usage`. **Dừng, chờ duyệt** trước khi chạy cả lô.
