import tempfile
import unittest
from pathlib import Path
import html_to_md


class HtmlToMdTests(unittest.TestCase):
    def test_conversion_keeps_structure_and_text(self):
        source = '<header><h1>Demo &amp; test</h1><div class="sub">Sub <b>bold</b></div></header><div class="cols"><section><h2>Part</h2><ul><li>One &lt;two <b>bold</b><ul><li><span class="t">Trap</span></li></ul></li><li class="trap">Danger</li></ul><table><tr><th>A</th><th>B</th></tr><tr><td>C</td><td>D</td></tr></table></section><section class="ans"><p><b>1.C</b> Answer</p></section></div>'
        result = html_to_md.convert(source)
        self.assertIn('# Demo & test', result)
        self.assertIn('- One <two **bold**', result)
        self.assertIn('  - !bay Trap', result)
        self.assertIn('- !bay Danger', result)
        self.assertIn('| A | B |\n|---|---|', result)
        self.assertIn('**1.C** Answer', result)


if __name__ == '__main__': unittest.main()
