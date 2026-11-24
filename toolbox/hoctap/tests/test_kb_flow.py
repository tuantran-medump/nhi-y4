import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SCRIPT = HERE / "kb_flow.py"


class KBFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.kb = self.root / "kb"
        self.kb.mkdir()
        self.out = self.root / "out"
        with (self.kb / "entities.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(("id", "loai", "ten", "ten_en", "mon", "bai"))
            w.writerows([
                ("x:root", "benh", 'Bệnh "gốc"', "", "x", ""),
                ("x:symptom", "trieu_chung", "Phù", "", "x", ""),
                ("x:diff", "benh", "Bệnh phân biệt", "", "x", ""),
                ("x:workup", "thu_thuat", "Làm xét nghiệm", "", "x", ""),
                ("x:hard", "thu_thuat", "Sinh thiết", "", "x", ""),
            ])
        with (self.kb / "edges.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(("tu", "quan_he", "den", "nguon", "ghi_chu"))
            w.writerows([
                ("x:root", "bieu_hien", "x:symptom", "[G1:p2]", ""),
                ("x:root", "phan_biet_voi", "x:diff", "[G1:p3]", ""),
                ("x:root", "xu_tri_phan_biet", "x:workup", "[G1:p4]", ""),
                ("x:root", "khi_cls_kho_phan_biet", "x:hard", "[G1:p5]", ""),
                ("x:root", "phan_biet_voi", "x:diff", "", ""),
                ("x:root", "phan_biet_voi", "x:diff", "bad", ""),
            ])

    def tearDown(self):
        self.tmp.cleanup()

    def test_approach_sources_gaps_and_mermaid_escaping(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.kb), "--root", "x:root", "--kind", "approach", "--out", str(self.out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        mmd = (self.out / "Bệnh _gốc_-approach.mmd").read_text(encoding="utf-8")
        self.assertIn('"Bệnh \\\"gốc\\\" [G1:p2]"', mmd)
        self.assertIn("[G1:p3]", mmd)
        self.assertIn("[G1:p4]", mmd)
        self.assertIn("[G1:p5]", mmd)
        with (self.out / "Bệnh _gốc_-approach-gaps.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["ly_do"] for r in rows))

    def test_dxtx_reverses_variant_relation_for_readable_flow(self):
        with (self.kb / "entities.csv").open("a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows([
                ("x:variant", "benh", "Thể tối thiểu", "", "x", ""),
                ("x:drug", "dieu_tri", "Corticoid", "", "x", ""),
                ("x:comp", "benh", "Biến chứng", "", "x", ""),
            ])
        with (self.kb / "edges.csv").open("a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows([
                ("x:variant", "la_the_cua", "x:root", "[G1:p6]", ""),
                ("x:variant", "dieu_tri", "x:drug", "[G1:p7]", ""),
                ("x:root", "bien_chung", "x:comp", "[G1:p8]", ""),
            ])
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.kb), "--root", "x:root", "--kind", "dxtx", "--out", str(self.out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        mmd = (self.out / 'Bệnh _gốc_-dxtx.mmd').read_text(encoding="utf-8")
        variant_id = next(line.split("[")[0].strip() for line in mmd.splitlines() if 'Thể tối thiểu' in line)
        root_id = next(line.split("[")[0].strip() for line in mmd.splitlines() if 'Bệnh \\\"gốc\\\"' in line)
        self.assertIn(f"{root_id} -->|\"thể [G1:p6]\"| {variant_id}", mmd)
        md = (self.out / 'Bệnh _gốc_-dxtx.md').read_text(encoding="utf-8")
        self.assertIn("- Thể tối thiểu [G1:p6]", md)
        self.assertIn("  - Corticoid [G1:p7]", md)


if __name__ == "__main__":
    unittest.main()
