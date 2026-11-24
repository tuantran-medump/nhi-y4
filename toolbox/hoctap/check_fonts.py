import argparse
from pathlib import Path
import re
import sys

import fitz


VIETNAMESE = "ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐĨŨƠƯ" + "àáâãèéêìíòóôõùúýăđĩũơư" + "ẤẦẨẪẬẮẰẲẴẶ" + "ấầẩẫậắằẳẵặ" + "ẾỀỂỄỆ" + "ếềểễệ" + "ỐỒỔỖỘỚỜỞỠỢ" + "ốồổỗộớờởỡợ" + "ỨỪỬỮỰ" + "ứừửữự" + "▲≥≤·"


def check_text_coverage(text: str, required: str = VIETNAMESE) -> list[str]:
    missing = sorted(set(required) - set(text))
    return [f"Thiếu ký tự bắt buộc: {char}" for char in missing]


def check_pdf(pdf: Path, allowed: list[str]) -> list[str]:
    errors = []
    doc = fitz.open(pdf)
    try:
        for page_number, page in enumerate(doc, 1):
            for block in page.get_text("dict").get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        value = span.get("text", "")
                        font = re.sub(r"^[A-Z]{6}\+", "", span.get("font", ""), flags=re.IGNORECASE)
                        bad_chars = sorted({c for c in value if ord(c) > 127})
                        if "\ufffd" in value or ".notdef" in value:
                            errors.append(f"Trang {page_number}: font {font}, ký tự lỗi U+FFFD hoặc .notdef")
                        if bad_chars and not any(name.casefold() in font.casefold() for name in allowed):
                            chars = "".join(bad_chars[:5])
                            errors.append(f"Trang {page_number}: font {font}, ký tự không được phép '{chars}'")
    finally:
        doc.close()
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kiểm tra font trong PDF")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--allow", nargs="+", default=[])
    parser.add_argument("--require-text", type=Path)
    args = parser.parse_args(argv)
    errors = check_pdf(args.pdf, args.allow)
    if args.require_text:
        try:
            text = args.require_text.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Không đọc được tệp văn bản: {exc}")
        else:
            errors.extend(check_text_coverage(text))
    if errors:
        print("\n".join(errors))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
