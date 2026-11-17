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

    def test_thinking_off_and_think_tag_stripped(self):
        sent = {}

        def fake_open(req, timeout):
            sent["body"] = json.loads(req.data)
            return FakeResp({"choices": [{"message": {"content": "<think>\n\n</think>\n\nBài 13"}}]})

        with mock.patch("urllib.request.urlopen", fake_open):
            self.assertEqual(vlm.ocr_page(b"x", url="http://x"), "Bài 13")
        self.assertEqual(sent["body"]["chat_template_kwargs"], {"enable_thinking": False})

    def test_half_pipe_and_rule_lines(self):
        page = "Bài 7 ◆ 85\n---\n|Bài 7. THIẾU VITAMIN A\n| quá mức và tập thể dục\n| a | b\n|---|---|"
        self.assertEqual(vlm.clean(page), "Bài 7 ◆ 85\nBài 7. THIẾU VITAMIN A\nquá mức và tập thể dục\n| a | b\n|---|---|")

    def test_loop_retried_then_raises(self):
        calls = []

        def fake_open(req, timeout):
            calls.append(json.loads(req.data)["temperature"])
            return FakeResp({"choices": [{"message": {"content": "| Bảng |\n" + "| " * 200},
                                          "finish_reason": "length"}]})

        with mock.patch("urllib.request.urlopen", fake_open):
            with self.assertRaises(vlm.Degenerate):
                vlm.ocr_page(b"x", url="http://x")
        self.assertEqual(calls, [0, 0.3])

    def test_loop_fixed_on_retry(self):
        answers = iter([{"content": "a " * 10 + "| " * 50, "finish_reason": "stop"},
                        {"content": "Trang đúng", "finish_reason": "stop"}])

        def fake_open(req, timeout):
            a = next(answers)
            return FakeResp({"choices": [{"message": {"content": a["content"]}, "finish_reason": a["finish_reason"]}]})

        with mock.patch("urllib.request.urlopen", fake_open):
            self.assertEqual(vlm.ocr_page(b"x", url="http://x"), "Trang đúng")

    def test_normal_table_not_flagged(self):
        table = "| Loại | A | B |\n|---|---|---|\n" + "\n".join(f"| sữa {i} | {i},5 |  |" for i in range(40))
        self.assertFalse(vlm.degenerate(table, "stop"))

    def test_strip_code_fence(self):
        self.assertEqual(vlm.clean("```text\nabc\n```"), "abc")
        self.assertEqual(vlm.clean("abc"), "abc")

    def test_unwrap_single_cell_rows(self):
        page = "|Bài 3. Nuôi trẻ ♦ 29|\n|+ Bà mẹ nhiễm HSV|\n| Liều | 10 mg |\n|---|---|"
        self.assertEqual(vlm.clean(page), "Bài 3. Nuôi trẻ ♦ 29\n+ Bà mẹ nhiễm HSV\n| Liều | 10 mg |\n|---|---|")

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
