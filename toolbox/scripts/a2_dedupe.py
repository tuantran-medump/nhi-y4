"""A2. Đánh dấu bản trùng trong data/manifest.csv.

Trùng hash là bản trùng. Trùng chữ (từ 0.97) chỉ là bản trùng khi số nét và ghi chú
bằng nhau, vì bản có ghi chú tay khác biệt vẫn phải giữ.

Chạy: python toolbox/scripts/a2_dedupe.py
"""
import os
import sys
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402
from scripts.a1_inventory import FIELDS  # noqa: E402

THRESHOLD = 0.97
MAX_WORDS = 4000


def _profile(path: str) -> tuple[list[str], int]:
    """Trả về danh sách từ và số annotation cộng nét vẽ của file PDF."""
    words: list[str] = []
    marks = 0
    try:
        with pymupdf.open(path) as d:
            for p in d:
                words += p.get_text().split()
                marks += sum(1 for _ in p.annots()) + len(p.get_drawings())
    except Exception:
        return [], -1
    return words, marks


def _same_text(a: list[str], b: list[str]) -> bool:
    if not a or not b or min(len(a), len(b)) / max(len(a), len(b)) < THRESHOLD:
        return False
    sa, sb = set(a), set(b)
    if len(sa & sb) / len(sa | sb) < 0.9:
        return False
    return SequenceMatcher(None, a[:MAX_WORDS], b[:MAX_WORDS], autojunk=False).ratio() >= THRESHOLD


def mark(rows: list[dict], root: str) -> list[dict]:
    first_by_hash: dict[str, str] = {}
    for r in rows:
        r["status"] = "primary"
        if r["sha256"] in first_by_hash:
            r["status"] = f"dup_of:{first_by_hash[r['sha256']]}"
        else:
            first_by_hash[r["sha256"]] = r["code"]
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        if r["status"] == "primary" and r["kind"] in ("text", "mixed"):
            groups.setdefault((r["specialty"], str(r["pages"])), []).append(r)
    for group in groups.values():
        if len(group) < 2:
            continue
        kept: list[tuple[dict, list[str], int]] = []
        for r in group:
            words, marks = _profile(os.path.join(root, r["path"]))
            twin = next((k for k in kept if k[2] == marks and marks >= 0 and _same_text(k[1], words)), None)
            if twin:
                r["status"] = f"dup_of:{twin[0]['code']}"
            else:
                kept.append((r, words, marks))
    return rows


def main() -> None:
    root = os.path.join(common.load_config()["source_root"], "Tài liệu")
    path = common.data_path("manifest.csv")
    rows = mark(common.read_csv(path), root)
    common.write_csv(path, rows, FIELDS)
    dups = sum(1 for r in rows if r["status"] != "primary")
    print(f"{len(rows)} file, {dups} bản trùng")


if __name__ == "__main__":
    main()
