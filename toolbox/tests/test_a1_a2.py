import _path  # noqa: F401
import os
import tempfile
import unicodedata
import unittest

import pymupdf

from scripts import a1_inventory, a2_dedupe


def make_pdf(path, text="Noi dung viem phoi tre em " * 10, ink=False):
    d = pymupdf.open()
    p = d.new_page()
    p.insert_textbox(pymupdf.Rect(50, 50, 500, 700), text)
    if ink:
        p.add_ink_annot([[(60, 60), (90, 90), (120, 60)]])
    d.save(path)
    d.close()


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = self.t.name
        os.makedirs(os.path.join(self.root, "Slide", "Hô hấp"))
        self.dir = os.path.join(self.root, "Slide", "Hô hấp")

    def tearDown(self):
        self.t.cleanup()


class TestInventory(Base):
    def test_codes_stable_on_rerun(self):
        make_pdf(os.path.join(self.dir, "b.pdf"), "bbb " * 50)
        first = a1_inventory.build(self.root)
        make_pdf(os.path.join(self.dir, "a.pdf"), "aaa " * 50)
        second = a1_inventory.build(self.root, previous=first)
        old = {r["path"]: r["code"] for r in first}
        new = {r["path"]: r["code"] for r in second}
        for path, code in old.items():
            self.assertEqual(new[path], code)
        self.assertEqual(len(set(new.values())), 2)

    def test_odd_filenames(self):
        names = ["[PKD] a.pdf", "ho^J kho tho.pdf", unicodedata.normalize("NFD", "Viêm phổi.pdf")]
        for i, n in enumerate(names):
            make_pdf(os.path.join(self.dir, n), f"file {i} " * 40)
        rows = a1_inventory.build(self.root)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["kind"] == "text" for r in rows))
        self.assertTrue(all(r["specialty"] == "Hô hấp" for r in rows))

    def test_corrupt_pdf_needs_manual(self):
        with open(os.path.join(self.dir, "x.pdf"), "wb") as f:
            f.write(b"not a pdf")
        make_pdf(os.path.join(self.dir, "ok.pdf"))
        kinds = {r["path"].rsplit(os.sep, 1)[-1]: r["kind"] for r in a1_inventory.build(self.root)}
        self.assertEqual(kinds["x.pdf"], "needs_manual")
        self.assertEqual(kinds["ok.pdf"], "text")

    def test_book_codes_fixed(self):
        tb = os.path.join(self.root, "Textbook")
        os.makedirs(tb)
        make_pdf(os.path.join(tb, "Nhi Khoa Tập 1 2025.pdf"), "t1 " * 50)
        make_pdf(os.path.join(tb, "Nhi Khoa Tập 2 2025.pdf"), "t2 " * 50)
        make_pdf(os.path.join(tb, "guideline.pdf"), "g " * 50)
        codes = sorted(r["code"] for r in a1_inventory.build(self.root))
        self.assertEqual(codes, ["G1", "G2", "R001"])


class TestDedupe(Base):
    def test_exact_dup_marked(self):
        make_pdf(os.path.join(self.dir, "a.pdf"))
        import shutil
        shutil.copy(os.path.join(self.dir, "a.pdf"), os.path.join(self.dir, "a (2).pdf"))
        rows = a2_dedupe.mark(a1_inventory.build(self.root), self.root)
        status = sorted(r["status"].split(":")[0] for r in rows)
        self.assertEqual(status, ["dup_of", "primary"])

    def test_same_text_different_file_marked(self):
        make_pdf(os.path.join(self.dir, "a.pdf"))
        d = pymupdf.open(os.path.join(self.dir, "a.pdf"))
        d.set_metadata({"title": "khac"})
        d.save(os.path.join(self.dir, "b.pdf"))
        d.close()
        rows = a2_dedupe.mark(a1_inventory.build(self.root), self.root)
        self.assertEqual(sorted(r["status"].split(":")[0] for r in rows), ["dup_of", "primary"])

    def test_annotated_copy_kept(self):
        make_pdf(os.path.join(self.dir, "a.pdf"))
        make_pdf(os.path.join(self.dir, "b.pdf"), ink=True)
        rows = a2_dedupe.mark(a1_inventory.build(self.root), self.root)
        self.assertEqual([r["status"] for r in rows], ["primary", "primary"])

    def test_different_text_kept(self):
        make_pdf(os.path.join(self.dir, "a.pdf"), "viem phoi " * 60)
        make_pdf(os.path.join(self.dir, "b.pdf"), "hen tre em nhu nhi " * 40)
        rows = a2_dedupe.mark(a1_inventory.build(self.root), self.root)
        self.assertEqual([r["status"] for r in rows], ["primary", "primary"])


if __name__ == "__main__":
    unittest.main()
