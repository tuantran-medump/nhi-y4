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
