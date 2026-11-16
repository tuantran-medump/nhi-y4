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


def clean(text: str) -> str:
    m = re.fullmatch(r"\s*```[^\n]*\n(.*?)\n?```\s*", text, re.S)
    return (m.group(1) if m else text).strip()


def ocr_page(png: bytes, url: str, timeout: int = 1800) -> str:
    body = {"messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
        {"type": "text", "text": PROMPT}]}],
        "temperature": 0, "max_tokens": 4096}
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return clean(json.loads(r.read())["choices"][0]["message"]["content"])


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
