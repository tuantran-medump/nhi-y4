import unittest
from check_roundtrip import plain_text
from html_to_md import convert
from build_cheatsheet import render


class CheckRoundtripTests(unittest.TestCase):
    def test_ignores_generated_annotations(self):
        self.assertEqual(plain_text('<div><span class="src">[G1:p2]</span><span class="kick">tag</span><div class="sub">sub</div>Hello &amp; bye</div>'), 'Hello & bye')

    def test_html_markdown_html_preserves_full_fake_content(self):
        original = '<html><head><title>Ignored</title></head><body><header><h1>Demo</h1><div class="sub">subtitle</div></header><div class="cols"><section><h2>Part</h2><ul><li>First <b>bold</b><ul><li>Nested &amp; text</li><li><span class="t">Trap</span></li></ul></li></ul><table><tr><th>A</th><th>B</th></tr><tr><td>C &lt; D</td><td>E</td></tr></table><p>Last sentence.</p></section><section class="ans"><p><b>1.C</b> Answer text.</p></section></div></body></html>'
        built = render(convert(original), 'warm')
        self.assertEqual(plain_text(original), plain_text(built))


if __name__ == '__main__': unittest.main()
