import _path  # noqa: F401
import unittest
from unittest import mock

from scripts import a3_ocr

CFG = {"tesseract": "t.exe", "tessdata_dir": "D:/best", "ocr_lang": "vie"}


class TestCommand(unittest.TestCase):
    def run_cmd(self, cfg):
        done = mock.Mock(stdout=b"x")
        with mock.patch.object(a3_ocr.common, "load_config", return_value=cfg), \
                mock.patch.object(a3_ocr.subprocess, "run", return_value=done) as run:
            a3_ocr.tesseract_page(b"png")
        return run.call_args[0][0]

    def test_uses_configured_model_and_language(self):
        cmd = self.run_cmd(CFG)
        self.assertEqual(cmd[cmd.index("--tessdata-dir") + 1], "D:/best")
        self.assertEqual(cmd[cmd.index("-l") + 1], "vie")

    def test_defaults_without_config(self):
        cmd = self.run_cmd({"tesseract": "t.exe"})
        self.assertNotIn("--tessdata-dir", cmd)
        self.assertEqual(cmd[cmd.index("-l") + 1], "vie+eng")


if __name__ == "__main__":
    unittest.main()
