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

    def test_flagged_line_without_note_still_printed(self):
        out = b6_pairs.pairs(BODY, NOTES, {7})
        self.assertIn("L7 ⚑ dòng 7", out)
        self.assertIn("(chưa có chú thích)", out)

    def test_uncarded_pages_ranked_by_clinical_signal(self):
        evidence = ("[S1:p1] liều 10 mg/kg/ngày trong 7 ngày\n"
                    "[S1:p2] câu chung chung\n"
                    "[S2:p5] độ nhạy 93%, độ đặc hiệu 95%\n"
                    "[S2:p5] chữ khác\n"
                    "[S3:p9] tiên lượng tốt, tái phát 10%")
        out = b6_pairs.uncarded_pages(evidence, "(x [S3:p9])", limit=2)
        # S2:p5 (2 số % + 2 từ = 6 điểm) trên S1:p1 (2 số có đơn vị + "liều" = 5); S3:p9 đã có trong thẻ, S1:p2 không có tín hiệu
        self.assertEqual([p for p, _, _ in out], ["S2:p5", "S1:p1"])
        self.assertEqual(out[0][2], "độ nhạy 93%, độ đặc hiệu 95%")  # câu có điểm cao nhất của trang

    def test_conflict_line_flagged(self):
        out = b6_pairs.pairs(BODY, NOTES, {9})
        self.assertIn("L9 ⚑ dòng 9", out)
        self.assertNotIn("L5 ⚑", out)


if __name__ == "__main__":
    unittest.main()
