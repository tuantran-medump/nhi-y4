"""B7. Ghép bài theo template, dựng PDF bằng Edge, thêm số trang, bookmark, link Drive.

Chạy: python toolbox/scripts/b7_render.py G1-B08
Đầu vào: kho/lessons/<lesson>/body.md và extra.json
extra.json có các khóa: summary, approach, experience, exam, conflicts, missing
"""
import base64
import datetime
import html as htmlmod
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymupdf  # noqa: E402

from lib import common  # noqa: E402

CITE = re.compile(r"\[([GSCNRE]\d*):p([^\]]+)\]")
LIST = re.compile(r"^(\s*)([-+*]|\d+\.|[IVXLC]+\.)\s+(.*)$")
EMPTY = "Không có trong nguồn"
MARK_CLASS = {"-": "m-dash", "+": "m-plus", "*": "m-star"}
GLYPH = {"-": "•", "+": "◦", "*": "▪"}
NOTE_SPAN = re.compile(r"\(([^()]*\[[SCNRE]\d+:p[^\]]+\][^()]*)\)")
CITE_RUN = re.compile(r"(?:\s*\[[GSCNRE]\d*:p[^\]]+\]){2,}")
NOTE_AUTHOR = re.compile(r"^((?:Giảng viên|Ghi chú|Tài liệu|Slide|Bài giảng|BS|ThS|TS|PGS|GS|Cô|Thầy|Anh|Chị"
                         r"|WHO|IMCI|GINA|AAP|KDIGO|UpToDate|Guideline|Đồng thuận|Bộ Y tế)\b[^:\[]{0,40}"
                         r"|[^\s:\[]+ \d{4}):")
CONFLICT_LABEL = re.compile(r"^(Sách|Nguồn|Kết luận[^:\[]{0,80}):\s*")
CITE_ANY = re.compile(r"\s*\[[GSCNRE]\d*:p[^\]]+\]")
BARE_CAPTION = re.compile(r"(?:Bảng|Hình)\s*\d+(?:\.\d+)?\.?(?:\s*\[[GSCNRE]\d*:p[^\]]+\])*")
CAPTION = re.compile(r"^(?:Bảng|Hình)\s*\d+(?:\.\d+)?\b")


def _expand(pages: str) -> list[int] | None:
    nums: list[int] = []
    for part in pages.split(","):
        m = re.fullmatch(r"p?(\d+)(?:-p?(\d+))?", part.strip())
        if not m:
            return None
        start = int(m.group(1))
        nums += range(start, int(m.group(2) or start) + 1)
    return nums


