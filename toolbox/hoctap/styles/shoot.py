"""Render one local HTML file with the installed Microsoft Edge."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote


EDGE = Path(r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--style", choices=("warm", "clean", "screen"), required=True)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--width", type=int, default=794)
    args = parser.parse_args()
    source = args.html.resolve(strict=True)
    if args.width < 320:
        parser.error("--width must be at least 320")
    if not EDGE.is_file():
        parser.error(f"Edge not found: {EDGE}")
    work = args.png.parent.resolve()
    work.mkdir(parents=True, exist_ok=True)
    rendered = work / f"{source.stem}-{args.style}.html"
    html = source.read_text(encoding="utf-8-sig")
    css_path = Path(__file__).resolve().parent / f"{args.style}.css"
    css_href = Path(os.path.relpath(css_path, work)).as_posix()
    html, links = re.subn(r'(<link\b[^>]*\bhref=["\'])[^"\']+(["\'][^>]*>)',
                          lambda m: f'{m.group(1)}{css_href}{m.group(2)}', html, count=1, flags=re.I)
    if links != 1:
        parser.error("input must have one stylesheet link")
    def set_body(match: re.Match) -> str:
        attrs = re.sub(r'\sclass=["\'][^"\']*["\']', '', match.group(1), flags=re.I)
        return f'<body{attrs} class="style-{args.style}">'
    html, bodies = re.subn(r'<body\b([^>]*)>', set_body, html, count=1, flags=re.I)
    if bodies != 1:
        parser.error("input must have a body element")
    rendered.write_text(html, encoding="utf-8", newline="\n")
    profile = Path(tempfile.mkdtemp(prefix=f"hoctap-edge-{args.style}-"))
    base = [str(EDGE), "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
            f"--window-size={args.width},900", f"--user-data-dir={profile}",
            "--allow-file-access-from-files", "--no-first-run", "--no-pdf-header-footer"]
    url = "file:///" + quote(rendered.as_posix(), safe=":/")
    args.png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([*base, f"--screenshot={args.png.resolve()}", url], check=True, timeout=60)
    if args.pdf:
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([*base, f"--print-to-pdf={args.pdf.resolve()}", url], check=True, timeout=60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
