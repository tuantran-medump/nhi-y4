"""B1. Cắt chữ của một bài từ kho theo bản đồ trang, kèm dấu trang.

Chạy: python toolbox/scripts/b1_slice.py G1-B08
Kết quả: kho/lessons/<lesson>/raw.txt
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402


def lesson_info(lesson: str) -> dict:
    return next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)


def strip_furniture(text: str) -> str:
    """Bỏ tiêu đề chạy, số trang, dấu CamScanner. Đây không phải nội dung sách."""
    lines = [ln for ln in text.splitlines() if not re.search(r"CamScanner|quét bằng", ln, re.I)]
    seen = 0
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        seen += 1
        if seen > 3:
            break
        if re.match(r"^\s*\d{1,3}\D{0,6}NHI\s*KHOA", ln, re.I) or re.match(r"^\s*B[àa]i\s*\d.*\D\d{1,3}\s*$", ln, re.I):
            del lines[i]
            break
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and re.fullmatch(r"\s*\d{1,3}\s*", lines[-1]):
        lines.pop()
    return "\n".join(lines)


def slice_lesson(lesson: str) -> str:
    book = lesson_info(lesson)["book"]
    rows = [r for r in common.read_csv(common.data_path(f"pagemap_{book}.csv"))
            if r["lesson"] == lesson and r["confidence"] != "duplicate"]
    parts = []
    for r in sorted(rows, key=lambda x: int(x["pdf_page"])):
        marker = f"<<p{r['pdf_page']}>>"  # trích dẫn dùng số trang của file PDF
        parts.append(marker + "\n" + strip_furniture(common.read_text(common.page_file(book, int(r["pdf_page"])))).strip())
    text = "\n".join(parts) + "\n"
    common.write_text(common.kho_path("lessons", lesson, "raw.txt"), text)
    return text


if __name__ == "__main__":
    print(len(slice_lesson(sys.argv[1]).splitlines()), "dòng")
