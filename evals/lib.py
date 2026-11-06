"""evals 共用的小工具：讀 frontmatter、列出案例、產生評估用的工作區基本檔案。只用標準函式庫。"""
import json
import os
import shutil

EVALS = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(EVALS)
SUITE = os.path.join(EVALS, "suite")
TEMPLATE = os.path.join(KIT, "template")

# 評估用工作區只放「狀態與工具」，不放任何規則（規則只由各 arm 的 plugin 注入）
WORKSPACE_FILES = ["TRUTH.md", "tasks/TEMPLATE.md", "tasks/README.md", "tools/task_new.sh", "tools/context.py"]
WORKSPACE_README = """# ops workspace

這個工作區管理 prod-eks、stg-eks 兩個 k8s context 和 web1–web3 三台主機。
環境與查詢方式見 TRUTH.md；任務紀錄在 tasks/。
"""


def parse_frontmatter(text):
    """解析 `---` 包住的 frontmatter。值寫成 JSON（YAML 的子集）或不加引號的純字串。"""
    if not text.startswith("---"):
        return {}, text
    _, head, body = text.split("---", 2)
    data = {}
    for line in head.strip().splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        raw = raw.strip()
        try:
            data[key.strip()] = json.loads(raw)
        except ValueError:
            data[key.strip()] = raw
    return data, body.lstrip("\n")


def cases():
    out = []
    for name in sorted(os.listdir(SUITE)):
        path = os.path.join(SUITE, name)
        if os.path.isfile(os.path.join(path, "prompt.md")):
            out.append(path)
    return out


def case_meta(case_dir):
    with open(os.path.join(case_dir, "prompt.md"), encoding="utf-8") as f:
        meta, body = parse_frontmatter(f.read())
    meta["prompt"] = body
    meta["name"] = os.path.basename(case_dir)
    graders = {}
    gdir = os.path.join(case_dir, "graders")
    for fname in sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []:
        with open(os.path.join(gdir, fname), encoding="utf-8") as f:
            g, gbody = parse_frontmatter(f.read())
        g["_body"] = gbody
        graders[fname[:-3]] = g
    meta["graders"] = graders
    return meta


def build_workspace_base():
    """從 template/ 產生 suite/_shared/workspace（每次建置都重建，確保和範本一致）。"""
    dest = os.path.join(SUITE, "_shared", "workspace")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    for rel in WORKSPACE_FILES:
        os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
        shutil.copy2(os.path.join(TEMPLATE, rel), os.path.join(dest, rel))
    with open(os.path.join(dest, "README.md"), "w", encoding="utf-8") as f:
        f.write(WORKSPACE_README)
    return dest
