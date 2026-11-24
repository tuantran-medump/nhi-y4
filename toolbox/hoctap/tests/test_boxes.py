import unittest

from boxes import parse_sections


class ParseSectionsTests(unittest.TestCase):
    def test_marker_sets_box(self):
        sections = parse_sections("## Tựa\n{hop: dieu-tri}\nNội dung")
        self.assertEqual(sections[0].box, "dieu-tri")

    def test_default_box(self):
        self.assertEqual(parse_sections("## Tựa\nNội dung")[0].box, "khai-niem")

    def test_marker_removed_from_lines(self):
        self.assertEqual(parse_sections("## Tựa\n\n{hop: lam-sang}\nNội dung")[0].lines, ["", "Nội dung"])

    def test_unknown_box_raises(self):
        with self.assertRaisesRegex(ValueError, r"2.*la-qua"):
            parse_sections("## Tựa\n{hop: la-qua}")

    def test_marker_not_under_heading_raises(self):
        with self.assertRaisesRegex(ValueError, r"1"):
            parse_sections("{hop: dieu-tri}\n## Tựa")

    def test_source_codes_preserved(self):
        value = "## Tựa\n[G1:p203]"
        self.assertEqual(parse_sections(value)[0].lines, ["[G1:p203]"])

    def test_preamble_section(self):
        sections = parse_sections("Mở đầu\n\n## Tựa\nNội dung")
        self.assertEqual((sections[0].title, sections[0].level, sections[0].box), ("", 0, "khai-niem"))
        self.assertEqual(sections[0].lines, ["Mở đầu", ""])

    def test_all_nine_boxes_accepted(self):
        names = "khai-niem dich-te-phan-loai benh-hoc lam-sang cls-chi-dinh dieu-tri canh-bao-bien-chung theo-doi tu-kiem-tra".split()
        md = "\n".join(f"## {i}\n{{hop: {name}}}" for i, name in enumerate(names))
        self.assertEqual([s.box for s in parse_sections(md)], names)


if __name__ == "__main__":
    unittest.main()
