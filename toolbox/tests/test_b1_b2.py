import _path  # noqa: F401
import os
import tempfile
import unittest

from lib import common
from scripts import b1_slice, b2_ocr_fix


class Home(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name
        common.write_csv(common.data_path("lessons.csv"),
                         [{"lesson": "G1-B08", "book": "G1"}, {"lesson": "G1-B09", "book": "G1"}],
                         ["lesson", "book"])
        rows = [(10, 118, "G1-B08", "ok"), (11, 119, "G1-B08", "ok"), (12, "", "G1-B08", "uncertain"),
                (13, 136, "G1-B09", "ok")]
        common.write_csv(common.data_path("pagemap_G1.csv"),
                         [dict(zip(["pdf_page", "printed_page", "lesson", "confidence"], r)) for r in rows],
                         ["pdf_page", "printed_page", "lesson", "confidence"])
        for p in (10, 11, 12, 13):
            common.write_text(common.page_file("G1", p), f"noi dung {p}")

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()


class TestSlice(Home):
    def test_slice_bounds(self):
        text = b1_slice.slice_lesson("G1-B08")
        self.assertIn("noi dung 12", text)
        self.assertNotIn("noi dung 13", text)

    def test_page_markers(self):
        text = b1_slice.slice_lesson("G1-B08")
        self.assertIn("<<p118>>", text)
        self.assertIn("<<pdf12?>>", text)

    def test_written_to_kho(self):
        b1_slice.slice_lesson("G1-B08")
        self.assertTrue(os.path.exists(common.kho_path("lessons", "G1-B08", "raw.txt")))


class TestFix(unittest.TestCase):
    def test_dict_whole_word_only(self):
        text, n = b2_ocr_fix.apply_dict("phồi và phồi2 aphồi", [("phồi", "phổi")])
        self.assertEqual(text, "phổi và phồi2 aphồi")
        self.assertEqual(n, 1)

    def test_patch_applied_on_line(self):
        out = b2_ocr_fix.apply_patch("a b\nc d", [{"line": 2, "old": "c", "new": "x"}])
        self.assertEqual(out, "a b\nx d")

    def test_patch_old_mismatch_raises(self):
        with self.assertRaises(ValueError):
            b2_ocr_fix.apply_patch("a b\nc d", [{"line": 1, "old": "zzz", "new": "x"}])

    def test_patch_line_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            b2_ocr_fix.apply_patch("a", [{"line": 5, "old": "a", "new": "x"}])

    def test_patch_adds_to_dict_when_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            path = os.path.join(t, "d.tsv")
            b2_ocr_fix.apply_patch("phồi", [{"line": 1, "old": "phồi", "new": "phổi", "learn": True}], path)
            b2_ocr_fix.apply_patch("cc", [{"line": 1, "old": "cc", "new": "dd"}], path)
            self.assertEqual(b2_ocr_fix.load_dict(path), [("phồi", "phổi")])

    def test_suspects_flags_garbled_tokens(self):
        lines = [n for n, _ in b2_ocr_fix.suspects("dòng sạch sẽ\nvi3m ph|ổi\n5 ngày 10 mg")]
        self.assertEqual(lines, [2])


if __name__ == "__main__":
    unittest.main()
