import _path  # noqa: F401
import os
import tempfile
import unittest

import pymupdf

from lib import common
from scripts import a6_assign

KW = [{"lesson": "G1-B08", "keywords": "viêm phổi", "folder_hint": "Hô hấp"}]


class TestSpecialtyScope(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = self.t.name
        os.environ["NHI_TOOLBOX_HOME"] = self.t.name
        d = pymupdf.open()
        d.new_page()
        d.save(os.path.join(self.root, "a.pdf"))
        d.close()

    def tearDown(self):
        del os.environ["NHI_TOOLBOX_HOME"]
        self.t.cleanup()

    def assigned(self, specialty):
        common.write_text(common.page_file("N001", 1), "có nhắc viêm phổi")
        row = {"code": "N001", "path": "a.pdf", "kind": "text", "specialty": specialty,
               "status": "primary", "pages": "1"}
        return [r["lesson"] for r in a6_assign.assign([row], KW, self.root)]

    def test_same_specialty_used(self):
        self.assertEqual(self.assigned("Hô hấp"), ["G1-B08"])

    def test_other_specialty_excluded(self):
        self.assertEqual(self.assigned("Thận niệu"), [])

    def test_general_notes_folder_used(self):
        self.assertEqual(self.assigned("Tổng hợp"), ["G1-B08"])

    def test_textbook_used(self):
        self.assertEqual(self.assigned(""), ["G1-B08"])

    def test_every_keyword_row_has_specialty(self):
        rows = common.read_csv(os.path.join(common.TOOLBOX, "data", "topic_keywords.csv"))
        self.assertEqual([r["lesson"] for r in rows if not r["folder_hint"]], [])


if __name__ == "__main__":
    unittest.main()
