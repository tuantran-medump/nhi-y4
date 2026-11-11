# Toolbox Nhi Y4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng bộ script, template và tài liệu để chạy quy trình trong playbook mà không làm lại việc cũ.

**Architecture:** Các script độc lập chạy theo bước, trao đổi qua file trong `toolbox/data` và `toolbox/kho`. Không script nào ghi vào `Tài liệu`. Chạy lại an toàn: bước đã có kết quả thì bỏ qua.

**Tech Stack:** Python 3.15, PyMuPDF (đã có), stdlib `unittest`, `zipfile`, `difflib`. Tesseract (cài khi người dùng đồng ý). Edge headless để in PDF.

**Spec:** `toolbox/PLAYBOOK.md`

## Global Constraints

- Không thêm thư viện Python ngoài PyMuPDF.
- Tên file so sánh sau khi chuẩn hóa Unicode NFC. Mọi file text đọc và ghi UTF-8.
- Đường dẫn gốc lấy từ `toolbox/config.json`, khóa `source_root`, `output_root`.
- Mã nguồn: `G1`, `G2`, `S###`, `C###`, `N###`, `R###`, `E###`.
- Với giáo trình, số trang trong trích dẫn là số trang in.
- Test chạy bằng: `python -m unittest discover -s toolbox/tests`.

## Review Focus

1. Câu tham khảo chỉ khác sách ở con số (5 ngày và 3 ngày) phải được giữ lại, không bị lọc là trùng.
2. OCR đọc sai hoặc không thấy số trang in: bản đồ trang đánh dấu `uncertain`, không suy đoán thành chắc chắn.
3. Tên file có dấu ngoặc vuông, ký tự `^J`, dạng NFD vẫn xử lý được.
4. File `.doc`, `.ppt` cũ hoặc PDF hỏng: đánh dấu `needs_manual`, không làm dừng cả lượt.
5. Lượt chạy bị ngắt giữa chừng: chạy lại tiếp từ trang chưa xong, không làm lại trang đã có.

---

### Task 1: Danh mục và loại trùng (A1, A2)

**Files:** Create `toolbox/config.json`, `toolbox/lib/common.py`, `toolbox/scripts/a1_inventory.py`, `toolbox/scripts/a2_dedupe.py`, `toolbox/.gitignore` (bỏ `kho/`), Test `toolbox/tests/test_a1_a2.py`

**Interfaces:**
- Produces: `common.load_config() -> dict`, `common.nfc(s: str) -> str`, `common.read_csv(path) -> list[dict]`, `common.write_csv(path, rows, fields)`
- Produces: `data/manifest.csv`, cột `code,path,sha256,pages,kind,folder,specialty,status`. `kind` thuộc `text|mixed|image|office|needs_manual`. `status` là `primary` hoặc `dup_of:<code>`.

- [ ] Viết test: `test_codes_stable_on_rerun` (chạy 2 lần, mã không đổi), `test_odd_filenames` (`[PKD] a.pdf`, tên chứa `^J`, tên NFD), `test_corrupt_pdf_needs_manual`, `test_exact_dup_marked`, `test_annotated_copy_kept` (cùng chữ, khác số vùng viết tay thì vẫn `primary`).
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết `a1_inventory.build(root) -> list[dict]`: giữ mã cũ theo sha256, cấp mã mới theo thư mục. Hai sách Nhi Khoa cố định `G1`, `G2`.
- [ ] Viết `a2_dedupe.mark(rows) -> list[dict]`: trùng hash, rồi trùng chữ (tỉ lệ `SequenceMatcher` từ 0.97), giữ bản nhiều annotation nhất.
- [ ] Chạy test, xác nhận PASS.

### Task 2: OCR và bản đồ trang (A3, A4)

**Files:** Create `toolbox/scripts/a3_ocr.py`, `toolbox/scripts/a4_pagemap.py`, `toolbox/data/lessons.csv` (33 bài từ mục 3 playbook, hiệp hội từ mục 2.4, cột `lesson,book,title,start_printed,society`), Test `toolbox/tests/test_a3_a4.py`

**Interfaces:**
- Consumes: `common`, `data/manifest.csv`
- Produces: `kho/<code>/p0001.txt`; `data/pagemap_G1.csv`, `data/pagemap_G2.csv`, cột `pdf_page,printed_page,lesson,confidence` (`ok|uncertain`); `data/gaps.csv`, cột `book,printed_page,lesson`

- [ ] Viết test: `test_resume_skips_done_pages` (giả lập engine, đếm số lần gọi), `test_printed_number_from_header` ("120 ♦ NHI KHOA - Tập 1" và "Bài 10. ... ♦ 157"), `test_unreadable_number_uncertain`, `test_gap_detected` (157 rồi 160 báo thiếu 158, 159), `test_out_of_sequence_number_uncertain` (số đọc nhầm làm nhảy ngược).
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết `a3_ocr.ocr_pages(pdf, code, pages=None, engine=tesseract_page)`: render 300 dpi, `tesseract -l vie+eng --psm 4`, ghi từng trang. Có cờ `--sample 1,2,3` cho kiểm thử.
- [ ] Viết `a4_pagemap.parse_printed(text) -> int|None` và `build_map(code, lessons) -> rows, gaps`.
- [ ] Chạy test, xác nhận PASS.

