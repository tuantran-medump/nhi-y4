"""B5. Gom bằng chứng cho một bài vào một file gọn để model mạnh đọc.

File đúng chủ đề (tên file có từ khóa của bài) giữ mọi câu khác sách.
File tổng hợp chỉ giữ câu có nhắc tới bài và câu liền kề.
Câu khác sách ở mức gần giống luôn được giữ. Câu trùng giữa các nguồn gộp một dòng, ghi đủ mã.

Chạy: python toolbox/scripts/b5_evidence.py G1-B08
Kết quả: kho/lessons/<lesson>/evidence.md
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402
from scripts.a6_assign import _pattern  # noqa: E402

MIN_WORDS = 3


def _key(text: str) -> str:
    return " ".join(w.strip(".,;:()") for w in common.nfc(text).lower().split())


def _noise(text: str) -> bool:
    words = text.split()
    return len(words) < MIN_WORDS or re.fullmatch(r"[\W\d_]*(?:slide|trang|page)?[\W\d_]*", text.lower()) is not None


def _read(lesson: str, code: str) -> list[dict]:
    path = common.kho_path("lessons", lesson, f"novel_{code}.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(line) for line in common.read_text(path).splitlines() if line.strip()]


def _keep(items: list[dict], pat, whole: bool) -> list[dict]:
    if whole:
        return items
    near: set[int] = set()
    for i, it in enumerate(items):
        if pat.search(common.nfc(it["text"])):
            near.update((i - 1, i, i + 1))
    return [it for i, it in enumerate(items) if i in near or it["reason"] == "changed_fact"]


def build(lesson: str) -> str:
    keyword = next(k for k in common.read_csv(common.data_path("topic_keywords.csv")) if k["lesson"] == lesson)
    pat = _pattern(keyword["keywords"])
    names = {r["code"]: common.nfc(os.path.basename(r["path"])) for r in common.read_csv(common.data_path("manifest.csv"))}
    seen: dict[str, dict] = {}
    inks: list[str] = []
    for row in common.read_csv(common.data_path("lesson_sources.csv")):
        if row["lesson"] != lesson:
            continue
        code = row["code"]
        whole = bool(pat.search(names.get(code, "")))
        for it in _keep(_read(lesson, code), pat, whole):
            if _noise(it["text"]):
                continue
            entry = seen.setdefault(_key(it["text"]), {"text": it["text"], "cites": [], "changed": False})
            cite = f"[{code}:p{it['page']}]"
            if cite not in entry["cites"]:
                entry["cites"].append(cite)
            entry["changed"] = entry["changed"] or it["reason"] == "changed_fact"
        for f in sorted(glob.glob(common.kho_path(code, "p[0-9][0-9][0-9][0-9].ink.txt"))):
            text = common.read_text(f).strip()
            if text:
                inks.append(f"(viết tay) [{code}:p{int(os.path.basename(f)[1:5])}] {text}")
    lines = [("!KHÁC SÁCH " if e["changed"] else "") + "".join(e["cites"]) + " " + e["text"] for e in seen.values()]
    out = "\n".join(lines + inks) + "\n"
    common.write_text(common.kho_path("lessons", lesson, "evidence.md"), out)
    return out


if __name__ == "__main__":
    text = build(sys.argv[1])
    print(len(text.splitlines()), "dòng,", len(text), "ký tự")
