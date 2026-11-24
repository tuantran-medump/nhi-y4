import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "excalidraw"))
from to_excalidraw import group_branches, strip_sources


class T(unittest.TestCase):
    def test_strip(self):
        self.assertEqual(strip_sources('n0["Phù [G1:p203]"]'), 'n0["Phù"]')
        self.assertEqual(strip_sources('a -->|"biểu hiện [S085:p3]"| b'), 'a -->|"biểu hiện"| b')

    def test_group_same_relation(self):
        m = 'n0["A"]\n  n1["B"]\n  n2["C"]\n  n3["D"]\n  n0 -->|"biểu hiện"| n1\n  n0 -->|"biểu hiện"| n2\n  n0 -->|"điều trị"| n3\n'
        r = group_branches(m)
        self.assertIn('g1(["Biểu hiện"])', r)
        self.assertIn("n0 --> g1", r)
        self.assertIn("g1 --> n1", r)
        self.assertIn("g1 --> n2", r)
        self.assertNotIn('-->|"biểu hiện"|', r)
        self.assertIn('n0 -->|"điều trị"| n3', r)


if __name__ == "__main__":
    unittest.main()
