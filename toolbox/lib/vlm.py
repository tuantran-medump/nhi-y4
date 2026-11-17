"""Chép chữ trang sách bằng model đọc ảnh chạy tại máy (llama.cpp llama-server).

Cấu hình ở config.json, khóa "vlm": server, model, mmproj, args, port.
Server chỉ sống trong khối `with Server(cfg):` và luôn bị tắt khi ra khỏi khối, kể cả khi lỗi.
"""
import base64
import json
import os
import re
import subprocess
import time
import urllib.request

PROMPT = ("Chép lại toàn bộ chữ trong ảnh trang sách tiếng Việt này, đúng từng chữ và từng dấu, "
          "giữ xuống dòng như trong ảnh. Bảng thì chép từng ô, ngăn bằng dấu |. Không dịch, "
          "không tóm tắt, không thêm lời giải thích, không bỏ sót dòng nào.")


def profile(cfg: dict, name: str | None) -> dict:
    """Cấu hình server theo hồ sơ: "vlm" là mặc định (nhanh), "vlm_profiles"[name] ghi đè từng khóa."""
    base = dict(cfg["vlm"])
    if name:
        base.update(cfg.get("vlm_profiles", {})[name])
    return base


_ONE_CELL = re.compile(r"^\|([^|]*)\|?\s*$")
_RULE = re.compile(r"^\s*-{3,}\s*$")


def clean(text: str) -> str:
    """Bỏ khung ```, dòng kẻ ---, và dấu | bọc dòng chỉ có một ô (Qwen hay coi cả trang là bảng một cột)."""
    m = re.fullmatch(r"\s*```[^\n]*\n(.*?)\n?```\s*", text, re.S)
    text = (m.group(1) if m else text).strip()
    return "\n".join(_ONE_CELL.sub(lambda g: g.group(1).strip(), ln) for ln in text.split("\n") if not _RULE.match(ln))


RETRY_NOTE = (" Ô trống trong bảng thì để trống một lần, tuyệt đối không lặp lại ký tự | hay cùng một cụm chữ "
              "nhiều lần.")
_LOOP = re.compile(r"(?:\|\s*){30,}|(.{4,40}?)\1{15,}", re.S)


class Degenerate(Exception):
    """Model lặp vô hạn hoặc bị cắt vì hết token: không dùng được kết quả trang này."""


def degenerate(text: str, finish_reason: str | None) -> bool:
    return finish_reason == "length" or bool(_LOOP.search(text))


def _ask(png: bytes, url: str, prompt: str, temperature: float, timeout: int) -> tuple[str, str | None]:
    body = {"messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
        {"type": "text", "text": prompt}]}],
        "temperature": temperature, "max_tokens": 4096}
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ch = json.loads(r.read())["choices"][0]
    return ch["message"]["content"], ch.get("finish_reason")


def ocr_page(png: bytes, url: str, timeout: int = 1800) -> str:
    """Chép một trang. Lặp hoặc bị cắt thì hỏi lại một lần; vẫn hỏng thì báo Degenerate."""
    for prompt, temp in ((PROMPT, 0), (PROMPT + RETRY_NOTE, 0.3)):
        text, reason = _ask(png, url, prompt, temp, timeout)
        if not degenerate(text, reason):
            return clean(text)
    raise Degenerate("model lặp hoặc bị cắt cả hai lần")


def _healthy(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            return b'"ok"' in r.read()
    except OSError:
        return False


class Server:
    def __init__(self, cfg: dict, log_path: str | None = None):
        self.cfg = cfg
        self.port = int(cfg.get("port", 8080))
        self.url = f"http://127.0.0.1:{self.port}/v1/chat/completions"
        self.log_path = log_path or os.devnull
        self.proc = None

    def __enter__(self):
        c = self.cfg
        args = [c["server"], "-m", c["model"], "--mmproj", c["mmproj"], *c.get("args", []),
                "--host", "127.0.0.1", "--port", str(self.port)]
        self._log = open(self.log_path, "w", encoding="utf-8")
        self.proc = subprocess.Popen(args, stdout=self._log, stderr=subprocess.STDOUT)
        try:
            for _ in range(300):
                if _healthy(self.port):
                    return self
                if self.proc.poll() is not None:
                    raise RuntimeError(f"llama-server dừng khi khởi động, xem {self.log_path}")
                time.sleep(1)
            raise RuntimeError("llama-server không sẵn sàng sau 300 giây")
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def ocr(self, png: bytes) -> str:
        return ocr_page(png, self.url)

    def __exit__(self, *exc):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if getattr(self, "_log", None):
            self._log.close()
        return False
