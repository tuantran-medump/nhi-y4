import unittest
from review_sources import render


class ReviewSourcesTests(unittest.TestCase):
    def test_links_and_unmatched_candidates_render(self):
        records = [{'line': 4, 'text': 'Ý cần rà [?]', 'codes': [], 'confidence': 'thap', 'matched_body_lines': [], 'candidates': [{'code': 'G1:p203', 'excerpt': 'Dòng chứng cứ', 'score': 8}, {'code': 'S085:p3', 'excerpt': 'Dòng khác', 'score': 4}]}]
        result = render('- Ý cần rà [?]', records, {'G1': 'https://example.test/g1'}, ['Dòng chứng cứ'])
        self.assertIn('[G1](https://example.test/g1) trang 203', result)
        self.assertIn('S085:p3 — chưa có link', result)
        self.assertIn('Dòng chứng cứ', result)


if __name__ == '__main__':
    unittest.main()
