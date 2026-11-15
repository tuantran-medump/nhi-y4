import _path  # noqa: F401
import unittest

from scripts import b6_pairs

BODY = "\n".join(f"{i}\tdòng {i}" for i in range(1, 11))
NOTES = [{"line": 9, "note": "(c [S1:p1])"}, {"line": 5, "note": "(a [S1:p1])"}, {"line": 5, "note": "(b [S2:p1])"}]


class TestPairs(unittest.TestCase):
    def test_pairs_groups_notes_under_book_line(self):
        out = b6_pairs.pairs(BODY, NOTES, set()).split("\n")
        self.assertEqual(out, ["L5 dòng 5", "  → (a [S1:p1])", "  → (b [S2:p1])",
                               "L9 dòng 9", "  → (c [S1:p1])"])

    def test_conflict_line_flagged(self):
        out = b6_pairs.pairs(BODY, NOTES, {9})
        self.assertIn("L9 ⚑ dòng 9", out)
        self.assertNotIn("L5 ⚑", out)


if __name__ == "__main__":
    unittest.main()
