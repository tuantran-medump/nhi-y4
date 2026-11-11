"""Lọc câu mới: bỏ câu nguồn tham khảo đã có trong sách, giữ phần khác biệt.

Câu chỉ bị bỏ khi giống hệt câu sách từng từ. Câu gần giống được giữ và gắn changed_fact,
vì khác một từ cũng có thể là khác thuốc, khác đường dùng, khác liều.

Chạy: python toolbox/scripts/b3_novel.py G1-B08
Kết quả: kho/lessons/<lesson>/novel_<code>.jsonl
"""
import json
import os
import sys
from collections import Counter
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402
from scripts.b2b_layout import split_units  # noqa: E402

SIMILAR = 0.9
TOP_CANDIDATES = 5

def _words(sentence: str) -> list[str]:
    return [w for w in (t.strip(".,;:()[]\"'") for t in common.nfc(sentence).lower().split()) if w]


def novel_sentences(book_text: str, source_pages: dict[int, str]) -> list[dict]:
    book = [_words(s) for s in split_units(book_text)]
    index: dict[str, list[int]] = {}
    for i, words in enumerate(book):
        for w in set(words):
            index.setdefault(w, []).append(i)
    result = []
    for page in sorted(source_pages):
        for sentence in split_units(source_pages[page]):
            words = _words(sentence)
            if not words:
                continue
            votes = Counter(i for w in set(words) for i in index.get(w, []))
            best, best_ratio = None, 0.0
            for i, _ in votes.most_common(TOP_CANDIDATES):
                ratio = SequenceMatcher(None, words, book[i], autojunk=False).ratio()
                if ratio > best_ratio:
                    best, best_ratio = i, ratio
            if best is not None and words == book[best]:
                continue
            reason = "changed_fact" if best_ratio >= SIMILAR else "new"
            result.append({"page": page, "text": sentence, "reason": reason})
    return result


def main() -> None:
    lesson = sys.argv[1]
    book_text = common.read_text(common.kho_path("lessons", lesson, "fixed.txt"))
    for row in common.read_csv(common.data_path("lesson_sources.csv")):
        if row["lesson"] != lesson:
            continue
        out = common.kho_path("lessons", lesson, f"novel_{row['code']}.jsonl")
        if os.path.exists(out):
            continue
        pages = {}
        for p in row["pages"].split(";"):
            f = common.page_file(row["code"], int(p))
            if os.path.exists(f):
                pages[int(p)] = common.read_text(f)
        found = novel_sentences(book_text, pages)
        common.write_text(out, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in found))
        print(row["code"], len(found), "câu mới")


if __name__ == "__main__":
    main()
