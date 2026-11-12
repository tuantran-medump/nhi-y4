import _path  # noqa: F401
import unittest

from scripts import b5_annotate
from scripts.b2b_layout import verify_words


class TestCite(unittest.TestCase):
    def test_fact_line_cited_with_current_pdf_page(self):
        out = b5_annotate.cite_book("<<p10>>\n- Liều 90 mg.\n<<p11>>\n- Sốt 3 ngày.", "G1")
        self.assertEqual(out, "<<p10>>\n- Liều 90 mg [G1:p10].\n<<p11>>\n- Sốt 3 ngày [G1:p11].")

    def test_keyword_line_cited(self):
        out = b5_annotate.cite_book("<<p10>>\n- Chỉ định nhập viện khi thở nhanh", "G1")
        self.assertEqual(out, "<<p10>>\n- Chỉ định nhập viện khi thở nhanh [G1:p10]")

    def test_plain_line_not_cited(self):
        self.assertEqual(b5_annotate.cite_book("<<p1>>\n- Bệnh xơ nang", "G1"), "<<p1>>\n- Bệnh xơ nang")

    def test_heading_not_cited(self):
        self.assertEqual(b5_annotate.cite_book("<<p1>>\n## 1. Liều 5 mg", "G1"), "<<p1>>\n## 1. Liều 5 mg")

    def test_block_not_cited(self):
        text = "<<p1>>\n<<block:t1>>\n| 5 mg |\n<<endblock>>"
        self.assertEqual(b5_annotate.cite_book(text, "G1"), text)

    def test_cited_body_still_verifies(self):
        fixed = "Liều 90 mg."
        self.assertEqual(verify_words(fixed, b5_annotate.cite_book("<<p1>>\n- Liều 90 mg.", "G1")), [])


class TestNotes(unittest.TestCase):
    def test_note_placed_before_final_period(self):
        out = b5_annotate.apply_notes("- Điều trị 5 ngày.", [{"line": 1, "note": "(Slide 2024: 3 ngày [S1:p4])"}])
        self.assertEqual(out, "- Điều trị 5 ngày (Slide 2024: 3 ngày [S1:p4]).")

    def test_note_without_citation_rejected(self):
        with self.assertRaises(ValueError):
            b5_annotate.apply_notes("- A.", [{"line": 1, "note": "(không mã)"}])

    def test_note_on_book_code_rejected(self):
        with self.assertRaises(ValueError):
            b5_annotate.apply_notes("- A.", [{"line": 1, "note": "(sách [G1:p2])"}])

    def test_note_on_page_marker_rejected(self):
        with self.assertRaises(ValueError):
            b5_annotate.apply_notes("<<p1>>", [{"line": 1, "note": "(x [S1:p1])"}])

    def test_noted_body_still_verifies(self):
        body = b5_annotate.apply_notes("- Điều trị 5 ngày.", [{"line": 1, "note": "(Slide 2024: 3 ngày [S1:p4])"}])
        self.assertEqual(verify_words("Điều trị 5 ngày.", body), [])


class TestConflictStar(unittest.TestCase):
    NOTE = {"line": 1, "note": "(Slide 2024: 3 ngày [S1:p4])", "resolve": "Kết luận theo AAP 2011: 5 ngày [E1:p2]"}

    def test_conflict_note_goes_on_star_lines_below_item(self):
        out = b5_annotate.apply_notes("  + Điều trị 5 ngày.\n- Tiếp.", [self.NOTE])
        self.assertEqual(out.split("\n"), ["  + Điều trị 5 ngày.",
                                           "      ⭐ (Slide 2024: 3 ngày [S1:p4])",
                                           "      ⭐ Kết luận theo AAP 2011: 5 ngày [E1:p2]",
                                           "- Tiếp."])

    def test_star_lines_keep_later_line_numbers(self):
        notes = [self.NOTE, {"line": 2, "note": "(Ghi chú lớp: x [S1:p1])"}]
        out = b5_annotate.apply_notes("- A.\n- B.", notes).split("\n")
        self.assertEqual(out[-1], "- B (Ghi chú lớp: x [S1:p1]).")

    def test_other_notes_on_conflict_line_also_go_on_star_lines(self):
        other = {"line": 1, "note": "(Ghi chú lớp: x [S2:p1])"}
        out = b5_annotate.apply_notes("- Điều trị 5 ngày.", [self.NOTE, other]).split("\n")
        self.assertEqual(out, ["- Điều trị 5 ngày.",
                               "    ⭐ (Slide 2024: 3 ngày [S1:p4])",
                               "    ⭐ (Ghi chú lớp: x [S2:p1])",
                               "    ⭐ Kết luận theo AAP 2011: 5 ngày [E1:p2]"])

    def test_resolve_needs_label_and_source(self):
        for bad in ("5 ngày [E1:p2]", "Kết luận theo AAP 2011: 5 ngày"):
            with self.assertRaises(ValueError):
                b5_annotate.apply_notes("- A.", [{**self.NOTE, "resolve": bad}])

    def test_unconfirmed_resolve_allowed_without_source(self):
        note = {**self.NOTE, "resolve": "Kết luận: Chưa thấy có nguồn hiệp hội/guideline xác nhận"}
        self.assertIn("⭐ Kết luận: Chưa thấy", b5_annotate.apply_notes("- A.", [note]))

    def test_star_body_still_verifies(self):
        body = b5_annotate.apply_notes("- Điều trị 5 ngày.", [self.NOTE])
        self.assertEqual(verify_words("Điều trị 5 ngày.", body), [])


if __name__ == "__main__":
    unittest.main()
