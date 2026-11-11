"""B2. Soát OCR từng trang: model nhỏ xem ảnh trang cạnh bản chữ, chỉ ghi các chỗ cần sửa.

Chạy:
  python toolbox/scripts/b2_review.py G1-B08 tasks   (tạo ảnh và chữ từng trang trong kho/lessons/<bài>/review)
  python toolbox/scripts/b2_review.py G1-B08 apply   (áp results/<id>.json vào fixed.txt)
Chỉ chạy apply khi đã soát xong cả lượt, vì số dòng tính theo fixed.txt lúc tạo task.
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402
from scripts import b2_ocr_fix  # noqa: E402

DPI = 160
MARKER = re.compile(r"^<<p(\d+)>>$")
pymupdf.TOOLS.mupdf_display_errors(False)


def _dir(lesson: str, *parts: str) -> str:
    return common.kho_path("lessons", lesson, "review", *parts)


def _fixed(lesson: str) -> str:
    return common.kho_path("lessons", lesson, "fixed.txt")


def _segments(text: str) -> list[tuple[int, int, int]]:
    """Trả về (trang, dòng đầu, dòng cuối) theo số dòng của toàn file, không tính dòng dấu trang."""
    lines = text.split("\n")
    marks = [(i + 1, int(m.group(1))) for i, ln in enumerate(lines) if (m := MARKER.match(ln.strip()))]
    out = []
    for k, (line_no, page) in enumerate(marks):
        end = marks[k + 1][0] - 1 if k + 1 < len(marks) else len(lines)
        out.append((page, line_no + 1, end))
    return out


def make_tasks(lesson: str, root: str | None = None) -> list[dict]:
    if root is None:
        root = os.path.join(common.load_config()["source_root"], "Tài liệu")
    book = next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)["book"]
    row = next(r for r in common.read_csv(common.data_path("manifest.csv")) if r["code"] == book)
    done = common.read_json(_dir(lesson, "done.json"), [])
    text = common.read_text(_fixed(lesson))
    lines = text.split("\n")
    shutil.rmtree(_dir(lesson, "results"), ignore_errors=True)
    os.makedirs(_dir(lesson, "results"), exist_ok=True)
    tasks = []
    with pymupdf.open(os.path.join(root, row["path"])) as d:
        for page, start, end in _segments(text):
            if page in done:
                continue
            tid = f"p{page:04d}"
            d[page - 1].get_pixmap(dpi=DPI).save(_dir(lesson, tid + ".png"))
            numbered = "".join(f"{n}\t{lines[n - 1]}\n" for n in range(start, end + 1) if lines[n - 1].strip())
            common.write_text(_dir(lesson, tid + ".txt"), numbered)
            tasks.append({"id": tid, "page": page, "image": tid + ".png", "text": tid + ".txt",
                          "start": start, "end": end})
    common.write_json(_dir(lesson, "tasks.json"), tasks)
    return tasks


def apply(lesson: str) -> dict:
    tasks = common.read_json(_dir(lesson, "tasks.json"), [])
    done = common.read_json(_dir(lesson, "done.json"), [])
    patch, missing, reviewed = [], [], []
    for t in tasks:
        if t["page"] in done:
            continue
        path = _dir(lesson, "results", t["id"] + ".json")
        if not os.path.exists(path):
            missing.append(t["page"])
            continue
        items = common.read_json(path, [])
        for p in items:
            if not t["start"] <= p["line"] <= t["end"]:
                raise ValueError(f"Trang {t['page']}: dòng {p['line']} nằm ngoài trang")
        patch += items
        reviewed.append(t["page"])
    if reviewed:
        common.write_text(_fixed(lesson), b2_ocr_fix.apply_patch(common.read_text(_fixed(lesson)), patch))
        common.write_json(_dir(lesson, "done.json"), done + reviewed)
    return {"applied": len(patch), "reviewed": reviewed, "missing": missing}


if __name__ == "__main__":
    if sys.argv[2] == "tasks":
        print(len(make_tasks(sys.argv[1])), "trang cần soát")
    else:
        print(apply(sys.argv[1]))
