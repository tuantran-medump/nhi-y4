import _path  # noqa: F401
import os
import tempfile
import unittest

from scripts import b3_novel, cards

BOOK = "Điều trị kháng sinh amoxicillin trong 5 ngày cho trẻ viêm phổi nhẹ. Liều 90 mg mỗi kg mỗi ngày chia hai lần uống. Trẻ có thể tiếp tục bú mẹ khi đang điều trị."


def texts(result):
    return [r["text"] for r in result]


class TestNovel(unittest.TestCase):
    def test_identical_dropped(self):
        src = {1: "Điều trị kháng sinh amoxicillin trong 5 ngày cho trẻ viêm phổi nhẹ."}
        self.assertEqual(b3_novel.novel_sentences(BOOK, src), [])

    def test_case_and_spacing_dropped(self):
        src = {1: "điều trị   kháng sinh amoxicillin trong 5 ngày\ncho trẻ viêm phổi nhẹ."}
        self.assertEqual(b3_novel.novel_sentences(BOOK, src), [])

    def test_changed_number_kept(self):
        src = {4: "Điều trị kháng sinh amoxicillin trong 3 ngày cho trẻ viêm phổi nhẹ."}
        res = b3_novel.novel_sentences(BOOK, src)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["page"], 4)
        self.assertEqual(res[0]["reason"], "changed_fact")

    def test_changed_unit_kept(self):
        src = {1: "Liều 90 mcg mỗi kg mỗi ngày chia hai lần uống."}
        self.assertEqual(b3_novel.novel_sentences(BOOK, src)[0]["reason"], "changed_fact")

    def test_negation_kept(self):
        src = {1: "Trẻ có thể không tiếp tục bú mẹ khi đang điều trị."}
        self.assertEqual(b3_novel.novel_sentences(BOOK, src)[0]["reason"], "changed_fact")

    def test_direction_kept(self):
        book = "Nguy cơ suy hô hấp tăng ở trẻ sinh non nhẹ cân có bệnh tim."
        src = {1: "Nguy cơ suy hô hấp giảm ở trẻ sinh non nhẹ cân có bệnh tim."}
        self.assertEqual(len(b3_novel.novel_sentences(book, src)), 1)

    def test_new_sentence_kept(self):
        src = {2: "Kinh nghiệm lâm sàng: nghe phổi lúc trẻ ngủ."}
        res = b3_novel.novel_sentences(BOOK, src)
        self.assertEqual(texts(res), ["Kinh nghiệm lâm sàng: nghe phổi lúc trẻ ngủ."])
        self.assertEqual(res[0]["reason"], "new")


class TestCards(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def test_card_returned_for_lesson(self):
        cards.add("S001", "G1-B08", "ý A", 3)
        self.assertEqual(cards.for_lesson("G1-B08"),
                         [{"code": "S001", "idea": "ý A", "page": 3, "lessons": ["G1-B08"]}])

    def test_card_reused_no_duplicate(self):
        cards.add("S001", "G1-B08", "ý A", 3)
        cards.add("S001", "G1-B09", "ý A", 3)
        self.assertEqual(len(cards.for_source("S001")), 1)
        self.assertEqual(len(cards.for_lesson("G1-B09")), 1)
        self.assertEqual(len(cards.for_lesson("G1-B08")), 1)

    def test_other_lesson_not_returned(self):
        cards.add("S001", "G1-B08", "ý A", 3)
        self.assertEqual(cards.for_lesson("G1-B11"), [])


if __name__ == "__main__":
    unittest.main()
