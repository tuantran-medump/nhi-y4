"""A3. OCR sách scan, mỗi trang một file trong kho. Chạy lại chỉ làm trang còn thiếu.

Chạy thử: python toolbox/scripts/a3_ocr.py G1 --sample 12,130,131
Chạy đủ:  python toolbox/scripts/a3_ocr.py G1
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402

DPI = 300


def _run_tesseract(png: bytes, extra: list[str]) -> str:
    cfg = common.load_config()
    exe = cfg["tesseract"]
    model = ["--tessdata-dir", cfg["tessdata_dir"]] if cfg.get("tessdata_dir") else []
    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, "p.png")
        with open(src, "wb") as f:
            f.write(png)
        res = subprocess.run([exe, src, "stdout", *model, "-l", cfg.get("ocr_lang", "vie+eng"), "--psm", "4", *extra],
                             capture_output=True, check=True)
    return res.stdout.decode("utf-8")


def tesseract_page(png: bytes) -> str:
    return _run_tesseract(png, [])


def tesseract_conf(png: bytes) -> tuple[str, float]:
    """Trả về chữ và độ tin cậy trung bình (0-100) của trang."""
    tsv = _run_tesseract(png, ["tsv"])
    words, confs = [], []
    for line in tsv.splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) == 12 and cols[11].strip() and float(cols[10]) >= 0:
            words.append(cols[11])
            confs.append(float(cols[10]))
    return " ".join(words), (sum(confs) / len(confs) if confs else 0.0)


def ocr_pages(pdf: str, code: str, pages: list[int] | None = None, engine=tesseract_page) -> int:
    done = 0
    with pymupdf.open(pdf) as d:
        for n in pages or range(1, d.page_count + 1):
            out = common.page_file(code, n)
            if os.path.exists(out):
                continue
            png = d[n - 1].get_pixmap(dpi=DPI).tobytes("png")
            common.write_text(out, engine(png))
            done += 1
    return done


def ocr_scans(rows: list[dict], root: str, engine=tesseract_conf, min_conf: float = 80) -> int:
    """OCR các trang chưa có chữ của nguồn tham khảo, để A6 gán bài được theo nội dung.

    Trang tin cậy thấp lưu riêng .lowocr.txt: chỉ dùng để tìm kiếm, không dùng làm nội dung.
    """
    done = 0
    for r in rows:
        if r["status"] != "primary" or r["code"] in ("G1", "G2") or r["kind"] not in ("image", "mixed"):
            continue
        with pymupdf.open(os.path.join(root, r["path"])) as d:
            for n in range(1, d.page_count + 1):
                good, low = common.page_file(r["code"], n), common.page_file(r["code"], n, "lowocr.txt")
                if os.path.exists(good) or os.path.exists(low):
                    continue
                text, conf = engine(d[n - 1].get_pixmap(dpi=DPI).tobytes("png"))
                common.write_text(good if conf >= min_conf else low, text)
                done += 1
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("code", help="G1, G2 hoặc scans (mọi trang scan của nguồn tham khảo)")
    ap.add_argument("--sample", help="danh sách trang PDF, ví dụ 12,130")
    a = ap.parse_args()
    if a.code == "scans":
        root = os.path.join(common.load_config()["source_root"], "Tài liệu")
        print(f"OCR xong {ocr_scans(common.read_csv(common.data_path('manifest.csv')), root)} trang mới")
        return
    row = next(r for r in common.read_csv(common.data_path("manifest.csv")) if r["code"] == a.code)
    pdf = os.path.join(common.load_config()["source_root"], "Tài liệu", row["path"])
    pages = [int(x) for x in a.sample.split(",")] if a.sample else None
    print(f"OCR xong {ocr_pages(pdf, a.code, pages)} trang mới")


if __name__ == "__main__":
    main()
