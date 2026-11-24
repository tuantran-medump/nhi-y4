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

Chưa kết luận: người dùng quyết giữ HTML hay đổi. Không đổi pipeline khi chưa duyệt.
