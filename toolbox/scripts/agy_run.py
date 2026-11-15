"""Giao một bước của giai đoạn B cho agy (Antigravity) ở chế độ chỉ đọc.

agy không ghi file: nó đọc đầu vào rồi in một JSON. Script tách, kiểm, rồi ghi JSON vào đúng file
mà luồng subagent cũ vẫn ghi, nên các script áp dụng giữ nguyên. Lỗi agy hoặc hết hạn mức thì dừng
bước đó và báo, không tự chuyển sang Claude.

Chạy: python toolbox/scripts/agy_run.py <bài> <bước> [--part i] [--model m] [--force]
"""
import json
import os
import re
import shlex
import subprocess
import sys
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HYDROGEN = "gemini-4-hydrogen-medium"
SONNET = "claude-sonnet-5-5-medium"
OPUS = "claude-opus-5-5-medium"
# Thiếu câu này, chế độ plan của agy lập kế hoạch rồi chờ duyệt thay vì trả lời (thăm dò 2026-11-15)
READ_ONLY_PREFIX = "Đây là câu hỏi chỉ đọc, KHÔNG lập kế hoạch, KHÔNG chờ duyệt, KHÔNG ghi file nào. "
FENCE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.S)


class AgyError(RuntimeError):
    pass


def extract_json(text: str) -> object:
    """Lấy đối tượng hoặc mảng JSON trong stdout (có thể bọc ```json hoặc kèm lời dẫn)."""
    candidates = FENCE.findall(text) + [text]
    for chunk in candidates:
        for open_ch, close_ch in (("{", "}"), ("[", "]")):
            i, j = chunk.find(open_ch), chunk.rfind(close_ch)
            if 0 <= i < j:
                try:
                    return json.loads(chunk[i:j + 1])
                except json.JSONDecodeError:
                    continue
    raise ValueError("stdout không có JSON hợp lệ")


def _cmd() -> list[str]:
    raw = os.environ.get("AGY_CMD", "agy")
    return json.loads(raw) if raw.lstrip().startswith("[") else shlex.split(raw)


def call(prompt: str, model: str, add_dirs: list[str], timeout_s: int = 1200) -> str:
    args = _cmd() + ["-p", READ_ONLY_PREFIX + prompt, "--mode", "plan", "--model", model,
                     "--print-timeout", f"{timeout_s}s"]
    for d in add_dirs:
        args += ["--add-dir", d]
    try:
        res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=timeout_s + min(30, timeout_s))  # agy treo không tự dừng
    except subprocess.TimeoutExpired as e:
        raise AgyError(f"agy quá {timeout_s}s") from e
    # Quá --print-timeout agy vẫn in phần trả lời dở, nên mã thoát phải xét trước
    if res.returncode != 0 or "AGY_ERROR:" in (res.stderr or ""):
        raise AgyError(f"agy thoát mã {res.returncode}: {(res.stderr or '')[-500:]}")
    return res.stdout


def ask_json(prompt: str, model: str, add_dirs: list[str], validate: Callable[[object], list[str]],
             timeout_s: int = 1200) -> object:
    errors: list[str] = []
    for attempt in range(2):
        text = prompt if attempt == 0 else prompt + "\n\nLần trước sai:\n- " + "\n- ".join(errors)
        out = call(text, model, add_dirs, timeout_s)
        try:
            data = extract_json(out)
        except ValueError as e:
            errors = [str(e)]
            continue
        errors = validate(data)
        if not errors:
            return data
    raise AgyError("JSON sai sau 2 lượt: " + "; ".join(errors[:10]))
