"""A3. OCR sách scan, mỗi trang một file trong kho. Chạy lại chỉ làm trang còn thiếu.

Chạy thử: python toolbox/scripts/a3_ocr.py G1 --sample 12,130,131
Chạy đủ:  python toolbox/scripts/a3_ocr.py G1
Chép lại bằng model đọc ảnh tại máy (khóa "vlm" trong config.json), giữ bản Tesseract ở p####.tess.txt:
          python toolbox/scripts/a3_ocr.py G1 --engine vlm --pages 223-240
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402

DPI = 300
VLM_DPI = 160  # ảnh khoảng 1323x1872, đúng cỡ ảnh đã thử (97% khớp)


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
    tsv = _run_tesseract(png, ["-c", "tessedit_create_tsv=1"])
    words, confs = [], []
    for line in tsv.splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) == 12 and cols[11].strip() and float(cols[10]) >= 0:
            words.append(cols[11])
            confs.append(float(cols[10]))
    return " ".join(words), (sum(confs) / len(confs) if confs else 0.0)


def ocr_pages(pdf: str, code: str, pages: list[int] | None = None, engine=tesseract_page,
              redo: bool = False, dpi: int = DPI) -> int:
    """redo=True: chép đè trang đã có, bản cũ (Tesseract) cất ở p####.tess.txt.
    Trang đã có .tess.txt nghĩa là đã chép lại rồi, chạy lại sẽ bỏ qua."""
    done = 0
    with pymupdf.open(pdf) as d:
        for n in pages or range(1, d.page_count + 1):
            out, tess = common.page_file(code, n), common.page_file(code, n, "tess.txt")
            if os.path.exists(out) and (not redo or os.path.exists(tess)):
                continue
            png = d[n - 1].get_pixmap(dpi=dpi).tobytes("png")
            text = engine(png)
            if redo and os.path.exists(out):
                os.replace(out, tess)
            common.write_text(out, text)
            done += 1
    return done


def parse_pages(spec: str) -> list[int]:
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += range(int(a), int(b or a) + 1)
    return out


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
    ap.add_argument("--sample", "--pages", dest="sample", help="trang PDF, ví dụ 12,130 hoặc 223-240")
    ap.add_argument("--engine", choices=["tesseract", "vlm"], default="tesseract")
    a = ap.parse_args()
    if a.code == "scans":
        root = os.path.join(common.load_config()["source_root"], "Tài liệu")
        print(f"OCR xong {ocr_scans(common.read_csv(common.data_path('manifest.csv')), root)} trang mới")
        return
    row = next(r for r in common.read_csv(common.data_path("manifest.csv")) if r["code"] == a.code)
    pdf = os.path.join(common.load_config()["source_root"], "Tài liệu", row["path"])
    pages = parse_pages(a.sample) if a.sample else None
    if a.engine == "tesseract":
        print(f"OCR xong {ocr_pages(pdf, a.code, pages)} trang mới")
        return
    from lib import vlm
    with vlm.Server(common.load_config()["vlm"], log_path=common.kho_path(a.code, "vlm_server.log")) as srv:
        def engine(png):
            t = time.time()
            text = srv.ocr(png)
            print(f"  trang xong sau {time.time() - t:.0f}s", flush=True)
            return text
        n = ocr_pages(pdf, a.code, pages, engine=engine, redo=True, dpi=VLM_DPI)
    print(f"Chép lại bằng model đọc ảnh xong {n} trang, server đã tắt")


if __name__ == "__main__":
    main()
