import _path  # noqa: F401
import json
import os
import sys
import tempfile
import unittest

from scripts import agy_run

FAKE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_agy.py")


class FakeAgy:
    """Đặt biến môi trường để agy_run gọi fake_agy.py thay cho agy thật."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, "calls.json")
        self._env = {k: os.environ.get(k) for k in ("AGY_CMD", "FAKE_AGY_OUT", "FAKE_AGY_EXIT", "FAKE_AGY_SLEEP", "FAKE_AGY_STATE", "NHI_TOOLBOX_HOME")}
        os.environ["AGY_CMD"] = json.dumps([sys.executable, FAKE])
        os.environ["FAKE_AGY_STATE"] = self.state
        for k in ("FAKE_AGY_OUT", "FAKE_AGY_EXIT", "FAKE_AGY_SLEEP"):
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def outputs(self, *outs):
        os.environ["FAKE_AGY_OUT"] = json.dumps(list(outs), ensure_ascii=False)

    def calls(self):
        return json.load(open(self.state, encoding="utf-8")) if os.path.exists(self.state) else []


class TestExtract(unittest.TestCase):
    def test_extract_json_from_fenced_and_prose(self):
        self.assertEqual(agy_run.extract_json('Đây:\n```json\n{"a": [1]}\n```\nXong'), {"a": [1]})

    def test_extract_json_none_raises(self):
        with self.assertRaises(ValueError):
            agy_run.extract_json("không có")


class TestCall(FakeAgy, unittest.TestCase):
    def test_call_nonzero_exit_raises(self):
        self.outputs('{"a": 1}')
        os.environ["FAKE_AGY_EXIT"] = "3"
        with self.assertRaises(agy_run.AgyError):
            agy_run.call("x", agy_run.HYDROGEN, [self.tmp])

    def test_call_timeout_raises(self):
        self.outputs("{}")
        os.environ["FAKE_AGY_SLEEP"] = "5"
        with self.assertRaises(agy_run.AgyError):
            agy_run.call("x", agy_run.HYDROGEN, [self.tmp], timeout_s=1)

    def test_call_is_read_only_plan_mode_with_prefix(self):
        self.outputs("{}")
        agy_run.call("việc", agy_run.HYDROGEN, [self.tmp])
        call = self.calls()[0]
        self.assertIn("--mode", call["argv"])
        self.assertEqual(call["argv"][call["argv"].index("--mode") + 1], "plan")
        self.assertNotIn("--dangerously-skip-permissions", call["argv"])
        self.assertTrue(call["prompt"].startswith(agy_run.READ_ONLY_PREFIX))

    def test_ask_json_retries_once_then_ok(self):
        self.outputs('{"x": 1}', '{"y": 2}')
        out = agy_run.ask_json("việc", agy_run.HYDROGEN, [self.tmp], lambda d: [] if "y" in d else ["thiếu y"])
        self.assertEqual(out, {"y": 2})
        calls = self.calls()
        self.assertEqual(len(calls), 2)
        self.assertIn("Lần trước sai", calls[1]["prompt"])

    def test_ask_json_fails_twice_raises(self):
        self.outputs("không phải json")
        with self.assertRaises(agy_run.AgyError):
            agy_run.ask_json("việc", agy_run.HYDROGEN, [self.tmp], lambda d: [])
        self.assertEqual(len(self.calls()), 2)


if __name__ == "__main__":
    unittest.main()
