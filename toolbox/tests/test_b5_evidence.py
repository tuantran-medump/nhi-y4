import _path  # noqa: F401
import json
import os
import tempfile
import unittest

from lib import common
from scripts import b4_ink, b5_evidence


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name
        common.write_csv(common.data_path("topic_keywords.csv"),
                         [{"lesson": "L", "keywords": "viêm phổi", "folder_hint": "Hô hấp"}],
                         ["lesson", "keywords", "folder_hint"])

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def source(self, code, name, sentences):
        rows = common.read_csv(common.data_path("manifest.csv"))
        rows.append({"code": code, "path": name})
        common.write_csv(common.data_path("manifest.csv"), rows, ["code", "path"])
        src = common.read_csv(common.data_path("lesson_sources.csv"))
        src.append({"lesson": "L", "code": code})
        common.write_csv(common.data_path("lesson_sources.csv"), src, ["lesson", "code"])
        common.write_text(common.kho_path("lessons", "L", f"novel_{code}.jsonl"),
                          "".join(json.dumps({"page": p, "text": t, "reason": r}, ensure_ascii=False) + "\n"
                                  for p, t, r in sentences))

    def lines(self):
        return b5_evidence.build("L").strip().split("\n")


class TestEvidence(Base):
    def test_topic_file_keeps_all_sentences(self):
        self.source("S1", "Viêm phổi.pdf", [(1, "Câu không nhắc tới bệnh nhưng dài đủ.", "new")])
        self.assertIn("[S1:p1] Câu không nhắc tới bệnh nhưng dài đủ.", self.lines())

    def test_general_file_keeps_only_keyword_and_neighbours(self):
        self.source("N1", "Tổng hợp.pdf", [(1, "Câu xa một hai ba.", "new"), (1, "Câu trước bốn năm sáu.", "new"),
                                           (1, "Điều trị viêm phổi bảy tám.", "new"), (1, "Câu sau chín mười.", "new"),
                                           (1, "Câu xa khác hẳn nhau.", "new")])
        text = "\n".join(self.lines())
        self.assertIn("Câu trước", text)
        self.assertIn("Điều trị viêm phổi", text)
        self.assertIn("Câu sau", text)
        self.assertNotIn("Câu xa", text)

    def test_duplicate_across_sources_listed_once_with_both_codes(self):
        self.source("S1", "Viêm phổi.pdf", [(2, "Liều amoxicillin 90 mg mỗi kg.", "new")])
        self.source("S2", "viêm phổi 2.pdf", [(5, "liều amoxicillin 90 mg mỗi kg", "new")])
        self.assertEqual(self.lines(), ["[S1:p2][S2:p5] Liều amoxicillin 90 mg mỗi kg."])

    def test_changed_fact_always_kept_and_flagged(self):
        self.source("N1", "Tổng hợp.pdf", [(1, "Một câu không nhắc nhưng khác sách.", "changed_fact")])
        self.assertEqual(self.lines(), ["!KHÁC SÁCH [N1:p1] Một câu không nhắc nhưng khác sách."])

    def test_short_noise_dropped(self):
        self.source("S1", "Viêm phổi.pdf", [(1, "Slide 12", "new"), (1, "Liều 5 mg", "new")])
        self.assertEqual(self.lines(), ["[S1:p1] Liều 5 mg"])

    def test_handwriting_included(self):
        self.source("S1", "Viêm phổi.pdf", [])
        common.write_text(common.page_file("S1", 3, "ink.txt"), "ghi chú tay")
        self.assertEqual(self.lines(), ["(viết tay) [S1:p3] ghi chú tay"])


class TestInkOnly(unittest.TestCase):
    def test_only_filter_selects_codes(self):
        rows = [{"lesson": "L", "code": "A"}, {"lesson": "L", "code": "B"}, {"lesson": "M", "code": "A"}]
        self.assertEqual([r["code"] for r in b4_ink._select(rows, "L", {"A"})], ["A"])

    def test_no_filter_keeps_lesson_rows(self):
        rows = [{"lesson": "L", "code": "A"}, {"lesson": "L", "code": "B"}]
        self.assertEqual(len(b4_ink._select(rows, "L", None)), 2)


if __name__ == "__main__":
    unittest.main()
