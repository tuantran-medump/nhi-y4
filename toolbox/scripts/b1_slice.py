"""B1. Cắt chữ của một bài từ kho theo bản đồ trang, kèm dấu trang.

Chạy: python toolbox/scripts/b1_slice.py G1-B08
Kết quả: kho/lessons/<lesson>/raw.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402


def lesson_info(lesson: str) -> dict:
    return next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)


def slice_lesson(lesson: str) -> str:
    book = lesson_info(lesson)["book"]
    rows = [r for r in common.read_csv(common.data_path(f"pagemap_{book}.csv")) if r["lesson"] == lesson]
    parts = []
    for r in sorted(rows, key=lambda x: int(x["pdf_page"])):
        marker = f"<<p{r['pdf_page']}>>"  # trích dẫn dùng số trang của file PDF
        parts.append(marker + "\n" + common.read_text(common.page_file(book, int(r["pdf_page"]))).strip())
    text = "\n".join(parts) + "\n"
    common.write_text(common.kho_path("lessons", lesson, "raw.txt"), text)
    return text


if __name__ == "__main__":
    print(len(slice_lesson(sys.argv[1]).splitlines()), "dòng")
