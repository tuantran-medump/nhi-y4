import _path  # noqa: F401
import os
import tempfile
import unittest
import zipfile

import pymupdf

from lib import common, ink
from scripts import a5_extract, a6_assign


def row(code, path, kind="text", specialty="Hô hấp", status="primary", pages=1):
    return {"code": code, "path": path, "kind": kind, "specialty": specialty,
            "status": status, "pages": str(pages), "folder": "Slide", "sha256": code}


class Home(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = self.t.name
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def pdf(self, name, texts):
        d = pymupdf.open()
        for t in texts:
            d.new_page().insert_textbox(pymupdf.Rect(50, 50, 500, 700), t)
        d.save(os.path.join(self.root, name))
        d.close()


class TestExtract(Home):
    def test_pdf_pages(self):
        self.pdf("a.pdf", ["trang mot", "trang hai"])
        a5_extract.extract(row("S001", "a.pdf", pages=2), self.root)
        self.assertIn("hai", common.read_text(common.page_file("S001", 2)))

    def test_docx_text(self):
        p = os.path.join(self.root, "a.docx")
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("word/document.xml",
                       '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                       "<w:body><w:p><w:r><w:t>Dòng một</w:t></w:r></w:p><w:p><w:r><w:t>Dòng hai</w:t></w:r></w:p></w:body></w:document>")
        a5_extract.extract(row("N001", "a.docx", "office"), self.root)
        self.assertEqual(common.read_text(common.page_file("N001", 1)), "Dòng một\nDòng hai")

    def test_pptx_one_page_per_slide(self):
        p = os.path.join(self.root, "a.pptx")
        ns = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
        with zipfile.ZipFile(p, "w") as z:
            for i in (1, 2, 10):
                z.writestr(f"ppt/slides/slide{i}.xml", f"<x {ns}><a:p><a:r><a:t>Slide {i}</a:t></a:r></a:p></x>")
        a5_extract.extract(row("S002", "a.pptx", "office"), self.root)
        self.assertEqual(common.read_text(common.page_file("S002", 3)), "Slide 10")

    def test_legacy_doc_needs_manual(self):
        with open(os.path.join(self.root, "a.doc"), "wb") as f:
            f.write(b"x")
        self.assertEqual(a5_extract.extract(row("N002", "a.doc", "needs_manual"), self.root), "needs_manual")

    def test_book_skipped(self):
        self.pdf("b.pdf", ["x"])
        self.assertEqual(a5_extract.extract(row("G1", "b.pdf", "image"), self.root), "skip")


class TestInk(unittest.TestCase):
    def setUp(self):
        self.d = pymupdf.open()
        self.p = self.d.new_page()

    def test_ink_annotation_detected(self):
        self.p.add_ink_annot([[(60, 60), (90, 90), (120, 60)]])
        self.assertEqual(len(ink.ink_regions(self.p)), 1)

    def test_vector_stroke_detected(self):
        s = self.p.new_shape()
        pts = [(100 + 5 * i, 100 + (i % 2) * 8) for i in range(25)]
        for i in range(0, 24, 3):
            s.draw_bezier(pts[i], pts[i + 1], pts[i + 2], pts[i + 3])
        s.finish(color=(0, 0, 1), closePath=False)
        s.commit()
        self.assertEqual(len(ink.ink_regions(self.p)), 1)

    def test_table_borders_not_ink(self):
        s = self.p.new_shape()
        for i in range(10):
            s.draw_line((50, 50 + 20 * i), (400, 50 + 20 * i))
            s.draw_rect(pymupdf.Rect(50, 50 + 20 * i, 100, 70 + 20 * i))
        s.finish(color=(0, 0, 0))
        s.commit()
        self.assertEqual(ink.ink_regions(self.p), [])

    def test_rounded_box_not_ink(self):
        s = self.p.new_shape()
        s.draw_rect(pymupdf.Rect(50, 50, 300, 200), radius=0.2)
        s.finish(color=(0, 0, 0))
        s.commit()
        self.assertEqual(ink.ink_regions(self.p), [])

    def test_nearby_strokes_merged(self):
        self.p.add_ink_annot([[(60, 60), (90, 90)]])
        self.p.add_ink_annot([[(95, 60), (120, 90)]])
        self.p.add_ink_annot([[(400, 600), (450, 650)]])
        self.assertEqual(len(ink.ink_regions(self.p)), 2)


class TestAssign(Home):
    KW = [{"lesson": "G1-B08", "keywords": "viêm phổi", "folder_hint": "Hô hấp"},
          {"lesson": "G1-B11", "keywords": "NTT", "folder_hint": "Thận niệu"}]

    def test_assign_by_folder_and_keyword(self):
        self.pdf("a.pdf", ["x", "y"])
        common.write_text(common.page_file("S001", 1), "không liên quan")
        common.write_text(common.page_file("S001", 2), "Viêm phổi cộng đồng")
        rows = a6_assign.assign([row("S001", "a.pdf", pages=2)], self.KW, self.root)
        self.assertEqual([(r["lesson"], r["pages"]) for r in rows], [("G1-B08", "2")])

    def test_folder_hint_blocks_other_specialty(self):
        self.pdf("a.pdf", ["x"])
        common.write_text(common.page_file("S001", 1), "NTT")
        self.assertEqual(a6_assign.assign([row("S001", "a.pdf")], self.KW, self.root), [])

    def test_short_keyword_whole_word(self):
        kw = [{"lesson": "X-01", "keywords": "ho", "folder_hint": "Hô hấp"}]
        self.pdf("a.pdf", ["x"])
        common.write_text(common.page_file("S001", 1), "cho thuốc, phổi khoẻ")
        self.assertEqual(a6_assign.assign([row("S001", "a.pdf")], kw, self.root), [])

    def test_filename_match_takes_all_pages(self):
        self.pdf("Viêm phổi.pdf", ["", ""])
        rows = a6_assign.assign([row("N001", "Viêm phổi.pdf", "image", pages=2)], self.KW, self.root)
        self.assertEqual(rows[0]["pages"], "1;2")

    def test_only_primary_assigned(self):
        self.pdf("Viêm phổi.pdf", ["x"])
        r = row("S001", "Viêm phổi.pdf", status="dup_of:S002")
        self.assertEqual(a6_assign.assign([r], self.KW, self.root), [])

    def test_books_not_references(self):
        self.pdf("Viêm phổi.pdf", ["x"])
        self.assertEqual(a6_assign.assign([row("G1", "Viêm phổi.pdf")], self.KW, self.root), [])

    def test_ink_pages_listed(self):
        d = pymupdf.open()
        d.new_page()
        d.new_page().add_ink_annot([[(60, 60), (90, 90)]])
        d.save(os.path.join(self.root, "Viêm phổi.pdf"))
        d.close()
        rows = a6_assign.assign([row("N001", "Viêm phổi.pdf", pages=2)], self.KW, self.root)
        self.assertEqual(rows[0]["ink_pages"], "2")


if __name__ == "__main__":
    unittest.main()
