#!/usr/bin/env python3
"""彙整盲測思想實驗：解盲、合併兩個小組、算分數、一致性、反事實消融，並輸出 compare.py 可讀的結果檔。

用法：python3 evals/thought/analyze.py [目錄]（預設 evals/thought/run；要有 mapping.json 與 out/*.json）
輸出：<目錄>/report.md、<目錄>/results/*.json
"""
import glob
import json
import math
import os
import statistics as st
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KIT, "evals", "thought", "run")
sys.path.insert(0, f"{KIT}/evals")
from lib import case_meta, cases  # noqa: E402

# A3 的 § 編號 → 規則 ID；消融時一起拿掉的項目
# 消融時要一起拿掉的項目：§n = 規則 Kn 的文字；H1 = 任務清單 hook（K2）；H2 = guard（K3/K4 的保證層）；H3 = PreCompact（K1）
def ablations():
    import re
    text = open(os.path.join(KIT, "template", "AGENTS.md"), encoding="utf-8").read()
    ids = re.findall(r"<!--\s*rule:K(\d+)\s*-->", text)
    abl = {f"K{i}": {f"§{i}"} for i in ids}
    abl.setdefault("K1", set()).add("H3")
    abl.setdefault("K2", set()).add("H1")
    abl.setdefault("K4", set()).add("H2")
    abl["K4g"] = {"H2"}
    return abl


ABLATIONS = ablations()


def load():
    mapping = json.load(open(f"{HERE}/mapping.json"))["panels"]
    data = {}  # data[panel][case][arm][grader] = {"p":…, "decisive":[…]}
    behaviors, notes = {}, {}
    for path in sorted(glob.glob(f"{HERE}/out/*.json")):
        doc = json.load(open(path, encoding="utf-8"))
        panel = os.path.basename(path)[0]
        for code, arms in doc["cases"].items():
            for x, res in arms.items():
                arm = mapping[panel][x]
                data.setdefault(panel, {}).setdefault(code, {})[arm] = res["graders"]
                behaviors.setdefault(code, {}).setdefault(arm, {})[panel] = res.get("behavior", "")
        for code, note in (doc.get("notes") or {}).items():
            notes.setdefault(code, {})[panel] = note
    return data, behaviors, notes


def weights():
    w = {}
    for d in cases():
        meta = case_meta(d)
        w[meta["name"][:3]] = {g: float(v.get("weight", 1)) for g, v in meta["graders"].items()}
    return w


def case_score(gr, wts, override=None):
    total = sum(wts.values())
    s = 0.0
    for g, wt in wts.items():
        p = (override or {}).get(g, gr.get(g, {}).get("p"))
        if p is None:
            return None
        s += wt * p
    return s / total


def pearson(xs, ys):
    if len(xs) < 3:
        return float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx and sy else float("nan")


