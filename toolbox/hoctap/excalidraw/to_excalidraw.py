"""Chuyển lưu đồ Mermaid (out/flow/*.mmd) sang file .excalidraw.

QUY TẮC 1: các nhánh cùng loại quan hệ của một nút gộp thành một nút loại (nút -> loại -> nội dung).
QUY TẮC 2: bản Excalidraw KHÔNG có chú thích nguồn (mã [G1:p203]...). Mã nguồn chỉ nằm ở bản Mermaid/HTML/PDF để kiểm.
Dùng: python excalidraw/to_excalidraw.py <file.mmd> <ra.excalidraw>
Cần out/excali/bundle.js (build bằng esbuild từ excalidraw/entry.js, xem README) và Edge.
"""
import json
import re
import subprocess
import sys
import tempfile
from html import unescape
from pathlib import Path

import os


def find_edge():
    for c in (os.environ.get('EDGE_PATH'), r'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', r'C:/Program Files/Microsoft/Edge/Application/msedge.exe'):
        if c and Path(c).is_file():
            return c
    raise SystemExit('Không thấy Edge (đặt EDGE_PATH)')

SRC_RE = re.compile(r"\s*\[[A-Z]+\d*:p\d+(?:-\d+)?(?:,p\d+(?:-\d+)?)*\]")


def strip_sources(mermaid: str) -> str:
    return SRC_RE.sub("", mermaid)


EDGE_RE = re.compile(r'^\s*(n\d+) -->\|"([^"]*)"\| (n\d+)\s*$')


def group_branches(mermaid: str) -> str:
    """Gộp các nhánh cùng loại quan hệ của một nút: nút -> nút loại (vd "Biểu hiện") -> từng nội dung.
    Chỉ gộp khi có từ 2 nhánh cùng loại trở lên."""
    lines = mermaid.splitlines()
    parsed = [(i, EDGE_RE.match(l)) for i, l in enumerate(lines)]
    groups = {}
    for i, m in parsed:
        if m:
            groups.setdefault((m.group(1), m.group(2).strip()), []).append(i)
    out, drop, extra, gid = list(lines), set(), [], 0
    for (src, label), idxs in groups.items():
        if len(idxs) < 2 or not label:
            continue
        gid += 1
        g = f"g{gid}"
        extra.append(f'  {g}(["{label[:1].upper() + label[1:]}"])')
        extra.append(f"  {src} --> {g}")
        for i in idxs:
            drop.add(i)
            extra.append(f"  {g} --> {EDGE_RE.match(lines[i]).group(3)}")
    return "\n".join([l for i, l in enumerate(out) if i not in drop] + extra) + "\n"


def main():
    mmd, out = Path(sys.argv[1]), Path(sys.argv[2])
    bundle = Path(__file__).resolve().parent.parent / "out" / "excali" / "bundle.js"
    d = group_branches(strip_sources(mmd.read_text(encoding="utf-8")))
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "bundle.js").write_bytes(bundle.read_bytes())
        (t / "r.html").write_text('<!doctype html><meta charset="utf-8"><pre id="out">x</pre><script src="bundle.js"></script><script>window.run(' + json.dumps(d) + ")</script>", encoding="utf-8")
        dom = subprocess.run([find_edge(), "--headless", "--disable-gpu", "--no-first-run", "--allow-file-access-from-files", "--virtual-time-budget=30000", "--dump-dom", (t / "r.html").as_uri()], capture_output=True, text=True, encoding="utf-8").stdout
    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    text = unescape(m.group(1)) if m else ""
    if not text.startswith("{"):
        raise SystemExit("Chuyển lỗi: " + text[:200])
    if SRC_RE.search(text):
        raise SystemExit("Còn mã nguồn trong bản Excalidraw")
    out.write_text(text, encoding="utf-8")
    print(f"Đã ghi {out} ({len(json.loads(text)['elements'])} phần tử, không có mã nguồn)")


if __name__ == "__main__":
    main()
