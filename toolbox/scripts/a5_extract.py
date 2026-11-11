"""A5. Trích chữ từng trang của mọi file có lớp chữ vào kho. Chạy lại bỏ qua trang đã có.

Chạy: python toolbox/scripts/a5_extract.py
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
pymupdf.TOOLS.mupdf_display_errors(False)


def _paragraphs(xml: bytes, ns: str) -> list[str]:
    root = ET.fromstring(xml)
    out = []
    for p in root.iter(f"{ns}p"):
        text = "".join(t.text or "" for t in p.iter(f"{ns}t"))
        if text.strip():
            out.append(text)
    return out


def _save(code: str, page: int, text: str) -> None:
    path = common.page_file(code, page)
    if not os.path.exists(path):
        common.write_text(path, text)


def extract(row: dict, root: str) -> str:
    """Trả về 'done', 'skip' hoặc 'needs_manual'."""
    code, kind = row["code"], row["kind"]
    if code in ("G1", "G2"):
        return "skip"  # sách đi qua OCR ở bước A3
    if kind == "needs_manual":
        return "needs_manual"
    path = os.path.join(root, row["path"])
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            with pymupdf.open(path) as d:
                for i, p in enumerate(d, 1):
                    text = p.get_text()
                    if text.strip():
                        _save(code, i, text)
        elif ext == ".docx":
            with zipfile.ZipFile(path) as z:
                _save(code, 1, "\n".join(_paragraphs(z.read("word/document.xml"), W)))
        elif ext == ".pptx":
            with zipfile.ZipFile(path) as z:
                names = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
                names.sort(key=lambda n: int(re.search(r"(\d+)\.xml", n).group(1)))
                for i, n in enumerate(names, 1):
                    _save(code, i, "\n".join(_paragraphs(z.read(n), A)))
        else:
            return "skip"
    except Exception:
        return "needs_manual"
    return "done"


def main() -> None:
    root = os.path.join(common.load_config()["source_root"], "Tài liệu")
    counts: dict[str, int] = {}
    for r in common.read_csv(common.data_path("manifest.csv")):
        if r["status"] != "primary":
            continue
        res = extract(r, root)
        counts[res] = counts.get(res, 0) + 1
        if res == "needs_manual":
            print("Cần xử lý tay:", r["code"], r["path"])
    print(counts)


if __name__ == "__main__":
    main()
