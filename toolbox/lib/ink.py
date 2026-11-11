"""Tìm vùng viết tay trên trang PDF: annotation Ink và nét vẽ vector tự do."""
import pymupdf

INK_ANNOT = 15
MIN_CURVES = 6
MERGE_GAP = 20


def _is_stroke(drawing: dict) -> bool:
    curves = sum(1 for item in drawing["items"] if item[0] == "c")
    return curves >= MIN_CURVES and curves > 4  # khung bo tròn chỉ có 4 đường cong


def _near(a: pymupdf.Rect, b: pymupdf.Rect) -> bool:
    return not (a.x1 + MERGE_GAP < b.x0 or b.x1 + MERGE_GAP < a.x0
                or a.y1 + MERGE_GAP < b.y0 or b.y1 + MERGE_GAP < a.y0)


def _merge(rects: list[pymupdf.Rect]) -> list[pymupdf.Rect]:
    regions: list[pymupdf.Rect] = []
    for r in rects:
        r = pymupdf.Rect(r)
        changed = True
        while changed:
            changed = False
            for other in regions:
                if _near(r, other):
                    r |= other
                    regions.remove(other)
                    changed = True
                    break
        regions.append(r)
    return sorted(regions, key=lambda x: (x.y0, x.x0))


def ink_regions(page: pymupdf.Page) -> list[pymupdf.Rect]:
    rects = [a.rect for a in page.annots() if a.type[0] == INK_ANNOT]
    rects += [d["rect"] for d in page.get_drawings() if _is_stroke(d)]
    return _merge(rects)
