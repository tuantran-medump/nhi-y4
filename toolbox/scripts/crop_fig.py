"""Cắt hình từ trang sách, vị trí tính theo tỉ lệ 0-1 của trang.

Chạy: python toolbox/scripts/crop_fig.py G1-B05 88 0.1 0.2 0.9 0.6 p0088f
Kết quả: kho/lessons/<bài>/fig/<tên>.png, trong bài dùng ![Hình](fig/<tên>.png)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402
from scripts.b7_render import crop_figure  # noqa: E402

pymupdf.TOOLS.mupdf_display_errors(False)


def crop(pdf: str, lesson: str, page: int, box: tuple[float, float, float, float], name: str) -> str:
    with pymupdf.open(pdf) as d:
        r = d[page - 1].rect
    rect = (box[0] * r.width, box[1] * r.height, box[2] * r.width, box[3] * r.height)
    out = common.kho_path("lessons", lesson, "fig", name + ".png")
    crop_figure(pdf, page, rect, out)
    return out


if __name__ == "__main__":
    lesson, page = sys.argv[1], int(sys.argv[2])
    box = tuple(float(x) for x in sys.argv[3:7])
    book = next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)["book"]
    row = next(r for r in common.read_csv(common.data_path("manifest.csv")) if r["code"] == book)
    print(crop(os.path.join(common.load_config()["source_root"], "Tài liệu", row["path"]), lesson, page, box, sys.argv[7]))
