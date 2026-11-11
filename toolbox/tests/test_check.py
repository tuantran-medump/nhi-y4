import _path  # noqa: F401
import os
import tempfile
import unittest

from lib import common
from scripts import check_lesson

FULL_EXTRA = {"summary": "- Tóm tắt [G1:p1]", "approach": "a", "experience": "b", "exam": "c", "conflicts": "d"}


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name
        common.write_csv(common.data_path("lessons.csv"),
                         [{"lesson": "L", "book": "G1", "title": "T", "society": "WHO", "group": "H"}],
                         ["lesson", "book", "title", "society", "group"])
        common.write_csv(common.data_path("manifest.csv"), [{"code": "G1", "path": "a.pdf"}, {"code": "S1", "path": "b.pdf"}],
                         ["code", "path"])

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def setup_lesson(self, fixed="Viêm phổi là bệnh.", body="- Viêm phổi là bệnh.", extra=None):
        common.write_text(common.kho_path("lessons", "L", "fixed.txt"), fixed)
        common.write_text(common.kho_path("lessons", "L", "body.md"), body)
        common.write_json(common.kho_path("lessons", "L", "extra.json"), FULL_EXTRA if extra is None else extra)

    def rules(self):
        return [i["rule"] for i in check_lesson.check("L")]


class TestCheck(Base):
    def test_clean_lesson_passes(self):
        self.setup_lesson()
        self.assertEqual(check_lesson.check("L"), [])

    def test_missing_section(self):
        self.setup_lesson(extra={"summary": "x"})
        self.assertIn("missing_section", self.rules())

    def test_missing_summary_is_error(self):
        self.setup_lesson(extra={**FULL_EXTRA, "summary": ""})
        self.assertIn("missing_summary", self.rules())

    def test_number_without_citation(self):
        self.setup_lesson(fixed="Liều 90 mg mỗi ngày.", body="- Liều 90 mg mỗi ngày.")
        self.assertIn("uncited_fact", self.rules())

    def test_number_with_citation_ok(self):
        self.setup_lesson(fixed="Liều 90 mg mỗi ngày.", body="- Liều 90 mg mỗi ngày [G1:p12].")
        self.assertNotIn("uncited_fact", self.rules())

    def test_unknown_source_code(self):
        self.setup_lesson(body="- Viêm phổi là bệnh [S999:p1].")
        self.assertIn("unknown_source", self.rules())

    def test_external_source_known(self):
        common.write_csv(common.data_path("external_sources.csv"), [{"code": "E1", "title": "WHO", "url": "u"}],
                         ["code", "title", "url"])
        self.setup_lesson(body="- Viêm phổi là bệnh [E1:p1].")
        self.assertNotIn("unknown_source", self.rules())

    def test_body_word_mismatch(self):
        self.setup_lesson(body="- Viêm phổi là bệnh nặng.")
        self.assertIn("body_changed", self.rules())

    def test_unresolved_marker(self):
        self.setup_lesson(fixed="Viêm [?phổi?] là bệnh.", body="- Viêm [?phổi?] là bệnh.")
        self.assertIn("unresolved", self.rules())

    def test_note_requires_citation(self):
        self.setup_lesson(body="- Viêm phổi là bệnh (Slide 2024: rút còn 3 ngày).")
        self.assertIn("body_changed", self.rules())

    def test_outside_textbook_skips_word_check(self):
        common.write_csv(common.data_path("lessons.csv"),
                         [{"lesson": "L", "book": "", "title": "T", "society": "", "group": "H"}],
                         ["lesson", "book", "title", "society", "group"])
        common.write_text(common.kho_path("lessons", "L", "body.md"), "- Nội dung từ slide [S1:p1].")
        common.write_json(common.kho_path("lessons", "L", "extra.json"), FULL_EXTRA)
        self.assertEqual(check_lesson.check("L"), [])


if __name__ == "__main__":
    unittest.main()
