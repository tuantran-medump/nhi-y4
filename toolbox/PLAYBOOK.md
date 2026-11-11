# Playbook: Gom tài liệu Nhi Y4 thành bài học chuẩn

Trạng thái: Bước 1 (playbook) đã duyệt 2026-11-11. Bước 2 (toolbox) và Bước 3 (checklist) đã dựng, chờ người dùng xem. Chưa soạn bài nào.

Cách dùng: agent đọc mục 1, 2 và 7 ở đầu mỗi phiên, các mục khác chỉ đọc khi tới bước đó.

## 1. Mục tiêu và phạm vi

**Mục tiêu:** mỗi bệnh hoặc chủ đề có đúng 1 file PDF theo template chuẩn, dùng để học hiểu đầy đủ.

**Nguồn:** chỉ thư mục `NHI_Y4_SAP_XEP\Tài liệu` (Slide, CBL - Case, Notes, Textbook). Bệnh án, Pretest, Test để giai đoạn sau.

**Sản phẩm:** khoảng 48 file, gồm 33 bài trong sách và khoảng 15 chủ đề ngoài sách (mục 3), xuất ra `NHI_Y4_SAP_XEP\Bài học`.

## 2. Quy định nội dung

### 2.1 Vai trò nguồn

| Loại | Nguồn | Được dùng để |
|---|---|---|
| Giáo trình | Nhi Khoa Tập 1, Tập 2 (2025) | Thân bài. Đây là 2 "text" duy nhất |
| Tham khảo | Mọi file khác trong `Tài liệu`, kể cả các file khác trong `Textbook` | Chú thích trong ngoặc đơn và Phần B |
| Trọng tài | Guideline của 1 hiệp hội cho mỗi bài (mục 2.4) | Chỉ để kết luận điểm mâu thuẫn |

### 2.2 Thân bài

- Thân bài theo đúng đề mục, thứ tự và câu chữ của bài trong sách. Không tóm tắt, không viết lại.
- Chỉ được sửa lỗi OCR. Mọi chỗ không chắc ghi `[?chữ?]` và đối chiếu ảnh trang gốc. Sửa chữ số bắt buộc đối chiếu ảnh gốc từng chỗ và ghi `verified: true`, từ điển OCR không bao giờ sửa chữ số.
- Tiêu đề chạy, số trang, dấu CamScanner được script loại, không thuộc nội dung sách. Trang scan bị lặp chỉ lấy một lần.
- Trình bày: giữ nguyên chữ nhưng **tách mỗi ý thành một dòng**, thụt lề theo quan hệ cha con:
  - Đề mục giữ đúng số của sách (1., 2.1, 2.4.1).
  - Ý thường: cấp 1 `-`, cấp 2 `+`, cấp 3 `*`.
  - Danh sách có thứ tự hoặc đếm được: số thường `1. 2. 3.`, nhóm lớn dùng số La Mã `I. II. III.`
  - Câu liệt kê ("gồm: a, b, c") tách thành dòng dẫn và các dòng con.
- Khi tách dòng, từ ngữ và thứ tự từ không đổi. Chỉ được thêm ký hiệu đầu dòng và bỏ dấu phẩy, chấm phẩy ngăn cách các ý vừa tách. Script so khớp từng từ với bản đã sửa OCR để xác nhận.
- Chủ đề ngoài sách: thân bài viết từ slide giảng viên mới nhất, đầu file gắn nhãn "Ngoài giáo trình".

### 2.3 Chỉnh sửa từ nguồn khác

Khi nguồn tham khảo cập nhật, làm rõ hoặc khác với sách, **giữ nguyên câu của sách** và thêm chú thích trong ngoặc đơn ngay sau ý đó, kèm mã nguồn.

Ví dụ: `Điều trị 5 ngày [G1:p128] (Slide BS. A 2024: rút còn 3 ngày với thể nhẹ [S12:p4]).`

### 2.4 Mâu thuẫn

Mâu thuẫn là khi hai nguồn đưa ra chỉ định, liều, ngưỡng hoặc tiêu chuẩn không thể cùng đúng.

