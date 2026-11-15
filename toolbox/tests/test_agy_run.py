import _path  # noqa: F401
import json
import os
import sys
import tempfile
import unittest

from scripts import agy_run

FAKE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_agy.py")


class FakeAgy:
    """Đặt biến môi trường để agy_run gọi fake_agy.py thay cho agy thật."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, "calls.json")
        self._env = {k: os.environ.get(k) for k in ("AGY_CMD", "FAKE_AGY_OUT", "FAKE_AGY_EXIT", "FAKE_AGY_SLEEP", "FAKE_AGY_STATE", "NHI_TOOLBOX_HOME")}
        os.environ["AGY_CMD"] = json.dumps([sys.executable, FAKE])
        os.environ["FAKE_AGY_STATE"] = self.state
        for k in ("FAKE_AGY_OUT", "FAKE_AGY_EXIT", "FAKE_AGY_SLEEP"):
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def outputs(self, *outs):
        os.environ["FAKE_AGY_OUT"] = json.dumps(list(outs), ensure_ascii=False)

    def calls(self):
        return json.load(open(self.state, encoding="utf-8")) if os.path.exists(self.state) else []


class TestExtract(unittest.TestCase):
    def test_extract_json_from_fenced_and_prose(self):
        self.assertEqual(agy_run.extract_json('Đây:\n```json\n{"a": [1]}\n```\nXong'), {"a": [1]})

    def test_extract_json_single_element_array(self):
        self.assertEqual(agy_run.extract_json('[{"line": 1}]'), [{"line": 1}])

    def test_extract_json_prose_with_braces(self):
        self.assertEqual(agy_run.extract_json('Ghi chú {xem dưới}:\n{"a": 1}\nXong {ok}'), {"a": 1})

    def test_extract_json_last_fence_wins(self):
        text = 'Ví dụ:\n```json\n{"ví": "dụ"}\n```\nKết quả:\n```json\n{"a": 2}\n```'
        self.assertEqual(agy_run.extract_json(text), {"a": 2})

    def test_extract_json_none_raises(self):
        with self.assertRaises(ValueError):
            agy_run.extract_json("không có")


class TestCall(FakeAgy, unittest.TestCase):
    def test_call_nonzero_exit_raises(self):
        self.outputs('{"a": 1}')
        os.environ["FAKE_AGY_EXIT"] = "3"
        with self.assertRaises(agy_run.AgyError):
            agy_run.call("x", agy_run.HYDROGEN, [self.tmp])

    def test_call_timeout_raises(self):
        self.outputs("{}")
        os.environ["FAKE_AGY_SLEEP"] = "5"
        with self.assertRaises(agy_run.AgyError):
            agy_run.call("x", agy_run.HYDROGEN, [self.tmp], timeout_s=1)

    def test_call_returns_response_and_rejects_non_success_status(self):
        self.outputs('{"a": 1}')
        self.assertEqual(agy_run.call("x", agy_run.HYDROGEN, [self.tmp]).strip(), '{"a": 1}')
        os.environ["FAKE_AGY_STATUS"] = "ERROR"
        try:
            with self.assertRaises(agy_run.AgyError):
                agy_run.call("x", agy_run.HYDROGEN, [self.tmp])
        finally:
            os.environ.pop("FAKE_AGY_STATUS", None)

    def test_call_empty_response_with_denied_action_raises_clear_error(self):
        self.outputs("")
        os.environ["FAKE_AGY_DENIED"] = "1"
        try:
            with self.assertRaisesRegex(agy_run.AgyError, "Bash"):
                agy_run.call("x", agy_run.HYDROGEN, [self.tmp])
        finally:
            os.environ.pop("FAKE_AGY_DENIED", None)

    def test_ask_json_retries_once_after_denied_tool(self):
        self.outputs("", '{"y": 2}')
        os.environ["FAKE_AGY_DENIED_CALLS"] = "1"
        try:
            out = agy_run.ask_json("việc", agy_run.HYDROGEN, [self.tmp], lambda d: [])
        finally:
            os.environ.pop("FAKE_AGY_DENIED_CALLS", None)
        self.assertEqual(out, {"y": 2})
        self.assertIn("bị từ chối", self.calls()[1]["prompt"])

    def test_prefix_forbids_shell_commands(self):
        self.assertIn("KHÔNG chạy lệnh", agy_run.READ_ONLY_PREFIX)

    def test_call_is_read_only_plan_mode_with_prefix(self):
        self.outputs("{}")
        agy_run.call("việc", agy_run.HYDROGEN, [self.tmp])
        call = self.calls()[0]
        self.assertIn("--mode", call["argv"])
        self.assertEqual(call["argv"][call["argv"].index("--mode") + 1], "plan")
        self.assertNotIn("--dangerously-skip-permissions", call["argv"])
        self.assertTrue(call["prompt"].startswith(agy_run.READ_ONLY_PREFIX))

    def test_ask_json_retries_once_then_ok(self):
        self.outputs('{"x": 1}', '{"y": 2}')
        out = agy_run.ask_json("việc", agy_run.HYDROGEN, [self.tmp], lambda d: [] if "y" in d else ["thiếu y"])
        self.assertEqual(out, {"y": 2})
        calls = self.calls()
        self.assertEqual(len(calls), 2)
        self.assertIn("Lần trước sai", calls[1]["prompt"])

    def test_ask_json_fails_twice_raises(self):
        self.outputs("không phải json")
        with self.assertRaises(agy_run.AgyError):
            agy_run.ask_json("việc", agy_run.HYDROGEN, [self.tmp], lambda d: [])
        self.assertEqual(len(self.calls()), 2)


BODY = "1\t<<p10>>\n2\t## Bài 1. BỆNH\n3\t- Điều trị 5 ngày.\n4\t\n5\t| a | b |\n6\t- Liều 2 mg/kg."
NOTE = {"line": 3, "note": "(Slide: 3 ngày [S088:p4])"}
CARDS = {"notes": [NOTE], "conflicts": [], "approach": [], "experience": [], "exam": []}


class TestSplitAndValidate(unittest.TestCase):
    def test_split_evidence_groups_by_source(self):
        text = "\n".join(f"[S{c}:p1] câu {i}" for c in ("001", "002", "003") for i in range(150))
        parts = agy_run.split_evidence(text, max_lines=400)
        self.assertEqual(len(parts), 2)
        for p in parts:
            codes = [l[1:5] for l in p.split("\n")]
            self.assertTrue(all(codes.count(c) in (0, 150) for c in ("S001", "S002", "S003")))

    def test_split_evidence_oversize_source_splits_at_line(self):
        text = "\n".join(f"[S001:p1] câu {i}" for i in range(900))
        parts = agy_run.split_evidence(text, max_lines=400)
        self.assertEqual(len(parts), 3)
        self.assertEqual("\n".join(parts), text)

    def test_split_evidence_strips_control_characters(self):
        parts = agy_run.split_evidence("[S001:p1] a\x00b\x07c\tđ")
        self.assertEqual(parts, ["[S001:p1] abc\tđ"])

    def test_split_evidence_untagged_line_follows_previous(self):
        text = "[S001:p1] a\n(viết tay) b\n[S002:p1] c"
        self.assertEqual(agy_run.split_evidence(text, max_lines=2), ["[S001:p1] a\n(viết tay) b", "[S002:p1] c"])

    def test_note_on_blank_marker_or_table_line_rejected(self):
        body = agy_run.body_lines(BODY)
        for line in (1, 4, 5):
            self.assertTrue(agy_run.valid_note_errors({**NOTE, "line": line}, body), line)
        self.assertEqual(agy_run.valid_note_errors(NOTE, body), [])

    def test_source_pages_handles_several_codes_in_one_bracket(self):
        got = agy_run._source_pages("(x [C029:p24, C030:p2][S107:p13,p16][S088:p70-72])")
        self.assertEqual(got, {"C029:p24", "C030:p2", "S107:p13", "S107:p16", "S088:p70"})

    def test_note_with_resolve_rejected(self):
        bad = {**NOTE, "resolve": "Kết luận theo X: y [E1:p1]"}
        self.assertTrue(agy_run.valid_note_errors(bad, agy_run.body_lines(BODY)))


class TestSteps(FakeAgy, unittest.TestCase):
    L = "G9-B01"

    def setUp(self):
        super().setUp()
        os.environ["NHI_TOOLBOX_HOME"] = self.tmp
        self.dir = os.path.join(self.tmp, "kho", "lessons", self.L)
        os.makedirs(self.dir)
        with open(os.path.join(self.dir, "body_numbered.txt"), "w", encoding="utf-8") as f:
            f.write(BODY)
        # Xen kẽ S088 và S091 để mỗi phần đều có cả hai mã, dữ liệu giả CARDS hợp lệ ở mọi phần
        ev = "\n".join(f"[S{c}:p1] câu {i}" for i in range(300) for c in ("088", "091"))
        with open(os.path.join(self.dir, "evidence.md"), "w", encoding="utf-8") as f:
            f.write(ev)
        os.makedirs(os.path.join(self.tmp, "data"))
        with open(os.path.join(self.tmp, "data", "lessons.csv"), "w", encoding="utf-8") as f:
            f.write("lesson,book,title,start_printed,society,group\nG9-B01,G9,Bệnh,1,KDIGO 2025,Thận\n")

    def log(self):
        p = os.path.join(self.dir, "agy", "log.jsonl")
        return [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []

    def test_cards_parts_all_use_hydrogen(self):
        self.outputs(json.dumps(CARDS))
        self.assertEqual(agy_run.run(self.L, "cards"), 0)
        models = [r["model"] for r in self.log() if r["status"] == "ok"]
        self.assertEqual(models, [agy_run.HYDROGEN, agy_run.HYDROGEN])
        self.assertTrue(os.path.exists(os.path.join(self.dir, "cards_2.json")))

    def test_cards_with_source_code_not_in_evidence_rejected(self):
        part = agy_run.STEPS["cards"].parts(self.L)[0]
        bad = {**CARDS, "experience": ["mẹo [S999:p1]"]}
        errs = agy_run.STEPS["cards"].validate(bad, self.L, part)
        self.assertTrue(any("S999" in e for e in errs))
        self.assertEqual(agy_run.STEPS["cards"].validate(CARDS, self.L, part), [])

    def test_compose_with_source_code_not_in_cards_rejected(self):
        with open(os.path.join(self.dir, "cards_1.json"), "w", encoding="utf-8") as f:
            json.dump(CARDS, f)
        part = agy_run.STEPS["compose"].parts(self.L)[0]
        extra = {k: "" for k in ("summary", "approach", "experience", "exam", "conflicts", "missing")}
        bad = {"notes": [NOTE], "extra": {**extra, "experience": "mẹo [C067:p1]"}}
        self.assertTrue(any("C067" in e for e in agy_run.STEPS["compose"].validate(bad, self.L, part)))
        self.assertEqual(agy_run.STEPS["compose"].validate({"notes": [NOTE], "extra": extra}, self.L, part), [])

    def test_compose_dropping_too_many_card_pages_rejected(self):
        cards = {**CARDS, "notes": [{"line": 3, "note": f"(Slide: ý {i} [S088:p{i}])"} for i in range(1, 21)]}
        with open(os.path.join(self.dir, "cards_1.json"), "w", encoding="utf-8") as f:
            json.dump(cards, f)
        part = agy_run.STEPS["compose"].parts(self.L)[0]
        extra = {k: "" for k in ("summary", "approach", "experience", "exam", "conflicts", "missing")}
        keep = lambda n: {"notes": [{"line": 3, "note": "(Slide: " + "; ".join(f"ý {i} [S088:p{i}]" for i in range(1, n + 1)) + ")"}],
                          "extra": extra}
        errs = agy_run.STEPS["compose"].validate(keep(18), self.L, part)  # bỏ 2/20 = 10% là quá ngưỡng 5%
        self.assertTrue(any("S088:p19" in e for e in errs), errs)
        self.assertEqual(agy_run.STEPS["compose"].validate(keep(19), self.L, part), [])  # bỏ 1/20 = 5% vẫn cho qua

    def test_rerun_skips_valid_existing_part(self):
        self.outputs(json.dumps(CARDS))
        agy_run.run(self.L, "cards")
        n = len(self.calls())
        agy_run.run(self.L, "cards")
        self.assertEqual(len(self.calls()), n)
        agy_run.run(self.L, "cards", part=1, force=True)
        self.assertEqual(len(self.calls()), n + 1)

    def test_compose_writes_notes_and_extra(self):
        with open(os.path.join(self.dir, "cards_1.json"), "w", encoding="utf-8") as f:
            json.dump(CARDS, f)
        extra = {k: "" for k in ("summary", "approach", "experience", "exam", "conflicts", "missing")}
        self.outputs(json.dumps({"notes": [NOTE], "extra": extra}))
        self.assertEqual(agy_run.run(self.L, "compose"), 0)
        self.assertEqual(json.load(open(os.path.join(self.dir, "notes.json"), encoding="utf-8")), [NOTE])
        self.assertEqual(set(json.load(open(os.path.join(self.dir, "extra.json"), encoding="utf-8"))), set(extra))
        self.assertEqual(self.log()[-1]["model"], agy_run.HYDROGEN_HIGH)

    def test_agy_error_writes_nothing_and_logs(self):
        self.outputs(json.dumps(CARDS))
        os.environ["FAKE_AGY_EXIT"] = "1"
        self.assertNotEqual(agy_run.run(self.L, "cards"), 0)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "cards_1.json")))
        self.assertEqual(self.log()[-1]["status"], "error")

    def _review_tasks(self):
        rv = os.path.join(self.dir, "review")
        os.makedirs(rv)
        with open(os.path.join(rv, "tasks.json"), "w", encoding="utf-8") as f:
            json.dump([{"id": "p0010", "image": "p0010.png", "text": "p0010.txt", "start": 2, "end": 4},
                       {"id": "p0011", "image": "p0011.png", "text": "p0011.txt", "start": 5, "end": 6}], f)
        for name, text in (("p0010.txt", "2\tchân đoán a\n4\tdòng bốn"), ("p0011.txt", "6\tliều 2 mg")):
            with open(os.path.join(rv, name), "w", encoding="utf-8") as f:
                f.write(text)
        return rv

    def test_review_batch_writes_one_result_per_id(self):
        rv = self._review_tasks()
        self.outputs(json.dumps({"p0010": [{"line": 2, "old": "chân", "new": "chẩn"}], "p0011": []}))
        self.assertEqual(agy_run.run(self.L, "review"), 0)
        self.assertEqual(json.load(open(os.path.join(rv, "results", "p0011.json"), encoding="utf-8")), [])

    def test_review_part_lists_each_image_and_text_file(self):
        rv = self._review_tasks()
        part = agy_run.STEPS["review"].parts(self.L)[0]
        for name in ("p0010.png", "p0010.txt", "p0011.png", "p0011.txt"):
            self.assertIn(os.path.join(rv, name), part.inputs)

    def test_review_item_with_bad_line_old_or_unverified_digit_rejected(self):
        self._review_tasks()
        bad = [{"line": 9, "old": "a", "new": "b"},            # ngoài trang
               {"line": 2, "old": "không có", "new": "b"},      # old không nằm trong dòng
               {"line": 2, "old": "a", "new": "4"}]             # đổi số mà không verified
        for item in bad:
            errs = agy_run.STEPS["review"].validate({"p0010": [item], "p0011": []}, self.L,
                                                    agy_run._batch_parts(os.path.join(self.dir, "review", "tasks.json"),
                                                                         os.path.join(self.dir, "review"))[0])
            self.assertTrue(errs, item)

    def _blocks(self):
        with open(os.path.join(self.dir, "fixed.txt"), "w", encoding="utf-8") as f:
            f.write("<<p10>>\n<<block:p0010a>>\nbảng\n<<endblock>>\n<<block:p0010f>>\nhình\n<<endblock>>")
        os.makedirs(os.path.join(self.dir, "review"), exist_ok=True)

    def test_blocks_writes_md_and_crops_figures(self):
        self._blocks()
        crops = []
        old = agy_run.crop_block
        agy_run.crop_block = lambda lesson, page, box, name: crops.append((page, tuple(box), name))
        try:
            self.outputs(json.dumps({"p0010a": {"md": "| A | B |\n|---|---|\n| 1 | 2 |", "crop": None},
                                     "p0010f": {"md": "![Hình](fig/p0010f.png)", "crop": [0.1, 0.2, 0.9, 0.6]}}))
            self.assertEqual(agy_run.run(self.L, "blocks"), 0)
        finally:
            agy_run.crop_block = old
        self.assertEqual(crops, [(10, (0.1, 0.2, 0.9, 0.6), "p0010f")])
        md = open(os.path.join(self.dir, "blocks", "p0010a.md"), encoding="utf-8").read()
        self.assertIn("|---|", md)
        part = agy_run.STEPS["blocks"].parts(self.L)[0]
        self.assertIn(os.path.join(self.dir, "review", "p0010.png"), part.inputs)

    def test_blocks_figure_needs_valid_crop(self):
        self._blocks()
        part = agy_run.STEPS["blocks"].parts(self.L)[0]
        table = {"md": "| A |\n|---|", "crop": None}
        for fig in ({"md": "![Hình](fig/p0010f.png)", "crop": None},
                    {"md": "![Hình](fig/p0010f.png)", "crop": [0.9, 0.2, 0.1, 0.6]},
                    {"md": "chữ", "crop": [0.1, 0.2, 0.9, 0.6]}):
            self.assertTrue(agy_run.STEPS["blocks"].validate({"p0010a": table, "p0010f": fig}, self.L, part), fig)

    def test_run_does_not_mark_progress_steps_done(self):
        self.outputs(json.dumps(CARDS))
        agy_run.run(self.L, "cards")
        state = json.load(open(os.path.join(self.tmp, "data", "progress.json"), encoding="utf-8")) \
            if os.path.exists(os.path.join(self.tmp, "data", "progress.json")) else {}
        self.assertNotIn("B5", state.get(self.L, {}))


if __name__ == "__main__":
    unittest.main()
