import csv, json, random, re, openpyxl, sys
D = "/home/claude/datasets"; O = "/home/claude/exp08"
rng = random.Random(20261106)
# MacGyver
p = list(openpyxl.load_workbook(f"{D}/MacGyver/data/MacGyver/problem_solution_pair.xlsx", read_only=True).worksheets[0].iter_rows(values_only=True))[1:]
hum = {str(r[0]): r[3] for r in list(openpyxl.load_workbook(f"{D}/MacGyver/data/MacGyver/additional_human_solutions.xlsx", read_only=True).worksheets[0].iter_rows(values_only=True))[1:]}
clean = lambda s: re.sub(r"\s*<br>\s*", "\n", str(s or "")).strip()
solv = sorted([r for r in p if r[2] == "Yes" and r[3] == "unconventional" and r[5] == "efficient"], key=lambda r: str(r[0]))
unsolv = sorted([r for r in p if r[2] == "No"], key=lambda r: str(r[0]))
mg = [dict(src_id=str(r[0]), problem=str(r[1]).strip(), solvable=True, reference=clean(r[4]), human_solution=clean(hum.get(str(r[0])))) for r in rng.sample(solv, 20)]
mg += [dict(src_id=str(r[0]), problem=str(r[1]).strip(), solvable=False, reference=clean(r[4]), human_solution=clean(hum.get(str(r[0])))) for r in rng.sample(unsolv, 10)]
rng.shuffle(mg)
for i, x in enumerate(mg, 1): x["id"] = f"MG{i:02d}"
# FalseQA
fq = list(csv.DictReader(open(f"{D}/FalseQA/dataset/test.csv")))
fp = [dict(src_q=x["question"], label=int(x["label"]), gold=x["answer"]) for x in rng.sample([x for x in fq if x["label"] == "1"], 10) + rng.sample([x for x in fq if x["label"] == "0"], 10)]
rng.shuffle(fp)
for i, x in enumerate(fp, 1): x["id"] = f"FP{i:02d}"
# GSM8K
gs = [json.loads(l) for l in open(f"{D}/grade-school-math/grade_school_math/data/test.jsonl")]
gsm = [dict(question=x["question"], answer=x["answer"].split("####")[-1].strip().replace(",", "")) for x in rng.sample(gs, 20)]
for i, x in enumerate(gsm, 1): x["id"] = f"GS{i:02d}"
for name, items in [("macgyver", mg), ("falseqa", fp), ("gsm8k", gsm)]:
    with open(f"{O}/items/{name}.jsonl", "w") as f:
        for x in items: f.write(json.dumps(x, ensure_ascii=False) + "\n")
# batches (problems only, no answers)
def write_batches(name, items, key, n):
    for b in range(0, len(items), 10):
        k = b // 10 + 1
        with open(f"{O}/batches/{name}-{k}.md", "w") as f:
            for x in items[b:b+10]:
                f.write(f"## {x['id']}\n\n{x[key]}\n\n")
write_batches("macgyver", mg, "problem", 10); write_batches("falseqa", fp, "src_q", 10); write_batches("gsm8k", gsm, "question", 10)
print(len(mg), sum(x["solvable"] for x in mg), len(fp), sum(x["label"] for x in fp), len(gsm))
