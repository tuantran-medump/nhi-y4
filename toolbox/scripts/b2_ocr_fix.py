"""B2. Sửa lỗi OCR: từ điển tích lũy, liệt kê dòng nghi lỗi, áp bản vá.

Chạy:
  python toolbox/scripts/b2_ocr_fix.py G1-B08 suspects
  python toolbox/scripts/b2_ocr_fix.py G1-B08 patch patch.json
Bản vá: [{"line": 12, "old": "phồi", "new": "phổi", "learn": true}]
Sửa chữ số bắt buộc đối chiếu ảnh gốc và ghi "verified": true.
Bọc bảng, hình bằng dòng <<block:t1>> và <<endblock>> để gõ lại riêng.
Kết quả: kho/lessons/<lesson>/fixed.txt
"""
import glob
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402

BEFORE = r"(?<![\w])"
AFTER = r"(?![\w])"
GARBLED = re.compile(r"[^\W\d_]+\d+[^\W\d_]+|[^\W\d_]+[|~^\\]+[^\W\d_]*|[|~^\\]+[^\W\d_]+"
                     r"|(?<![^\W\d_])(?:\d+[OolI]+\d*|[OolI]+[.,]?\d+)(?![^\W\d_])")


def _has_digit(s: str) -> bool:
    return any(c.isdigit() for c in s)


def _digits(s: str) -> list[str]:
    return [c for c in re.sub(r"<<[^>]*>>", "", s) if c.isdigit()]


def load_dict(path: str | None = None) -> list[tuple[str, str]]:
    path = path or common.data_path("ocr_dict.tsv")
    if not os.path.exists(path):
        return []
    lines = common.read_text(path).splitlines()[1:]
    return [tuple(ln.split("\t")[:2]) for ln in lines if "\t" in ln]


def _learn(path: str, wrong: str, right: str) -> None:
    if _has_digit(wrong) or _has_digit(right):
        return  # số phải được đối chiếu từng chỗ, không tự sửa hàng loạt
    table = load_dict(path)
    if (wrong, right) not in table:
        table.append((wrong, right))
    common.write_text(path, "wrong\tright\n" + "".join(f"{w}\t{r}\n" for w, r in table))


def apply_dict(text: str, table: list[tuple[str, str]]) -> tuple[str, int]:
    total = 0
    for wrong, right in table:
        if _has_digit(wrong) or _has_digit(right):
            continue
        text, n = re.subn(BEFORE + re.escape(wrong) + AFTER, lambda _m, r=right: r, text)
        total += n
    return text, total


def apply_patch(text: str, patch: list[dict], dict_path: str | None = None) -> str:
    lines = text.split("\n")
    for p in patch:  # kiểm tra hết trước khi sửa để không ghi dở
        n = p["line"]
        if not 1 <= n <= len(lines) or p["old"] not in lines[n - 1]:
            raise ValueError(f"Dòng {n} không khớp: {p['old']!r}")
        if _digits(p["old"]) != _digits(p["new"]) and not p.get("verified"):
            raise ValueError(f"Dòng {n} đổi số, cần đối chiếu ảnh gốc rồi ghi verified: true")
    for p in patch:
        lines[p["line"] - 1] = lines[p["line"] - 1].replace(p["old"], p["new"], 1)
    for p in patch:
        if p.get("learn"):
            _learn(dict_path or common.data_path("ocr_dict.tsv"), p["old"], p["new"])
    return "\n".join(lines)


def suspects(text: str) -> list[tuple[int, str]]:
    return [(i, ln) for i, ln in enumerate(text.split("\n"), 1)
            if not ln.startswith("<<") and (GARBLED.search(ln) or "[?" in ln)]


def _pairs(line: str) -> list[str]:
    words = [w.strip(".,;:()[]\"'-–") for w in common.nfc(line).lower().split()]
    out = []
    for a, b in zip(words, words[1:]):
        if a.isalpha() and b.isalpha():
            out.append(f"{a} {b}")
    return out


def bigram_counts(texts: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for text in texts:
        for line in text.split("\n"):
            for pair in _pairs(line):
                counts[pair] = counts.get(pair, 0) + 1
    return counts


def rare_bigrams(text: str, counts: dict[str, int]) -> list[tuple[int, str, str]]:
    """Cặp từ chưa từng xuất hiện trong tài liệu có lớp chữ: nơi dễ còn lỗi dấu."""
    found, in_block = [], False
    for n, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("<<block:"):
            in_block = True
        elif stripped == "<<endblock>>":
            in_block = False
        elif not in_block and not stripped.startswith("<<"):
            found += [(n, pair, stripped) for pair in _pairs(line) if pair not in counts]
    return found


def _base(s: str) -> str:
    plain = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in plain if not unicodedata.combining(c))


def diacritic_suspects(text: str, counts: dict[str, int], ratio: int = 10) -> list[tuple[int, str, str]]:
    """Cặp từ chỉ khác dấu so với một cặp phổ biến hơn hẳn trong kho: nghi sai dấu, kèm gợi ý."""
    best: dict[str, tuple[int, str]] = {}
    for pair, n in counts.items():
        key = _base(pair)
        if n > best.get(key, (0, ""))[0]:
            best[key] = (n, pair)
    found, in_block = [], False
    for no, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("<<block:"):
            in_block = True
        elif stripped == "<<endblock>>":
            in_block = False
        elif not in_block and not stripped.startswith("<<"):
            for pair in _pairs(line):
                top = best.get(_base(pair))
                if top and top[1] != pair and top[0] >= ratio * max(counts.get(pair, 0), 1):
                    found.append((no, pair, top[1]))
    return found


def corpus() -> dict[str, int]:
    """Kho cặp từ từ các file có lớp chữ thật, không dùng bản OCR."""
    texts = []
    for r in common.read_csv(common.data_path("manifest.csv")):
        if r["kind"] in ("text", "office") and r["status"] == "primary":
            for f in glob.glob(common.kho_path(r["code"], "p[0-9][0-9][0-9][0-9].txt")):
                texts.append(common.read_text(f))
    return bigram_counts(texts)


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
    if cmd == "bigrams":
        for i, pair, ln in rare_bigrams(text, corpus()):
            print(f"{i}\t{pair}\t{ln}")
    if cmd == "diacritics":
        for i, pair, better in diacritic_suspects(text, corpus()):
            print(f"{i}\t{pair}\t{better}")
    print(f"Từ điển sửa {n} chỗ")


if __name__ == "__main__":
    main()
