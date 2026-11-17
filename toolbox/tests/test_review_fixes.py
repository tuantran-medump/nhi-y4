"""Test tái hiện các lỗi reviewer độc lập đã tìm ra."""
import _path  # noqa: F401
import json
import os
import tempfile
import unittest

import pymupdf

from lib import common
from scripts import a1_inventory, a2_dedupe, a3_ocr, a4_pagemap, a5_extract, a6_assign, b1_slice, b2_ocr_fix, b3_novel, b7_render, check_lesson
from scripts.b2b_layout import apply_layout, split_units, verify_words

LESSONS = [{"lesson": "G1-B10", "book": "G1", "title": "T", "start_printed": "155"}]
MAP_FIELDS = ["pdf_page", "printed_page", "lesson", "confidence"]


class Home(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = self.t.name
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def numbered(self, numbers):
        for i, n in enumerate(numbers, 1):
            common.write_text(common.page_file("G1", i), f"{n} ♦ NHI KHOA - Tập 1\nNoi dung")

    def pdf(self, name, text):
        d = pymupdf.open()
        d.new_page().insert_textbox(pymupdf.Rect(50, 50, 500, 700), text)
        d.save(os.path.join(self.root, name))
        d.close()


class TestPageMap(Home):
    def test_duplicate_scan_page_does_not_break_chain(self):
        self.numbered([157, 158, 158, 159, 160])
        rows, gaps = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual([r["confidence"] for r in rows], ["ok", "ok", "duplicate", "ok", "ok"])
        self.assertEqual(gaps, [])

    def test_real_gap_found_after_duplicate(self):
        self.numbered([157, 158, 158, 159, 160, 162, 163])
        _, gaps = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual([g["printed_page"] for g in gaps], [161])

    def test_lesson_title_page_without_number(self):
        lessons = [{"lesson": "G1-B06", "book": "G1", "title": "A", "start_printed": "83"},
                   {"lesson": "G1-B07", "book": "G1", "title": "B", "start_printed": "105"}]
        self.numbered([102, 103])
        common.write_text(common.page_file("G1", 3), "Bài 7. VIÊM TIỂU PHẾ QUẢN CẤP\nTS.BS. A\nMỤC TIÊU HỌC TẬP\nCâu.")
        common.write_text(common.page_file("G1", 4), "106 ♦ NHI KHOA - Tập 1\nNoi dung")
        rows, gaps = a4_pagemap.build_map("G1", lessons)
        self.assertEqual((rows[2]["lesson"], rows[2]["printed_page"], rows[2]["confidence"]), ("G1-B07", 105, "ok"))
        self.assertEqual([g["printed_page"] for g in gaps], [104])

    def test_manual_override_applied(self):
        self.numbered([157, 158, 159])
        common.write_csv(common.data_path("pagemap_overrides.csv"),
                         [{"book": "G1", "pdf_page": "3", "printed_page": "170", "lesson": "G1-B11"}],
                         ["book", "pdf_page", "printed_page", "lesson"])
        lessons = LESSONS + [{"lesson": "G1-B11", "book": "G1", "title": "N", "start_printed": "170"}]
        rows, _ = a4_pagemap.build_map("G1", lessons)
        self.assertEqual((rows[2]["lesson"], rows[2]["printed_page"], rows[2]["confidence"]), ("G1-B11", 170, "ok"))

    def test_misread_last_page_uncertain(self):
        self.numbered([156, 157, 158, 162])
        rows, gaps = a4_pagemap.build_map("G1", LESSONS)
        self.assertEqual(rows[-1]["confidence"], "uncertain")
        self.assertEqual(gaps, [])


class TestSlice(Home):
    def setup_map(self, rows):
        common.write_csv(common.data_path("lessons.csv"), [{"lesson": "L", "book": "G1"}], ["lesson", "book"])
        common.write_csv(common.data_path("pagemap_G1.csv"), [dict(zip(MAP_FIELDS, r)) for r in rows], MAP_FIELDS)

    def test_duplicate_page_skipped(self):
        self.setup_map([(1, 10, "L", "ok"), (2, 10, "L", "duplicate")])
        common.write_text(common.page_file("G1", 1), "mot")
        common.write_text(common.page_file("G1", 2), "hai")
        self.assertNotIn("hai", b1_slice.slice_lesson("L"))

    def test_headers_and_watermark_removed(self):
        self.setup_map([(1, 123, "L", "ok")])
        common.write_text(common.page_file("G1", 1),
                          "Bài 8. Viêm phổi ♦ 123\nĐiều trị trong 5 ngày.\nĐược quét bằng CamScanner\n")
        text = b1_slice.slice_lesson("L")
        self.assertIn("Điều trị trong 5 ngày.", text)
        self.assertNotIn("CamScanner", text)
        self.assertNotIn("♦", text)

    def test_running_header_lower_on_page_removed(self):
        self.setup_map([(1, 130, "L", "ok")])
        common.write_text(common.page_file("G1", 1), "Câu một.\nCâu hai.\nCâu ba.\nCâu bốn.\n130 ®$ NHI KHOA - Tập í\nCâu năm.\n")
        text = b1_slice.slice_lesson("L")
        self.assertNotIn("NHI KHOA", text)
        self.assertIn("Câu năm.", text)

    def test_garbled_running_header_removed(self):
        self.setup_map([(1, 108, "L", "ok")])
        common.write_text(common.page_file("G1", 1), "Câu một.\n1446 $ NHI KHOA - Tập 1\nCâu hai.\n\\O& © NHI KHOA - Tập 1\nBài9.Hentrẻem ® 3141\nCâu ba.\n")
        text = b1_slice.slice_lesson("L")
        self.assertNotIn("NHI KHOA", text)
        self.assertNotIn("®", text)
        self.assertIn("Câu ba.", text)

    def test_bottom_page_number_removed(self):
        self.setup_map([(1, 173, "L", "ok")])
        common.write_text(common.page_file("G1", 1), "Bài 13. ĐẶC ĐIỂM\nCâu.\n\n173\n")
        text = b1_slice.slice_lesson("L")
        self.assertIn("Bài 13. ĐẶC ĐIỂM", text)
        self.assertNotIn("173", text)


class TestNovel(unittest.TestCase):
    BOOK = ("Điều trị bằng amoxicillin uống liều 90 mg/kg chia hai lần trong 5 ngày cho trẻ viêm phổi nhẹ. "
            "Suy dinh dưỡng khi cân nặng theo tuổi dưới -3 SD so với quần thể tham chiếu của WHO. "
            "Trẻ dưới 2 tuổi dùng 5 ngày còn trẻ trên 2 tuổi dùng 10 ngày theo phác đồ.")

    def kept(self, sentence):
        return len(b3_novel.novel_sentences(self.BOOK, {1: sentence})) == 1

    def test_compound_unit_kept(self):
        self.assertTrue(self.kept("Điều trị bằng amoxicillin uống liều 90 mcg/kg chia hai lần trong 5 ngày cho trẻ viêm phổi nhẹ."))

    def test_word_number_kept(self):
        self.assertTrue(self.kept("Điều trị bằng amoxicillin uống liều 90 mg/kg chia ba lần trong 5 ngày cho trẻ viêm phổi nhẹ."))

    def test_drug_name_kept(self):
        self.assertTrue(self.kept("Điều trị bằng azithromycin uống liều 90 mg/kg chia hai lần trong 5 ngày cho trẻ viêm phổi nhẹ."))

    def test_route_kept(self):
        self.assertTrue(self.kept("Điều trị bằng amoxicillin tiêm liều 90 mg/kg chia hai lần trong 5 ngày cho trẻ viêm phổi nhẹ."))

    def test_sign_kept(self):
        self.assertTrue(self.kept("Suy dinh dưỡng khi cân nặng theo tuổi dưới +3 SD so với quần thể tham chiếu của WHO."))

    def test_swapped_values_kept(self):
        self.assertTrue(self.kept("Trẻ dưới 2 tuổi dùng 10 ngày còn trẻ trên 2 tuổi dùng 5 ngày theo phác đồ."))


class TestAssign(Home):
    def test_textbook_guideline_assigned(self):
        self.pdf("kdigo.pdf", "x")
        common.write_text(common.page_file("R001", 1), "HCTH ở trẻ em")
        row = {"code": "R001", "path": "kdigo.pdf", "kind": "text", "specialty": "", "status": "primary", "pages": "1"}
        kw = [{"lesson": "G1-B13", "keywords": "HCTH", "folder_hint": "Thận niệu"}]
        self.assertEqual([r["lesson"] for r in a6_assign.assign([row], kw, self.root)], ["G1-B13"])

    def test_low_confidence_ocr_used_for_matching(self):
        self.pdf("a.pdf", "x")
        common.write_text(common.page_file("N001", 1, "lowocr.txt"), "viêm phổi")
        row = {"code": "N001", "path": "a.pdf", "kind": "image", "specialty": "Hô hấp", "status": "primary", "pages": "1"}
        kw = [{"lesson": "G1-B08", "keywords": "viêm phổi", "folder_hint": "Hô hấp"}]
        self.assertEqual(a6_assign.assign([row], kw, self.root)[0]["pages"], "1")

    def test_every_book_lesson_has_keywords(self):
        lessons = common.read_csv(os.path.join(common.TOOLBOX, "data", "lessons.csv"))
        kw = {r["lesson"] for r in common.read_csv(os.path.join(common.TOOLBOX, "data", "topic_keywords.csv"))}
        self.assertEqual([r["lesson"] for r in lessons if r["lesson"] not in kw], [])


class TestScans(Home):
    def row(self):
        return {"code": "N001", "path": "a.pdf", "kind": "image", "status": "primary"}

    def test_scan_high_confidence_saved(self):
        self.pdf("a.pdf", "")
        a3_ocr.ocr_scans([self.row()], self.root, engine=lambda png: ("chữ", 90.0))
        self.assertEqual(common.read_text(common.page_file("N001", 1)), "chữ")

    def test_scan_low_confidence_kept_apart(self):
        self.pdf("a.pdf", "")
        a3_ocr.ocr_scans([self.row()], self.root, engine=lambda png: ("mờ", 30.0))
        self.assertFalse(os.path.exists(common.page_file("N001", 1)))
        self.assertEqual(common.read_text(common.page_file("N001", 1, "lowocr.txt")), "mờ")


class TestVerify(unittest.TestCase):
    def test_sign_at_line_start_kept(self):
        body = apply_layout(["- 3 SD"], [{"line": 1, "level": 2, "marker": "+"}])
        self.assertEqual(verify_words("- 3 SD", body), [])
        self.assertTrue(verify_words("- 3 SD", "  + 3 SD"))

    def test_list_number_change_caught(self):
        self.assertTrue(verify_words("1. Câu", "2. Câu"))

    def test_heading_number_change_caught(self):
        self.assertTrue(verify_words("1. ĐẠI CƯƠNG", "## 7. ĐẠI CƯƠNG"))

    def test_added_list_number_allowed(self):
        self.assertEqual(verify_words("Câu một", "1. Câu một"), [])

    def test_species_initial_change_caught(self):
        self.assertTrue(verify_words("C. difficile gây bệnh", "- V. difficile gây bệnh"))

    def test_spaced_decimal_change_caught(self):
        self.assertTrue(verify_words("liều 2, 5 mg", "- liều 2 5 mg"))

    def test_fake_page_marker_not_ignored(self):
        self.assertTrue(verify_words("a", "<<bịa đặt>>\n- a"))

    def test_block_excluded_from_word_check(self):
        fixed = "Câu.\n<<block:t1>>\nA B 1 2\n<<endblock>>\nSau."
        body = "- Câu.\n<<block:t1>>\n| A | B |\n|---|---|\n| 1 | 2 |\n<<endblock>>\n- Sau."
        self.assertEqual(verify_words(fixed, body), [])

    def test_block_is_one_unit(self):
        self.assertEqual(split_units("Câu.\n<<block:t1>>\nA B\n<<endblock>>\nSau."), ["Câu.", "<<block:t1>>", "Sau."])


class TestOcrGuard(unittest.TestCase):
    def test_digit_change_requires_verified(self):
        with self.assertRaises(ValueError):
            b2_ocr_fix.apply_patch("5OO mg", [{"line": 1, "old": "5OO", "new": "300"}])

    def test_verified_digit_change_allowed(self):
        out = b2_ocr_fix.apply_patch("5OO mg", [{"line": 1, "old": "5OO", "new": "500", "verified": True}])
        self.assertEqual(out, "500 mg")

    def test_dict_never_learns_digits(self):
        with tempfile.TemporaryDirectory() as t:
            path = os.path.join(t, "d.tsv")
            b2_ocr_fix.apply_patch("5", [{"line": 1, "old": "5", "new": "3", "learn": True, "verified": True}], path)
            self.assertEqual(b2_ocr_fix.load_dict(path), [])

    def test_dict_skips_digit_entries(self):
        self.assertEqual(b2_ocr_fix.apply_dict("5 ngày", [("5", "3")]), ("5 ngày", 0))

    def test_suspects_flags_digit_lookalikes(self):
        text = "5OO mg\nl0 mg\n1O mg\nO,5 mg\n10 mg sạch"
        self.assertEqual([n for n, _ in b2_ocr_fix.suspects(text)], [1, 2, 3, 4])


class TestCheckBlocks(Home):
    def setup_lesson(self, fixed, body):
        common.write_csv(common.data_path("lessons.csv"), [{"lesson": "L", "book": "G1", "title": "T"}],
                         ["lesson", "book", "title"])
        common.write_csv(common.data_path("manifest.csv"), [{"code": "G1", "path": "a"}], ["code", "path"])
        common.write_text(common.kho_path("lessons", "L", "fixed.txt"), fixed)
        common.write_text(common.kho_path("lessons", "L", "body.md"), body)
        common.write_json(common.kho_path("lessons", "L", "extra.json"),
                          {"summary": "s", "approach": "", "experience": "", "exam": "", "conflicts": ""})

    def rules(self):
        return [i["rule"] for i in check_lesson.check("L")]

    def test_table_block_passes(self):
        self.setup_lesson("<<block:t1>>\nLiều 90 mg\n<<endblock>>", "<<block:t1>>\n| Liều | 90 mg |\n<<endblock>>")
        self.assertEqual(self.rules(), [])

    def test_decimal_separator_ignored_in_block(self):
        self.setup_lesson("<<block:t1>>\n<2.0 ua\n<<endblock>>", "<<block:t1>>\n| ≤ 2,0 µg |\n<<endblock>>")
        self.assertEqual(self.rules(), [])

    def test_figure_block_numbers_not_checked(self):
        self.setup_lesson("<<block:p0088f>>\nrác 12 34\n<<endblock>>", "<<block:p0088f>>\n![Hình](fig/p0088f.png)\n<<endblock>>")
        self.assertEqual(self.rules(), [])

    def test_subscript_digits_count_as_numbers(self):
        self.setup_lesson("<<block:t1>>\nthiếu B12, B6\n<<endblock>>", "<<block:t1>>\n| thiếu B₁₂, B₆ |\n<<endblock>>")
        self.assertEqual(self.rules(), [])

    def test_block_number_lost_caught(self):
        self.setup_lesson("<<block:t1>>\nLiều 90 mg\n<<endblock>>", "<<block:t1>>\n| Liều | 50 mg |\n<<endblock>>")
        self.assertIn("block_number", self.rules())

    def test_unfilled_block_caught(self):
        self.setup_lesson("<<block:t1>>\nA\n<<endblock>>", "<<block:t1>>")
        self.assertIn("unfilled_block", self.rules())


class TestDedupe(Home):
    def test_updated_dose_not_marked_duplicate(self):
        base = " ".join(f"tu{i}" for i in range(300))
        self.pdf("a.pdf", base + " lieu 50 mg")
        self.pdf("b.pdf", base + " lieu 90 mg")
        rows = a2_dedupe.mark(a1_inventory.build(self.root), self.root)
        self.assertEqual([r["status"] for r in rows], ["primary", "primary"])


class TestMissingText(Home):
    def test_uncertain_gap_not_listed_as_exact(self):
        common.write_csv(common.data_path("gaps.csv"),
                         [{"book": "G1", "printed_page": str(p), "lesson": "L", "note": "thiếu 1 trang trong khoảng này"}
                          for p in (2, 3, 4)], ["book", "printed_page", "lesson", "note"])
        common.write_text(common.kho_path("lessons", "L", "body.md"), "- a\n")
        common.write_json(common.kho_path("lessons", "L", "extra.json"), {"summary": "s"})
        md = b7_render.assemble({"lesson": "L", "book": "G1", "title": "T", "society": ""})
        self.assertIn("2-4", md)
        self.assertIn("thiếu 1 trang", md)
        self.assertNotIn("2, 3, 4", md)


class TestBadFiles(Home):
    def test_corrupt_image_needs_manual(self):
        with open(os.path.join(self.root, "a.png"), "wb") as f:
            f.write(b"not an image")
        self.assertEqual(a1_inventory.classify(os.path.join(self.root, "a.png"))[0], "needs_manual")

    def test_corrupt_docx_saved_as_needs_manual(self):
        with open(os.path.join(self.root, "a.docx"), "wb") as f:
            f.write(b"not a zip")
        rows = [{"code": "N001", "path": "a.docx", "kind": "office", "status": "primary"}]
        a5_extract.run(rows, self.root)
        self.assertEqual(rows[0]["kind"], "needs_manual")


if __name__ == "__main__":
    unittest.main()


class TestBlockWrapGuard(unittest.TestCase):
    def test_block_name_digits_not_a_digit_change(self):
        out = b2_ocr_fix.apply_patch("Sơ sinh", [{"line": 1, "old": "Sơ sinh", "new": "<<block:t128a>>\nSơ sinh"}])
        self.assertEqual(out, "<<block:t128a>>\nSơ sinh")