def _compress(nums: list[int]) -> str:
    parts, ordered = [], sorted(set(nums))
    start = prev = ordered[0]
    for n in ordered[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        parts.append(f"p{start}" if start == prev else f"p{start}-{prev}")
        start = prev = n
    return ",".join(parts)


def _merge(cites: list[tuple[str, str]]) -> str:
    """Gộp các mã cùng nguồn: [S1:p53,p56,p61-67]."""
    pages: dict[str, list[int]] = {}
    raw: list[str] = []
    for code, value in cites:
        nums = _expand(value)
        if nums is None:
            raw.append(f"[{code}:p{value}]")
        else:
            pages.setdefault(code, []).extend(nums)
    return "".join(f"[{c}:{_compress(n)}]" for c, n in pages.items()) + "".join(raw)


def _sentence_end(buf: str, text: str, i: int) -> bool:
    if re.search(r"(?:^|[\s(.])[^\W\d_]{1,2}\.$", buf):
        return False
    rest = text[i:]
    if not rest.strip():
        return True
    if not rest[0].isspace():
        return False
    nxt = rest.strip()[0]
    return nxt.isupper() or nxt.isdigit() or nxt in "[("


def tidy_citations(text: str) -> str:
    """Đưa mã nguồn về cuối câu và gộp số trang. Mã trong ngoặc đơn ở nguyên trong ngoặc."""
    text = CITE_RUN.sub(lambda m: " " + _merge(CITE.findall(m.group(0))), text)
    done: list[list] = []
    buf, cites, depth, i = "", [], 0, 0
    while i < len(text):
        m = CITE.match(text, i) if depth == 0 else None
        if m:
            if not buf.strip() and done:
                done[-1][1].append(m.groups())
            else:
                cites.append(m.groups())
                buf = buf.rstrip()
            i = m.end()
            continue
        ch = text[i]
        depth += ch == "("
        depth = max(depth - (ch == ")"), 0)
        buf += ch
        i += 1
        if depth == 0 and ch in ".!?" and _sentence_end(buf, text, i):
            done.append([buf.strip(), cites])
            buf, cites = "", []
    if buf.strip():
        done.append([buf.strip(), cites])
    elif cites and done:
        done[-1][1] += cites
    return " ".join(s + (" " + _merge(c) if c else "") for s, c in done)


def _inline(text: str, links: dict) -> str:
    out = htmlmod.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', out)

    def note(m: re.Match) -> str:
        body = NOTE_AUTHOR.sub(r"<b>\1:</b>", m.group(1), count=1)
        return f'<span class="note">({body})</span>'

    out = NOTE_SPAN.sub(note, out)

    def cite(m: re.Match) -> str:
        code = m.group(1)
        label = f"{code} p" + m.group(2).replace(",p", ", p")
        kind = "book" if code.startswith("G") else "ref"
        span = f'<span class="cite {kind}">{label}</span>'
        url = links.get(code)
        return f'<a class="cite-link" href="{htmlmod.escape(url)}">{span}</a>' if url else span

    return CITE.sub(cite, out)


def _item(text: str, links: dict) -> str:
    """Nội dung một dòng danh sách. Nhãn trong mục mâu thuẫn in đậm, dòng kết luận có nền kem."""
    m = CONFLICT_LABEL.match(text)
    if not m:
        return _inline(text, links)
    html = f"<b>{htmlmod.escape(m.group(1), quote=False)}:</b> {_inline(text[m.end():], links)}"
    return f'<span class="note resolve">{html}</span>' if m.group(1).startswith("Kết luận") else html


def _table(rows: list[str], links: dict) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [r for r in cells[1:] if not all(set(c) <= set("-: ") for c in r)]
    out = "<table><tr>" + "".join(f"<th>{_inline(c, links)}</th>" for c in head) + "</tr>"
    for r in body:
        out += "<tr>" + "".join(f"<td>{_inline(c, links)}</td>" for c in r) + "</tr>"
    return out + "</table>"


def md_to_html(md: str, links: dict) -> str:
    out: list[str] = []
    depth = 0
    lines = md.split("\n")

    def close_to(target: int) -> None:
        nonlocal depth
        while depth > target:
            out.append("</li></ul>")
            depth -= 1

    i, heading = 0, 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if re.fullmatch(r"\s*<<.*>>\s*", line):
            continue
        m = LIST.match(line)
        if m and not line.lstrip().startswith("**"):
            level = len(m.group(1)) // 2 + 1
            marker, text = m.group(2), tidy_citations(m.group(3))
            if CAPTION.match(text):
                close_to(0)
                if BARE_CAPTION.fullmatch(text) and i < len(lines) and LIST.match(lines[i]):
                    text = tidy_citations(text.split(" [")[0] + " " + LIST.match(lines[i]).group(3)
                                          + "".join(CITE_ANY.findall(text)))
                    i += 1
                out.append(f'<p class="caption">{_inline(text, links)}</p>')
                continue
            if level > depth:
                while depth < level:
                    out.append("<ul>")
                    depth += 1
            else:
                close_to(level)
                out.append("</li>")
            cls = MARK_CLASS.get(marker, "m-num")
            out.append(f'<li class="{cls}" data-m="{GLYPH.get(marker, marker)}">{_item(text, links)}')
            continue
        close_to(0)
        if not line.strip():
            continue
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            heading += 1
            n = len(h.group(1))
            attr = f' id="h{heading}"' if n > 1 else ""
            out.append(f"<h{n}{attr}>{_inline(h.group(2), links)}</h{n}>")
        elif line.startswith("|"):
            block = [line]
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(_table(block, links))
        elif line.startswith(">"):
            out.append(f'<div class="box">{_inline(tidy_citations(line[1:].strip()), links)}</div>')
        else:
            img = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line.strip())
            if img:
                out.append(f'<img src="{htmlmod.escape(img.group(2))}" alt="{htmlmod.escape(img.group(1))}">')
            else:
                tidy = tidy_citations(line)
                cls = ' class="caption"' if CAPTION.match(tidy) else ""
                out.append(f"<p{cls}>{_inline(tidy, links)}</p>")
    close_to(0)
    return "\n".join(out)


def _load_links() -> dict:
    links = {r["code"]: r["url"] for r in common.read_csv(common.data_path("drive_links.csv")) if r.get("url")}
    for r in common.read_csv(common.data_path("external_sources.csv")):
        if r.get("url"):
            links[r["code"]] = r["url"]
    return links


def _sources_table(text: str) -> str:
    codes = sorted({m.group(1) for m in CITE.finditer(text)})
    if not codes:
        return EMPTY
    names = {r["code"]: os.path.basename(r["path"]) for r in common.read_csv(common.data_path("manifest.csv"))}
    names.update({r["code"]: r["title"] for r in common.read_csv(common.data_path("external_sources.csv"))})
    links = _load_links()
    rows = ["| Mã | Nguồn | Link |", "|---|---|---|"]
    for c in codes:
        link = f"[Mở]({links[c]})" if links.get(c) else "Chưa gắn"
        rows.append(f"| {c} | {names.get(c, 'Chưa có trong danh mục')} | {link} |")
    return "\n".join(rows)


def _gap_lines(gaps: list[dict]) -> list[str]:
    lines = []
    exact = [g["printed_page"] for g in gaps if not g.get("note")]
    if exact:
        lines.append("- Thiếu trang in trong bản scan: " + ", ".join(exact))
    groups: dict[str, list[int]] = {}
    for g in gaps:
        if g.get("note"):
            groups.setdefault(g["note"], []).append(int(g["printed_page"]))
    for note, pages in groups.items():
        lines.append(f"- Trang in {min(pages)}-{max(pages)}: {note}, chưa rõ trang nào")
    return lines


