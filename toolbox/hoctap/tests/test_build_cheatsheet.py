import unittest
from build_cheatsheet import render


class BuildCheatsheetTests(unittest.TestCase):
    def test_render_styles_sources_and_escaping(self):
        page = render('# Demo\n\n## Part\n{hop: lam-sang}\n- A [G1:p3] [?]\n- B <30 g/L\n- C <script>alert(1)</script>', 'warm')
        self.assertIn('class="bx lam-sang"', page)
        self.assertIn('class="kick"', page)
        self.assertIn('<span class="src">[G1:p3]</span>', page)
        self.assertIn('<span class="src miss">[?]</span>', page)
        self.assertIn('&lt;30 g/L', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('class="trap"', render('# D\n## P\n- !bay x', 'clean'))
        self.assertIn('<td>A</td>', render('# D\n## P\n| A | B |', 'screen'))
        self.assertIn('<th>A</th>', render('# D\n## P\n| A | B |\n|---|---|', 'screen'))
        with self.assertRaises(SystemExit): render('# D', 'bad')

    def test_rong_marker_adds_wide_class_and_is_not_printed(self):
        nl = chr(10)
        page = render(nl.join(['# D', '## P', '{hop: lam-sang}', '{rong}', '- x']), 'warm')
        self.assertIn('class="bx lam-sang wide"', page)
        self.assertNotIn('{rong}', page)
        self.assertNotIn('wide', render(nl.join(['# D', '## P', '{hop: lam-sang}', '- x']), 'warm'))


if __name__ == '__main__': unittest.main()
