import _path  # noqa: F401
import unittest

from scripts.b2b_layout import apply_layout, split_units, verify_words


class TestUnits(unittest.TestCase):
    def test_wrapped_lines_joined(self):
        self.assertEqual(split_units("Viêm phổi là\nbệnh thường gặp."), ["Viêm phổi là bệnh thường gặp."])

    def test_sentences_split(self):
        self.assertEqual(split_units("Câu một. Câu hai."), ["Câu một.", "Câu hai."])

    def test_abbreviation_not_split(self):
        self.assertEqual(split_units("Do S. pneumoniae gây ra."), ["Do S. pneumoniae gây ra."])

    def test_bullet_starts_new_unit(self):
        self.assertEqual(split_units("Gồm\n- a\n- b"), ["Gồm", "- a", "- b"])

    def test_page_marker_own_unit(self):
        self.assertEqual(split_units("<<p118>>\nCâu."), ["<<p118>>", "Câu."])

    def test_heading_own_unit(self):
        self.assertEqual(split_units("Câu trước.\n2.4. Phân loại\nCâu sau."),
                         ["Câu trước.", "2.4. Phân loại", "Câu sau."])


class TestLayout(unittest.TestCase):
    def test_default_marker(self):
        self.assertEqual(apply_layout(["Câu."], []), "- Câu.")

    def test_markers_levels(self):
        units = ["a", "b", "c", "d", "e"]
        table = [{"line": 2, "level": 2, "marker": "+"}, {"line": 3, "level": 3, "marker": "*"},
                 {"line": 4, "level": 1, "marker": "1."}, {"line": 5, "level": 1, "marker": "I."}]
        self.assertEqual(apply_layout(units, table).split("\n"),
                         ["- a", "  + b", "    * c", "1. d", "I. e"])

    def test_split_list_sentence(self):
        out = apply_layout(["Vi khuẩn gồm: a, b, c."], [{"line": 1, "level": 1, "marker": "-", "split": ["gồm:", ","]}])
        self.assertEqual(out.split("\n"), ["- Vi khuẩn gồm:", "  + a", "  + b", "  + c."])

    def test_book_heading_number_kept(self):
        self.assertEqual(apply_layout(["2.4.1. Theo giải phẫu"], []), "#### 2.4.1. Theo giải phẫu")

    def test_ocr_bullet_replaced(self):
        self.assertEqual(apply_layout(["- Câu."], [{"line": 1, "level": 2, "marker": "+"}]), "  + Câu.")

    def test_same_number_not_doubled(self):
        self.assertEqual(apply_layout(["1. Câu."], [{"line": 1, "level": 1, "marker": "1."}]), "1. Câu.")

    def test_join_prev_across_page(self):
        out = apply_layout(["Câu bị", "<<p2>>", "ngắt."], [{"line": 3, "join_prev": True}])
        self.assertEqual(out.split("\n"), ["- Câu bị ngắt.", "<<p2>>"])

    def test_page_marker_untouched(self):
        self.assertEqual(apply_layout(["<<p1>>"], []), "<<p1>>")


class TestVerify(unittest.TestCase):
    FIXED = "Vi khuẩn gồm: a, b, c. Điều trị 5 ngày."

    def test_verify_passes_when_only_markers_added(self):
        body = "- Vi khuẩn gồm:\n  + a\n  + b\n  + c.\n- Điều trị 5 ngày."
        self.assertEqual(verify_words(self.FIXED, body), [])

    def test_semicolon_after_number_dropped_at_split(self):
        fixed = "Liều: 0,9 µg ở tuổi 1 – 3; 1,2 µg ở tuổi 4 – 8; 1,8 µg."
        body = "- Liều: 0,9 µg ở tuổi 1 – 3\n- 1,2 µg ở tuổi 4 – 8\n- 1,8 µg."
        self.assertEqual(verify_words(fixed, body), [])

    def test_decimal_comma_still_protected(self):
        self.assertTrue(verify_words("Liều 2, 5 mg.", "- Liều 2\n- 5 mg."))

    def test_verify_fails_on_changed_word(self):
        self.assertTrue(verify_words(self.FIXED, "- Vi khuẩn gồm: a, b, c.\n- Điều trị 3 ngày."))

    def test_verify_fails_on_reordered_word(self):
        self.assertTrue(verify_words(self.FIXED, "- Vi khuẩn gồm: b, a, c.\n- Điều trị 5 ngày."))

    def test_verify_fails_on_dropped_word(self):
        self.assertTrue(verify_words(self.FIXED, "- Vi khuẩn gồm: a, b, c."))

    def test_verify_ignores_separator_commas(self):
        self.assertEqual(verify_words("a, b; c", "- a\n+ b\n* c"), [])

    def test_decimal_comma_change_caught(self):
        self.assertTrue(verify_words("liều 10,5 mg", "- liều 105 mg"))

    def test_ignores_page_markers(self):
        self.assertEqual(verify_words("<<p1>>\nCâu.", "<<p1>>\n- Câu."), [])

    def test_heading_verified(self):
        self.assertEqual(verify_words("1. ĐẠI CƯƠNG\nCâu.", "## 1. ĐẠI CƯƠNG\n- Câu."), [])

    def test_ignores_citations_and_notes(self):
        body = "- Điều trị 5 ngày [G1:p128] (Slide BS. A 2024: rút còn 3 ngày [S12:p4])."
        self.assertEqual(verify_words("Điều trị 5 ngày.", body), [])

    def test_book_parenthesis_still_checked(self):
        self.assertTrue(verify_words("Bệnh (cấp) nặng.", "- Bệnh nặng."))


if __name__ == "__main__":
    unittest.main()
