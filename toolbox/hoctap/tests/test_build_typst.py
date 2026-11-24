import unittest
from unittest.mock import patch

from build_typst import box_colors, esc, inline, render


class BuildTypstTests(unittest.TestCase):
    def test_typst_markup_escapes_special_characters(self):
        self.assertEqual(esc('#$@*_<[\\`'), r'\#\$\@\*\_\<\[\\\`')
        rendered = inline('x # y $z @a *b* _c_ <30 [G1:p3] [?]', '#2f6db0')
        self.assertIn(r'\# y \$z \@a \*b\* \_c\_ \<30', rendered)
        self.assertIn('\[G1:p3\]', rendered)
        self.assertIn('a3261a', rendered)

    def test_all_box_colors_match_tokens(self):
        expected = ['#2f6db0', '#1f7f78', '#8a6a1c', '#3b7d3a', '#b8611f', '#b23a62', '#a3261a', '#4b6177', '#7b6400']
        self.assertEqual([box_colors()[key][0] for key in box_colors()], expected)
        self.assertIn('#block(fill: rgb("#2f6db0")', render('# X\n## Part\n{hop: khai-niem}\n- Hi'))


if __name__ == '__main__':
    unittest.main()
