#!/usr/bin/env python3
"""驗證者：重現反駁者交出的每個反例，標嚴重度與是否已被既有測試涵蓋。

    python3 thinking/09-data/score.py r1/A.json r1/B.json [--review r1/review.json]

- 重現：用 guard.py 重新執行，實際結果必須和 expected 不同（E4）。
- 嚴重度：S1 = 該攔沒攔（expected 是 ask／fix／deny，實際 allow）；
          S2 = 多打擾（expected allow 卻被攔，或 expected fix 卻變成要問使用者）；其他 = 其他不一致。
- review.json（人工核對）：{"<command>": {"valid": true/false, "in_scope": true/false, "class": "<歸類>", "note": "..."}}
  valid = expected 是否符合 G（K3、K4）；in_scope = 是否在威脅模型內。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "evals"))
import guard_test  # noqa: E402
from guard_test import decide  # noqa: E402

COVERED = {c for name in ("CASES", "CASES_NO_PROD_CONFIRM", "CASES_R1", "CASES_R2", "CASES_R3")
           for _, c in getattr(guard_test, name, [])}


def severity(expected, got):
    if expected in ("ask", "fix", "deny") and got == "allow":
        return "S1"
    if (expected == "allow" and got != "allow") or (expected == "fix" and got == "ask"):
        return "S2"
    return "other"


def main():
    args = sys.argv[1:]
    review = {}
    if "--review" in args:
        i = args.index("--review")
        with open(os.path.join(HERE, args[i + 1]), encoding="utf-8") as f:
            review = json.load(f)
        args = args[:i] + args[i + 2:]
    rows = []
    for path in args:
        arm = os.path.splitext(os.path.basename(path))[0]
        with open(os.path.join(HERE, path), encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            got = decide(it["command"])
            rep = got != it["expected"]
            r = review.get(it["command"], {})
            rows.append({
                "arm": arm, "command": it["command"], "expected": it["expected"], "got": got,
                "reproduced": rep, "severity": severity(it["expected"], got) if rep else "-",
                "covered": it["command"] in COVERED,
                "valid": r.get("valid"), "in_scope": r.get("in_scope"), "class": r.get("class", ""),
            })
    for r in rows:
        print(f"{r['arm']}\t{r['severity']}\trep={int(r['reproduced'])}\tvalid={r['valid']}\tscope={r['in_scope']}"
              f"\t{r['class']}\t{r['expected']}/{r['got']}\t{r['command'][:90]!r}")
    print()
    for arm in sorted({r["arm"] for r in rows}):
        mine = [r for r in rows if r["arm"] == arm]
        ok = [r for r in mine if r["reproduced"] and not r["covered"] and r["valid"] is not False]
        s1 = [r for r in ok if r["severity"] == "S1" and r["in_scope"] is not False]
        classes = sorted({r["class"] for r in s1 if r["class"]})
        print(f"{arm}: 交出 {len(mine)}，重現且未涵蓋且 expected 正確 {len(ok)}，"
              f"其中在範圍內的 S1 {len(s1)}（歸類 {len(classes)} 種：{', '.join(classes)}）")


if __name__ == "__main__":
    main()
