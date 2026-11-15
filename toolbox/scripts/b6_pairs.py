"""B6. In từng dòng sách có chú thích cùng các chú thích của nó, để Claude đọc trọn một lượt và quyết mâu thuẫn.

Chạy: python toolbox/scripts/b6_pairs.py G2-B01
Dòng đánh dấu ⚑ là dòng mà bước rút thẻ (agy) đã báo mâu thuẫn. Claude vẫn đọc hết mọi dòng để bắt điểm bị sót.
"""
import json
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
    # Dòng agy báo mâu thuẫn mà bản nháp không giữ chú thích vẫn phải hiện ra cho Claude xét
    for line in sorted(set(by_line) | conflict_lines):
        flag = " ⚑" if line in conflict_lines else ""
        text = body[line - 1].strip() if 0 < line <= len(body) else "(ngoài thân bài)"
        out.append(f"L{line}{flag} {text}")
        out += [f"  → {note}" for note in by_line.get(line, ["(chưa có chú thích)"])]
    return "\n".join(out)


EVIDENCE_LINE = re.compile(r"^\[([SCNR]\d+):p(\d+)\]\s*(.*)")
UNIT = re.compile(r"\d+(?:[.,]\d+)?\s*(?:mg|g/|mL|ml|%|ngày|tuần|tháng|năm|giờ|mmHg|CFU|mmol|µg|UI|lần)", re.I)
STRONG = re.compile(r"liều|chỉ định|dự phòng|tiên lượng|biến chứng|lọc thận|lọc máu|khuyến cáo|guideline|AAP|KDIGO|"
                    r"ISPN|NICE|độ nhạy|độ đặc hiệu|tái phát|suy thận", re.I)


def _signal(line: str) -> int:
    return 2 * len(UNIT.findall(line)) + len(STRONG.findall(line))


def uncarded_pages(evidence: str, card_text: str, limit: int = 40) -> list[tuple[str, int, str]]:
    """Trang bằng chứng mà thẻ không nhắc tới, xếp theo tín hiệu lâm sàng; ý mất ở bước rút thẻ thì bước soạn nháp
    không bắt được (G1-B11 mất 4 chú thích kiểu này). Chỉ để Claude xem ở B6, không tự bắt agy làm lại."""
    from scripts.agy_run import _source_pages
    in_cards = _source_pages(card_text)
    pages: dict[str, list[str]] = {}
    for raw in evidence.split("\n"):
        m = EVIDENCE_LINE.match(raw.strip())
        if m:
            pages.setdefault(f"{m.group(1)}:p{m.group(2)}", []).append(m.group(3))
    ranked = []
    for page, lines in pages.items():
        score = sum(_signal(t) for t in lines)
        if page not in in_cards and score > 0:
            ranked.append((page, score, max(lines, key=_signal)[:200]))
    ranked.sort(key=lambda x: -x[1])
    return ranked[:limit]


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
    folder = common.kho_path("lessons", lesson)
    cards = "".join(common.read_text(os.path.join(folder, f)) for f in os.listdir(folder) if re.fullmatch(r"cards_\d+\.json", f))
    evidence_path = os.path.join(folder, "evidence.md")
    if cards and os.path.exists(evidence_path):
        # trang đã có trong bài (chú thích, Phần B) cũng coi như đã dùng
        used = cards + json.dumps(notes, ensure_ascii=False) + json.dumps(
            common.read_json(os.path.join(folder, "extra.json"), {}), ensure_ascii=False)
        top = uncarded_pages(common.read_text(evidence_path), used)
        print(f"\n## Trang bằng chứng chưa có trong thẻ ({len(top)} trang nhiều tín hiệu lâm sàng nhất)")
        print("Ý đáng giữ thì thêm chú thích vào notes.json (dòng sách tương ứng).")
        for page, score, line in top:
            print(f"- [{page}] ({score}) {line}")


if __name__ == "__main__":
    main()
