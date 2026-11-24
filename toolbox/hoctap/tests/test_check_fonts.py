import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import fitz

from check_fonts import check_pdf, check_text_coverage


class CheckFontsTests(unittest.TestCase):
    def make_pdf(self, path, pages):
        doc = fitz.open()
        for text in pages:
            page = doc.new_page()
            page.insert_text((72, 72), text, fontname="helv")
        doc.save(path)
        doc.close()

    def test_ascii_only_ignored(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.pdf"
            self.make_pdf(path, ["Plain ASCII"])
            self.assertEqual(check_pdf(path, []), [])

    def test_all_pages_checked(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.pdf"
            self.make_pdf(path, ["Page one", "Page two", "Tiếng Việt"])
            errors = check_pdf(path, ["Definitely not this font"])
            self.assertTrue(any("trang 3" in e.lower() for e in errors), errors)

    def test_subset_prefix_stripped(self):
        class FakePage:
            def get_text(self, kind):
                return {"blocks": [{"lines": [{"spans": [{"text": "ế", "font": "ABCDEF+Inter Display"}]}]}]}
        class FakeDoc:
            def __iter__(self): return iter([FakePage()])
            def close(self): pass
        import check_fonts
        old = check_fonts.fitz.open
        check_fonts.fitz.open = lambda _: FakeDoc()
        try:
            self.assertEqual(check_fonts.check_pdf(Path("fake.pdf"), ["inter"]), [])
        finally:
            check_fonts.fitz.open = old

    def test_text_coverage(self):
        self.assertTrue(check_text_coverage("ă", "ăâ"))


if __name__ == "__main__":
    unittest.main()
