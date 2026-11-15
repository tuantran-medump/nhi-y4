"""B8. Dựng bài theo format mẫu "b14 - xuất huyết giảm tiểu cầu", lưu đồ vẽ lại bằng Mermaid.

Chạy: python toolbox/scripts/b8_render_b14.py G1-B16 [G1-B09 ...]   (không đối số: mọi bài đã có body.md)
Đầu vào giống b7. Lưu đồ vẽ lại đặt ở kho/lessons/<bài>/diagrams/<block>.mmd: khối <<block:X>> tương ứng
(ảnh + bản gõ lại) được thay bằng sơ đồ. Kết quả ra thư mục "<output_root> - mẫu B14", không ghi đè bản b7.
"""
import base64
import html as htmlmod
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402
from scripts import b7_render as b7  # noqa: E402

TEMPLATES = os.path.join(common.TOOLBOX, "templates")
FONTS = {"inter": "Inter.ttf", "inter_italic": "Inter-Italic.ttf", "coiny": "Coiny.ttf", "oswald": "Oswald.ttf",
         "lora_italic": "Lora-Italic.ttf", "greatvibes": "GreatVibes.ttf"}
BLOCK = re.compile(r"<<block:(\w+)>>\n.*?<<endblock>>", re.S)
TOKEN = "@@DIAGRAM:{}@@"
CLASSDEFS = """
  classDef start fill:#efe7fb,stroke:#9b7fd1,color:#3b2a5c
  classDef ask fill:#fff4dc,stroke:#e0a83a,color:#5a3d06
  classDef act fill:#e6f1fb,stroke:#6fa3d6,color:#163b5e
  classDef danger fill:#fde8e6,stroke:#e0786e,color:#6b1d16
  classDef ok fill:#e7f5e8,stroke:#79b77e,color:#1d4a22
  classDef note fill:none,stroke:none,color:#6b6257
  classDef dot fill:#e0a83a,stroke:#e0a83a
"""
MERMAID_INIT = """mermaid.initialize({startOnLoad: false, theme: 'base', securityLevel: 'loose',
  themeVariables: {fontFamily: 'Inter, Arial, sans-serif', fontSize: '14px', lineColor: '#a08a6a',
    primaryColor: '#fffaf1', primaryBorderColor: '#d8c7a8', edgeLabelBackground: '#fffdf9'},
  flowchart: {htmlLabels: true, curve: 'basis', nodeSpacing: 28, rankSpacing: 38, padding: 10, wrappingWidth: 420}});
document.fonts.ready.then(() => mermaid.run());"""
OUT_SUFFIX = " - mẫu B14"


def page_css() -> str:
    css = common.read_text(os.path.join(TEMPLATES, "b14.css"))
    for key, name in FONTS.items():
        with open(os.path.join(TEMPLATES, "fonts", name), "rb") as f:
            css = css.replace("{{" + key + "}}", base64.b64encode(f.read()).decode("ascii"))
    return css


def swap_diagrams(md: str, lesson: str) -> tuple[str, dict]:
    """Thay khối ảnh + bản gõ lại bằng token nếu đã có sơ đồ vẽ lại."""
    found: dict[str, str] = {}

    def sub(m: re.Match) -> str:
        path = common.kho_path("lessons", lesson, "diagrams", m.group(1) + ".mmd")
        if not os.path.exists(path):
            return m.group(0)
        src = common.read_text(path).rstrip() + "\n" + CLASSDEFS
        found[m.group(1)] = src
        return TOKEN.format(m.group(1))

    return BLOCK.sub(sub, md), found


def gradient_title(text: str) -> str:
    """Tô chuyển màu đỏ sang cam theo từng chữ cái (background-clip:text để lại viền khi Edge in)."""
    a, b = (0xC9, 0x41, 0x3A), (0xEF, 0x9D, 0x5C)
    chars = list(text)
    n = max(len(chars) - 1, 1)
    out = []
    for i, ch in enumerate(chars):
        t = i / n
        rgb = "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))
        out.append(f'<span style="color:#{rgb}">{htmlmod.escape(ch)}</span>' if ch.strip() else ch)
    return "".join(out)


def print_pdf(html_path: str, pdf_path: str) -> None:
    """Như b7 nhưng chờ script Mermaid vẽ xong trước khi in."""
    edge = common.load_config()["edge"]
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                        "--virtual-time-budget=20000", "--run-all-compositor-stages-before-draw",
                        f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}",
                        "file:///" + html_path.replace("\\", "/")],
                       check=True, capture_output=True, timeout=240)


def render(lesson: str) -> str:
    info = next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)
    md, diagrams = swap_diagrams(b7.assemble(info), lesson)
    body = b7.md_to_html(md, b7._load_links())
    for name, src in diagrams.items():
        block = f'<div class="diagram"><pre class="mermaid">{htmlmod.escape(src, quote=False)}</pre></div>'
        body = re.sub(rf"<p>\s*{re.escape(TOKEN.format(name))}\s*</p>", lambda _m: block, body)
    title_end = body.index("</h1>") + 5
    title = f'<h1 class="doc-title">{gradient_title(info["title"])}</h1>'
    body = re.sub(r'<li class="m-\w+" data-m="[^"]*">(Lưu đồ \d+(?:\.\d+)?.*?)(?=</li>|<ul>|<div)',
                  lambda m: f'<p class="caption">{m.group(1).strip()}</p>', body, flags=re.S)
    byline = f'<div class="byline">Nhi khoa Y4 <span>· {htmlmod.escape(info["group"])} · {lesson}</span></div><hr class="rule">'
    mermaid_js = "file:///" + os.path.join(TEMPLATES, "vendor", "mermaid.min.js").replace("\\", "/")
    script = f'<script src="{mermaid_js}"></script><script>{MERMAID_INIT}</script>' if diagrams else ""
    page = (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>{htmlmod.escape(info["title"])}</title>'
            f"<style>{page_css()}</style></head><body>{title}{byline}{b7._nav(body)}{body[title_end:]}{script}</body></html>")
    html_path = common.kho_path("lessons", lesson, "lesson_b14.html")
    common.write_text(html_path, page)
    out_root = common.load_config()["output_root"] + OUT_SUFFIX
    out_path = os.path.join(out_root, info["group"], info["title"] + ".pdf")
    print_pdf(html_path, out_path)
    headings = [(len(m.group(1)), m.group(2)) for m in re.finditer(r"^(#{1,4})\s+(.*)$", md, re.M)]
    b7.finish_pdf(out_path, headings)
    return out_path


if __name__ == "__main__":
    lessons = sys.argv[1:] or sorted(d for d in os.listdir(common.kho_path("lessons"))
                                     if os.path.exists(common.kho_path("lessons", d, "body.md")))
    for name in lessons:
        print(render(name), flush=True)
