import _path  # noqa: F401
import os
import re
import tempfile
import unittest

from scripts import b7_render, b8_render_b14


class TestB8(unittest.TestCase):
    def test_b7_functions_used_by_b8_exist(self):
        for name in ("assemble", "md_to_html", "_load_links", "_nav", "finish_pdf"):
            self.assertTrue(callable(getattr(b7_render, name, None)), name)

    def test_swap_diagrams_replaces_only_blocks_with_mmd(self):
        tmp = tempfile.mkdtemp()
        old = os.environ.get("NHI_TOOLBOX_HOME")
        os.environ["NHI_TOOLBOX_HOME"] = tmp
        try:
            d = os.path.join(tmp, "kho", "lessons", "G9-B01", "diagrams")
            os.makedirs(d)
            with open(os.path.join(d, "p1a.mmd"), "w", encoding="utf-8") as f:
                f.write("flowchart TD\n  A-->B")
            md = "<<block:p1a>>\nảnh\n<<endblock>>\n<<block:p2b>>\nảnh 2\n<<endblock>>"
            out, found = b8_render_b14.swap_diagrams(md, "G9-B01")
            self.assertIn("@@DIAGRAM:p1a@@", out)
            self.assertIn("<<block:p2b>>", out)
            self.assertEqual(list(found), ["p1a"])
        finally:
            if old is None:
                os.environ.pop("NHI_TOOLBOX_HOME", None)
            else:
                os.environ["NHI_TOOLBOX_HOME"] = old

    def test_gradient_title_keeps_text(self):
        html = b8_render_b14.gradient_title("Bài 1")
        self.assertEqual(re.sub(r"<[^>]+>", "", html), "Bài 1")
        self.assertTrue(html.startswith('<span style="color:#c9413a">'))


if __name__ == "__main__":
    unittest.main()
