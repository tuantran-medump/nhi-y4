import _path  # noqa: F401
import unittest

from scripts import b7_render as r


class TestTidy(unittest.TestCase):
    def test_citation_moved_after_final_period(self):
        self.assertEqual(r.tidy_citations("Liều 90 mg [G1:p10]."), "Liều 90 mg. [G1:p10]")

    def test_mid_sentence_citation_moved_to_sentence_end(self):
        self.assertEqual(r.tidy_citations("Viêm phổi nặng [G1:p129]: nhiệt độ cao."),
                         "Viêm phổi nặng: nhiệt độ cao. [G1:p129]")

    def test_each_sentence_keeps_its_own(self):
        self.assertEqual(r.tidy_citations("Câu một [S1:p1]. Câu hai [S2:p2]."),
                         "Câu một. [S1:p1] Câu hai. [S2:p2]")

    def test_pages_of_same_source_merged(self):
        self.assertEqual(r.tidy_citations("Câu [S1:p56][S1:p53]."), "Câu. [S1:p53,p56]")

    def test_contiguous_pages_become_range(self):
        self.assertEqual(r.tidy_citations("Câu [S1:p61][S1:p62][S1:p63][S1:p67]."), "Câu. [S1:p61-63,p67]")

    def test_existing_range_expanded_and_merged(self):
        self.assertEqual(r.tidy_citations("Câu [S1:p61-63][S1:p64]."), "Câu. [S1:p61-64]")

    def test_different_sources_kept(self):
        self.assertEqual(r.tidy_citations("Câu [S1:p1][N2:p3]."), "Câu. [S1:p1][N2:p3]")

    def test_note_citation_stays_inside_parenthesis(self):
        self.assertEqual(r.tidy_citations("Điều trị [G1:p9] (Slide: 3 ngày [S1:p4])."),
                         "Điều trị (Slide: 3 ngày [S1:p4]). [G1:p9]")

    def test_merged_inside_note(self):
        self.assertEqual(r.tidy_citations("A (ghi chú [S1:p4][S1:p5])."), "A (ghi chú [S1:p4-5]).")

    def test_species_abbreviation_not_sentence_end(self):
        self.assertEqual(r.tidy_citations("Do S. pneumoniae [G1:p1] gây ra."), "Do S. pneumoniae gây ra. [G1:p1]")

    def test_no_period_line(self):
        self.assertEqual(r.tidy_citations("Thở nhanh [G1:p1]"), "Thở nhanh [G1:p1]")


class TestStyle(unittest.TestCase):
    def test_citation_badge_book(self):
        html = r.md_to_html("- Câu. [G1:p10]", {})
        self.assertIn('<span class="cite book">G1 p10</span>', html)

    def test_citation_badge_reference_with_page_list(self):
        html = r.md_to_html("- Câu. [S12:p53,p56,p61-67]", {})
        self.assertIn('<span class="cite ref">S12 p53, p56, p61-67</span>', html)

    def test_badge_linked_when_url(self):
        html = r.md_to_html("- Câu. [S12:p4]", {"S12": "https://d/x"})
        self.assertIn('<a class="cite-link" href="https://d/x"><span class="cite ref">S12 p4</span></a>', html)

    def test_table_caption_italic_not_bullet(self):
        html = r.md_to_html("- Bảng 8.1. Nguyên nhân theo tuổi [G1:p128]", {})
        self.assertIn('<p class="caption">', html)
        self.assertNotIn("<li", html)

    def test_figure_caption_italic(self):
        self.assertIn('<p class="caption">', r.md_to_html("Hình 8.2. Tổn thương phổi", {}))

    def test_bare_caption_joined_with_next_line(self):
        html = r.md_to_html("- Bảng 8.5. [G1:p138]\n- Điều trị ngoại trú theo kinh nghiệm", {})
        self.assertEqual(html.count('class="caption"'), 1)
        self.assertNotIn("<li", html)
        self.assertIn("Điều trị ngoại trú theo kinh nghiệm", html)

    def test_sentence_mentioning_table_stays_list(self):
        self.assertIn("<li", r.md_to_html("- Xem Bảng 8.1 để chọn thuốc.", {}))

    def test_note_styled(self):
        self.assertIn('<span class="note">', r.md_to_html("- Câu (Slide: 3 ngày [S1:p4]).", {}))

    def test_note_author_bold(self):
        html = r.md_to_html("- Câu (Giảng viên: 3 ngày [S1:p4]).", {})
        self.assertIn('<span class="note">(<b>Giảng viên:</b> 3 ngày', html)

    def test_note_named_doctor_bold(self):
        self.assertIn("<b>Slide BS Nguyễn Thanh, 2017:</b>",
                      r.md_to_html("- Câu (Slide BS Nguyễn Thanh, 2017: x [S1:p4]).", {}))

    def test_note_author_with_year_bold(self):
        self.assertIn("<b>Simel 2009:</b>", r.md_to_html("- Câu (Simel 2009: x [S1:p4]).", {}))

    def test_note_content_colon_not_bold(self):
        self.assertNotIn("<b>", r.md_to_html("- Câu (Phân biệt viêm phổi không sốt: x [S1:p4]).", {}))

    def test_note_without_author_not_bold(self):
        self.assertNotIn("<b>", r.md_to_html("- Câu (nội dung thêm [S1:p4]).", {}))

    def test_conflict_labels_bold(self):
        html = r.md_to_html("- Sách: a [G1:p1]\n- Nguồn: b [S1:p1]", {})
        self.assertIn("<b>Sách:</b>", html)
        self.assertIn("<b>Nguồn:</b>", html)

    def test_conflict_ruling_bold_on_cream(self):
        html = r.md_to_html("- Kết luận theo PIDS/IDSA 2011: nội dung [E2:p1]", {})
        self.assertIn('<span class="note resolve"><b>Kết luận theo PIDS/IDSA 2011:</b>', html)

    def test_book_parenthesis_not_styled(self):
        self.assertNotIn('class="note"', r.md_to_html("- Bệnh (cấp) nặng.", {}))

    def test_handwriting_box(self):
        html = r.md_to_html("> ✍ Ghi chú tay: nội dung", {})
        self.assertIn('class="box"', html)

    def test_bullet_glyphs(self):
        html = r.md_to_html("- a\n  + b\n    * c", {})
        self.assertIn('data-m="•"', html)
        self.assertIn('data-m="◦"', html)
        self.assertIn('data-m="▪"', html)


if __name__ == "__main__":
    unittest.main()
