"""A1. Lập danh mục file nguồn, cấp mã ổn định qua các lần chạy.

Chạy: python toolbox/scripts/a1_inventory.py
Kết quả: data/manifest.csv
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402

FIELDS = ["code", "path", "sha256", "pages", "kind", "folder", "specialty", "status"]
PREFIX = {"Slide": "S", "CBL - Case": "C", "Notes": "N", "Textbook": "R"}
BOOKS = {"Nhi Khoa Tập 1 2025.pdf": "G1", "Nhi Khoa Tập 2 2025.pdf": "G2"}
IMAGE_EXT = {".png", ".jpg", ".jpeg"}
OFFICE_EXT = {".docx", ".pptx"}
pymupdf.TOOLS.mupdf_display_errors(False)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(path: str) -> tuple[str, int]:
    ext = os.path.splitext(path)[1].lower()
    if ext in OFFICE_EXT:
        return "office", 0
    if ext in IMAGE_EXT:
        try:
            with pymupdf.open(path) as d:
                d[0].get_pixmap()  # ảnh hỏng chỉ báo lỗi khi đọc trang
                return "image", 1
        except Exception:
            return "needs_manual", 0
    if ext != ".pdf":
        return "needs_manual", 0
    try:
        with pymupdf.open(path) as d:
            if d.needs_pass:
                return "needs_manual", 0
            n = d.page_count
            texted = sum(1 for p in d if len(p.get_text().strip()) >= 80)
    except Exception:
        return "needs_manual", 0
    if n == 0:
        return "needs_manual", 0
    if texted >= 0.8 * n:
        return "text", n
    if texted <= 0.1 * n:
        return "image", n
    return "mixed", n


def build(root: str, previous: list[dict] | None = None) -> list[dict]:
    previous = previous or []
    by_path = {common.nfc(r["path"]): r for r in previous}
    by_hash: dict[str, list[str]] = {}
    for r in previous:
        by_hash.setdefault(r["sha256"], []).append(r["code"])
    used = {r["code"] for r in previous}
    rows = []
    for dp, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files, key=common.nfc):
            full = os.path.join(dp, name)
            rel = os.path.relpath(full, root)
            parts = common.nfc(rel).split(os.sep)
            kind, pages = classify(full)
            rows.append({
                "code": "", "path": rel, "sha256": sha256(full), "pages": pages, "kind": kind,
                "folder": parts[0] if len(parts) > 1 else "",
                "specialty": parts[1] if len(parts) > 2 else "",
                "status": "primary",
            })
    taken = set()
    for r in rows:  # giữ mã cũ: theo đường dẫn trước, rồi theo hash nếu file đã chuyển chỗ
        old = by_path.get(common.nfc(r["path"]))
        if old and old["sha256"] == r["sha256"]:
            r["code"] = old["code"]
            taken.add(r["code"])
    for r in rows:
        if not r["code"]:
            for code in by_hash.get(r["sha256"], []):
                if code not in taken:
                    r["code"] = code
                    taken.add(code)
                    break
    counters: dict[str, int] = {}
    for r in rows:
        if r["code"]:
            continue
        book = BOOKS.get(common.nfc(os.path.basename(r["path"])))
        if book and r["folder"] == "Textbook":
            r["code"] = book
            taken.add(book)
            continue
        prefix = PREFIX.get(r["folder"], "R")
        n = counters.get(prefix, 0)
        while True:
            n += 1
            code = f"{prefix}{n:03d}"
            if code not in taken and code not in used:
                break
        counters[prefix] = n
        r["code"] = code
        taken.add(code)
    return rows


def main() -> None:
    root = os.path.join(common.load_config()["source_root"], "Tài liệu")
    path = common.data_path("manifest.csv")
    rows = build(root, common.read_csv(path))
    common.write_csv(path, rows, FIELDS)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    print(f"{len(rows)} file: {counts}")


if __name__ == "__main__":
    main()