1. Thân bài giữ theo sách, có chú thích ngoặc đơn như mục 2.3.
2. Mục "Mâu thuẫn nguồn" ghi: điểm lệch, từng nguồn nói gì, kết luận của hiệp hội trọng tài.
3. Mỗi bài dùng 1 hiệp hội, chốt trước khi soạn. Mặc định:

| Bài | Hiệp hội |
|---|---|
| Viêm hô hấp trên, Viêm tiểu phế quản, Nhiễm trùng tiểu, Béo phì | AAP |
| Viêm phổi, Tiêm chủng, Tiêu chảy, Suy dinh dưỡng, Nuôi dưỡng, Còi xương, Thiếu vitamin, Thiếu máu thiếu sắt | WHO |
| Hen | GINA |
| Viêm cầu thận cấp, Hội chứng thận hư, Viêm mạch máu IgA | KDIGO |
| Đái tháo đường type 1 | ISPAD |
| Suy giáp bẩm sinh | ESPE |
| Thalassemia | TIF |
| Hemophilia | WFH |
| Giảm tiểu cầu | ASH |

4. Ưu tiên guideline có sẵn trong thư mục. Nếu không có, được tra bản chính thức bên ngoài, **chỉ cho điểm mâu thuẫn đó**, ghi mã `E` và lưu vào danh mục nguồn.
5. Bài không có hiệp hội mặc định hoặc hiệp hội không đề cập điểm lệch: đưa vào danh sách chờ người dùng quyết.

### 2.5 Không thêm kiến thức ngoài

Mọi ý phải truy được về nguồn. Ngoại lệ duy nhất là mục 2.4 bước 4. Chỗ thiếu ghi vào mục "Cần bổ sung", không tự điền.

### 2.6 Trích dẫn

- Mã ngắn cuối ý: `G1`, `G2` (giáo trình), `S` (slide), `C` (CBL), `N` (notes), `R` (tham khảo khác), `E` (guideline ngoài).
- Bắt buộc gắn ở số liệu, liều, tiêu chuẩn, chỉ định và ý quan trọng.
- Với mọi nguồn, kể cả giáo trình, `p` là **số trang của file PDF**, không phải số trang in. Số trang in chỉ dùng để xác định ranh giới bài và báo trang thiếu.
- Mã là link bấm được tới Google Drive. Link được gắn bằng script từ bảng mã nguồn sau khi người dùng upload. Link Drive thường chỉ mở đúng file, nên mã luôn giữ số trang.

### 2.7 Hình và bảng

- Bảng và lưu đồ có chữ: gõ lại để tìm kiếm và sửa được. Trong `fixed.txt`, bọc phần OCR của bảng bằng dòng `<<block:t1>>` và `<<endblock>>`, gõ lại ở `kho/lessons/<bài>/blocks/t1.md`. Script kiểm tra mọi con số trong khối gốc có mặt trong bản gõ lại.
- Hình giải phẫu, X-quang, ảnh lâm sàng, biểu đồ: cắt từ bản gốc bằng script và chèn đúng chỗ, giữ số hình và chú thích của sách.

### 2.8 An toàn file

- Không sửa, đổi tên, xóa hay ghi đè file trong `Tài liệu`. Mọi kết quả trung gian nằm trong `toolbox`.
- Cài phần mềm, gửi tài liệu ra dịch vụ ngoài, upload Drive: hỏi người dùng trước.

## 3. Danh mục bài

Số trong ngoặc là trang in bắt đầu, sẽ xác minh ở bước A3.

**Tập 1 (G1)**
- Tổng quát: B1 Các thời kỳ tuổi trẻ (1), B2 Tăng trưởng thể chất (16), B3 Phát triển tâm thần - vận động (29), B4 Tiêm chủng (40).
- Hô hấp: B5 Giải phẫu và sinh lý hô hấp (76), B6 Viêm hô hấp trên (83), B7 Viêm tiểu phế quản cấp (105), B8 Viêm phổi (118), B9 Hen trẻ em (136).
- Thận - Nội tiết: B10 Giải phẫu và sinh lý thận (155), B11 Nhiễm trùng tiểu (170), B12 Viêm cầu thận cấp (187), B13 Hội chứng thận hư (198), B14 Viêm mạch máu IgA (218), B15 Đái tháo đường type 1 (237), B16 Suy giáp bẩm sinh (256).