def main():
    data, behaviors, notes = load()
    W = weights()
    codes = sorted(W)
    arms = ["a0", "a1", "a2", "a3"]
    panels = sorted(data)

    # 各小組的案例分數
    scores = {p: {c: {a: case_score(data[p][c][a], W[c]) for a in arms if a in data[p].get(c, {})}
                  for c in codes if c in data[p]} for p in panels}

    # 反事實消融（每個小組各算，再平均）
    abl = {}
    for p in panels:
        for c in codes:
            if c not in data[p] or "a3" not in data[p][c]:
                continue
            a3, a0 = data[p][c]["a3"], data[p][c]["a0"]
            for k, items in ABLATIONS.items():
                override = {}
                for g, v in a3.items():
                    if v["p"] >= 0.5 and set(v.get("decisive", [])) & items:
                        override[g] = a0[g]["p"]
                abl.setdefault(k, {}).setdefault(c, []).append(case_score(a3, W[c], override))

    # 合併兩組
    merged = {a: {} for a in arms}
    for c in codes:
        for a in arms:
            vals = [scores[p][c][a] for p in panels if c in scores[p] and a in scores[p][c]]
            if vals:
                merged[a][c] = st.mean(vals)
    for k, per_case in abl.items():
        merged[f"a3-no-{k}"] = {c: st.mean(v) for c, v in per_case.items()}

    # 一致性
    gx, gy, cx, cy, top_agree, n_cases = [], [], [], [], 0, 0
    if len(panels) == 2:
        pa, pb = panels
        for c in codes:
            if c not in data[pa] or c not in data[pb]:
                continue
            n_cases += 1
            for a in arms:
                for g in W[c]:
                    gx.append(data[pa][c][a][g]["p"])
                    gy.append(data[pb][c][a][g]["p"])
                cx.append(scores[pa][c][a])
                cy.append(scores[pb][c][a])
            ra = max(arms, key=lambda a: scores[pa][c][a])
            rb = max(arms, key=lambda a: scores[pb][c][a])
            top_agree += ra == rb

    # 輸出成 compare.py 的格式
    res_dir = f"{HERE}/results"
    os.makedirs(res_dir, exist_ok=True)
    for f in glob.glob(f"{res_dir}/*.json"):
        os.remove(f)
    for a, sc in merged.items():
        if a == "a0":
            continue
        doc = {"schemaVersion": 1, "partial": False, "cases": []}
        for c in codes:
            if c not in sc:
                continue
            name = next(os.path.basename(d) for d in cases() if os.path.basename(d).startswith(c))
            agg = {"score": round(sc[c], 4)}
            if a == "a1" and c in merged["a0"]:
                agg["delta"] = round(sc[c] - merged["a0"][c], 4)
            doc["cases"].append({"name": name, "aggregates": agg})
        json.dump(doc, open(f"{res_dir}/{a}.json", "w"), indent=1)

    out = subprocess.run(["python3", f"{KIT}/evals/compare.py", res_dir], capture_output=True, text=True).stdout

    lines = ["# 第 1 輪思想實驗結果（盲測、兩個獨立評分小組）", ""]
    lines.append(f"- 評分者：{len(glob.glob(f'{HERE}/out/*.json'))} 位（小組 {', '.join(panels)}），每個案例由兩個小組各評一次。")
    if gx:
        mad = st.mean(abs(x - y) for x, y in zip(gx, gy))
        lines.append(f"- grader 層級一致性：平均絕對差 {mad:.2f}，Pearson r = {pearson(gx, gy):.2f}（n={len(gx)}）")
        lines.append(f"- 案例分數一致性：Pearson r = {pearson(cx, cy):.2f}（n={len(cx)}）；兩組認定的最佳組別相同：{top_agree}/{n_cases} 個案例")
    lines.append("- 消融分數是反事實推估：評分者指出某條規則是關鍵時，拿掉它就退回「無規則組」的機率。")
    lines.append("")
    lines.append(out)

    # A3 的弱點（失敗歸因用）
    lines.append("## a3 的弱點：兩組平均通過機率 < 0.7 的 grader\n")
    lines.append("| 案例 | grader | a3 p | a0 p | 評分者預測的 a3 行為（小組 A／B） |")
    lines.append("|---|---|---|---|---|")
    for c in codes:
        for g in W[c]:
            ps = [data[p][c]["a3"][g]["p"] for p in panels if c in data[p]]
            p0 = [data[p][c]["a0"][g]["p"] for p in panels if c in data[p]]
            if ps and st.mean(ps) < 0.7:
                beh = " ／ ".join(behaviors[c]["a3"].get(p, "")[:220].replace("|", "\\|").replace("\n", " ") for p in panels)
                lines.append(f"| {c} | {g} | {st.mean(ps):.2f} | {st.mean(p0):.2f} | {beh} |")
    lines.append("")
    lines.append("## 評分者的不確定點\n")
    for c in codes:
        for p in panels:
            if notes.get(c, {}).get(p):
                lines.append(f"- **{c}（{p}）**：{notes[c][p]}")
    report = "\n".join(lines) + "\n"
    open(f"{HERE}/report.md", "w", encoding="utf-8").write(report)
    print(report)


if __name__ == "__main__":
    main()
