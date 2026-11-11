"""B2b. Tách câu, xếp cấp dòng theo bảng của agent, so khớp từng từ với bản đã sửa OCR.

Chạy:
  python toolbox/scripts/b2b_layout.py G1-B08 units          (in các dòng đánh số)
  python toolbox/scripts/b2b_layout.py G1-B08 apply table.json
Bảng chỉ cần ghi dòng khác mặc định:
  [{"line":3,"level":2,"marker":"+","split":["gồm:",","]},{"line":9,"join_prev":true}]
Kết quả: kho/lessons/<lesson>/body.md
"""
import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402

PAGE = re.compile(r"^<<.*>>$")
BULLET = re.compile(r"^\s*[-+*•–]\s+")
HEAD = re.compile(r"^(\d+(?:\.\d+)*)\.\s+\S")
NUMBER = r"(?:\d+\.|[IVXLC]+\.)"
DEFAULT_MARKER = {1: "-", 2: "+", 3: "*"}
NOTE = re.compile(r"\s*\([^()]*\[[SCNRE]\d+:p[^\]]*\][^()]*\)")
CITE = re.compile(r"\s*\[[GSCNRE]\d*:p[^\]]*\]")
END_COMMA = re.compile(r"[,;](?=\s|$)")


def _is_heading(line: str) -> bool:
    return bool(HEAD.match(line)) and len(line) < 90 and not line.rstrip().endswith((".", ";", ":", ","))


def _sentences(par: str) -> list[str]:
    out, start = [], 0
    for m in re.finditer(r"(?<=[.!?;])\s+(?=\S)", par):
        before = par[start:m.start()]
        nxt = par[m.end()]
        if before.endswith(".") and re.search(r"(?:^|\s|\.)[^\W\d_]{1,2}\.$", before):
            continue
        if before.endswith(";") or nxt.isupper() or nxt.isdigit() or nxt == "(":
            out.append(before)
            start = m.end()
    out.append(par[start:])
    return [s.strip() for s in out if s.strip()]


def split_units(text: str) -> list[str]:
    units: list[str] = []
    par: list[str] = []

    def flush() -> None:
        if par:
            units.extend(_sentences(" ".join(par)))
            par.clear()

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            flush()
        elif PAGE.match(line) or _is_heading(line):
            flush()
            units.append(line)
        else:
            if BULLET.match(line):
                flush()
            par.append(line)
    flush()
    return units


def _line(text: str, level: int, marker: str) -> str:
    text = BULLET.sub("", text, count=1)
    if text.startswith(marker + " "):
        text = text[len(marker) + 1:]
    return "  " * (level - 1) + marker + " " + text


def apply_layout(units: list[str], table: list[dict]) -> str:
    by_line = {t["line"]: t for t in table}
    out: list[str] = []
    for i, unit in enumerate(units, 1):
        t = by_line.get(i, {})
        if PAGE.match(unit):
            out.append(unit)
        elif t.get("join_prev"):
            idx = max(k for k, v in enumerate(out) if not PAGE.match(v))
            out[idx] += " " + unit
        elif not t and _is_heading(unit):
            depth = HEAD.match(unit).group(1).count(".") + 1
            out.append("#" * (depth + 1) + " " + unit)
        else:
            level = t.get("level", 1)
            marker = t.get("marker", DEFAULT_MARKER.get(level, "-"))
            if "split" in t:
                lead, sep = t["split"]
                cut = unit.index(lead) + len(lead)
                out.append(_line(unit[:cut], level, marker))
                child = t.get("child_marker", DEFAULT_MARKER.get(level + 1, "-"))
                for part in unit[cut:].split(sep):
                    if part.strip():
                        out.append(_line(part.strip(), level + 1, child))
            else:
                out.append(_line(unit, level, marker))
    return "\n".join(out)


def _strip_fixed(line: str) -> str:
    line = BULLET.sub("", line, count=1)
    return re.sub(rf"^\s*{NUMBER}\s+", "", line, count=1)


def _strip_body(line: str) -> str:
    if re.match(r"^\s*#+\s", line):
        return re.sub(r"^\s*#+\s+(?:\d+\.\s+)?", "", line, count=1)
    if BULLET.match(line):
        return re.sub(rf"^\s*{NUMBER}\s+", "", BULLET.sub("", line, count=1), count=1)
    return re.sub(rf"^\s*{NUMBER}\s+", "", line, count=1)


def _tokens(text: str, strip) -> list[str]:
    words: list[str] = []
    for line in text.split("\n"):
        if PAGE.match(line.strip()):
            continue
        words += END_COMMA.sub(" ", strip(line)).split()
    return words


def verify_words(fixed: str, body: str) -> list[str]:
    """Trả về danh sách khác biệt. Rỗng nghĩa là câu chữ của sách không đổi."""
    clean = CITE.sub("", NOTE.sub("", body))
    a, b = _tokens(fixed, _strip_fixed), _tokens(clean, _strip_body)
    if a == b:
        return []
    ops = SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    return [f"{tag}: sách={' '.join(a[i1:i2])!r} bài={' '.join(b[j1:j2])!r} (từ {i1})"
            for tag, i1, i2, j1, j2 in ops if tag != "equal"]


def main() -> None:
    lesson, cmd = sys.argv[1], sys.argv[2]
    fixed = common.read_text(common.kho_path("lessons", lesson, "fixed.txt"))
    units = split_units(fixed)
    if cmd == "units":
        for i, u in enumerate(units, 1):
            print(f"{i}\t{u}")
        return
    with open(sys.argv[3], encoding="utf-8") as f:
        body = apply_layout(units, json.load(f))
    diffs = verify_words(fixed, body)
    if diffs:
        print("\n".join(diffs))
        sys.exit("Câu chữ bị đổi, chưa ghi body.md")
    common.write_text(common.kho_path("lessons", lesson, "body.md"), body + "\n")
    print("Khớp từng từ, đã ghi body.md")


if __name__ == "__main__":
    main()