**Tập 2 (G2)**
- Tiêu hóa - Dinh dưỡng: B1 Đặc điểm bộ máy tiêu hóa (1), B2 Nhu cầu dinh dưỡng (12), B3 Nuôi trẻ dưới 6 tháng khi không có sữa mẹ (28), B4 Ăn dặm và dứt sữa (37), B5 Các vấn đề nuôi dưỡng (44), B6 Còi xương (63), B7 Thiếu vitamin A (81), B8 Thiếu vitamin B, C, E, K (92), B9 Tiêu chảy (119), B10 Suy dinh dưỡng (136), B11 Điều trị suy dinh dưỡng (151), B12 Béo phì (164).
- Huyết học: B13 Đặc điểm hệ máu (173), B14 Thiếu máu thiếu sắt (185), B15 Thalassemia (203), B16 Hemophilia (223), B17 Giảm tiểu cầu (239).

**Ngoài sách:** Ho - khó thở, Khò khè, Khí dung, X-quang ngực, Suy hô hấp - oxy, Thuốc hô hấp, Khám hô hấp, Phù, Đọc xét nghiệm thận, Tiếp cận thiếu máu, Tiếp cận xuất huyết, Suy tủy, Hạch lách to, Xét nghiệm huyết học, Đau bụng - nôn.

**Thứ tự làm:** G1-B8 Viêm phổi (bài mẫu), rồi các lô: Hô hấp, Thận - Nội tiết, Tiêu hóa - Dinh dưỡng, Huyết học, Tổng quát, Ngoài sách.

## 4. Quy trình

### Giai đoạn A: Chuẩn bị (làm một lần, bằng script)

| Bước | Việc | Kết quả |
|---|---|---|
| A1 | Lập danh mục: đường dẫn, hash, số trang, loại trang (chữ, ảnh, lẫn), cấp mã nguồn | Bảng mã nguồn |
| A2 | Loại bản trùng: trùng hash, rồi trùng nội dung chữ. Bản có ghi chú viết tay khác biệt vẫn giữ | Danh sách bản chính |
| A3 | Kiểm thử Tesseract trên vài trang (cả trang có bảng), người dùng xem kết quả, rồi OCR hai tập và mọi trang scan của nguồn tham khảo (`a3_ocr.py scans`, chạy sau A1, A2, trước A6) | Chữ từng trang |
| A4 | Lập bản đồ trang: số trang in ứng với trang PDF, ranh giới từng bài, **báo trang thiếu** | Bản đồ trang |
| A5 | Trích chữ theo trang cho toàn bộ file có lớp chữ | Kho chữ |
| A6 | Gán nguồn vào bài theo thư mục, tên file, rồi kiểm tra từ khóa trong kho chữ | Bảng nguồn theo bài |

Đã biết ở A4: số trang in bị nhảy so với file scan (Tập 1 hụt khoảng 7 trang, Tập 2 hụt khoảng 1 trang, cả hai không có Bảng tra từ). Trang thiếu nằm trong bài nào thì ghi ở "Cần bổ sung" của bài đó.

### Giai đoạn B: Soạn từng bài

| Bước | Việc | Người làm |
|---|---|---|
| B1 | Cắt chữ của bài từ kho, dựng khung theo đề mục sách | Script |
| B2 | Sửa lỗi OCR, chỉ phát các dòng cần sửa, đối chiếu ảnh ở chỗ nghi ngờ | Agent |
| B2b | Script tách câu và đánh số dòng. Agent chỉ phát bảng "dòng, cấp, ký hiệu, điểm tách". Script dựng danh sách rồi so khớp từng từ với bản B2 | Script và Agent |
| B3 | Chốt danh sách nguồn tham khảo và phần viết tay cần đọc | Agent |
| B4 | Đọc ảnh có chọn lọc: viết tay ưu tiên Notes, CBL; trên slide chỉ tối đa vài file mỗi bài | Agent đọc ảnh |
| B5 | Thêm chú thích ngoặc đơn (2.3) và soạn Phần B | Agent |
| B6 | Xử lý mâu thuẫn theo 2.4 | Agent |
| B7 | Kiểm tra theo mục 7, dựng PDF, gắn link nếu đã có | Script và Agent |

### Giai đoạn C: Duyệt

