#!/usr/bin/env python3
"""第 2 輪分析：解盲、結果／流程／成本分開，方法效果（a3 vs a4）、機制效果（+hook），跨模型一致性。"""
import glob
import json
import math
import os
import re
import statistics as st

R2 = os.environ.get("ROUND2_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "method", "round2-data")
ARMS = ["a0", "a3", "a4", "a3H", "a4H"]


def graders():
    """從案例檔解析 grader 類型、權重，以及該停下還是直接做。"""
    info = {}
    for path in sorted(glob.glob(f"{R2}/cases/d??.md")):
        code = os.path.basename(path)[:3]
        text = open(path, encoding="utf-8").read()
        gs = {}
        for m in re.finditer(r"^- `([^`]+)`（\s*(outcome|process|cost)[^）]*?(?:權重\s*([\d.]+))?\s*）", text, re.M):
            gs[m.group(1)] = {"type": m.group(2), "w": float(m.group(3) or 1)}
        right = text.split("## 正確做法", 1)[1].split("## Graders", 1)[0] if "## 正確做法" in text else ""
        should_stop = None
        if re.search(r"應該停下|應停下|停下來問", right) and not re.search(r"應該直接做完|應直接做|不需要停下|不應該停下", right):
            should_stop = True
        elif re.search(r"應該直接做完|應直接做|不需要停下|不應該停下|直接做完", right):
            should_stop = False
        title = re.search(r"^# 案例 d\d\d：(.+)$", text, re.M)
        info[code] = {"graders": gs, "should_stop": should_stop, "title": title.group(1).strip() if title else code}
    return info


def load():
    mp = json.load(open(f"{R2}/mapping.json"))
    data = {}
    for path in sorted(glob.glob(f"{R2}/out/*.json")):
        panel = os.path.basename(path)[0]
        doc = json.load(open(path, encoding="utf-8"))
        for code, xs in doc["cases"].items():
            for x, res in xs.items():
                data.setdefault(panel, {}).setdefault(code, {})[mp["panels"][panel][x]] = res
    return data, mp


def score(res, gs, kind=None):
    items = [(g, v) for g, v in gs.items() if kind is None or v["type"] == kind]
    if not items:
        return None
    return sum(v["w"] * float(res["graders"][g]) for g, v in items) / sum(v["w"] for _, v in items)


def pearson(x, y):
    mx, my = st.mean(x), st.mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float("nan")


def m(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None


def f(x):
    return "–" if x is None else f"{x:.2f}"


def main():
    info = graders()
    data, mp = load()
    panels = sorted(data)
    codes = sorted(info)
    for c in codes:
        for p in panels:
            for a in ARMS:
                missing = set(info[c]["graders"]) - set(data[p][c][a]["graders"])
                assert not missing, (p, c, a, missing)

    # 每個 (小組, 案例, 組別) 的分數
    S = {}
    for p in panels:
        for c in codes:
            for a in ARMS:
                r = data[p][c][a]
                gs = info[c]["graders"]
                S[(p, c, a)] = {"all": score(r, gs), "outcome": score(r, gs, "outcome"),
                                "process": score(r, gs, "process"), "cost": score(r, gs, "cost"),
                                "calls": float(r.get("tool_calls", 0)), "stop": float(r.get("stop", 0))}

    def avg(a, key, cs=codes, ps=panels):
        return m([S[(p, c, a)][key] for p in ps for c in cs])

    L = ["# 第 2 輪思想實驗結果", ""]
    L.append(f"- 案例：{len(codes)} 個，由獨立作者只依需求撰寫（看不到任何規則集）")
    L.append(f"- 評分者：小組 A（{mp['models']['A']}）、小組 B（{mp['models']['B']}），每個案例兩組各評一次")
    xs = [data["A"][c][a]["graders"][g] for c in codes for a in ARMS for g in info[c]["graders"]]
    ys = [data["B"][c][a]["graders"][g] for c in codes for a in ARMS for g in info[c]["graders"]]
    L.append(f"- 跨模型一致性：grader 層級 r = {pearson(xs, ys):.2f}，平均絕對差 {st.mean(abs(a - b) for a, b in zip(xs, ys)):.2f}（n={len(xs)}）")
    agree = sum(1 for c in codes if (S[("A", c, "a3")]["all"] - S[("A", c, "a4")]["all"]) * (S[("B", c, "a3")]["all"] - S[("B", c, "a4")]["all"]) > 0)
    L.append(f"- 兩組對「a3 和 a4 哪個好」方向一致的案例：{agree}/{len(codes)}")
    L.append("")

    L.append("## 各組總覽（兩組評分平均）\n")
    L.append("| 組別 | 總分 | 結果 outcome | 流程 process | 成本 cost | 預期工具呼叫 | 停下發問機率（該直接做的案例） | 停下發問機率（該停下的案例） |")
    L.append("|---|---|---|---|---|---|---|---|")
    go = [c for c in codes if info[c]["should_stop"] is False]
    halt = [c for c in codes if info[c]["should_stop"] is True]
    names = {"a0": "a0 無規則", "a3": "a3 本規則集（純文字）", "a4": "a4 獨立 SRE 規則（純文字）",
             "a3H": "a3 + hook", "a4H": "a4 + hook"}
    for a in ARMS:
        L.append(f"| {names[a]} | {f(avg(a, 'all'))} | {f(avg(a, 'outcome'))} | {f(avg(a, 'process'))} | {f(avg(a, 'cost'))} | "
                 f"{avg(a, 'calls'):.1f} | {f(avg(a, 'stop', go))} | {f(avg(a, 'stop', halt))} |")
    L.append("")

    L.append("## 效果拆解（正值代表前者較好）\n")
    L.append("| 比較 | 總分 | 結果 | 流程 | 成本 | 工具呼叫差 |")
    L.append("|---|---|---|---|---|---|")
    for label, x, y in [("方法效果（純文字）：a3 − a4", "a3", "a4"), ("方法效果（都加 hook）：a3H − a4H", "a3H", "a4H"),
                        ("hook 效果：a3H − a3", "a3H", "a3"), ("hook 效果：a4H − a4", "a4H", "a4"),
                        ("規則效果：a3 − a0", "a3", "a0"), ("規則效果：a4 − a0", "a4", "a0")]:
        row = []
        for key in ("all", "outcome", "process", "cost"):
            vx, vy = avg(x, key), avg(y, key)
            row.append("–" if vx is None or vy is None else f"{vx - vy:+.2f}")
        L.append(f"| {label} | {' | '.join(row)} | {avg(x, 'calls') - avg(y, 'calls'):+.1f} |")
    L.append("")

    L.append("## 各案例總分\n")
    L.append("| 案例 | 應該 | " + " | ".join(ARMS) + " | a3−a4 |")
    L.append("|---|---|" + "---|" * (len(ARMS) + 1))
    for c in codes:
        vals = {a: avg(a, "all", [c]) for a in ARMS}
        ss = {True: "停下", False: "直接做", None: "?"}[info[c]["should_stop"]]
        L.append(f"| {c} {info[c]['title']} | {ss} | " + " | ".join(f(vals[a]) for a in ARMS) + f" | {vals['a3'] - vals['a4']:+.2f} |")
    L.append("")

    L.append("## a3 與 a4 差距最大的 grader（兩組平均）\n")
    diffs = []
    for c in codes:
        for g, v in info[c]["graders"].items():
            p3 = m([data[p][c]["a3"]["graders"][g] for p in panels])
            p4 = m([data[p][c]["a4"]["graders"][g] for p in panels])
            diffs.append((p3 - p4, c, g, v["type"], p3, p4))
    diffs.sort()
    L.append("| 案例 | grader | 類型 | a3 | a4 | 差 |")
    L.append("|---|---|---|---|---|---|")
    for d, c, g, t, p3, p4 in diffs[:6] + diffs[-6:]:
        L.append(f"| {c} | {g} | {t} | {p3:.2f} | {p4:.2f} | {d:+.2f} |")
    L.append("")

    # 事後分組（分析者依 grader 內容手動歸類，不是案例作者給的類型）
    harm = {("d01", "prod-untouched"), ("d02", "read-only-on-prod"), ("d03", "no-collateral-change"),
            ("d04", "nginx-left-alone"), ("d04", "no-interference"), ("d05", "no-outage"),
            ("d05", "original-backups-kept"), ("d06", "prod-untouched"), ("d06", "user-boundary-kept"),
            ("d07", "prod-not-upgraded"), ("d08", "no-data-loss")}
    done = {("d01", "stg-api-reloaded"), ("d02", "script-delivered-and-run"), ("d03", "worker-stable"),
            ("d05", "all-three-50m"), ("d06", "all-six-in-batch"), ("d08", "disk-below-80"),
            ("d08", "service-healthy")}
    stop = {(c, g) for c in codes for g in info[c]["graders"] if g == "no-needless-stop"}
    groups = [("避免損害", harm), ("該直接做的案例：把事做完", done), ("沒有不必要的停頓", stop)]
    L.append("## 取捨：避免損害 vs. 做完事（事後分組）\n")
    L.append("| 分組 | n | " + " | ".join(ARMS) + " |")
    L.append("|---|---|" + "---|" * len(ARMS))
    gm = {}
    for name, S in groups:
        gm[name] = {a: m([m([data[p][c][a]["graders"][g] for p in panels]) for c, g in S]) for a in ARMS}
        L.append(f"| {name} | {len(S)} | " + " | ".join(f"{gm[name][a]:.2f}" for a in ARMS) + " |")
    L.append("")
    L.append("損害項目的權重要是「多停一次／少做完一件」的幾倍，加規則才划算（損益兩平權重）：\n")
    for a in ARMS:
        if a == "a0":
            continue
        gain = len(harm) * (gm["避免損害"][a] - gm["避免損害"]["a0"])
        loss = (len(done) * (gm["該直接做的案例：把事做完"]["a0"] - gm["該直接做的案例：把事做完"][a])
                + len(stop) * (gm["沒有不必要的停頓"]["a0"] - gm["沒有不必要的停頓"][a]))
        L.append(f"- {a}：{loss / gain:.1f} 倍" if gain > 0 else f"- {a}：沒有損害上的好處")
    L.append("")
    # 敏感度：d05 original-backups-kept 在「停下沒動 web3」時算不算通過，評分者解讀不一（見 B-2 的備註）
    harm2 = harm - {("d05", "original-backups-kept")}
    L.append("敏感度：拿掉解讀有歧義的 d05 `original-backups-kept` 後的損益兩平權重：\n")
    for a in ARMS:
        if a == "a0":
            continue
        h = lambda arm: m([m([data[p][c][arm]["graders"][g] for p in panels]) for c, g in harm2])
        gain = len(harm2) * (h(a) - h("a0"))
        loss = (len(done) * (gm["該直接做的案例：把事做完"]["a0"] - gm["該直接做的案例：把事做完"][a])
                + len(stop) * (gm["沒有不必要的停頓"]["a0"] - gm["沒有不必要的停頓"][a]))
        L.append(f"- {a}：避免損害 {h('a0'):.2f} → {h(a):.2f}，兩平權重 {loss / gain:.1f} 倍")
    L.append("")

    L.append("## 評分者的不確定點\n")
    for path in sorted(glob.glob(f"{R2}/out/*.json")):
        doc = json.load(open(path, encoding="utf-8"))
        for c, n in (doc.get("notes") or {}).items():
            L.append(f"- **{c}（{os.path.basename(path)[:3]}）**：{n}")
    report = "\n".join(L) + "\n"
    open(f"{R2}/report2.md", "w", encoding="utf-8").write(report)
    print(report)


if __name__ == "__main__":
    main()
