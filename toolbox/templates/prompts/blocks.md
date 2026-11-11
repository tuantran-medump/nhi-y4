# Gõ lại bảng, lưu đồ và cắt hình (model nhỏ)

Đầu vào: `kho/lessons/<bài>/fixed.txt` có các khối giữa dòng `<<block:ID>>` và `<<endblock>>`. ID dạng `p0128a` cho biết trang PDF 128. Ảnh trang: `kho/lessons/<bài>/review/p0128.png`.

Ghi mỗi khối thành `kho/lessons/<bài>/blocks/<ID>.md`.

**Bảng:** Markdown dạng pipe (`| A | B |`, dòng thứ hai `|---|---|`).
- Đủ mọi hàng, cột, đúng từng chữ, dấu, số, đơn vị, ký hiệu ≥ ≤ > < như trên ảnh. Không suy đoán liều.
- Ô nhiều ý ngăn bằng ` ; `, không xuống dòng trong ô, không dùng `|` trong nội dung.
- Ô gộp nhiều hàng: lặp lại nội dung ở mỗi hàng.
- Không chép tên bảng nếu nó nằm ngoài khối.
- Chữ không chắc ghi `[?chữ?]`.

**Lưu đồ, sơ đồ có chữ** (khối tận cùng bằng chữ cái khác `f`): cắt hình gốc rồi gõ lại nội dung dưới hình bằng danh sách thụt lề `-`, `+`, `*`, dùng `→` cho mũi tên.

**Hình** (khối tận cùng bằng `f`): chỉ cắt hình, file `.md` chỉ có một dòng `![Hình](fig/<ID>.png)`.

**Cách cắt hình:** `python toolbox/scripts/crop_fig.py <bài> <trang> <x0> <y0> <x1> <y1> <ID>`, tọa độ là tỉ lệ 0-1 của trang. Xem lại `kho/lessons/<bài>/fig/<ID>.png` để chắc đủ hình, không dính chữ thân bài, không dính tên hình. Chèn vào `.md`: `![Hình](fig/<ID>.png)`.

Trang khó đọc số thì render rõ hơn bằng PyMuPDF ở 260 dpi. Script tạm để trong `kho/lessons/<bài>/tmp/`, không dùng thư mục tạm chung.