def assemble(info: dict) -> str:
    lesson = info["lesson"]
    extra = common.read_json(common.kho_path("lessons", lesson, "extra.json"), {})
    body = common.read_text(common.kho_path("lessons", lesson, "body.md")).strip()
    missing = (extra.get("missing") or "").strip()
    gap_lines = _gap_lines([g for g in common.read_csv(common.data_path("gaps.csv")) if g["lesson"] == lesson])
    if gap_lines:
        missing = "\n".join(([missing] if missing else []) + gap_lines)
    values = {
        "title": info["title"], "lesson": lesson, "society": info.get("society") or "Không áp dụng",
        "date": datetime.date.today().isoformat(),
        "label": "" if info.get("book") else "> Ngoài giáo trình: bài này không có trong Nhi Khoa Tập 1, 2.",
        "body": body, "missing": missing or EMPTY,
    }
    for key in ("summary", "approach", "experience", "exam", "conflicts"):
        values[key] = (extra.get(key) or "").strip() or EMPTY
    values["sources"] = _sources_table(body + "\n" + "\n".join(str(v) for v in extra.values()))
    md = common.read_text(os.path.join(common.TOOLBOX, "templates", "lesson.md"))
    for key, value in values.items():
        md = md.replace("{{" + key + "}}", value)
    return md


def crop_figure(pdf: str, page: int, rect: tuple, out: str, dpi: int = 200) -> None:
    """Cắt hình từ trang gốc. rect tính theo điểm PDF."""
    with pymupdf.open(pdf) as d:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        d[page - 1].get_pixmap(dpi=dpi, clip=pymupdf.Rect(rect)).save(out)


def _nav(page_html: str) -> str:
    items = re.findall(r'<h([23])\s+id="(h\d+)">(.*?)</h\1>', page_html)
    if not items:
        return ""
    links = "".join(f'<a class="l{n}" href="#{i}">{re.sub("<.*?>", "", t)}</a>' for n, i, t in items)
    return f"<nav><b>Mục lục</b>{links}</nav>"


def print_pdf(html_path: str, pdf_path: str) -> None:
    edge = common.load_config()["edge"]
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}",
                        "file:///" + html_path.replace("\\", "/")],
                       check=True, capture_output=True, timeout=180)


def finish_pdf(pdf_path: str, headings: list[tuple[int, str]]) -> None:
    """Thêm số trang và bookmark sau khi Edge in xong."""
    tmp = pdf_path + ".tmp.pdf"
    with pymupdf.open(pdf_path) as d:
        toc, start = [], 0
        for level, title in headings:
            for n in range(start, d.page_count):
                if d[n].search_for(title[:40]):
                    toc.append([max(1, level), title, n + 1])
                    start = n
                    break
        for n, page in enumerate(d, 1):
            page.insert_text((page.rect.width / 2 - 10, page.rect.height - 22), f"{n}/{d.page_count}",
                             fontsize=9, color=(0.4, 0.4, 0.4))
        if toc:
            base = toc[0][0]
            fixed, prev = [], 0
            for level, title, page in toc:
                level = min(level - base + 1, prev + 1)
                level = max(level, 1)
                fixed.append([level, title, page])
                prev = level
            d.set_toc(fixed)
        d.save(tmp, garbage=3, deflate=True)
    os.replace(tmp, pdf_path)


def page_css() -> str:
    """CSS của bài, font Inter nhúng thẳng để Edge in được mà không cần cài font."""
    css = common.read_text(os.path.join(common.TOOLBOX, "templates", "lesson.css"))
    for key, name in (("inter", "Inter.ttf"), ("inter_italic", "Inter-Italic.ttf")):
        with open(os.path.join(common.TOOLBOX, "templates", "fonts", name), "rb") as f:
            css = css.replace("{{" + key + "}}", base64.b64encode(f.read()).decode("ascii"))
    return css


def render(lesson: str, out_path: str | None = None) -> str:
    info = next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)
    md = assemble(info)
    body = md_to_html(md, _load_links())
    css = page_css()
    title_end = body.index("</h1>") + 5
    page = (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>{htmlmod.escape(info["title"])}</title>'
            f"<style>{css}</style></head><body>{body[:title_end]}{_nav(body)}{body[title_end:]}</body></html>")
    html_path = common.kho_path("lessons", lesson, "lesson.html")
    common.write_text(html_path, page)
    if out_path is None:
        out_path = os.path.join(common.load_config()["output_root"], info["group"], info["title"] + ".pdf")
    print_pdf(html_path, out_path)
    headings = [(len(m.group(1)), m.group(2)) for m in re.finditer(r"^(#{1,4})\s+(.*)$", md, re.M)]
    finish_pdf(out_path, headings)
    return out_path


if __name__ == "__main__":
    print(render(sys.argv[1]))
