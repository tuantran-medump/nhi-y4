"""A4. Bản đồ trang in với trang PDF, ranh giới bài, trang thiếu.

Chạy: python toolbox/scripts/a4_pagemap.py G1
Kết quả: data/pagemap_G1.csv, data/gaps.csv
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402

FIELDS = ["pdf_page", "printed_page", "lesson", "confidence"]
GAP_FIELDS = ["book", "printed_page", "lesson", "note"]
MAX_JUMP = 15


def parse_printed(text: str) -> int | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines[:3]:
        m = re.match(r"^(\d{1,3})\D{0,6}NHI\s*KHOA", ln, re.I)
        if m:
            return int(m.group(1))
        if re.match(r"^B[àa]i\s*\d", ln, re.I):
            m = re.search(r"(\d{1,3})\s*$", ln)
            if m and not re.match(r"^B[àa]i\s*\d{1,3}\s*$", ln, re.I):
                return int(m.group(1))
    if lines and re.fullmatch(r"\d{1,3}", lines[-1]):
        return int(lines[-1])
    return None


def _accepted(parsed: list[tuple[int, int]]) -> set[int]:
    """Giữ dãy dài nhất có số trang tăng ít nhất bằng số trang PDF, loại số đọc nhầm."""
    n = len(parsed)
    best = [1] * n
    prev = [-1] * n
    for j in range(n):
        for i in range(j):
            dp, dv = parsed[j][0] - parsed[i][0], parsed[j][1] - parsed[i][1]
            if dp <= dv <= dp + MAX_JUMP and best[i] + 1 > best[j]:
                best[j], prev[j] = best[i] + 1, i
    if not n:
        return set()
    k = max(range(n), key=lambda x: best[x])
    keep = set()
    while k != -1:
        keep.add(parsed[k][0])
        k = prev[k]
    return keep


def _lesson_of(printed: int | None, starts: list[tuple[int, str]]) -> str:
    if printed is None:
        return ""
    cur = ""
    for s, name in starts:
        if printed >= s:
            cur = name
    return cur


def build_map(code: str, lessons: list[dict]) -> tuple[list[dict], list[dict]]:
    files = sorted(glob.glob(common.kho_path(code, "p[0-9][0-9][0-9][0-9].txt")))
    numbers = {int(os.path.basename(f)[1:5]): parse_printed(common.read_text(f)) for f in files}
    parsed = [(p, v) for p, v in sorted(numbers.items()) if v is not None]
    keep = _accepted(parsed)
    good = {p: v for p, v in parsed if p in keep}
    starts = sorted((int(r["start_printed"]), r["lesson"]) for r in lessons if r["book"] == code)
    rows, gaps = [], []
    anchors = sorted(good)
    for p in sorted(numbers):
        if p in good:
            value, conf = good[p], "ok"
        else:
            before = max((a for a in anchors if a < p), default=None)
            after = min((a for a in anchors if a > p), default=None)
            value = None
            if before is not None and after is not None and good[after] - good[before] == after - before:
                value = good[before] + (p - before)
            conf = "uncertain"
        rows.append({"pdf_page": p, "printed_page": "" if value is None else value,
                     "lesson": _lesson_of(value, starts), "confidence": conf})
    for r_i, row in enumerate(rows):  # trang chưa rõ số nằm giữa bài thì theo trang trước
        if row["lesson"] == "" and r_i and anchors and anchors[0] < row["pdf_page"]:
            row["lesson"] = rows[r_i - 1]["lesson"]
    for a, b in zip(anchors, anchors[1:]):
        extra = (good[b] - good[a]) - (b - a)
        if extra <= 0:
            continue
        exact = b - a == 1
        for v in range(good[a] + 1, good[b]):
            gaps.append({"book": code, "printed_page": v, "lesson": _lesson_of(v, starts),
                         "note": "" if exact else f"thiếu {extra} trang trong khoảng này"})
    return rows, gaps


def main() -> None:
    code = sys.argv[1]
    lessons = common.read_csv(common.data_path("lessons.csv"))
    rows, gaps = build_map(code, lessons)
    common.write_csv(common.data_path(f"pagemap_{code}.csv"), rows, FIELDS)
    path = common.data_path("gaps.csv")
    others = [g for g in common.read_csv(path) if g["book"] != code]
    common.write_csv(path, others + gaps, GAP_FIELDS)
    unsure = sum(1 for r in rows if r["confidence"] != "ok")
    print(f"{code}: {len(rows)} trang, {unsure} chưa chắc số trang, {len(gaps)} trang thiếu")


if __name__ == "__main__":
    main()