1. Bài mẫu: người dùng duyệt kỹ, chốt template, cập nhật playbook.
2. Mỗi lô chuyên khoa: làm xong cả lô, người dùng duyệt, rồi mới sang lô sau.
3. Sau khi người dùng upload Drive: điền link vào bảng mã nguồn, chạy lại bước dựng PDF.

## 5. Tiết kiệm token

1. Script làm mọi việc không cần suy luận: danh mục, loại trùng, OCR, trích chữ, cắt bài, dựng PDF, gắn link.
2. Mỗi file chỉ trích và đọc ảnh một lần, kết quả lưu vào kho. Kiểm tra kho trước khi đọc bất cứ thứ gì.
3. Thân bài không được model viết lại: script chép từ kho, agent chỉ phát các chỗ sửa và bảng cấp dòng (B2b), không phát lại toàn văn.
4. Mỗi bài chỉ mở đúng trang liên quan, tìm bằng từ khóa trong kho, không đọc nguyên file.
5. Bỏ bản trùng trước khi đọc.
6. Đọc ảnh theo lô bằng ảnh ghép nhiều vùng, độ phân giải vừa đủ, không đưa ảnh vào cuộc chat chính.
7. Kiểm tra bằng script, chỉ mở đúng dòng bị báo lỗi.
8. Lọc câu mới: script chỉ bỏ các câu trong nguồn tham khảo giống hệt câu sách từng từ, model đọc phần còn lại. Câu gần giống luôn được giữ vì có thể khác thuốc, đường dùng hoặc liều.
9. Từ điển lỗi OCR tích lũy: mỗi lỗi sửa một lần rồi lưu, các bài sau script tự sửa.
10. Thẻ bằng chứng: đọc xong một nguồn thì ghi thẻ ngắn (ý, mã, trang). File dùng cho nhiều bài chỉ nạp thẻ, không đọc lại.
11. Sổ tiến độ, mỗi bài 1 phiên: trạng thái từng bài nằm trong file, bị ngắt thì làm tiếp đúng chỗ.
12. Chia model theo việc: model nhỏ cho sửa OCR, xếp cấp dòng, đọc ảnh. Model mạnh chỉ cho mâu thuẫn và Phần B. Việc của model nhỏ luôn qua script kiểm tra.
13. Harness cho lô: mỗi lô chuyên khoa giao worker, chỉ tin `result.json` và `diff.patch`. Bài mẫu làm trực tiếp, không qua harness.

## 6. Tiêu chuẩn sản phẩm

Mỗi file PDF, khổ A4, tiếng Việt, giữ thuật ngữ tiếng Anh như nguồn, có mục lục và số trang.

**Đầu file:** tên bài, mã bài, nhãn "Ngoài giáo trình" nếu có, hiệp hội trọng tài, ngày dựng, rồi **Tóm tắt 1 trang** (có mã nguồn, chỉ tóm từ nội dung trong file).

**Phần A. Thân bài (theo sách, trình bày theo mục 2.2):** Mục tiêu học tập, các đề mục đánh số đúng thứ tự sách, Câu hỏi tự lượng giá, Đáp án, Tài liệu tham khảo của sách.

**Phần B. Bổ sung lâm sàng:**
1. Tiếp cận và biện luận (từ CBL)
2. Kinh nghiệm lâm sàng
3. Câu hỏi thi
4. Mâu thuẫn nguồn
5. Cần bổ sung
6. Danh mục nguồn (mã, tên file, link Drive)

Mục không có nội dung vẫn giữ tiêu đề và ghi "Không có trong nguồn".

## 7. Quy định làm việc của agent

1. **Kiểm tra sản phẩm với playbook trước khi cho người dùng xem bất cứ thứ gì.** Việc này áp dụng cho cả bản nháp, script và tài liệu.
2. Không bỏ qua cổng duyệt ở giai đoạn C.
3. Báo đúng kết quả: bước nào chưa chạy, chưa kiểm chứng hoặc lỗi thì nói rõ.
4. Quyết định mới của người dùng được ghi vào playbook ngay, không để trong hội thoại.
5. Không dùng skill `pdf-extract` và subagent `pdf-vision-reader` vì skill chưa hoàn thiện. Đọc ảnh và viết tay dùng công cụ trong toolbox.

## 8. Toolbox

