import _path  # noqa: F401
import os
import tempfile
import unittest

import pymupdf

from lib import common
from scripts import a1_inventory, b4_ink

SRC_FIELDS = ["lesson", "code", "pages", "score", "ink_pages"]


def boom(png):
    raise AssertionError("không được OCR trang này")


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = self.t.name
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def ink_pdf(self, name="a.pdf", strokes=1):
        d = pymupdf.open()
        p = d.new_page()
        for i in range(strokes):
            y = 40 + i * 60
            p.add_ink_annot([[(60, y), (90 + 7 * i, y + 20), (120 + 11 * i, y)]])
        d.save(os.path.join(self.root, name))
        d.close()

    def blank_pdf(self, name="s.pdf"):
        d = pymupdf.open()
        d.new_page()
        d.save(os.path.join(self.root, name))
        d.close()

    def setup_data(self, sources, manifest):
        common.write_csv(common.data_path("lesson_sources.csv"), sources, SRC_FIELDS)
        common.write_csv(common.data_path("manifest.csv"), manifest, a1_inventory.FIELDS)

    def ink_case(self, strokes=1, lessons=("L1",)):
        self.ink_pdf(strokes=strokes)
        self.setup_data([{"lesson": l, "code": "N001", "pages": "1", "score": 1, "ink_pages": "1"} for l in lessons],
                        [{"code": "N001", "path": "a.pdf", "kind": "text", "status": "primary"}])

    def answer(self, lesson, tasks, text="chữ tay"):
        for t in tasks:
            common.write_json(common.kho_path("ink", lesson, "results", t["id"] + ".json"),
                              {k: text for k in t["items"]})


class TestTasks(Base):
    def test_sheet_labels_match_items(self):
        self.ink_case(strokes=3)
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=boom)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(sorted(tasks[0]["items"]), ["1", "2", "3"])
        self.assertTrue(os.path.exists(common.kho_path("ink", "L1", tasks[0]["image"])))

    def test_region_outside_page_skipped(self):
        d = pymupdf.open()
        d.new_page().add_ink_annot([[(900, 1200), (950, 1250)]])
        d.save(os.path.join(self.root, "a.pdf"))
        d.close()
        self.setup_data([{"lesson": "L1", "code": "N001", "pages": "1", "score": 1, "ink_pages": "1"}],
                        [{"code": "N001", "path": "a.pdf", "kind": "text", "status": "primary"}])
        self.assertEqual(b4_ink.make_tasks("L1", self.root, conf_engine=boom), [])

    def test_sheet_limit(self):
        self.ink_case(strokes=13)
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=boom)
        self.assertEqual([len(t["items"]) for t in tasks], [12, 1])

    def test_cached_region_not_requeued(self):
        self.ink_case()
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=boom)
        self.answer("L1", tasks)
        b4_ink.merge("L1")
        self.assertEqual(b4_ink.make_tasks("L1", self.root, conf_engine=boom), [])

    def test_region_shared_across_lessons_read_once(self):
        self.ink_case(lessons=("L1", "L2"))
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=boom)
        self.answer("L1", tasks)
        b4_ink.merge("L1")
        self.assertEqual(b4_ink.make_tasks("L2", self.root, conf_engine=boom), [])
        self.assertEqual(b4_ink.merge("L2")["missing"], [])
        self.assertIn("chữ tay", common.read_text(common.page_file("N001", 1, "ink.txt")))

    def test_merge_reports_missing(self):
        self.ink_case(strokes=2)
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=boom)
        common.write_json(common.kho_path("ink", "L1", "results", tasks[0]["id"] + ".json"), {"1": "có"})
        self.assertEqual(b4_ink.merge("L1")["missing"], [tasks[0]["id"] + ":2"])

    def test_string_result_accepted_for_single_item(self):
        self.ink_case()
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=boom)
        common.write_json(common.kho_path("ink", "L1", "results", tasks[0]["id"] + ".json"), "chữ tay")
        self.assertEqual(b4_ink.merge("L1")["missing"], [])

    def test_uncertain_counted(self):
        self.ink_case()
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=boom)
        self.answer("L1", tasks, "liều [?5?] mg")
        self.assertEqual(b4_ink.merge("L1")["uncertain"], 1)

    def scan_case(self):
        self.blank_pdf()
        self.setup_data([{"lesson": "L1", "code": "S001", "pages": "1", "score": 1, "ink_pages": ""}],
                        [{"code": "S001", "path": "s.pdf", "kind": "image", "status": "primary"}])

    def test_scan_page_tesseract_first(self):
        self.scan_case()
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=lambda png: ("chữ in", 91.0))
        self.assertEqual(tasks, [])
        self.assertEqual(common.read_text(common.page_file("S001", 1)), "chữ in")

    def test_low_confidence_page_becomes_task(self):
        self.scan_case()
        tasks = b4_ink.make_tasks("L1", self.root, conf_engine=lambda png: ("mờ", 40.0))
        self.assertEqual(tasks[0]["kind"], "page")
        self.assertFalse(os.path.exists(common.page_file("S001", 1)))

    def test_page_with_text_not_ocred(self):
        self.scan_case()
        common.write_text(common.page_file("S001", 1), "đã có")
        self.assertEqual(b4_ink.make_tasks("L1", self.root, conf_engine=boom), [])


if __name__ == "__main__":
    unittest.main()
