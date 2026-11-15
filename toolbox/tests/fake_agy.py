"""agy giả cho test.

FAKE_AGY_OUT: JSON mảng chuỗi, lượt thứ i in phần tử i (hết thì in phần tử cuối).
FAKE_AGY_EXIT: mã thoát (mặc định 0). FAKE_AGY_SLEEP: số giây ngủ trước khi in.
FAKE_AGY_STATE: file JSON ghi lại các lượt gọi {"argv": [...], "prompt": "..."}.
"""
import json
import os
import sys
import time

state_path = os.environ["FAKE_AGY_STATE"]
calls = json.load(open(state_path, encoding="utf-8")) if os.path.exists(state_path) else []
argv = sys.argv[1:]
prompt = argv[argv.index("-p") + 1] if "-p" in argv else ""
calls.append({"argv": argv, "prompt": prompt})
with open(state_path, "w", encoding="utf-8") as f:
    json.dump(calls, f, ensure_ascii=False)

time.sleep(float(os.environ.get("FAKE_AGY_SLEEP", "0")))
outs = json.loads(os.environ.get("FAKE_AGY_OUT", '[""]'))
sys.stdout.reconfigure(encoding="utf-8")
text = outs[min(len(calls) - 1, len(outs) - 1)]
if "--output-format" in argv and argv[argv.index("--output-format") + 1] == "json":
    status = os.environ.get("FAKE_AGY_STATUS", "SUCCESS")
    wrapper = {"status": status, "response": text}
    if os.environ.get("FAKE_AGY_DENIED"):
        wrapper["denied_actions"] = [{"action": "command", "display_name": "Bash"}]
    print(json.dumps(wrapper, ensure_ascii=False))
else:
    print(text)
code = int(os.environ.get("FAKE_AGY_EXIT", "0"))
if code:
    print("AGY_ERROR: {\"status\":\"FAKE\"}", file=sys.stderr)
sys.exit(code)
