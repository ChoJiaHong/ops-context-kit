import json, random, re, os, glob
E = "/home/claude/exp08"; A = "/home/claude/answerer/out"
arms = ["A0", "A1", "A2"]
ans = {a: {} for a in arms}
for a in arms:
    for f in glob.glob(f"{A}/{a}/*.json"):
        ans[a].update(json.load(open(f))["items"])
items = {n: [json.loads(l) for l in open(f"{E}/items/{n}.jsonl")] for n in ["macgyver", "falseqa", "gsm8k"]}
# FalseQA: only batch 1 (FP01-FP10) is complete for all arms
fq_ids = [x["id"] for x in items["falseqa"] if all(x["id"] in ans[a] for a in arms)]
mg_solv = [x for x in items["macgyver"] if x["solvable"]]
mapping = {}
for judge, seed in [("J1", 101), ("J2", 202)]:
    rng = random.Random(seed); mapping[judge] = {}
    out = [f"# MacGyver 可解題評分（{judge}）\n"]
    for x in mg_solv:
        order = arms[:]; rng.shuffle(order); mapping[judge][x["id"]] = dict(zip("甲乙丙", order))
        out.append(f"## {x['id']}\n\n**題目**\n\n{x['problem']}\n\n**參考解（經人工判定為可行且有效率）**\n\n{x['reference']}\n")
        if x.get("human_solution"): out.append(f"**另一個人類解**\n\n{x['human_solution']}\n")
        for lab, a in zip("甲乙丙", order):
            out.append(f"**答案{lab}**\n\n{ans[a][x['id']]['final'].strip()}\n")
    open(f"{E}/judge/{judge}-macgyver.md", "w").write("\n".join(out))
    out = [f"# FalseQA 評分（{judge}）\n"]
    for x in items["falseqa"]:
        if x["id"] not in fq_ids: continue
        order = arms[:]; rng.shuffle(order); mapping[judge][x["id"]] = dict(zip("甲乙丙", order))
        kind = "**這題含有錯誤前提。**" if x["label"] == 1 else "**這題是正常問題，前提沒有錯。**"
        out.append(f"## {x['id']}\n\n**問題**\n\n{x['src_q']}\n\n{kind}\n\n**參考回答**\n\n{x['gold']}\n")
        for lab, a in zip("甲乙丙", order):
            out.append(f"**答案{lab}**\n\n{ans[a][x['id']]['final'].strip()}\n")
    open(f"{E}/judge/{judge}-falseqa.md", "w").write("\n".join(out))
json.dump(mapping, open(f"{E}/judge/mapping.json", "w"), ensure_ascii=False, indent=1)
print("mg solvable", len(mg_solv), "fq", fq_ids)
