# hoctap: công cụ dựng sản phẩm học tập

Kết quả chạy thử thật ngày 2026-11-24 trên máy người dùng (Windows 11, Node 24.21, npm 11.19). Kế hoạch: `docs/superpowers/plans/2026-11-24-kb-y4-giai-doan-2.md` (Task 1).

## Đã cài và chạy được

| Công cụ | Cách cài | Lệnh đã chạy | Kết quả |
|---|---|---|---|
| Typst 0.15.1 | `winget install -e --id Typst.Typst` | `typst compile out/t.typ out/t.pdf` | Ra PDF 36 KB trong 0,5 giây, có chữ Việt, ≥, ▲ (font Arial). Phải mở shell mới mới có `typst` trong PATH; trước đó dùng đường dẫn đầy đủ `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Typst.Typst_Microsoft.Winget.Source_8wekyb3d8bbwe\typst-x86_64-pc-windows-msvc\typst.exe`. |
| Mermaid CLI (`mmdc`) | `npm i @mermaid-js/mermaid-cli` (cục bộ) | `node_modules/.bin/mmdc -i out/t.mmd -o out/t.svg -p out/pp.json` | Ra SVG trong 2,1 giây, nhãn tiếng Việt đúng. Script cài Chrome của puppeteer **không chạy** nên phải trỏ tới Edge bằng file cấu hình `{"executablePath": "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "args": ["--no-sandbox"]}`. |
| markmap-cli | `npm i markmap-cli` (cục bộ) | `node_modules/.bin/markmap out/t.md -o out/t.html --no-open --offline` | Ra HTML trong 1,6 giây. **Không có `--offline` thì HTML tải d3 và markmap từ cdn.jsdelivr.net**, mở không có mạng sẽ trống; dùng `--offline` (345 KB). |
| Font `@fontsource` | `npm i @fontsource/<tên>` | chưa kiểm glyph | Đã cài inter, oswald, dancing-script, patrick-hand, source-serif-4, source-sans-3, be-vietnam-pro, jetbrains-mono. Gói con tiếng Việt và glyph sẽ kiểm bằng `check_fonts.py` ở Task 3. |

## Chưa dùng được / chưa thử

- Excalidraw: chưa cài, để Task 8 (không chặn).
- Chưa kiểm font tải thêm có đủ glyph Việt trong PDF dựng thật.

## Ghi chú

- `out/` và `node_modules/` không đưa vào git.
- Edge headless in PDF: `--print-to-pdf` kèm `--user-data-dir` riêng và `--allow-file-access-from-files` (như bản dựng thử).

## Typst so với HTML (Task 5)

Chạy thật ngày 2026-11-24 trên HCTH, phong cách B14 ấm (`python build_typst.py content/HCTH.md --out out` và `python build_cheatsheet.py content/HCTH.md --style warm --out out --pdf`).

| Tiêu chí | HTML + Edge | Typst 0.15.1 |
|---|---|---|
| Thời gian dựng (đo 2 lần, từ lệnh Python) | 1,25–1,30 s | 0,25–0,26 s (typst 0,13–0,15 s) |
| Số trang | 3 | 3 |
| Chữ Việt, `≥ ≤ α β ▲ ·` | `check_fonts` OK (kèm cảnh báo Type3) | `check_fonts` OK với Inter, Oswald |
| Rơi chữ so với bản HTML | `check_roundtrip` khớp | không mất chữ (lệch chỉ do ngắt dòng và dấu nháy) |
| Độ giống bản mẫu | chuẩn | gần: hộp, màu, nhãn, bẫy thi, bảng có đủ; tiêu đề đổi sang Oswald (Typst không đọc woff2, máy chỉ có Great Vibes ttf, vỡ chữ Việt hoa), ghi chú `span.k` dùng Inter thay Patrick Hand |
| Độ dễ sửa | CSS 23 dòng + 67 dòng dựng | 121 dòng dựng, bố cục nằm trong chuỗi mã sinh `.typ` |
| Chỗ chưa ổn | | các dòng của ý bị xuống dòng chồng khít nhau trong hộp (khoảng cách dòng trong `block` chưa chỉnh); chưa có Dancing Script và Patrick Hand dạng ttf |

**Quyết định (người dùng, 2026-11-24): giữ HTML + Edge.** `build_typst.py` giữ lại như bản thử, không dùng cho sản phẩm chính.

## Lưu đồ và sơ đồ tư duy từ KB (Task 6)

