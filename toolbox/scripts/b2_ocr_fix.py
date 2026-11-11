"""B2. Sửa lỗi OCR: từ điển tích lũy, liệt kê dòng nghi lỗi, áp bản vá.

Chạy:
  python toolbox/scripts/b2_ocr_fix.py G1-B08 suspects
  python toolbox/scripts/b2_ocr_fix.py G1-B08 patch patch.json
Bản vá: [{"line": 12, "old": "phồi", "new": "phổi", "learn": true}]
Kết quả: kho/lessons/<lesson>/fixed.txt
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402

BEFORE = r"(?<![\w])"
AFTER = r"(?![\w])"
GARBLED = re.compile(r"[^\W\d_]+\d+[^\W\d_]+|[^\W\d_]+[|~^\\]+[^\W\d_]*|[|~^\\]+[^\W\d_]+")


def load_dict(path: str | None = None) -> list[tuple[str, str]]:
    path = path or common.data_path("ocr_dict.tsv")
    if not os.path.exists(path):
        return []
    lines = common.read_text(path).splitlines()[1:]
    return [tuple(ln.split("\t")[:2]) for ln in lines if "\t" in ln]


def _learn(path: str, wrong: str, right: str) -> None:
    table = load_dict(path)
    if (wrong, right) not in table:
        table.append((wrong, right))
    common.write_text(path, "wrong\tright\n" + "".join(f"{w}\t{r}\n" for w, r in table))


def apply_dict(text: str, table: list[tuple[str, str]]) -> tuple[str, int]:
    total = 0
    for wrong, right in table:
        text, n = re.subn(BEFORE + re.escape(wrong) + AFTER, lambda _m, r=right: r, text)
        total += n
    return text, total


def apply_patch(text: str, patch: list[dict], dict_path: str | None = None) -> str:
    lines = text.split("\n")
    for p in patch:  # kiểm tra hết trước khi sửa để không ghi dở
        n = p["line"]
        if not 1 <= n <= len(lines) or p["old"] not in lines[n - 1]:
            raise ValueError(f"Dòng {n} không khớp: {p['old']!r}")
    for p in patch:
        lines[p["line"] - 1] = lines[p["line"] - 1].replace(p["old"], p["new"], 1)
    for p in patch:
        if p.get("learn"):
            _learn(dict_path or common.data_path("ocr_dict.tsv"), p["old"], p["new"])
    return "\n".join(lines)


def suspects(text: str) -> list[tuple[int, str]]:
    return [(i, ln) for i, ln in enumerate(text.split("\n"), 1)
            if not ln.startswith("<<") and (GARBLED.search(ln) or "[?" in ln)]


def main() -> None:
    lesson, cmd = sys.argv[1], sys.argv[2]
    fixed = common.kho_path("lessons", lesson, "fixed.txt")
    source = fixed if os.path.exists(fixed) else common.kho_path("lessons", lesson, "raw.txt")
    text, n = apply_dict(common.read_text(source), load_dict())
    if cmd == "patch":
        with open(sys.argv[3], encoding="utf-8") as f:
            text = apply_patch(text, json.load(f))
    common.write_text(fixed, text)
    if cmd == "suspects":
        for i, ln in suspects(text):
            print(f"{i}: {ln}")
    print(f"Từ điển sửa {n} chỗ")


if __name__ == "__main__":
    main()
