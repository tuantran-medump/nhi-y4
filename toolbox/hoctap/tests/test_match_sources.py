import unittest
from match_sources import match

class MatchSourcesTests(unittest.TestCase):
    def test_numeric_match_and_code_from_exact_line(self):
        md = '## Data\n- Tỉ lệ 65–80% MCD\n'
        body = 'Tỉ lệ 65–80% gặp ở MCD [G1:p10].\nMCD thường gặp [G1:p99].\n'
        out, records = match(md, body)
        self.assertIn('[G1:p10]', out)
        self.assertEqual(records[0]['matched_body_lines'], [1])

    def test_k_span_requires_non_book_code(self):
        md = '## Data\n- <span class="k">Slide cập nhật 60–150 mg</span>\n'
        body = 'Slide cập nhật 60–150 mg [G1:p11].\nSlide cập nhật 60–150 mg [S085:p3].\n'
        out, _ = match(md, body)
        self.assertIn('[S085:p3]', out)
        self.assertNotIn('[G1:p11]', out)

    def test_unmatched_gets_question_mark(self):
        out, records = match('## Data\n- Từ hiếm gặp xyzquux\n', 'Nội dung khác [G1:p2].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_rerun_does_not_duplicate_codes(self):
        md = '## Data\n- Tỉ lệ 65–80% MCD\n'
        body = 'Tỉ lệ 65–80% MCD [G1:p10].\n'
        once, _ = match(md, body)
        twice, _ = match(once, body)
        self.assertEqual(twice.count('[G1:p10]'), 1)

    def test_short_number_alone_does_not_match(self):
        out, records = match('## Data\n- Lưu hành 16/100.000 ở trẻ em\n', 'Kết quả xét nghiệm có chỉ số 16 [G1:p222].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_short_age_range_does_not_match_neighbor_age(self):
        out, records = match('## Data\n- 1–12 tuổi: thể điển hình, nguyên phát, MCD\n', 'Hội chứng thận hư nguyên phát trước 1 tuổi [G1:p205].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_other_number_cannot_be_rescued_by_shared_phrase(self):
        out, records = match('## Data\n- 75% khởi phát trước 6 tuổi\n', 'Hội chứng thận hư nguyên phát khởi phát sớm trước 1 tuổi [G1:p205].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_range_endpoint_is_not_a_standalone_numeric_match(self):
        out, records = match('## Data\n- Tái phát <span class="n">50%</span>\n', 'Tái phát thường xuyên chiếm 40–50% [G1:p217].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_decimal_digit_is_not_a_standalone_number(self):
        out, records = match('## Data\n- Thử vào ngày thứ 5 để đánh giá đáp ứng lâm sàng\n', 'Liều prednison là 1,5 mg/kg/ngày cho trẻ [G1:p217].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_ratio_does_not_match_an_age_range(self):
        out, records = match('## Data\n- Nam:nữ <span class="n">2:1</span>\n', 'Tuổi khởi bệnh từ 1–12 tuổi [G1:p215].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_numbered_question_is_not_evidence(self):
        out, records = match('## Data\n- Phù do underfill và overfill\n', '2. Trình bày phù do underfill và overfill [G1:p203].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_same_percent_in_unrelated_topic_is_not_enough(self):
        md = '## Data\n- Không tái phát 10–20%; tái phát xa 30–40%; tái phát thường xuyên 40–50%\n'
        body = 'Loại nguyên nhân thứ phát: chỉ gặp 10% trường hợp [G1:p214].\n'
        out, records = match(md, body)
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_same_duration_in_unrelated_topic_is_not_enough(self):
        md = '## Data\n- Dùng thuốc ít nhất 12 tháng để điều trị bệnh thận\n'
        body = 'Tái phát thường xuyên được định nghĩa là 2 lần trong 6 tháng hoặc 3 lần trong 12 tháng [G1:p217].\n'
        out, records = match(md, body)
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_common_dose_alone_is_not_enough(self):
        out, records = match('## Data\n- Enalapril, tối đa 40 mg/ngày để giảm đạm niệu\n', 'Prednison tối đa 40 mg/ngày, đạm niệu âm tính [G1:p217].\n')
        self.assertTrue(out.rstrip().endswith('[?]'))
        self.assertEqual(records[0]['codes'], [])

    def test_exact_numeric_cluster_selects_correct_line(self):
        md = '## Data\n- Mới mắc 2,92/100.000 trẻ; lưu hành 16/100.000\n'
        body = 'Xét nghiệm khác có giá trị 16 [G1:p222].\nTỉ lệ lưu hành 16/100.000 trẻ [G1:p211].\nBệnh cầu thận thường gặp nhất, mới mắc 2,92/100.000 trẻ hàng năm [G1:p203].\n'
        out, records = match(md, body)
        self.assertIn('[G1:p203]', out)
        self.assertNotIn('[G1:p222]', out)
        self.assertEqual(records[0]['confidence'], 'vua')

    def test_maximum_three_codes(self):
        md = '## Data\n- MCD nephrotic syndrome proteinuria edema [span?]\n'
        body = 'MCD nephrotic syndrome proteinuria edema [G1:p1] [G1:p2] [G1:p3] [G1:p4] [G1:p5]\n'
        out, records = match(md, body)
        self.assertLessEqual(len(records[0]['codes']), 3)

if __name__ == '__main__':
    unittest.main()