`python kb_flow.py C:/Users/Admin/orca/kb-y4/nhi --root nhi:hcth --kind approach|dxtx --out out/flow` sinh `.mmd` (Mermaid) và `.md` (markmap) cho HCTH và VCTC. Mỗi nút và cạnh có mã nguồn của cạnh KB; cạnh không nguồn bị loại vào `*-gaps.csv` (lần chạy 2026-11-24: 0 cạnh bị loại). `check_diagram.py <file> --kb <KB>` kiểm mã nguồn, nhãn trùng thực thể KB và nhánh "CLS khó phân biệt"; cả 8 file qua. Dựng thật: `node_modules/.bin/mmdc -i x.mmd -o x.svg -p out/pp.json` (4 file, ra SVG) và `node_modules/.bin/markmap x.md -o x.html --no-open --offline` (4 file, ra HTML). Nhãn cạnh Mermaid ghi cả quan hệ ("cần phân biệt [S114:p4]").

Hạn chế đã biết: KB thiếu nhánh `la_the_cua` cho VCTC, cách xử trí phân biệt HCTH với hội chứng Cushing do corticoid, và VCTC với bệnh thận IgA / viêm cầu thận tăng sinh màng; nên các lưu đồ chỉ đầy đủ như KB hiện có. Lưu đồ tiếp cận xếp phẳng quanh gốc, chưa gom nhánh trong Mermaid (markmap có gom nhóm).

## Bảng so sánh và bảng phân độ (Task 7)

Nguồn `content/SO-SANH-HCTH-VCTC.md` (không vào git), dùng cú pháp bảng ống của CONTRACT, dựng bằng `build_cheatsheet.py` cả ba style, `check_fonts` OK. Ô nào cũng có mã nguồn của bài tương ứng (kiểm bằng script: 109 ô dữ liệu, thiếu mã chỉ ở ô tiêu đề cột của bảng phân độ). Chỉ giữ ý cả hai bài đều có; albumin và lipid bị bỏ vì B12 không nêu. B12 không có phân độ nặng nhẹ chính thức cho VCTC nên mục phân độ chủ yếu là phần HCTH và bậc xử trí THA của VCTC. Một số ô lấy mã trang theo dấu `<<pN>>` gần nhất vì câu gốc không có mã riêng; một số ô lấy cả nhóm mã chung từ ghi chú.

## Thử Excalidraw (Task 8)

Chạy thật 2026-11-24. Cài `@excalidraw/mermaid-to-excalidraw` 3.6.0 và `@excalidraw/excalidraw` 0.18 (kèm react, react-dom); gói bằng `npx esbuild excalidraw/entry.js --bundle --format=iife --define:process.env.NODE_ENV='"production"' --define:process.env.IS_PREACT='"false"'` (esbuild chạy qua `npx`, không lưu vào package.json); nạp vào trang HTML và chạy trong Edge headless (`--virtual-time-budget=30000 --dump-dom`). Kết quả:

- Lưu đồ tiếp cận VCTC (18 nút, 21 cạnh) chuyển được sang file `.excalidraw` (78 phần tử: rectangle, arrow, text; nhãn tiếng Việt kèm mã nguồn đủ dấu).
- File mở được bằng thư viện Excalidraw: `restore` rồi `exportToSvg` (`excalidraw/render.js`) ra hình kiểu vẽ tay đúng nội dung (ảnh trong `out/excali/`).
- **Chưa kiểm:** mở file bằng giao diện tương tác của excalidraw.com (hộp chọn file hệ thống, công cụ trình duyệt không nạp được), và MCP của yctimlin. Chỉ hỗ trợ flowchart như nguồn nói; bố cục tự động còn đè nhãn cạnh lên nhau.
- Không dùng cho sản phẩm chính; chỉ khi người dùng muốn sửa tay lưu đồ.

### Quy tắc bản Excalidraw (người dùng chốt 2026-11-24)

- **Không chú thích nguồn** (mã `[G1:p203]`...) trong bản Excalidraw; mã chỉ ở Mermaid/HTML/PDF để kiểm.
- **Gộp nhánh cùng loại:** nút → nút loại (vd "Biểu hiện") → từng nội dung, khi một nút có từ 2 nhánh cùng quan hệ.
- Dùng `python excalidraw/to_excalidraw.py <file.mmd> <ra.excalidraw>` (đã áp cả hai quy tắc, có test).
