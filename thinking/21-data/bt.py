#!/usr/bin/env python3
"""回測實驗的輔助程式。

  bt.py split                      依固定種子把 kept 的題卡分成 dev / heldout
  bt.py problems <set>             產生給作答者看的題目（只有 problem 與 context）
  bt.py packets <set> <run>...     把各組答案的 Proposals 抽出、打亂、去標籤，產生評審包與對照表
  bt.py score <set>                讀評審結果，解盲，計分
"""
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20261107


def cards():
    return [c for c in json.loads((HERE / "cases.json").read_text()) if c["verdict"].startswith("keep")]


def split():
    ids = sorted(c["id"] for c in cards())
    rng = random.Random(SEED)
    rng.shuffle(ids)
    half = len(ids) // 2
    out = {"dev": sorted(ids[:half]), "heldout": sorted(ids[half:])}
    (HERE / "split.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


def subset(name):
    ids = json.loads((HERE / "split.json").read_text())[name]
    by = {c["id"]: c for c in cards()}
    return [by[i] for i in ids]


def problems(name):
    lines = [f"# Problems ({name})\n"]
    for c in subset(name):
        lines += [f"## {c['id']}\n", f"Problem: {c['problem']}\n", f"Context: {c['context']}\n"]
    path = HERE / "runs" / f"problems-{name}.md"
    path.write_text("\n".join(lines))
    print(path)


def proposals(text):
    """回傳 {case_id: 'P1: ...\nP2: ...'}，只取 Proposals 段落。"""
    out = {}
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        cid = block.split("\n", 1)[0].strip()
        m = re.search(r"^### Proposals\s*\n(.*)", block, flags=re.M | re.S)
        out[cid] = m.group(1).strip() if m else ""
    return out


def packets(name, runs):
    rng = random.Random(f"{SEED}-{name}")
    answers = {r: proposals((HERE / "runs" / f"{r}.md").read_text()) for r in runs}
    key, lines = {}, [f"# Judge packet ({name})\n"]
    for c in subset(name):
        order = list(runs)
        rng.shuffle(order)
        key[c["id"]] = {}
        lines += [
            f"## {c['id']}\n",
            f"Problem: {c['problem']}\n",
            "Core mechanism of the real tool:\n" + "\n".join(f"- {m}" for m in c["core_mechanism"]) + "\n",
            f"Score 2 (full match): {c['full_match']}\n",
            f"Score 1 (partial match): {c['partial_match']}\n",
            f"Score 0 (not a match), including: {'; '.join(c['not_a_match'])}\n",
        ]
        for i, r in enumerate(order, 1):
            label = f"S{i}"
            key[c["id"]][label] = r
            body = answers[r].get(c["id"]) or "(no proposals)"
            lines += [f"### {label}\n", body + "\n"]
    (HERE / "judge" / f"packet-{name}.md").write_text("\n".join(lines))
    (HERE / "judge" / f"key-{name}.json").write_text(json.dumps(key, indent=2) + "\n")
    print(HERE / "judge" / f"packet-{name}.md")


def arm(run):
    return run.split("-")[0]


def score(name):
    key = json.loads((HERE / "judge" / f"key-{name}.json").read_text())
    judges = sorted((HERE / "judge").glob(f"scores-{name}-*.json"))
    rows = {}  # (case, run) -> list of (best, p1, alt)
    for j in judges:
        for item in json.loads(j.read_text()):
            run = key[item["case"]][item["set"]]
            rows.setdefault((item["case"], run), []).append((item["best"], item["p1"], item.get("alt", False)))
    runs = sorted({r for (_, r) in rows})
    arms = sorted({arm(r) for r in runs})
    cases = [c["id"] for c in subset(name)]

    def mean(xs):
        return sum(xs) / len(xs) if xs else float("nan")

    per = {}  # (case, arm) -> mean best over runs and judges
    for cid in cases:
        for a in arms:
            vals = [v for (c, r), vs in rows.items() if c == cid and arm(r) == a for v in vs]
            per[(cid, a)] = (mean([v[0] for v in vals]), mean([v[1] for v in vals]), mean([1.0 if v[2] else 0.0 for v in vals]))
    print(f"judges: {[j.name for j in judges]}")
    print("case".ljust(28) + "".join(a.rjust(8) for a in arms))
    for cid in cases:
        print(cid.ljust(28) + "".join(f"{per[(cid, a)][0]:8.2f}" for a in arms))
    print("-" * (28 + 8 * len(arms)))
    for label, k in (("mean best", 0), ("mean P1", 1), ("alt rate", 2)):
        print(label.ljust(28) + "".join(f"{mean([per[(c, a)][k] for c in cases]):8.2f}" for a in arms))
    print("hit rate (best>=1.5)".ljust(28) + "".join(f"{mean([1.0 if per[(c, a)][0] >= 1.5 else 0.0 for c in cases]):8.2f}" for a in arms))
    # 逐題比較：C 對其他組的勝負
    for a in arms:
        for b in arms:
            if a < b:
                w = sum(per[(c, a)][0] > per[(c, b)][0] for c in cases)
                l = sum(per[(c, a)][0] < per[(c, b)][0] for c in cases)
                print(f"{a} vs {b}: {a} wins {w}, loses {l}, ties {len(cases) - w - l}")
    # 評審一致度
    agree = [len({v[0] for v in vs}) == 1 for vs in rows.values() if len(vs) > 1]
    if agree:
        print(f"judge agreement on best score: {sum(agree)}/{len(agree)}")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"split": lambda: split(), "problems": lambda: problems(args[0]),
     "packets": lambda: packets(args[0], args[1:]), "score": lambda: score(args[0])}[cmd]()
