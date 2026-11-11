"""A6. Gán nguồn tham khảo vào bài theo chuyên khoa, tên file và từ khóa trong kho.

Chạy: python toolbox/scripts/a6_assign.py
Kết quả: data/lesson_sources.csv
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common, ink  # noqa: E402

FIELDS = ["lesson", "code", "pages", "score", "ink_pages"]
GENERAL = {"", "Tổng hợp"}  # Textbook và Notes\\Tổng hợp dùng được cho mọi chuyên khoa
NOT_LETTER_BEFORE = r"(?<![^\W\d_])"
NOT_LETTER_AFTER = r"(?![^\W\d_])"


def _pattern(keywords: str) -> re.Pattern:
    words = [common.nfc(k.strip()) for k in keywords.split(";") if k.strip()]
    return re.compile(NOT_LETTER_BEFORE + "(" + "|".join(map(re.escape, words)) + ")" + NOT_LETTER_AFTER, re.I)


def _page_texts(code: str) -> dict[int, str]:
    files = glob.glob(common.kho_path(code, "p[0-9][0-9][0-9][0-9].txt"))
    files += glob.glob(common.kho_path(code, "p[0-9][0-9][0-9][0-9].lowocr.txt"))
    return {int(os.path.basename(f)[1:5]): common.nfc(common.read_text(f)) for f in files}


def _ink_pages(path: str) -> set[int]:
    if not path.lower().endswith(".pdf"):
        return set()
    try:
        with pymupdf.open(path) as d:
            return {i for i, p in enumerate(d, 1) if ink.ink_regions(p)}
    except Exception:
        return set()


def assign(manifest: list[dict], keywords: list[dict], root: str) -> list[dict]:
    compiled = [(k["lesson"], k.get("folder_hint", ""), _pattern(k["keywords"])) for k in keywords]
    rows = []
    for m in manifest:
        if m["status"] != "primary" or m["code"] in ("G1", "G2") or m["kind"] == "needs_manual":
            continue
        texts = _page_texts(m["code"])
        name = common.nfc(os.path.basename(m["path"]))
        total = int(m["pages"] or 0) or max(texts, default=0)
        inks = None
        for lesson, hint, pat in compiled:
            if hint and m["specialty"] not in GENERAL and hint != m["specialty"]:
                continue
            hits = {p: len(pat.findall(t)) for p, t in texts.items()}
            hits = {p: n for p, n in hits.items() if n}
            by_name = bool(pat.search(name))
            pages = set(range(1, total + 1)) if by_name else set(hits)
            if not pages:
                continue
            if inks is None:
                inks = _ink_pages(os.path.join(root, m["path"]))
            rows.append({"lesson": lesson, "code": m["code"],
                         "pages": ";".join(map(str, sorted(pages))),
                         "score": sum(hits.values()) + (len(pages) if by_name else 0),
                         "ink_pages": ";".join(map(str, sorted(pages & inks)))})
    return rows


def main() -> None:
    root = os.path.join(common.load_config()["source_root"], "Tài liệu")
    rows = assign(common.read_csv(common.data_path("manifest.csv")),
                  common.read_csv(common.data_path("topic_keywords.csv")), root)
    common.write_csv(common.data_path("lesson_sources.csv"), rows, FIELDS)
    print(f"{len(rows)} liên kết bài - nguồn")


if __name__ == "__main__":
    main()
