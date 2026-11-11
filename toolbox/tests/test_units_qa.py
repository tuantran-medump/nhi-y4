import _path  # noqa: F401
import unittest

from scripts import b2_ocr_fix
from scripts.b2b_layout import split_units


class TestUnits(unittest.TestCase):
    def test_list_number_stays_with_sentence(self):
        self.assertEqual(split_units("1. Trình bày đặc điểm dịch tễ."), ["1. Trình bày đặc điểm dịch tễ."])

    def test_lesson_number_stays(self):
        self.assertEqual(split_units("Bài 8. VIÊM PHỔI"), ["Bài 8. VIÊM PHỔI"])

    def test_uppercase_line_stands_alone(self):
        self.assertEqual(split_units("VIÊM PHỔI\nPGS.TS.BS. Nguyễn A"), ["VIÊM PHỔI", "PGS.TS.BS. Nguyễn A"])

    def test_sentence_after_number_value_still_splits(self):
        self.assertEqual(split_units("Liều là 5. Sau đó giảm."), ["Liều là 5.", "Sau đó giảm."])


class TestRareBigrams(unittest.TestCase):
    CORPUS = b2_ocr_fix.bigram_counts(["mục tiêu học tập", "viêm phổi trẻ em", "tiểu thùy phổi"])

    def test_unseen_pair_flagged(self):
        found = b2_ocr_fix.rare_bigrams("mục tiểu học tập", self.CORPUS)
        self.assertEqual([(n, b) for n, b, _ in found], [(1, "mục tiểu"), (1, "tiểu học")])

    def test_known_text_clean(self):
        self.assertEqual(b2_ocr_fix.rare_bigrams("Viêm phổi trẻ em", self.CORPUS), [])

    def test_case_insensitive_and_markers_skipped(self):
        self.assertEqual(b2_ocr_fix.rare_bigrams("<<p12>>\nVIÊM PHỔI", self.CORPUS), [])

    def test_numbers_ignored(self):
        self.assertEqual(b2_ocr_fix.rare_bigrams("viêm 12 phổi", self.CORPUS), [])

    def test_block_content_skipped(self):
        text = "<<block:t1>>\nxx yy\n<<endblock>>\nviêm phổi"
        self.assertEqual(b2_ocr_fix.rare_bigrams(text, self.CORPUS), [])


class TestDiacritics(unittest.TestCase):
    CORPUS = {"viêm phổi": 500, "tiểu thùy": 40, "tiêu chảy": 300, "tiêu hóa": 90, "có thể": 900, "da dày": 2, "dạ dày": 60}

    def found(self, text):
        return [(n, p, s) for n, p, s in b2_ocr_fix.diacritic_suspects(text, self.CORPUS)]

    def test_wrong_tone_flagged_with_suggestion(self):
        self.assertEqual(self.found("viêm phối"), [(1, "viêm phối", "viêm phổi")])

    def test_valid_looking_word_flagged(self):
        self.assertEqual(self.found("tiêu thùy"), [(1, "tiêu thùy", "tiểu thùy")])

    def test_correct_pair_not_flagged(self):
        self.assertEqual(self.found("tiêu chảy"), [])

    def test_comparable_frequency_not_flagged(self):
        corpus = {"bàn tay": 30, "bạn tay": 20}
        self.assertEqual(b2_ocr_fix.diacritic_suspects("bạn tay", corpus), [])

    def test_seen_rare_variant_flagged(self):
        self.assertEqual(self.found("da dày"), [(1, "da dày", "dạ dày")])


if __name__ == "__main__":
    unittest.main()
