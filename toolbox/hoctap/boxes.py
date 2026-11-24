from dataclasses import dataclass
import re


_BOXES = frozenset({
    "khai-niem", "dich-te-phan-loai", "benh-hoc", "lam-sang",
    "cls-chi-dinh", "dieu-tri", "canh-bao-bien-chung", "theo-doi", "tu-kiem-tra",
})
LABELS = {
    "khai-niem": "khái niệm", "dich-te-phan-loai": "dịch tễ và phân loại", "benh-hoc": "bệnh học",
    "lam-sang": "lâm sàng", "cls-chi-dinh": "cận lâm sàng và chỉ định", "dieu-tri": "điều trị",
    "canh-bao-bien-chung": "cảnh báo và biến chứng", "theo-doi": "theo dõi", "tu-kiem-tra": "tự kiểm tra",
}
assert set(LABELS) == _BOXES
_HEADING = re.compile(r"^(#{2,3})\s+(.*)$")
_MARKER = re.compile(r"^\{hop:\s*(.*?)\s*\}$")


@dataclass
class Section:
    title: str
    level: int
    box: str
    lines: list[str]
    line_no: int


def parse_sections(md: str) -> list[Section]:
    source = md.splitlines()
    sections: list[Section] = []
    title, level, box, start, lines = "", 0, "khai-niem", 0, []
    has_heading = False

    def finish() -> None:
        if has_heading or lines:
            sections.append(Section(title, level, box, lines.copy(), start or 1))

    for number, line in enumerate(source, 1):
        heading = _HEADING.match(line)
        if heading:
            finish()
            title, level, box, start, lines = heading.group(2), len(heading.group(1)), "khai-niem", number, []
            has_heading = True
            continue
        marker = _MARKER.match(line)
        if marker:
            if not has_heading or any(item.strip() for item in lines):
                raise ValueError(f"Dòng {number}: dấu hộp nằm ngoài vị trí ngay dưới tiêu đề")
            name = marker.group(1)
            if name not in _BOXES:
                raise ValueError(f"Dòng {number}: mã hộp không hợp lệ '{name}'")
            box = name
            continue
        if line.startswith("{hop:"):
            raise ValueError(f"Dòng {number}: dấu hộp không hợp lệ")
        lines.append(line)
    finish()
    return sections
