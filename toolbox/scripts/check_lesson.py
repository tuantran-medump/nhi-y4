"""Kiểm tra một bài theo playbook. In JSON các lỗi, rỗng nghĩa là đạt.

Chạy: python toolbox/scripts/check_lesson.py G1-B08
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402
from scripts.b2b_layout import verify_words  # noqa: E402

CITE = re.compile(r"\[([GSCNRE]\d*):p[^\]]+\]")
FACT = re.compile(r"\d+(?:[.,]\d+)?\s*(?:mg|mcg|µg|g/|ml|mL|UI|IU|mmol|mEq|%|ngày|giờ|lần)", re.I)
SECTIONS = ["approach", "experience", "exam", "conflicts"]
BLOCK = re.compile(r"<<block:([\w-]+)>>\n(.*?)<<endblock>>", re.S)
OPEN = re.compile(r"^<<block:([\w-]+)>>\s*$", re.M)
NUM = re.compile(r"\d+(?:[.,]\d+)?")


SUBSCRIPT = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹", "01234567890123456789")


def _numbers(text: str) -> set[str]:
    """Số trong chữ; chỉ số dưới/trên (B₁₂, m²) tính như số thường."""
    return {n.replace(",", ".") for n in NUM.findall(text.translate(SUBSCRIPT))}


def check(lesson: str) -> list[dict]:
    info = next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)
    body = common.read_text(common.kho_path("lessons", lesson, "body.md"))
    extra = common.read_json(common.kho_path("lessons", lesson, "extra.json"), {})
    issues: list[dict] = []

    def add(rule: str, line: int, msg: str) -> None:
        issues.append({"rule": rule, "line": line, "msg": msg})

    if not str(extra.get("summary", "")).strip():
        add("missing_summary", 0, "Thiếu Tóm tắt 1 trang")
    for key in SECTIONS:
        if key not in extra:
            add("missing_section", 0, f"extra.json thiếu khóa {key}, nếu không có nội dung ghi chuỗi rỗng")
    known = {r["code"] for r in common.read_csv(common.data_path("manifest.csv"))}
    known |= {r["code"] for r in common.read_csv(common.data_path("external_sources.csv"))}
    all_text = body + "\n" + "\n".join(str(v) for v in extra.values())
    for code in sorted({m.group(1) for m in CITE.finditer(all_text)} - known):
        add("unknown_source", 0, f"Mã nguồn không có trong danh mục: {code}")
    filled = dict(BLOCK.findall(body))
    for name in OPEN.findall(body):
        if name not in filled:
            add("unfilled_block", 0, f"Chưa gõ lại khối {name}")
    in_block = False
    for n, line in enumerate(body.split("\n"), 1):
        if OPEN.match(line):
            in_block = True
        if line.strip() == "<<endblock>>":
            in_block = False
        if in_block:
            continue
        if FACT.search(line) and not CITE.search(line) and "Chưa thấy có nguồn" not in line:
            add("uncited_fact", n, line.strip())
        if "[?" in line:
            add("unresolved", n, line.strip())
    if info.get("book"):
        fixed = common.read_text(common.kho_path("lessons", lesson, "fixed.txt"))
        for d in verify_words(fixed, body):
            add("body_changed", 0, d)
        for name, source in BLOCK.findall(fixed):
            lost = _numbers(source) - _numbers(filled.get(name, ""))
            if name in filled and lost and not name.endswith("f"):  # khối tận cùng f là hình
                add("block_number", 0, f"Khối {name} thiếu số so với sách: {sorted(lost)}")
    return issues


if __name__ == "__main__":
    found = check(sys.argv[1])
    print(json.dumps(found, ensure_ascii=False, indent=1))
    sys.exit(1 if found else 0)
