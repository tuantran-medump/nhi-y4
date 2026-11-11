import _path  # noqa: F401
import os
import tempfile
import unittest

import pymupdf

from lib import common
from scripts import b2_review


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = self.t.name
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name
        d = pymupdf.open()
        for _ in range(3):
            d.new_page()
        d.save(os.path.join(self.root, "book.pdf"))
        d.close()
        common.write_csv(common.data_path("lessons.csv"), [{"lesson": "L", "book": "G1"}], ["lesson", "book"])
        common.write_csv(common.data_path("manifest.csv"), [{"code": "G1", "path": "book.pdf"}], ["code", "path"])
        common.write_text(common.kho_path("lessons", "L", "fixed.txt"),
                          "<<p2>>\ndòng một\ndòng hai\n<<p3>>\ndòng ba\n")

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def result(self, task, patch):
        common.write_json(common.kho_path("lessons", "L", "review", "results", task["id"] + ".json"), patch)


class TestTasks(Base):
    def test_one_task_per_page_with_global_lines(self):
        tasks = b2_review.make_tasks("L", self.root)
        self.assertEqual([t["page"] for t in tasks], [2, 3])
        text = common.read_text(common.kho_path("lessons", "L", "review", tasks[1]["text"]))
        self.assertEqual(text, "5\tdòng ba\n")

    def test_page_image_written(self):
        task = b2_review.make_tasks("L", self.root)[0]
        self.assertTrue(os.path.exists(common.kho_path("lessons", "L", "review", task["image"])))

    def test_reviewed_page_not_requeued(self):
        tasks = b2_review.make_tasks("L", self.root)
        self.result(tasks[0], [])
        b2_review.apply("L")
        self.assertEqual([t["page"] for t in b2_review.make_tasks("L", self.root)], [3])


class TestApply(Base):
    def test_patches_applied_and_missing_reported(self):
        tasks = b2_review.make_tasks("L", self.root)
        self.result(tasks[0], [{"line": 2, "old": "một", "new": "1 chữ", "verified": True}])
        report = b2_review.apply("L")
        self.assertEqual(report["missing"], [3])
        self.assertIn("1 chữ", common.read_text(common.kho_path("lessons", "L", "fixed.txt")))

    def test_patch_outside_its_page_rejected(self):
        tasks = b2_review.make_tasks("L", self.root)
        self.result(tasks[0], [{"line": 5, "old": "ba", "new": "x"}])
        with self.assertRaises(ValueError):
            b2_review.apply("L")
        self.assertIn("dòng ba", common.read_text(common.kho_path("lessons", "L", "fixed.txt")))

    def test_digit_guard_still_applies(self):
        tasks = b2_review.make_tasks("L", self.root)
        self.result(tasks[0], [{"line": 2, "old": "một", "new": "1"}])
        with self.assertRaises(ValueError):
            b2_review.apply("L")

    def test_apply_twice_does_not_reapply(self):
        tasks = b2_review.make_tasks("L", self.root)
        self.result(tasks[0], [{"line": 2, "old": "một", "new": "một một"}])
        b2_review.apply("L")
        b2_review.apply("L")
        self.assertIn("dòng một một\n", common.read_text(common.kho_path("lessons", "L", "fixed.txt")))
        self.assertNotIn("một một một", common.read_text(common.kho_path("lessons", "L", "fixed.txt")))


if __name__ == "__main__":
    unittest.main()
