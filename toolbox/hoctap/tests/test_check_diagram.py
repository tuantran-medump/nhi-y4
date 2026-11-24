import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SCRIPT = HERE / "check_diagram.py"


class CheckDiagramTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.kb = self.root / "kb"
        self.kb.mkdir()
        with (self.kb / "entities.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(("id", "loai", "ten", "ten_en", "mon", "bai"))
            w.writerows([("x:root", "benh", "Bệnh gốc", "", "x", ""), ("x:hard", "thu_thuat", "Sinh thiết", "", "x", "")])
        with (self.kb / "edges.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(("tu", "quan_he", "den", "nguon", "ghi_chu"))
            w.writerow(("x:root", "khi_cls_kho_phan_biet", "x:hard", "[G1:p2]", ""))
        self.diagram = self.root / "diagram.mmd"

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, body):
        self.diagram.write_text(body, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(self.diagram), "--kb", str(self.kb), "--kind", "approach"], capture_output=True, text=True)

    def test_rejects_missing_source_unknown_label_and_missing_hard_branch(self):
        result = self.check('flowchart TD\n A["Bệnh gốc"]\n C["Lạ [G1:p2]"]\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn("nguồn", result.stdout.lower())
        self.assertIn("nhãn", result.stdout.lower())
        self.assertIn("khó phân biệt", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
