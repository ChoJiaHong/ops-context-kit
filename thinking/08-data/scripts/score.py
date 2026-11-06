import json, glob, re, statistics as st
E = "/home/claude/exp08"; A = "/home/claude/answerer/out"; J = "/home/claude/judging/out"
arms = ["A0", "A1", "A2"]
ans = {a: {} for a in arms}
for a in arms:
    for f in glob.glob(f"{A}/{a}/*.json"): ans[a].update(json.load(open(f))["items"])
items = {n: [json.loads(l) for l in open(f"{E}/items/{n}.jsonl")] for n in ["macgyver", "falseqa", "gsm8k"]}
mp = json.load(open(f"{E}/judge/mapping.json"))
verdict = lambda t: "UNSOLVABLE" if re.search(r"VERDICT:\s*UNSOLVABLE", t, re.I) else ("SOLVABLE" if re.search(r"VERDICT:\s*SOLVABLE", t, re.I) else "NONE")
R = {}
# MacGyver unsolvable (auto)
uns = [x for x in items["macgyver"] if not x["solvable"]]
R["mg_unsolvable_correct"] = {a: sum(verdict(ans[a][x["id"]]["final"]) == "UNSOLVABLE" for x in uns) / len(uns) for a in arms}
sol = [x for x in items["macgyver"] if x["solvable"]]
R["mg_solvable_false_unsolvable"] = {a: sum(verdict(ans[a][x["id"]]["final"]) == "UNSOLVABLE" for x in sol) / len(sol) for a in arms}
# MacGyver solvable (judges)
jm = {j: json.load(open(f"{J}/{j}-macgyver.json"))["items"] for j in ["J1", "J2"]}
def mg_metric(j, a, key):
    vals = []
    for x in sol:
        lab = {v: k for k, v in mp[j][x["id"]].items()}[a]
        r = jm[j][x["id"]][lab]
        vals.append(int(r["goal"]) * int(r["feasible"]) if key == "success" else int(r[key]))
    return sum(vals) / len(vals)
for key in ["success", "goal", "feasible", "efficient", "hallucination"]:
    R[f"mg_{key}"] = {a: {j: mg_metric(j, a, key) for j in ["J1", "J2"]} for a in arms}
# per-item success for agreement / overall MG score
R["mg_overall_correct"] = {}  # solvable success (avg judges) + unsolvable correct, over 30
for a in arms:
    s = sum(st.mean([mg_metric(j, a, "success") for j in ["J1", "J2"]]) * len(sol) for _ in [0])
    R["mg_overall_correct"][a] = (s + R["mg_unsolvable_correct"][a] * len(uns)) / (len(sol) + len(uns))
# FalseQA (judges, batch 1 only)
jf = {j: json.load(open(f"{J}/{j}-falseqa.json"))["items"] for j in ["J1", "J2"]}
fq = [x for x in items["falseqa"] if x["id"] in jf["J1"]]
def fq_metric(j, a, label=None):
    v = []
    for x in fq:
        if label is not None and x["label"] != label: continue
        lab = {v_: k for k, v_ in mp[j][x["id"]].items()}[a]
        v.append(int(jf[j][x["id"]][lab]["correct"]))
    return sum(v) / len(v)
R["fq_correct"] = {a: {j: fq_metric(j, a) for j in ["J1", "J2"]} for a in arms}
R["fq_false_premise_detected"] = {a: {j: fq_metric(j, a, 1) for j in ["J1", "J2"]} for a in arms}
R["fq_normal_ok"] = {a: {j: fq_metric(j, a, 0) for j in ["J1", "J2"]} for a in arms}
R["fq_n"] = {"total": len(fq), "false_premise": sum(x["label"] for x in fq)}
# GSM8K (auto)
def num(t):
    m = re.search(r"ANSWER:\s*\$?(-?[\d,]*\.?\d+)", t)
    return float(m.group(1).replace(",", "")) if m else None
gs = items["gsm8k"]
R["gsm_acc"] = {a: sum(num(ans[a][x["id"]]["final"]) == float(x["answer"]) for x in gs) / len(gs) for a in arms}
R["gsm_chars"] = {a: st.mean(len(ans[a][x["id"]]["analysis"]) + len(ans[a][x["id"]]["final"]) for x in gs) for a in arms}
R["mg_chars"] = {a: st.mean(len(ans[a][x["id"]]["analysis"]) + len(ans[a][x["id"]]["final"]) for x in items["macgyver"]) for a in arms}
# judge agreement on MG success
agree = []
for x in sol:
    for a in arms:
        s = []
        for j in ["J1", "J2"]:
            lab = {v: k for k, v in mp[j][x["id"]].items()}[a]; r = jm[j][x["id"]][lab]
            s.append(int(r["goal"]) * int(r["feasible"]))
        agree.append(s[0] == s[1])
R["mg_judge_agreement"] = sum(agree) / len(agree)
json.dump(R, open(f"{E}/results.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
