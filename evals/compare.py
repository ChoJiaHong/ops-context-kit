#!/usr/bin/env python3
"""讀 run.sh 產生的 <arm>.json，輸出比較報告與剪枝建議（思考模型第 ⑦ 步）。

用法：python3 evals/compare.py evals/results/<時間戳記> [--eps 0.10] [--delta 0.15]
輸出：終端機表格 + <結果目錄>/summary.md
"""
import argparse
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import case_meta, cases  # noqa: E402

TIE = 0.05


def load(results_dir):
    arms, baseline, notes = {}, {}, []
    for path in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        arm = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        if doc.get("partial"):
            notes.append(f"{arm}：結果不完整（{doc.get('partialReason')}），比較時要小心")
        scores = {}
        for c in doc.get("cases", []):
            agg = c.get("aggregates") or {}
            if agg.get("score") is None:
                continue
            scores[c["name"]] = agg["score"]
            if agg.get("delta") is not None and c["name"] not in baseline:
                baseline[c["name"]] = agg["score"] - agg["delta"]
        arms[arm] = scores
    if baseline:
        arms = {"a0": baseline, **arms}
    return arms, notes


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def sign_test(wins, losses):
    """雙尾精確二項檢定（排除平手）。"""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def fmt(x):
    return "  –  " if x is None else f"{x:5.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("--eps", type=float, default=0.10, help="規則貢獻低於這個值就建議刪除")
    ap.add_argument("--delta", type=float, default=0.15, help="任何案例因為這條規則退步超過這個值，就建議改寫")
    args = ap.parse_args()

    arms, notes = load(args.results_dir)
    if not arms:
        sys.exit("結果目錄裡沒有 <arm>.json")
    tags = {os.path.basename(d): case_meta(d).get("tags", []) for d in cases()}
    names = sorted({n for s in arms.values() for n in s})
    order = sorted(arms, key=lambda a: (a != "a0", not a.startswith("a1"), not a.startswith("a2"), a))
    lines = []

    lines.append("## 各案例分數（0–1，多次執行的平均）\n")
    lines.append("| 案例 | tags | " + " | ".join(order) + " |")
    lines.append("|---|---|" + "---|" * len(order))
    for n in names:
        lines.append(f"| {n} | {' '.join(tags.get(n, []))} | " + " | ".join(fmt(arms[a].get(n)) for a in order) + " |")
    lines.append("| **平均** | | " + " | ".join(fmt(mean(arms[a].get(n) for n in names)) for a in order) + " |\n")

    if "a3" in arms:
        lines.append("## a3 和其他組的配對比較\n")
        lines.append(f"| 對照組 | a3 平均差 | a3 勝 | a3 敗 | 平手(±{TIE}) | 符號檢定 p |")
        lines.append("|---|---|---|---|---|---|")
        for other in [a for a in order if a != "a3" and not a.startswith("a3-no-")]:
            pairs = [(arms["a3"][n], arms[other][n]) for n in names if n in arms["a3"] and n in arms[other]]
            if not pairs:
                continue
            w = sum(1 for x, y in pairs if x - y > TIE)
            lo = sum(1 for x, y in pairs if y - x > TIE)
            lines.append(f"| {other} | {mean(x - y for x, y in pairs):+.2f} | {w} | {lo} | {len(pairs) - w - lo} | "
                         f"{sign_test(w, lo):.3f} |")
        lines.append("")

        ablations = [a for a in order if a.startswith("a3-no-")]
        if ablations:
            lines.append(f"## 規則剪枝（c_k = a3 − a3-no-K，只算標了 K 的案例；ε={args.eps}、δ={args.delta}）\n")
            lines.append("| 規則 | 相關案例 | c_k | 拿掉後最多變好 | 建議 |")
            lines.append("|---|---|---|---|---|")
            for ab in ablations:
                rid = ab.split("a3-no-", 1)[1]
                tag = "K4" if rid == "K4g" else rid
                rel = [n for n in names if tag in tags.get(n, []) and n in arms["a3"] and n in arms[ab]]
                if not rel:
                    lines.append(f"| {rid} | （沒有標 {tag} 的案例） | – | – | 先補案例 |")
                    continue
                c = mean(arms["a3"][n] - arms[ab][n] for n in rel)
                worst = max(arms[ab][n] - arms["a3"][n] for n in rel)
                if worst > args.delta:
                    advice = "有案例因這條規則退步：改寫"
                elif c < args.eps:
                    advice = "貢獻不足：考慮刪除或合併"
                else:
                    advice = "保留"
                lines.append(f"| {rid} | {len(rel)} | {c:+.2f} | {worst:+.2f} | {advice} |")
            lines.append("")

    if notes:
        lines.append("## 注意\n")
        lines.extend(f"- {n}" for n in notes)
        lines.append("")
    lines.append("判讀：分數差小於 ±0.05 視為平手；案例數少時符號檢定的 p 值偏大，要累積更多案例再下結論。")

    text = "\n".join(lines) + "\n"
    print(text)
    with open(os.path.join(args.results_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("# 實驗結果\n\n" + text)


if __name__ == "__main__":
    main()