### Task 3: Trích chữ và gán nguồn (A5, A6)

**Files:** Create `toolbox/scripts/a5_extract.py`, `toolbox/scripts/a6_assign.py`, `toolbox/lib/ink.py`, `toolbox/data/topic_keywords.csv` (cột `lesson,keywords,folder_hint`), Test `toolbox/tests/test_a5_a6.py`

**Interfaces:**
- Produces: `kho/<code>/p0001.txt` cho file có chữ, `.docx` và `.pptx`; `data/lesson_sources.csv`, cột `lesson,code,pages,score,ink_pages`; `ink.ink_regions(page) -> list[Rect]` (annotation Ink và nét vẽ vector, gộp các nét gần nhau thành vùng)

- [ ] Viết test: `test_docx_text`, `test_pptx_one_page_per_slide`, `test_legacy_doc_needs_manual`, `test_assign_by_folder_and_keyword`, `test_only_primary_assigned`, `test_ink_annotation_detected`, `test_vector_stroke_detected`, `test_table_borders_not_ink` (đường kẻ bảng, khung slide không tính là viết tay), `test_ink_pages_listed`.
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết `a5_extract.extract(row)` và `a6_assign.assign(manifest, keywords) -> rows`. Điểm là số từ khóa trùng trên trang, `pages` chỉ gồm trang có điểm lớn hơn 0.
- [ ] Chạy test, xác nhận PASS.

### Task 4: Cắt bài và từ điển lỗi OCR (B1, B2)

**Files:** Create `toolbox/scripts/b1_slice.py`, `toolbox/scripts/b2_ocr_fix.py`, `toolbox/data/ocr_dict.tsv` (cột `wrong`, `right`), Test `toolbox/tests/test_b1_b2.py`

**Interfaces:**
- Consumes: pagemap, `kho/G*/`
- Produces: `kho/lessons/<lesson>/raw.txt` với dấu trang `<<p120>>`; `b2_ocr_fix.apply_dict(text, table) -> (text, n)`; `b2_ocr_fix.apply_patch(text, patch) -> text` với patch JSON `[{"line":12,"old":"...","new":"..."}]`; `kho/lessons/<lesson>/fixed.txt`; lệnh `suspects` in các dòng nghi lỗi kèm số dòng

- [ ] Viết test: `test_slice_bounds` (bài dừng trước trang đầu bài sau), `test_page_markers`, `test_dict_whole_word_only`, `test_patch_old_mismatch_raises`, `test_patch_adds_to_dict_when_flagged`.
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết các hàm trên. Patch có `old` không khớp thì báo lỗi và không ghi.
- [ ] Chạy test, xác nhận PASS.

### Task 5: Xếp cấp dòng và so khớp từng từ (B2b)

**Files:** Create `toolbox/scripts/b2b_layout.py`, Test `toolbox/tests/test_b2b.py`

**Interfaces:**
- Consumes: `fixed.txt`
- Produces: `split_units(text) -> list[str]` đánh số dòng; `apply_layout(units, table) -> str`, bảng JSON `[{"line":3,"level":2,"marker":"+","split":["gồm:",","]}]`; `verify_words(fixed, body) -> list[str]` (rỗng là khớp); `kho/lessons/<lesson>/body.md`

- [ ] Viết test: `test_markers_levels` (`-`, `+`, `*`, `1.`, `I.`), `test_split_list_sentence`, `test_verify_passes_when_only_markers_added`, `test_verify_fails_on_changed_word`, `test_verify_fails_on_reordered_word`, `test_verify_ignores_separator_commas`, `test_book_heading_number_kept`.
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết các hàm. `verify_words` bỏ ký hiệu đầu dòng, dấu phẩy và chấm phẩy, dấu trang, rồi so chuỗi từ.
- [ ] Chạy test, xác nhận PASS.

### Task 6: Lọc câu mới và thẻ bằng chứng

**Files:** Create `toolbox/scripts/b3_novel.py`, `toolbox/scripts/cards.py`, Test `toolbox/tests/test_b3_cards.py`

**Interfaces:**
- Produces: `novel_sentences(book_text, source_pages: dict[int,str]) -> list[{"page","text","reason"}]`; `kho/lessons/<lesson>/novel_<code>.jsonl`; `cards.add(code, lesson, idea, page)`, `cards.for_lesson(lesson) -> list[dict]`, lưu `data/cards/<code>.jsonl`

