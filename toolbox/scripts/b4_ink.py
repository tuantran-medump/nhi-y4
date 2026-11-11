"""B4. Chuẩn bị ảnh cho agent đọc viết tay và trang scan, rồi gom kết quả vào kho.

Chạy:
  python toolbox/scripts/b4_ink.py G1-B08 tasks [S059,N029]   (tạo kho/ink/<lesson>/tasks.json và ảnh ghép, có thể chỉ định mã nguồn)
  python toolbox/scripts/b4_ink.py G1-B08 merge    (gom results/<id>.json vào kho)
Mỗi vùng chỉ đọc một lần: kết quả lưu trong data/ink_cache.json theo hash ảnh.
"""
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common, ink  # noqa: E402

MAX_ITEMS = 12
REGION_DPI = 150
SCAN_DPI = 300
MIN_CONF = 80
PAD = 6
COLS, CELL_W, CELL_H = 3, 300, 200
SHEET_DPI = 130
pymupdf.TOOLS.mupdf_display_errors(False)


def _cache() -> dict:
    return common.read_json(common.data_path("ink_cache.json"), {})


def _tasks_file(lesson: str) -> str:
    return common.kho_path("ink", lesson, "tasks.json")


def _sheet(pngs: list[bytes], out: str) -> None:
    rows = (len(pngs) + COLS - 1) // COLS
    d = pymupdf.open()
    page = d.new_page(width=COLS * CELL_W, height=rows * CELL_H)
    for i, png in enumerate(pngs):
        x, y = (i % COLS) * CELL_W, (i // COLS) * CELL_H
        page.insert_image(pymupdf.Rect(x + 4, y + 18, x + CELL_W - 4, y + CELL_H - 4), stream=png)
        page.insert_text((x + 4, y + 14), f"[{i + 1}]", fontsize=12, color=(1, 0, 0))
        page.draw_rect(pymupdf.Rect(x, y, x + CELL_W, y + CELL_H), color=(0.7, 0.7, 0.7))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    page.get_pixmap(dpi=SHEET_DPI).save(out)
    d.close()


def _select(rows: list[dict], lesson: str, only: set[str] | None) -> list[dict]:
    return [r for r in rows if r["lesson"] == lesson and (only is None or r["code"] in only)]


def make_tasks(lesson: str, root: str | None = None, conf_engine=None, only: set[str] | None = None) -> list[dict]:
    if root is None:
        root = os.path.join(common.load_config()["source_root"], "Tài liệu")
    if conf_engine is None:
        from scripts.a3_ocr import tesseract_conf as conf_engine
    if os.path.exists(_tasks_file(lesson)):
        merge(lesson)  # giữ các kết quả đã đọc trước khi đánh số lại task
    shutil.rmtree(common.kho_path("ink", lesson, "results"), ignore_errors=True)
    os.makedirs(common.kho_path("ink", lesson, "results"), exist_ok=True)
    manifest = {r["code"]: r for r in common.read_csv(common.data_path("manifest.csv"))}
    cache = _cache()
    regions, pages, cached = [], [], []
    for row in _select(common.read_csv(common.data_path("lesson_sources.csv")), lesson, only):
        m = manifest[row["code"]]
        if m["kind"] == "needs_manual":
            continue
        path = os.path.join(root, m["path"])
        if os.path.splitext(path)[1].lower() not in (".pdf", ".png", ".jpg", ".jpeg"):
            continue
        ink_pages = {int(p) for p in row["ink_pages"].split(";") if p}
        wanted = {int(p) for p in row["pages"].split(";") if p}
        with pymupdf.open(path) as d:
            for n in sorted(wanted):
                if n > d.page_count:
                    continue
                page = d[n - 1]
                if n in ink_pages:
                    for rect in ink.ink_regions(page):
                        clip = (rect + (-PAD, -PAD, PAD, PAD)) & page.rect
                        if clip.is_empty or clip.width < 2 or clip.height < 2:
                            continue  # nét nằm ngoài trang
                        png = page.get_pixmap(dpi=REGION_DPI, clip=clip).tobytes("png")
                        item = {"code": row["code"], "page": n, "sha": hashlib.sha256(png).hexdigest()}
                        (cached if item["sha"] in cache else regions).append((item, png))
                if m["kind"] in ("image", "mixed") and not os.path.exists(common.page_file(row["code"], n)):
                    png = page.get_pixmap(dpi=SCAN_DPI).tobytes("png")
                    item = {"code": row["code"], "page": n, "sha": hashlib.sha256(png).hexdigest()}
                    if item["sha"] in cache:
                        cached.append((item, png))
                        continue
                    low = os.path.exists(common.page_file(row["code"], n, "lowocr.txt"))
                    text, conf = ("", 0.0) if low else conf_engine(png)
                    if conf >= MIN_CONF:
                        common.write_text(common.page_file(row["code"], n), text)
                    else:
                        small = page.get_pixmap(dpi=REGION_DPI).tobytes("png")
                        pages.append((item, small))
    tasks = []
    for start in range(0, len(regions), MAX_ITEMS):
        chunk = regions[start:start + MAX_ITEMS]
        tid = f"t{len(tasks) + 1:03d}"
        _sheet([png for _, png in chunk], common.kho_path("ink", lesson, f"{tid}.png"))
        tasks.append({"id": tid, "kind": "ink", "image": f"{tid}.png",
                      "items": {str(i + 1): it for i, (it, _) in enumerate(chunk)}})
    for item, png in pages:
        tid = f"t{len(tasks) + 1:03d}"
        with open(_ensure(common.kho_path("ink", lesson, f"{tid}.png")), "wb") as f:
            f.write(png)
        tasks.append({"id": tid, "kind": "page", "image": f"{tid}.png", "items": {"1": item}})
    common.write_json(_tasks_file(lesson), {"tasks": tasks, "cached": [it for it, _ in cached]})
    return tasks


def _ensure(path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def merge(lesson: str) -> dict:
    state = common.read_json(_tasks_file(lesson), {"tasks": [], "cached": []})
    cache = _cache()
    missing = []
    items = list(state["cached"])
    for t in state["tasks"]:
        result = common.read_json(common.kho_path("ink", lesson, "results", t["id"] + ".json"), {})
        for label, item in t["items"].items():
            if label in result:
                cache[item["sha"]] = result[label]
                items.append(item)
            elif item["sha"] in cache:
                items.append(item)
            else:
                missing.append(f"{t['id']}:{label}")
    common.write_json(common.data_path("ink_cache.json"), cache)
    per_page: dict[tuple, list[str]] = {}
    uncertain = 0
    for item in items:
        text = cache[item["sha"]]
        uncertain += text.count("[?")
        if text.strip():
            per_page.setdefault((item["code"], item["page"]), []).append(text)
    for (code, page), texts in per_page.items():
        common.write_text(common.page_file(code, page, "ink.txt"), "\n".join(texts))
    return {"missing": missing, "uncertain": uncertain}


def main() -> None:
    lesson, cmd = sys.argv[1], sys.argv[2]
    if cmd == "tasks":
        only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
        tasks = make_tasks(lesson, only=only)
        print(f"{len(tasks)} ảnh cần đọc, {sum(len(t['items']) for t in tasks)} vùng")
    else:
        print(merge(lesson))


if __name__ == "__main__":
    main()
