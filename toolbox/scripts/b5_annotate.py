"""B5. Gắn mã trang sách tự động và chèn chú thích ngoặc đơn vào thân bài.

Chạy:
  python toolbox/scripts/b5_annotate.py G1-B08 number        (in thân bài có số dòng, ghi body_numbered.txt)
  python toolbox/scripts/b5_annotate.py G1-B08 apply notes.json
notes.json: [{"line": 12, "note": "(Slide 2024: rút còn 3 ngày [S12:p4])"}]
Luôn dựng từ body.base.md nên chạy lại không bị gắn trùng.
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402

PAGE = re.compile(r"^<<p(\d+)>>$")
FACT = re.compile(r"\d|chỉ định|tiêu chuẩn|chống chỉ định|liều", re.I)
NOTE_OK = re.compile(r"^\([^()]*\[[SCNRE]\d+:p[^\]]*\][^()]*\)$")
STAR = "⭐"
RESOLVE_OK = re.compile(r"^Kết luận[^:\[]{0,80}:\s*\S")
SOURCE = re.compile(r"\[[SCNRE]\d+:p[^\]]*\]")
UNCONFIRMED = "Chưa thấy có nguồn hiệp hội/guideline xác nhận"


def _insert(line: str, text: str) -> str:
    stripped = line.rstrip()
    if stripped.endswith((".", ";", ":", ",")):
        return stripped[:-1] + " " + text + stripped[-1]
    return stripped + " " + text


def cite_book(body: str, book: str) -> str:
    out, page, in_block = [], None, False
    for line in body.split("\n"):
        s = line.strip()
        m = PAGE.match(s)
        if m:
            page = m.group(1)
        elif s.startswith("<<block:"):
            in_block = True
        elif s == "<<endblock>>":
            in_block = False
        elif s and not in_block and page and not s.startswith("#") and FACT.search(s):
            line = _insert(line, f"[{book}:p{page}]")
        out.append(line)
    return "\n".join(out)


def apply_notes(body: str, notes: list[dict]) -> str:
    lines = body.split("\n")
    for n in notes:
        target = lines[n["line"] - 1].strip()
        if not NOTE_OK.match(n["note"]):
            raise ValueError(f"Dòng {n['line']}: chú thích phải trong ngoặc đơn và có mã nguồn tham khảo: {n['note']}")
        if not target or target.startswith("<<") or target.startswith("|"):
            raise ValueError(f"Dòng {n['line']} không chèn chú thích được")
        resolve = n.get("resolve")
        if resolve is not None and not (RESOLVE_OK.match(resolve) and (SOURCE.search(resolve) or UNCONFIRMED in resolve)):
            raise ValueError(f"Dòng {n['line']}: kết luận mâu thuẫn phải mở đầu 'Kết luận theo ...:' và có mã nguồn: {resolve}")
    stars: dict[int, list[str]] = {}
    for n in sorted(notes, key=lambda x: x["line"]):
        i = n["line"] - 1
        if n.get("resolve"):  # chú thích mâu thuẫn: xuống dòng ⭐ thụt vào dưới ý, kèm kết luận
            stars.setdefault(i, []).extend([n["note"], n["resolve"]])
        else:
            lines[i] = _insert(lines[i], n["note"])
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        pad = " " * (len(line) - len(line.lstrip()) + 4)
        out += [f"{pad}{STAR} {text}" for text in stars.get(i, [])]
    return "\n".join(out)


def _paths(lesson: str) -> tuple[str, str]:
    return common.kho_path("lessons", lesson, "body.md"), common.kho_path("lessons", lesson, "body.base.md")


def _cited(lesson: str) -> str:
    body, base = _paths(lesson)
    if not os.path.exists(base):
        shutil.copy(body, base)
    book = next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)["book"]
    return cite_book(common.read_text(base), book) if book else common.read_text(base)


def main() -> None:
    lesson, cmd = sys.argv[1], sys.argv[2]
    text = _cited(lesson)
    if cmd == "number":
        numbered = "".join(f"{i}\t{ln}\n" for i, ln in enumerate(text.split("\n"), 1))
        common.write_text(common.kho_path("lessons", lesson, "body_numbered.txt"), numbered)
        print(len(text.split("\n")), "dòng")
        return
    with open(sys.argv[3], encoding="utf-8") as f:
        text = apply_notes(text, json.load(f))
    common.write_text(_paths(lesson)[0], text)
    print("Đã ghi body.md")


if __name__ == "__main__":
    main()