- [ ] Viết test: `test_identical_dropped`, `test_changed_number_kept` (5 ngày và 3 ngày), `test_changed_unit_kept` (mg và mcg), `test_negation_kept` (có "không"), `test_new_sentence_kept`, `test_card_reused_no_duplicate`.
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết các hàm. Câu bị bỏ chỉ khi tương đồng từ 0.9 **và** tập số, đơn vị, từ phủ định trùng hoàn toàn với câu sách.
- [ ] Chạy test, xác nhận PASS.

### Task 7: Đọc viết tay và trang scan (B4)

**Files:** Create `toolbox/scripts/b4_ink.py`, Test `toolbox/tests/test_b4.py`

**Interfaces:**
- Consumes: `ink.ink_regions`, `data/lesson_sources.csv`
- Produces: `make_tasks(lesson) -> list[dict]`, ghi `kho/ink/<lesson>/tasks.json` và ảnh ghép; mỗi task có `id`, `image`, `items` (nhãn `[n]` ứng với `code`, `page`, vùng); `merge(lesson) -> {"missing": [...], "uncertain": n}`, ghi `kho/<code>/p0001.ink.txt`; cache `data/ink_cache.json` theo sha256 của ảnh vùng

Agent đọc ảnh là subagent model nhỏ, theo prompt `read_ink.md`, ghi `kho/ink/<lesson>/results/<id>.json`.

- [ ] Viết test: `test_sheet_labels_match_items`, `test_cached_region_not_requeued`, `test_region_shared_across_lessons_read_once`, `test_merge_reports_missing`, `test_scan_page_tesseract_first` (trang scan chữ in có độ tin cậy OCR từ 80 thì không tạo task), `test_low_confidence_page_becomes_task`, `test_uncertain_counted` (đếm `[?chữ?]`).
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết các hàm. Ảnh ghép tối đa 12 vùng, render 150 dpi, nhãn đỏ cạnh mỗi vùng.
- [ ] Chạy test, xác nhận PASS.

### Task 8: Dựng PDF, gắn link, sổ tiến độ (B7, C3)

**Files:** Create `toolbox/scripts/b7_render.py`, `toolbox/scripts/progress.py`, `toolbox/templates/lesson.md`, `toolbox/templates/lesson.css`, `toolbox/data/drive_links.csv` (cột `code,url`), Test `toolbox/tests/test_b7.py`

**Interfaces:**
- Consumes: `body.md`, `kho/lessons/<lesson>/extra.md`
- Produces: `md_to_html(md, links: dict) -> str`; `render(lesson)` ghi `<output_root>/<Chuyên khoa>/<Tên bài>.pdf`; `progress.get(lesson)`, `progress.set(lesson, step, note="")`, `progress.next_step(lesson)`, lưu `data/progress.json`

- [ ] Viết test: `test_nested_lists`, `test_table`, `test_image`, `test_citation_linked_when_url`, `test_citation_plain_when_no_url`, `test_progress_resume`, `test_template_sections_order` (Tóm tắt trước Phần A, đủ 6 mục Phần B).
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết các hàm. In bằng `msedge --headless --print-to-pdf`, font Arial, khổ A4, có số trang. Hình cắt bằng PyMuPDF.
- [ ] Chạy test và dựng thử 1 file mẫu, mở bằng PyMuPDF xác nhận dấu tiếng Việt trích ra đúng và link tồn tại.

### Task 9: Kiểm tra bài, prompt theo model, chỉ mục playbook

**Files:** Create `toolbox/scripts/check_lesson.py`, `toolbox/templates/prompts/ocr_fix.md`, `layout.md`, `read_ink.md`, `compose_extra.md`, `batch_brief.md`; Modify `toolbox/PLAYBOOK.md` (thêm mục 8 "Toolbox"); Test `toolbox/tests/test_check.py`

**Interfaces:**
- Produces: `check(lesson) -> list[{"rule","line","msg"}]`, in JSON

- [ ] Viết test: `test_missing_section`, `test_number_without_citation` (dòng có liều mà không có mã), `test_unknown_source_code`, `test_body_word_mismatch`, `test_unresolved_marker` (`[?chữ?]` còn sót được báo).
- [ ] Chạy test, xác nhận FAIL.
- [ ] Viết `check`. Viết 5 prompt ngắn, mỗi prompt ghi model dùng (nhỏ: `ocr_fix`, `layout`, `read_ink`; mạnh: `compose_extra`).
- [ ] Thêm mục 8 vào playbook: bảng mỗi file, công dụng, bước dùng, quy định "kiểm tra `kho` và `data` trước khi đọc nguồn". Bước B4 ghi rõ đọc ảnh dùng `scripts/b4_ink.py` và prompt `read_ink.md`, không dùng skill `pdf-extract` hay subagent `pdf-vision-reader`.
- [ ] Chạy toàn bộ test, xác nhận PASS.

## Làm sau khi toolbox xong (cần người dùng đồng ý riêng)

- Cài Tesseract và dữ liệu tiếng Việt.
- `harness init`, cần repo có ít nhất 1 commit, trước lô đầu tiên.
