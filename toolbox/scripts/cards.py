"""Thẻ bằng chứng: đọc một nguồn xong ghi ý ngắn, các bài sau nạp thẻ thay vì đọc lại.

Lưu ở data/cards/<code>.json.
Chạy: python toolbox/scripts/cards.py G1-B08   (in thẻ của bài)
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402


def _path(code: str) -> str:
    return common.data_path("cards", f"{code}.json")


def for_source(code: str) -> list[dict]:
    return common.read_json(_path(code), [])


def add(code: str, lesson: str, idea: str, page: int) -> None:
    items = for_source(code)
    card = next((c for c in items if c["idea"] == idea and c["page"] == page), None)
    if card is None:
        card = {"code": code, "idea": idea, "page": page, "lessons": []}
        items.append(card)
    if lesson not in card["lessons"]:
        card["lessons"].append(lesson)
    common.write_json(_path(code), items)


def for_lesson(lesson: str) -> list[dict]:
    found = []
    for f in sorted(glob.glob(common.data_path("cards", "*.json"))):
        found += [c for c in common.read_json(f, []) if lesson in c["lessons"]]
    return found


if __name__ == "__main__":
    for c in for_lesson(sys.argv[1]):
        print(f"[{c['code']}:p{c['page']}] {c['idea']}")
