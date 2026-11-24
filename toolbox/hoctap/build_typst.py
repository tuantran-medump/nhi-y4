import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from boxes import LABELS, parse_sections


TOKENS = Path(__file__).parent / "styles" / "tokens.css"
FONT_DIR = Path(__file__).parent.parent / "templates" / "fonts"


def box_colors() -> dict[str, tuple[str, str]]:
    css = TOKENS.read_text(encoding="utf-8")
    result = {}
    for name in LABELS:
        stem = name.replace("-", "-")
        border = re.search(rf"--hop-{stem}:\s*(#[0-9a-fA-F]{{6}})", css)
        fill = re.search(rf"--hop-{stem}-nen:\s*(#[0-9a-fA-F]{{6}})", css)
        if not border or not fill:
            raise ValueError(f"Thiếu màu cho hộp {name} trong {TOKENS}")
        result[name] = border.group(1), fill.group(1)
    return result


def esc(text: str) -> str:
    return "".join("\\" + c if c in "#$@*_<[]~\\`" else c for c in text)


def inline(text: str, color: str) -> str:
    pattern = re.compile(r'<span class="([nkt])">(.*?)</span>|\*\*(.+?)\*\*|\[([A-Z]+\d*:p\d+)\]|(\[\?\])')
    out, pos = [], 0
    for m in pattern.finditer(text):
        out.append(esc(text[pos:m.start()]))
        if m[1] == "n": out.append(f'#text(fill: rgb("{color}"), weight: "bold")[{esc(m[2])}]')
        elif m[1] == "k": out.append(f'#highlight(fill: rgb("#fdeeb4"))[{esc(m[2])}]')
        elif m[1] == "t": out.append(f'#text(fill: rgb("#a3261a"))[{esc(m[2])}]')
        elif m[3] is not None: out.append(f'#text(weight: "bold")[{esc(m[3])}]')
        elif m[4] is not None: out.append(f'#text(size: 7pt, fill: rgb("#665f58"))[\[{esc(m[4])}\]]')
        else: out.append(r'#text(weight: "bold", fill: rgb("#a3261a"))[\[?\]]')
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out)


def _table(rows: list[str], color: str, fill: str) -> str:
    cells = [[x.strip() for x in row.strip().strip("|").split("|")] for row in rows]
    header = len(cells) > 1 and all(re.fullmatch(r":?-{3,}:?", c) for c in cells[1])
    if header:
        cells.pop(1)
    count = max(map(len, cells))
    rendered = []
    for ri, row in enumerate(cells):
        for cell in row:
            rendered.append(f'table.cell(fill: rgb("{fill}"), inset: 3pt)[{inline(cell, color)}]' if header and ri == 0 else f'[{inline(cell, color)}]')
    return f'#table(columns: {count}, stroke: rgb("{color}").transparentize(65%), inset: 3pt, {", ".join(rendered)})'


def render(md: str) -> str:
    sections = parse_sections(md)
    lines = md.splitlines()
    title = next((x[2:].strip() for x in lines if x.startswith("# ")), "")
    first = next((i for i, x in enumerate(lines) if x.startswith("## ")), len(lines))
    subtitle = " · ".join(x.strip() for x in lines[1:first] if x.strip())
    colors = box_colors()
    out = ['#set page("a4", margin: 9mm)', '#set text(font: "Inter", size: 8.5pt, lang: "vi", region: "VN", fill: rgb("#2e2418"))', '#set par(leading: 0.62em)', '#set page(fill: rgb("#fffaf1"))', '#set heading(numbering: none)', '#show heading.where(level: 2): it => none', f'#align(left)[#text(font: "Oswald", size: 20pt, fill: rgb("#a8561f"), weight: "bold")[{esc(title)}] #h(1fr) #text(size: 7.5pt)[{inline(subtitle, "#a8561f")}]]', '#line(length: 100%, stroke: 1.2pt + rgb("#d8c7a8"))', '#v(6pt)', '#columns(2, gutter: 6mm)[']
    for sec in sections:
        if sec.level == 0: continue
        color, pale = colors[sec.box]
        out.append(f'#block(breakable: false, above: 4pt, below: 4pt, stroke: rgb("{color}"), radius: 3pt, inset: 0pt)[#block(fill: rgb("{color}"), inset: (x: 5pt, y: 3pt))[#text(fill: white, weight: "bold")[{inline(sec.title, color)}] #h(1fr) #text(font: "Oswald", size: 8pt, fill: white)[{esc(LABELS[sec.box])}]] #block(inset: 5pt)[')
        i = 0
        while i < len(sec.lines):
            line = sec.lines[i]
            if not line.strip(): i += 1; continue
            if line.lstrip().startswith("|"):
                rows = []
                while i < len(sec.lines) and sec.lines[i].lstrip().startswith("|"):
                    rows.append(sec.lines[i]); i += 1
                out.append(_table(rows, color, pale)); continue
            if re.match(r"^\s*- ", line):
                items = []
                while i < len(sec.lines) and re.match(r"^\s*- ", sec.lines[i]):
                    current = sec.lines[i]; depth = (len(current) - len(current.lstrip())) // 2
                    body = current.strip()[2:]
                    trap = body.startswith("!bay ")
                    items.append((depth, body[5:] if trap else body, trap)); i += 1
                for depth, body, trap in items:
                    prefix = '#block(inset: (left: 5pt, right: 1pt), above: 1pt, below: 1pt)['
                    body = inline(body, color)
                    if trap:
                        out.append(prefix + f'#block(stroke: (dash: "dashed", paint: rgb("#a3261a")), fill: rgb("#fbe9e6"), inset: 3pt)[#text(fill: rgb("#a3261a"), size: 7pt, weight: "bold")[bẫy thi] {body}]]')
                    else:
                        out.append(prefix + f'#h({depth * 9}pt) #text(fill: rgb("{color}"))[•] {body}]')
                continue
            out.append(f'#block(above: 2pt, below: 2pt)[{inline(line.strip(), color)}]'); i += 1
        out.append("]]")
    out.append("]")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    output = args.out / "typst"
    output.mkdir(parents=True, exist_ok=True)
    source, pdf = output / f"{args.input.stem}.typ", output / f"{args.input.stem}.pdf"
    source.write_text(render(args.input.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    start = time.perf_counter()
    typst = shutil.which("typst") or str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages/Typst.Typst_Microsoft.Winget.Source_8wekyb3d8bbwe/typst-x86_64-pc-windows-msvc/typst.exe")
    subprocess.run([typst, "compile", "--font-path", str(FONT_DIR), str(source), str(pdf)], check=True)
    print(f"Dựng PDF: {time.perf_counter() - start:.3f} giây")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
