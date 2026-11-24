# Hợp đồng giữa nội dung, trình dựng và CSS (Task 3-4)

Mọi bên (trình dựng `build_cheatsheet.py`, ba file CSS, agy) bám đúng file này. Muốn đổi thì sửa file này trước, báo Claude.

## 1. Nội dung (Markdown, `content/<BÀI>.md`, không vào git)

- Dòng `# Tiêu đề` (một dòng, trước mọi mục) là tiêu đề chính. Các dòng văn bản ngay dưới đó, trước mục `##` đầu tiên, là dòng phụ đầu trang (`div.sub`), giữ nguyên HTML nội tuyến.
- Mỗi mục: `## Tên mục`, tiếp theo (tùy chọn) dòng `{hop: <loai>}` đúng như `boxes.py` đọc. Không có thì `khai-niem`. Dùng `boxes.parse_sections`.
- Thân mục: danh sách `- ` (lồng bằng thụt 2 dấu cách), bảng dạng ống `| a | b |` (dòng ngăn `|---|` đánh dấu hàng đầu là `th`; bảng không có dòng ngăn thì mọi hàng là `td`), đoạn văn thường.
- `**đậm**` là `<b>`.
- Ba loại nhấn nội tuyến, viết bằng HTML nguyên văn: `<span class="n">số cần nhớ</span>`, `<span class="k">nguồn khác sách</span>`, `<span class="t">bẫy</span>`. Đây là **ba thẻ duy nhất** được đi qua; mọi `<`, `>`, `&` khác trong văn bản là ký tự thường và trình dựng thoát thành thực thể (vì vậy `<30 g/L` viết thẳng được).
- Ý "bẫy thi" cả dòng: mục danh sách bắt đầu bằng `- !bay ` (bỏ `!bay `, thêm `class="trap"` vào `li`).
- Mã nguồn cuối ý: `[G1:p203]`, `[S085:p3]`, `[E16:p17]`… (chữ cái + số tùy chọn, `:p`, số trang; nhiều mã đứng liền hoặc cách nhau dấu cách). Trình dựng bọc từng mã thành `<span class="src">[G1:p203]</span>`, không bao giờ làm mất.
- Ý chưa tìm được nguồn: `[?]` → `<span class="src miss">[?]</span>`. `check_sources` (xem dưới) liệt kê mọi `[?]` để người dùng quyết.
- Không bịa nội dung, không gộp hay cắt chữ khi chuyển từ HTML cũ sang Markdown.

## 2. HTML dựng ra (đầu vào của CSS)

```html
<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>…</title>
<link rel="stylesheet" href="../styles/<style>.css"></head><body class="style-<style>">
<header><h1>Tiêu đề</h1><div class="sub">…</div></header>
<div class="cols">
<section class="bx khai-niem"><h2>Tên mục<span class="kick">khái niệm</span></h2>
  <ul><li>… <span class="n">…</span> <span class="src">[G1:p203]</span></li>
      <li class="trap">…</li></ul>
  <table><tr><th>…</th></tr><tr><td>…</td></tr></table>
</section>
</div></body></html>
```

- Lớp hộp = đúng chín mã `boxes.py`: `khai-niem`, `dich-te-phan-loai`, `benh-hoc`, `lam-sang`, `cls-chi-dinh`, `dieu-tri`, `canh-bao-bien-chung`, `theo-doi`, `tu-kiem-tra`. Luôn có thêm lớp `bx` ở `section`.
- `span.kick` chứa nhãn tiếng Việt của loại hộp. Bảng mã → nhãn nằm **một chỗ** trong `boxes.py` (`LABELS`): khái niệm · dịch tễ và phân loại · bệnh học · lâm sàng · cận lâm sàng và chỉ định · điều trị · cảnh báo và biến chứng · theo dõi · tự kiểm tra.
- Thứ tự phần tử trong `section` luôn là: `h2` rồi (`ul` | `table` | `p`) lặp lại.
- Lớp `style-<style>` trên `body`; `<style>` là `warm`, `clean` hoặc `screen`.

## 3. CSS

- `styles/tokens.css`: chín cặp biến `--hop-<ma>` (viền/tiêu đề) và `--hop-<ma>-nen` (nền nhạt), giá trị theo spec (khái niệm `#2f6db0`, dịch tễ `#1f7f78`, bệnh học `#8a6a1c`, lâm sàng `#3b7d3a`, cận lâm sàng `#b8611f`, điều trị `#b23a62`, cảnh báo `#a3261a`, theo dõi `#4b6177`, tự kiểm tra `#7b6400`; không dùng tím). Mỗi style file `@import "tokens.css"` ở dòng đầu.
- Font: `@font-face` trỏ đường dẫn tương đối `../node_modules/@fontsource/<tên>/files/<tên>-<subset>-<weight>-<style>.woff2`, mỗi font khai tối thiểu subset `latin`, `latin-ext`, `vietnamese` (kèm `unicode-range`). Không dùng `file:///` tuyệt đối.
- `warm`: B14 ấm (Inter, Oswald, Dancing Script, Patrick Hand), viền và dải tiêu đề cùng màu hộp.
- `clean`: **đen trắng**, không màu. Phân loại bằng nhãn chữ `kick` (luôn hiện, chữ in hoa nhỏ) làm dấu hiệu chính, ký hiệu đầu tiêu đề và kiểu kẻ (đôi, đứt, đậm) là phụ. `li.trap` giữ ▲ và chữ nghiêng. Chỉ dùng glyph Source Sans 3/Source Serif 4 có sẵn hoặc đã qua `check_fonts.py`.
- `screen`: dải tiêu đề đúng chín màu, ô nền nhạt, Be Vietnam Pro và JetBrains Mono.
- `span.src`: nhỏ, xám, không ngắt dòng giữa mã; `span.src.miss` nổi bật (để người dùng thấy ý thiếu nguồn).
- `@page` A4, `-webkit-print-color-adjust:exact`.
