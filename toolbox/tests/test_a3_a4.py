import _path  # noqa: F401
import os
import tempfile
import unittest

import pymupdf

from lib import common
from scripts import a3_ocr, a4_pagemap

LESSONS = [
    {"lesson": "G1-B10", "book": "G1", "title": "Thận", "start_printed": "155"},
    {"lesson": "G1-B11", "book": "G1", "title": "NTT", "start_printed": "170"},
]


class Home(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def pages(self, texts):
        for i, t in enumerate(texts, 1):
            common.write_text(common.page_file("G1", i), t)


def even(n):
    return f"{n} ♦ NHI KHOA - Tập 1\n\nNoi dung"


def odd(n):
    return f"Bài 10. Đặc điểm hệ thận ♦ {n}\n\nNoi dung"


class TestOcr(Home):
    def test_resume_skips_done_pages(self):
        pdf = os.path.join(self.t.name, "b.pdf")
        d = pymupdf.open()
        for _ in range(3):
            d.new_page()
        d.save(pdf)
        d.close()
        common.write_text(common.page_file("G1", 2), "da co")
        calls = []

        def engine(png):
            calls.append(1)
            return "moi"

        a3_ocr.ocr_pages(pdf, "G1", engine=engine)
        self.assertEqual(len(calls), 2)
        self.assertEqual(common.read_text(common.page_file("G1", 2)), "da co")
        self.assertEqual(common.read_text(common.page_file("G1", 3)), "moi")

    def test_sample_pages_only(self):
        pdf = os.path.join(self.t.name, "b.pdf")
        d = pymupdf.open()
        for _ in range(3):
            d.new_page()
        d.save(pdf)
        d.close()
        a3_ocr.ocr_pages(pdf, "G1", pages=[2], engine=lambda png: "x")
        self.assertTrue(os.path.exists(common.page_file("G1", 2)))
        self.assertFalse(os.path.exists(common.page_file("G1", 1)))


    def test_redo_keeps_tesseract_copy(self):
        pdf = os.path.join(self.t.name, "b.pdf")
        d = pymupdf.open()
        for _ in range(2):
            d.new_page()
        d.save(pdf)
        d.close()
        common.write_text(common.page_file("G1", 1), "tess cu")
        a3_ocr.ocr_pages(pdf, "G1", engine=lambda png: "vlm moi", redo=True)
        self.assertEqual(common.read_text(common.page_file("G1", 1)), "vlm moi")
        self.assertEqual(common.read_text(common.page_file("G1", 1, "tess.txt")), "tess cu")
        self.assertEqual(common.read_text(common.page_file("G1", 2)), "vlm moi")
        self.assertFalse(os.path.exists(common.page_file("G1", 2, "tess.txt")))

    def test_engine_skip_keeps_old_text(self):
        pdf = os.path.join(self.t.name, "b.pdf")
        d = pymupdf.open()
        d.new_page()
        d.save(pdf)
        d.close()
        common.write_text(common.page_file("G1", 1), "tess cu")
        a3_ocr.ocr_pages(pdf, "G1", engine=lambda png: None, redo=True)
        self.assertEqual(common.read_text(common.page_file("G1", 1)), "tess cu")
        self.assertEqual(common.read_text(common.page_file("G1", 1, "tess.txt")), "tess cu")
        self.assertEqual(common.read_text(common.kho_path("G1", "vlm_failed.txt")).split(), ["1"])

    def test_redo_resumes_after_interrupt(self):
        pdf = os.path.join(self.t.name, "b.pdf")
        d = pymupdf.open()
        d.new_page()
        d.save(pdf)
        d.close()
        common.write_text(common.page_file("G1", 1), "vlm da lam")
        common.write_text(common.page_file("G1", 1, "tess.txt"), "tess cu")
        calls = []
        a3_ocr.ocr_pages(pdf, "G1", engine=lambda png: calls.append(1) or "x", redo=True)
        self.assertEqual(calls, [])
        self.assertEqual(common.read_text(common.page_file("G1", 1)), "vlm da lam")


class TestParse(unittest.TestCase):
    def test_printed_number_from_header(self):
        self.assertEqual(a4_pagemap.parse_printed("120 ♦ NHI KHOA - Tập 1\nabc"), 120)
        self.assertEqual(a4_pagemap.parse_printed("Bài 10. Đặc điểm ... ♦ 157\nabc"), 157)

    def test_number_at_page_bottom(self):
        self.assertEqual(a4_pagemap.parse_printed("Bài 13. ĐẶC ĐIỂM\nnoi dung dai\n\n173\n"), 173)

    def test_unreadable_returns_none(self):
        self.assertIsNone(a4_pagemap.parse_printed("noi dung khong co so trang\nabc"))


class TestMap(Home):
    def test_unreadable_number_uncertain(self):
        self.pages([even(156), "khong doc duoc", even(158)])
        rows, gaps = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual(rows[1]["confidence"], "uncertain")
        self.assertEqual(rows[0]["confidence"], "ok")
        self.assertEqual(gaps, [])

    def test_gap_detected(self):
        self.pages([odd(157), even(160), odd(161)])
        rows, gaps = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual([g["printed_page"] for g in gaps], [158, 159])
        self.assertEqual(gaps[0]["lesson"], "G1-B10")

    def test_out_of_sequence_number_uncertain(self):
        self.pages([even(160), odd(161), even(16), odd(163), even(164)])
        rows, gaps = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual(rows[2]["confidence"], "uncertain")
        self.assertEqual(gaps, [])

    def test_lesson_boundary(self):
        self.pages([odd(169), even(170), odd(171)])
        rows, _ = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual([r["lesson"] for r in rows], ["G1-B10", "G1-B11", "G1-B11"])

    def test_front_matter_has_no_lesson(self):
        self.pages(["Lời nói đầu", "MỤC LỤC", odd(155)])
        rows, _ = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual(rows[0]["lesson"], "")
        self.assertEqual(rows[2]["lesson"], "G1-B10")


if __name__ == "__main__":
    unittest.main()
