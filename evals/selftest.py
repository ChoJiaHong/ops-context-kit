#!/usr/bin/env python3
"""不呼叫模型，檢查評估案例本身有沒有寫對：

每個案例的 selftest.json 有兩條「模擬的 agent 行為」：
  good  照規則做 → 所有可程式判定的 grader 都要通過
  bad   典型的錯誤做法 → 至少一個 grader 要失敗（代表這個案例有鑑別力）

會真的執行 scaffold.sh 與模擬器；llm grader 會略過（要跑真的評估才知道）。
用法：python3 evals/selftest.py [案例名稱片段]
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import build_workspace_base, case_meta, cases  # noqa: E402

DETERMINISTIC = {"regex", "tool_used", "tool_order", "file_exists"}


def encode(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def run_actions(ws, home, actions):
    env = dict(os.environ, HOME=home)
    calls = []
    for a in actions:
        tool = a["tool"]
        inp = {k: v for k, v in a.items() if k != "tool"}
        calls.append((tool, inp))
        if tool == "Bash":
            subprocess.run(["bash", "-c", a["command"]], cwd=ws, env=env, capture_output=True, text=True, timeout=60)
        elif tool == "Write":
            path = os.path.join(ws, a["file_path"])
            os.makedirs(os.path.dirname(path) or ws, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(a["content"])
        elif tool == "Edit":
            path = os.path.join(ws, a["file_path"])
            text = open(path, encoding="utf-8").read()
            if a["old_string"] not in text:
                raise RuntimeError(f"selftest Edit 找不到 old_string：{a['old_string']!r}")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace(a["old_string"], a["new_string"], 1))
    return calls


def listing(ws):
    out = set()
    for d, _, files in os.walk(ws):
        for name in files:
            out.add(os.path.relpath(os.path.join(d, name), ws))
    return out


def target_text(g, ws, calls, created):
    target = g.get("target", "last_message")
    if target == "trace":
        return "\n".join(encode({"type": "tool_use", "name": t, "input": i}) for t, i in calls)
    if target == "files":
        return "\n".join(sorted(created))
    if isinstance(target, dict) and target.get("source") == "file":
        path = os.path.join(ws, target["path"])
        return open(path, encoding="utf-8").read() if os.path.exists(path) else None
    return None  # last_message：模擬不了


def grade(g, ws, calls, created):
    kind = g["type"]
    if kind == "regex":
        text = target_text(g, ws, calls, created)
        if text is None:
            return None if g.get("target", "last_message") == "last_message" else False
        flags = re.I if "i" in g.get("flags", "") else 0
        hits = len(re.findall(g["pattern"], text, flags))
        match = g.get("match", "contains")
        if match == "not_contains":
            return hits == 0
        if match.startswith("count:"):
            return hits == int(match.split(":", 1)[1])
        return hits > 0
    if kind == "tool_used":
        n = sum(1 for t, i in calls if t == g["tool"]
                and (not g.get("input_match") or re.search(g["input_match"], encode(i))))
        return g.get("min", 1) <= n <= g.get("max", float("inf"))
    if kind == "tool_order":
        def first(spec):
            spec = spec if isinstance(spec, dict) else {"tool": spec}
            for idx, (t, i) in enumerate(calls):
                if t == spec["tool"] and (not spec.get("input_match") or re.search(spec["input_match"], encode(i))):
                    return idx
            return None
        b, a = first(g["before"]), first(g["after"])
        return b is not None and a is not None and b < a
    if kind == "file_exists":
        hit = any(fnmatch.fnmatch(p, g["path"]) for p in created)
        return hit if g.get("exists", True) else not hit
    return None


def run_variant(case_dir, meta, actions):
    with tempfile.TemporaryDirectory() as tmp:
        ws, home = os.path.join(tmp, "ws"), os.path.join(tmp, "home")
        os.makedirs(ws)
        os.makedirs(home)
        r = subprocess.run(["bash", os.path.join(case_dir, "scaffold.sh")], cwd=ws,
                           env=dict(os.environ, HOME=home), capture_output=True, text=True, timeout=120)
        if r.returncode:
            return {"_scaffold": f"失敗：{r.stderr.strip()[-300:]}"}
        before = listing(ws)
        calls = run_actions(ws, home, actions)
        created = listing(ws) - before
        return {name: grade(g, ws, calls, created) for name, g in meta["graders"].items() if g["type"] in DETERMINISTIC}


def main():
    build_workspace_base()
    flt = sys.argv[1] if len(sys.argv) > 1 else ""
    failures = 0
    for case_dir in cases():
        if flt not in os.path.basename(case_dir):
            continue
        meta = case_meta(case_dir)
        with open(os.path.join(case_dir, "selftest.json"), encoding="utf-8") as f:
            spec = json.load(f)
        good = run_variant(case_dir, meta, spec["good"])
        bad = run_variant(case_dir, meta, spec["bad"])
        good_ok = all(v is not False for v in good.values()) and "_scaffold" not in good
        bad_ok = any(v is False for v in bad.values())
        status = "✅" if good_ok and bad_ok else "❌"
        failures += status == "❌"
        fmt = lambda d: " ".join(f"{k}={'✓' if v else ('–' if v is None else '✗')}" for k, v in d.items())
        print(f"{status} {meta['name']}\n    good: {fmt(good)}\n    bad:  {fmt(bad)}")
    print(f"\n{'全部通過' if not failures else f'{failures} 個案例有問題'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
