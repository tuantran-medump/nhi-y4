"""Tiện ích dùng chung: đường dẫn, CSV, chuẩn hóa Unicode."""
import csv
import json
import os
import unicodedata

TOOLBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def home() -> str:
    """Thư mục gốc toolbox. Test đặt NHI_TOOLBOX_HOME để không đụng dữ liệu thật."""
    return os.environ.get("NHI_TOOLBOX_HOME", TOOLBOX)


def data_path(*parts: str) -> str:
    return os.path.join(home(), "data", *parts)


def kho_path(*parts: str) -> str:
    return os.path.join(home(), "kho", *parts)


def load_config() -> dict:
    with open(os.path.join(TOOLBOX, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: list[dict], fields: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def read_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def write_text(path: str, text: str) -> None:
    """Ghi qua file tạm để lượt bị ngắt không để lại file dở."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def page_file(code: str, page: int, suffix: str = "txt") -> str:
    return kho_path(code, f"p{page:04d}.{suffix}")