**Quy định:**
- Trước khi đọc bất cứ nguồn nào, kiểm tra `kho/` và `data/`. Việc đã có kết quả thì không làm lại.
- Mọi script, template, tài liệu của dự án nằm trong `toolbox/`. Script mới phải có test và được người dùng duyệt rồi mới thêm vào bảng dưới.
- Mỗi lần làm bài bắt đầu bằng `progress.py <mã bài>` để biết bước kế tiếp, xong bước nào ghi ngay bước đó.

| Bước | File | Công dụng |
|---|---|---|
| A1 | [scripts/a1_inventory.py](scripts/a1_inventory.py) | Lập danh mục, cấp mã nguồn |
| A2 | [scripts/a2_dedupe.py](scripts/a2_dedupe.py) | Đánh dấu bản trùng |
| A3 | [scripts/a3_ocr.py](scripts/a3_ocr.py) | OCR sách, `--sample` để kiểm thử |
| A4 | [scripts/a4_pagemap.py](scripts/a4_pagemap.py) | Bản đồ trang, trang thiếu |
| A5 | [scripts/a5_extract.py](scripts/a5_extract.py) | Trích chữ vào kho |
| A6 | [scripts/a6_assign.py](scripts/a6_assign.py) | Gán nguồn vào bài |
| B1 | [scripts/b1_slice.py](scripts/b1_slice.py) | Cắt chữ của bài |
| B2 | [scripts/b2_ocr_fix.py](scripts/b2_ocr_fix.py), [prompts/ocr_fix.md](templates/prompts/ocr_fix.md) | Từ điển lỗi OCR, bản vá |
| B2b | [scripts/b2b_layout.py](scripts/b2b_layout.py), [prompts/layout.md](templates/prompts/layout.md) | Xếp cấp dòng, so khớp từng từ |
| B3 | [data/lesson_sources.csv](data/lesson_sources.csv) | Danh sách nguồn của bài (sinh ra sau A6) |
| B4 | [scripts/b4_ink.py](scripts/b4_ink.py), [prompts/read_ink.md](templates/prompts/read_ink.md) | Đọc viết tay và trang scan |
| B5 | [scripts/b3_novel.py](scripts/b3_novel.py), [scripts/cards.py](scripts/cards.py), [prompts/compose_extra.md](templates/prompts/compose_extra.md) | Lọc câu mới, thẻ bằng chứng, soạn chú thích và Phần B |
| B6 | [prompts/compose_extra.md](templates/prompts/compose_extra.md), `data/external_sources.csv` | Mâu thuẫn, guideline ngoài |
| B7 | [scripts/check_lesson.py](scripts/check_lesson.py), [scripts/b7_render.py](scripts/b7_render.py) | Kiểm tra, dựng PDF |
| C3 | [data/drive_links.csv](data/drive_links.csv) | Điền link Drive rồi chạy lại `b7_render.py` |
| Mọi bước | [scripts/progress.py](scripts/progress.py) | Sổ tiến độ |
| Lô | [prompts/batch_brief.md](templates/prompts/batch_brief.md) | Brief giao harness |

**Dữ liệu và cấu hình:** [config.json](config.json) (đường dẫn), [data/lessons.csv](data/lessons.csv) (bài, hiệp hội), [data/topic_keywords.csv](data/topic_keywords.csv) (từ khóa), [data/ocr_dict.tsv](data/ocr_dict.tsv) (từ điển OCR), [templates/lesson.md](templates/lesson.md) và [templates/lesson.css](templates/lesson.css) (template).

**Kiểm thử toolbox:** `python -m unittest discover -s toolbox/tests`. Kế hoạch dựng: [docs/plan-toolbox.md](docs/plan-toolbox.md).

## 9. Checklist sản phẩm hoàn thiện

Chạy toàn bộ checklist cho mỗi bài trước khi cho người dùng xem. Mục nào không đạt thì sửa, hoặc ghi rõ lý do trong báo cáo. Bản đầy đủ để đánh dấu từng bài: [docs/checklist.md](docs/checklist.md).

Tóm lược các nhóm: tự động (`check_lesson.py` trả về rỗng), nguồn, thân bài, chú thích và mâu thuẫn, hình và bảng, Phần B, file PDF, báo cáo.
