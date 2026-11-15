"""Giao một bước của giai đoạn B cho agy (Antigravity) ở chế độ chỉ đọc.

agy không ghi file: nó đọc đầu vào rồi in một JSON. Script tách, kiểm, rồi ghi JSON vào đúng file
mà luồng subagent cũ vẫn ghi, nên các script áp dụng giữ nguyên. Lỗi agy hoặc hết hạn mức thì dừng
bước đó và báo, không tự chuyển sang Claude.

Chạy: python toolbox/scripts/agy_run.py <bài> <bước> [--part i] [--model m] [--force]
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import common  # noqa: E402
from scripts.b2_ocr_fix import _digits  # noqa: E402
from scripts.b5_annotate import NOTE_OK  # noqa: E402

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
    decoder = json.JSONDecoder()
    for chunk in FENCE.findall(text)[::-1] + [text]:  # khối ```json cuối cùng thường là câu trả lời
        best, best_len, i = None, 0, 0
        while i < len(chunk):
            if chunk[i] in "{[":
                try:
                    obj, end = decoder.raw_decode(chunk, i)
                except json.JSONDecodeError:
                    i += 1
                    continue
                if end - i > best_len:  # lấy giá trị dài nhất, tránh {...} lẻ trong lời dẫn
                    best, best_len = obj, end - i
                i = end
            else:
                i += 1
        if best_len:
            return best
    raise ValueError("stdout không có JSON hợp lệ")


def _cmd() -> list[str]:
    raw = os.environ.get("AGY_CMD", "agy")
    return json.loads(raw) if raw.lstrip().startswith("[") else shlex.split(raw)


def call(prompt: str, model: str, add_dirs: list[str], timeout_s: int = 1200) -> str:
    args = _cmd() + ["-p", READ_ONLY_PREFIX + prompt, "--mode", "plan", "--model", model,
                     "--print-timeout", f"{timeout_s}s", "--output-format", "json"]
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
    # --output-format json: {"status": "SUCCESS", "response": "..."}; ở dạng chữ thô agy có lúc in rỗng
    try:
        wrapper = json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise AgyError(f"agy không trả JSON bọc ngoài: {res.stdout[:300]}") from e
    if wrapper.get("status") != "SUCCESS":
        raise AgyError(f"agy status {wrapper.get('status')}: {str(wrapper)[:300]}")
    return wrapper.get("response") or ""


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


# ---------- Các bước ----------

VISION_OK = True  # thăm dò 2026-11-15: agy đọc được ảnh trang ở chế độ plan
CODE_AT_START = re.compile(r"^\[([SCNRE]\d+):")
BATCH = 6
PROMPTS = os.path.join(common.TOOLBOX, "templates", "prompts")
EXTRA_KEYS = ("summary", "approach", "experience", "exam", "conflicts", "missing")
CARD_KEYS = ("notes", "conflicts", "approach", "experience", "exam")


def split_evidence(text: str, max_lines: int = 400) -> list[str]:
    """Chia bằng chứng thành phần vừa một lượt gọi; mỗi nguồn nằm trọn một phần trừ khi riêng nó quá dài."""
    groups: list[list[str]] = []
    code = None
    for line in text.split("\n"):
        m = CODE_AT_START.match(line)
        if not groups or (m and m.group(1) != code):
            groups.append([])
            if m:
                code = m.group(1)
        groups[-1].append(line)
    parts: list[list[str]] = []
    fresh = True  # phần cuối có nhận thêm nhóm được không (phần cắt từ nguồn quá dài thì không)
    for g in groups:
        if len(g) > max_lines:
            parts += [g[i:i + max_lines] for i in range(0, len(g), max_lines)]
            fresh = False
        elif parts and fresh and len(parts[-1]) + len(g) <= max_lines:
            parts[-1] = parts[-1] + g
        else:
            parts.append(list(g))
            fresh = True
    return ["\n".join(p) for p in parts]


def body_lines(numbered: str) -> list[str]:
    return [line.split("\t", 1)[1] if "\t" in line else "" for line in numbered.split("\n")]


def valid_note_errors(note: object, body: list[str]) -> list[str]:
    if not isinstance(note, dict):
        return [f"chú thích không phải object: {note!r}"[:120]]
    errs = []
    text, line = str(note.get("note", "")), note.get("line")
    if not NOTE_OK.match(text):
        errs.append(f"dòng {line}: note phải trong một cặp ngoặc đơn, có mã [S..:p..]: {text[:80]}")
    if not isinstance(line, int) or not 1 <= line <= len(body):
        errs.append(f"line không hợp lệ: {line}")
    else:
        s = body[line - 1].strip()
        if not s or s.startswith(("<<", "|")):
            errs.append(f"dòng {line} là dòng trống, dòng <<...>> hoặc dòng bảng")
    if "resolve" in note:
        errs.append(f"dòng {line}: không được có resolve (Claude làm ở B6)")
    return errs


@dataclass
class Part:
    index: int
    total: int
    model: str
    inputs: list[str]
    ids: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Step:
    b_step: str
    prompt_file: str
    shape: str
    parts: Callable[[str], list[Part]]
    validate: Callable[[object, str, Part], list[str]]
    write: Callable[[str, Part, object], None]
    done: Callable[[str, Part], bool]
    vision: bool = False


def _lesson_path(lesson: str, *p: str) -> str:
    return common.kho_path("lessons", lesson, *p)


def _notes_errors(notes: object, lesson: str) -> list[str]:
    if not isinstance(notes, list):
        return ["notes phải là mảng"]
    body = body_lines(common.read_text(_lesson_path(lesson, "body_numbered.txt")))
    return [e for n in notes for e in valid_note_errors(n, body)]


# cards (B5a): phần lẻ Hydrogen, phần chẵn Sonnet, đều qua agy
def _cards_parts(lesson: str) -> list[Part]:
    chunks = split_evidence(common.read_text(_lesson_path(lesson, "evidence.md")))
    out = []
    for i, chunk in enumerate(chunks, 1):
        path = _lesson_path(lesson, "agy", f"evidence_{i}.md")
        common.write_text(path, chunk)
        out.append(Part(i, len(chunks), HYDROGEN if i % 2 else SONNET, [_lesson_path(lesson, "body_numbered.txt"), path]))
    return out


def _cards_validate(d: object, lesson: str, part: Part) -> list[str]:
    if not isinstance(d, dict):
        return ["phải là object"]
    errs = [f"thiếu hoặc sai khóa {k} (mảng)" for k in CARD_KEYS if not isinstance(d.get(k), list)]
    return errs or _notes_errors(d["notes"], lesson)


def _cards_done(lesson: str, part: Part) -> bool:
    path = _lesson_path(lesson, f"cards_{part.index}.json")
    return os.path.exists(path) and not _cards_validate(common.read_json(path, None), lesson, part)


# compose (B5b): Opus qua agy, không resolve, không tra web
def _compose_parts(lesson: str) -> list[Part]:
    info = next(r for r in common.read_csv(common.data_path("lessons.csv")) if r["lesson"] == lesson)
    folder = _lesson_path(lesson)
    cards = sorted(os.path.join(folder, f) for f in os.listdir(folder) if re.fullmatch(r"cards_\d+\.json", f))
    note = (f"Hiệp hội ưu tiên của bài: {info.get('society') or 'không có'}. Không thêm khóa resolve, không tra web, "
            "không sửa data/external_sources.csv, bỏ qua phần chạy lệnh kiểm tra. Trong conflicts, dòng kết luận "
            "ghi đúng `- Kết luận: (Claude quyết ở B6)`.")
    return [Part(1, 1, OPUS, [_lesson_path(lesson, "body_numbered.txt"), *cards], note=note)]


def _compose_validate(d: object, lesson: str, part: Part) -> list[str]:
    if not isinstance(d, dict) or not isinstance(d.get("extra"), dict):
        return ["phải là object có notes (mảng) và extra (object)"]
    errs = [f"extra thiếu hoặc sai khóa {k} (chuỗi)" for k in EXTRA_KEYS if not isinstance(d["extra"].get(k), str)]
    return errs + _notes_errors(d.get("notes"), lesson)


def _compose_write(lesson: str, part: Part, d: dict) -> None:
    common.write_json(_lesson_path(lesson, "notes.json"), d["notes"])
    common.write_json(_lesson_path(lesson, "extra.json"), d["extra"])


# layout (B2b)
def _layout_validate(d: object, lesson: str, part: Part) -> list[str]:
    if not isinstance(d, list):
        return ["phải là mảng"]
    return [f"mục thiếu line số nguyên: {x!r}"[:120] for x in d if not (isinstance(x, dict) and isinstance(x.get("line"), int))]


# review (B2) và ink (B4): theo lô id, mỗi id một file kết quả
def _batch_parts(tasks_path: str, base_dir: str) -> list[Part]:
    raw = common.read_json(tasks_path, [])
    tasks = raw.get("tasks", []) if isinstance(raw, dict) else raw
    lots = [tasks[i:i + BATCH] for i in range(0, len(tasks), BATCH)]
    parts = []
    for i, lot in enumerate(lots, 1):
        # Liệt kê từng file ảnh, chữ: chỉ đưa thư mục thì agy có lúc kết thúc mà không trả lời (chạy thử G2-B01)
        files = [os.path.join(base_dir, t[k]) for t in lot for k in ("image", "text") if t.get(k)]
        ids = [t["id"] for t in lot]
        parts.append(Part(i, len(lots), HYDROGEN, [tasks_path, *files], ids=ids, note="Chỉ làm các id: " + ", ".join(ids)))
    return parts


def _batch_validate(value_errors: Callable[[str, str, object], list[str]]) -> Callable[[object, str, Part], list[str]]:
    def check(d: object, lesson: str, part: Part) -> list[str]:
        if not isinstance(d, dict):
            return ["phải là object {id: kết quả}"]
        errs = [f"thiếu id {i}" for i in part.ids if i not in d] + [f"id lạ {k}" for k in d if k not in part.ids]
        return errs + [e for k, v in d.items() if k in part.ids for e in value_errors(lesson, k, v)]
    return check


def _review_value(lesson: str, _id: str, v: object) -> list[str]:
    """Kiểm như b2_review.apply và b2_ocr_fix.apply_patch, để một mục sai không chặn cả bài lúc áp."""
    if not isinstance(v, list):
        return [f"{_id}: phải là mảng"]
    task = next((t for t in common.read_json(_lesson_path(lesson, "review", "tasks.json"), []) if t["id"] == _id), {})
    text = common.read_text(_lesson_path(lesson, "review", task.get("text", _id + ".txt")))
    page = {int(n): s for n, s in (row.split("\t", 1) for row in text.split("\n") if "\t" in row)}
    errs = []
    for p in v:
        if not isinstance(p, dict) or not isinstance(p.get("line"), int) or not all(isinstance(p.get(k), str) for k in ("old", "new")):
            errs.append(f"{_id}: mục phải có line (số), old, new (chuỗi): {p!r}"[:150])
        elif not int(task.get("start", 0)) <= p["line"] <= int(task.get("end", 0)) or p["line"] not in page:
            errs.append(f"{_id}: dòng {p['line']} nằm ngoài trang")
        elif p["old"] not in page[p["line"]]:
            errs.append(f"{_id}: dòng {p['line']} không chứa {p['old']!r}")
        elif _digits(p["old"]) != _digits(p["new"]) and not p.get("verified"):
            errs.append(f"{_id}: dòng {p['line']} đổi số, phải đối chiếu ảnh rồi ghi verified: true")
    return errs


def _ink_value(lesson: str, _id: str, v: object) -> list[str]:
    raw = common.read_json(common.kho_path("ink", lesson, "tasks.json"), {})
    items = next((t.get("items", {}) for t in raw.get("tasks", []) if t["id"] == _id), {})
    if not isinstance(v, dict):
        return [f"{_id}: phải là object nhãn -> chữ"]
    return [f"{_id}: thiếu nhãn {k}" for k in items if k not in v]


def _review_dir(lesson: str) -> str:
    return _lesson_path(lesson, "review", "results")


def _ink_dir(lesson: str) -> str:
    return common.kho_path("ink", lesson, "results")


def _batch_write(results_dir: Callable[[str], str]) -> Callable[[str, Part, dict], None]:
    def write(lesson: str, part: Part, d: dict) -> None:
        for k in part.ids:
            common.write_json(os.path.join(results_dir(lesson), f"{k}.json"), d[k])
    return write


def _batch_done(results_dir: Callable[[str], str]) -> Callable[[str, Part], bool]:
    return lambda lesson, part: all(os.path.exists(os.path.join(results_dir(lesson), f"{k}.json")) for k in part.ids)


def _write_json_to(name: str) -> Callable[[str, Part, object], None]:
    return lambda lesson, part, d: common.write_json(_lesson_path(lesson, name), d)


def _exists(name: str) -> Callable[[str, Part], bool]:
    return lambda lesson, part: os.path.exists(_lesson_path(lesson, name))


STEPS: dict[str, Step] = {
    "cards": Step("B5", "cards.md",
                  '{"notes": [...], "conflicts": [...], "approach": [...], "experience": [...], "exam": [...]}',
                  _cards_parts, _cards_validate,
                  lambda lesson, p, d: common.write_json(_lesson_path(lesson, f"cards_{p.index}.json"), d),
                  _cards_done),
    "compose": Step("B5", "compose_lesson.md",
                    '{"notes": [{"line": n, "note": "(...)"}], "extra": {"summary": "", "approach": "", '
                    '"experience": "", "exam": "", "conflicts": "", "missing": ""}}',
                    _compose_parts, _compose_validate, _compose_write,
                    lambda lesson, p: _exists("notes.json")(lesson, p) and _exists("extra.json")(lesson, p)),
    "layout": Step("B2b", "layout.md", '[{"line": n, "level": 2, "marker": "+"}, ...]',
                   lambda lesson: [Part(1, 1, HYDROGEN, [_lesson_path(lesson, "units.txt")])],
                   _layout_validate, _write_json_to("layout.json"), _exists("layout.json")),
    "review": Step("B2", "ocr_fix.md", '{"<id>": [{"line": n, "old": "...", "new": "..."}], ...}',
                   lambda lesson: _batch_parts(_lesson_path(lesson, "review", "tasks.json"), _lesson_path(lesson, "review")),
                   _batch_validate(_review_value), _batch_write(_review_dir), _batch_done(_review_dir), vision=True),
    "ink": Step("B4", "read_ink.md", '{"<id>": {"1": "nội dung", ...}, ...}',
                lambda lesson: _batch_parts(common.kho_path("ink", lesson, "tasks.json"), common.kho_path("ink", lesson)),
                _batch_validate(_ink_value), _batch_write(_ink_dir), _batch_done(_ink_dir), vision=True),
}


def build_prompt(step: Step, part: Part) -> str:
    inputs = "\n".join(f"- {p}" for p in part.inputs)
    return (f"Làm theo quy tắc nội dung trong file {os.path.join(PROMPTS, step.prompt_file)} (chỗ nào bảo ghi file "
            f"thì thay bằng in ra). Câu trả lời cuối chỉ gồm MỘT JSON hợp lệ dạng: {step.shape}\n"
            f"Đầu vào (đọc hết):\n{inputs}\n{part.note}").strip()


def _log(lesson: str, rec: dict) -> None:
    path = _lesson_path(lesson, "agy", "log.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(lesson: str, step_name: str, part: int | None = None, model: str | None = None, force: bool = False) -> int:
    step = STEPS[step_name]
    if step.vision and not VISION_OK:
        print(f"Bước {step_name} cần đọc ảnh mà agy chưa đọc được, làm theo luồng cũ")
        return 2
    parts = step.parts(lesson)
    dirs = sorted({_lesson_path(lesson), PROMPTS} | {os.path.dirname(f) for p in parts for f in p.inputs})
    done = 0
    for p in parts:
        if part is not None and p.index != part:
            continue
        if not force and step.done(lesson, p):
            done += 1
            continue
        use = model or p.model
        t = time.time()
        try:
            data = ask_json(build_prompt(step, p), use, dirs, lambda d, p=p: step.validate(d, lesson, p))
        except AgyError as e:
            _log(lesson, {"step": step_name, "part": p.index, "model": use, "seconds": round(time.time() - t),
                          "status": "error", "error": str(e)[:300]})
            print(f"DỪNG {lesson} {step_name} phần {p.index}/{p.total}: {e}")
            return 1
        step.write(lesson, p, data)
        done += 1
        _log(lesson, {"step": step_name, "part": p.index, "model": use, "seconds": round(time.time() - t), "status": "ok"})
        print(f"{lesson} {step_name} phần {p.index}/{p.total} xong ({use}, {round(time.time() - t)}s)")
    # Không ghi progress.json: progress coi mọi khóa là bước đã xong, mà sau agy còn bước áp và kiểm tra.
    # Trạng thái agy nằm trong agy/log.jsonl; bước B chỉ ghi vào sổ khi đã áp và kiểm xong.
    print(f"{lesson} {step_name}: {done}/{len(parts)} phần có kết quả hợp lệ")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson")
    ap.add_argument("step", choices=sorted(STEPS))
    ap.add_argument("--part", type=int)
    ap.add_argument("--model")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(run(a.lesson, a.step, a.part, a.model, a.force))


if __name__ == "__main__":
    main()
