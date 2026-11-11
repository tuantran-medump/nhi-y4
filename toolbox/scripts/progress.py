"""Sổ tiến độ từng bài, để bị ngắt hoặc sang phiên mới vẫn làm tiếp đúng chỗ.

Chạy:
  python toolbox/scripts/progress.py G1-B08            (xem bước kế tiếp)
  python toolbox/scripts/progress.py G1-B08 B2 "ghi chú"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402

STEPS = ["B1", "B2", "B2b", "B3", "B4", "B5", "B6", "B7"]


def _path() -> str:
    return common.data_path("progress.json")


def get(lesson: str) -> dict:
    return common.read_json(_path(), {}).get(lesson, {})


def set(lesson: str, step: str, note: str = "") -> None:  # noqa: A001
    if step not in STEPS:
        raise ValueError(f"Bước không hợp lệ: {step}")
    state = common.read_json(_path(), {})
    state.setdefault(lesson, {})[step] = note
    common.write_json(_path(), state)


def next_step(lesson: str) -> str | None:
    done = get(lesson)
    return next((s for s in STEPS if s not in done), None)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        set(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    print("Bước kế tiếp:", next_step(sys.argv[1]))
