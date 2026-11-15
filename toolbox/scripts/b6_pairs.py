"""B6. In từng dòng sách có chú thích cùng các chú thích của nó, để Claude đọc trọn một lượt và quyết mâu thuẫn.

Chạy: python toolbox/scripts/b6_pairs.py G2-B01
Dòng đánh dấu ⚑ là dòng mà bước rút thẻ (agy) đã báo mâu thuẫn. Claude vẫn đọc hết mọi dòng để bắt điểm bị sót.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402
from scripts.agy_run import body_lines  # noqa: E402


def pairs(body_numbered: str, notes: list[dict], conflict_lines: set[int]) -> str:
    body = body_lines(body_numbered)
    by_line: dict[int, list[str]] = {}
    for n in notes:
        by_line.setdefault(n["line"], []).append(n["note"])
    out = []
    for line in sorted(by_line):
        flag = " ⚑" if line in conflict_lines else ""
        text = body[line - 1].strip() if 0 < line <= len(body) else "(ngoài thân bài)"
        out.append(f"L{line}{flag} {text}")
        out += [f"  → {note}" for note in by_line[line]]
    return "\n".join(out)


def _conflict_lines(lesson: str) -> set[int]:
    folder = common.kho_path("lessons", lesson)
    lines: set[int] = set()
    for f in os.listdir(folder):
        if re.fullmatch(r"cards_\d+\.json", f):
            for c in common.read_json(os.path.join(folder, f), {}).get("conflicts", []):
                if isinstance(c, dict) and isinstance(c.get("line"), int):
                    lines.add(c["line"])
    return lines


def main() -> None:
    lesson = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8")
    body = common.read_text(common.kho_path("lessons", lesson, "body_numbered.txt"))
    notes = common.read_json(common.kho_path("lessons", lesson, "notes.json"), [])
    print(pairs(body, notes, _conflict_lines(lesson)))


if __name__ == "__main__":
    main()
