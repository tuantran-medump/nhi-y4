import unittest
from check_sources import inspect


class CheckSourcesTests(unittest.TestCase):
    def test_counts_and_missing_locations(self):
        report = inspect('# X\n## Y\n- Good [G1:p1]\n- Bad [?]\n| A | B |\n|---|---|\n| C | D [S1:p2] |')
        self.assertEqual((report['with_source'], report['without_source']), (2, 1))
        self.assertEqual(report['missing'], [(4, '- Bad [?]')])


if __name__ == '__main__': unittest.main()
