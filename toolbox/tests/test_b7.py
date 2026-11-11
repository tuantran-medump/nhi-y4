import _path  # noqa: F401
import os
import re
import tempfile
import unittest

from lib import common
from scripts import b7_render, progress


class TestHtml(unittest.TestCase):
    def test_heading(self):
        self.assertIn('<h2 id="h1">1. ĐẠI CƯƠNG</h2>', b7_render.md_to_html("## 1. ĐẠI CƯƠNG", {}))

    def test_nested_lists(self):
        html = b7_render.md_to_html("- a\n  + b\n    * c\n- d", {})
        self.assertLess(html.index("a"), html.index("b"))
        self.assertEqual(html.count("<ul"), 3)
        self.assertEqual(html.count("</ul>"), 3)
        self.assertIn('class="m-plus"', html)
        self.assertIn('class="m-star"', html)

    def test_numbered_marker_kept_verbatim(self):
        html = b7_render.md_to_html("1. một\nI. hai", {})
        self.assertIn('data-m="1."', html)
        self.assertIn('data-m="I."', html)

    def test_table(self):
        html = b7_render.md_to_html("| A | B |\n|---|---|\n| 1 | 2 |", {})
        self.assertIn("<th>A</th>", html)
        self.assertIn("<td>2</td>", html)

    def test_image(self):
        self.assertIn('<img src="h.png" alt="Hình 1">', b7_render.md_to_html("![Hình 1](h.png)", {}))

    def test_citation_linked_when_url(self):
        html = b7_render.md_to_html("- Câu [S12:p4]", {"S12": "https://drive/x"})
        self.assertIn('href="https://drive/x"', html)

    def test_citation_plain_when_no_url(self):
        html = b7_render.md_to_html("- Câu [S12:p4]", {})
        self.assertNotIn("<a ", html)
        self.assertIn("S12 p4", html)

    def test_page_marker_hidden(self):
        self.assertNotIn("p118", b7_render.md_to_html("<<p118>>\n- Câu", {}))

    def test_html_escaped(self):
        self.assertIn("&lt; 5", b7_render.md_to_html("- tuổi < 5", {}))

    def test_box(self):
        self.assertIn('class="box"', b7_render.md_to_html("> Lưu ý", {}))


class TestNavAndCrop(unittest.TestCase):
    def test_nav_lists_main_headings(self):
        nav = b7_render._nav(b7_render.md_to_html("# Tên\n## 1. Đại cương\n### 1.1. Dịch tễ", {}))
        self.assertIn("1. Đại cương", nav)
        self.assertIn("1.1. Dịch tễ", nav)
        self.assertNotIn("Tên", nav)

    def test_long_nav_uses_two_columns(self):
        short = b7_render._nav(b7_render.md_to_html("## A\n## B", {}))
        long_md = "\n".join(f"## Mục {i}" for i in range(40))
        self.assertNotIn('class="long"', short)
        self.assertIn('<nav class="long">', b7_render._nav(b7_render.md_to_html(long_md, {})))

    def test_crop_figure_size(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as t:
            src = os.path.join(t, "a.pdf")
            d = pymupdf.open()
            d.new_page()
            d.save(src)
            d.close()
            out = os.path.join(t, "o", "h.png")
            b7_render.crop_figure(src, 1, (0, 0, 72, 36), out, dpi=100)
            pix = pymupdf.Pixmap(out)
            self.assertEqual((pix.width, pix.height), (100, 50))


class TestConfig(unittest.TestCase):
    def test_config_loads_with_required_keys(self):
        cfg = common.load_config()
        for key in ("source_root", "output_root", "tesseract", "edge"):
            self.assertTrue(cfg[key])


class TestTemplate(unittest.TestCase):
    def test_template_sections_order(self):
        t = common.read_text(os.path.join(common.TOOLBOX, "templates", "lesson.md"))
        order = ["Tóm tắt", "Phần A", "{{body}}", "Phần B", "Tiếp cận và biện luận", "Kinh nghiệm lâm sàng",
                 "Câu hỏi thi", "Mâu thuẫn nguồn", "Cần bổ sung", "Danh mục nguồn"]
        pos = [t.index(s) for s in order]
        self.assertEqual(pos, sorted(pos))


class TestAssemble(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def test_label_outside_textbook(self):
        common.write_text(common.kho_path("lessons", "X-02", "body.md"), "- a\n")
        common.write_json(common.kho_path("lessons", "X-02", "extra.json"), {"summary": "tt"})
        md = b7_render.assemble({"lesson": "X-02", "book": "", "title": "Khò khè", "society": ""})
        self.assertIn("Ngoài giáo trình", md)

    def test_empty_section_says_not_in_source(self):
        common.write_text(common.kho_path("lessons", "G1-B08", "body.md"), "- a\n")
        common.write_json(common.kho_path("lessons", "G1-B08", "extra.json"), {"summary": "tt"})
        md = b7_render.assemble({"lesson": "G1-B08", "book": "G1", "title": "Viêm phổi", "society": "WHO"})
        self.assertNotIn("Ngoài giáo trình", md)
        self.assertGreaterEqual(md.count("Không có trong nguồn"), 3)
        self.assertNotIn("{{", md)

    def test_sources_table_uses_short_link(self):
        common.write_csv(common.data_path("manifest.csv"), [{"code": "S1", "path": "a.pdf"}], ["code", "path"])
        common.write_csv(common.data_path("drive_links.csv"), [{"code": "S1", "url": "https://d/x"}], ["code", "url"])
        common.write_text(common.kho_path("lessons", "G1-B08", "body.md"), "- a [S1:p1]\n")
        common.write_json(common.kho_path("lessons", "G1-B08", "extra.json"), {"summary": "tt"})
        md = b7_render.assemble({"lesson": "G1-B08", "book": "G1", "title": "T", "society": ""})
        self.assertIn("| S1 | a.pdf | [Mở](https://d/x) |", md)

    def test_gaps_listed_in_missing_section(self):
        common.write_csv(common.data_path("gaps.csv"),
                         [{"book": "G1", "printed_page": "120", "lesson": "G1-B08", "note": ""}],
                         ["book", "printed_page", "lesson", "note"])
        common.write_text(common.kho_path("lessons", "G1-B08", "body.md"), "- a\n")
        common.write_json(common.kho_path("lessons", "G1-B08", "extra.json"), {"summary": "tt"})
        md = b7_render.assemble({"lesson": "G1-B08", "book": "G1", "title": "Viêm phổi", "society": "WHO"})
        self.assertRegex(md, r"Thiếu trang.*120")


class TestProgress(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def test_progress_resume(self):
        self.assertEqual(progress.next_step("L"), "B1")
        progress.set("L", "B1")
        progress.set("L", "B2", "xong 12 chỗ")
        self.assertEqual(progress.next_step("L"), "B2b")
        self.assertEqual(progress.get("L")["B2"], "xong 12 chỗ")

    def test_all_done(self):
        for s in progress.STEPS:
            progress.set("L", s)
        self.assertIsNone(progress.next_step("L"))

    def test_unknown_step_rejected(self):
        with self.assertRaises(ValueError):
            progress.set("L", "B99")


if __name__ == "__main__":
    unittest.main()
