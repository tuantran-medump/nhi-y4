import _path  # noqa: F401
import json
import unittest
from unittest import mock

from lib import vlm


class FakeResp:
    def __init__(self, obj):
        self.data = json.dumps(obj).encode()

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestVlm(unittest.TestCase):
    def test_ocr_sends_image_and_returns_text(self):
        sent = {}

        def fake_open(req, timeout):
            sent["body"] = json.loads(req.data)
            return FakeResp({"choices": [{"message": {"content": "Bài 14\nchữ"}}]})

        with mock.patch("urllib.request.urlopen", fake_open):
            out = vlm.ocr_page(b"\x89PNG", url="http://x/v1/chat/completions")
        self.assertEqual(out, "Bài 14\nchữ")
        parts = sent["body"]["messages"][0]["content"]
        self.assertTrue(parts[0]["image_url"]["url"].startswith("data:image/png;base64,"))
        self.assertEqual(sent["body"]["temperature"], 0)

    def test_strip_code_fence(self):
        self.assertEqual(vlm.clean("```text\nabc\n```"), "abc")
        self.assertEqual(vlm.clean("abc"), "abc")

    def test_server_always_stopped(self):
        proc = mock.Mock()
        proc.poll.return_value = None
        cfg = {"server": "s.exe", "model": "m.gguf", "mmproj": "p.gguf", "args": [], "port": 8080}
        with mock.patch("subprocess.Popen", return_value=proc), \
                mock.patch.object(vlm, "_healthy", return_value=True):
            with self.assertRaises(RuntimeError):
                with vlm.Server(cfg):
                    raise RuntimeError("lỗi giữa chừng")
        proc.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
