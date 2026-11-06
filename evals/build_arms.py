#!/usr/bin/env python3
"""把每個實驗組（arm）打包成一個 Claude Code plugin，供 `claude plugin eval` 評估。

arm：
  a1         官方 best practices 精簡版（evals/arms/a1-official.md）
  a2         agent-context-kit 改編版（evals/arms/a2-agent-context-kit.md）+ 列出 tasks/ 的 hook
  a3         本規則集（template/AGENTS.md + CLAUDE.md）+ 全部 hooks
  a3-no-<X>  a3 拿掉規則 X（K1…K10）；K4g 只拿掉 guard hook，保留 K4 文字

用法：python3 evals/build_arms.py [--arms a1,a2,a3] [--ablate K2,K4g|all] [--out evals/build]
"""
import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import EVALS, SUITE, TEMPLATE, build_workspace_base  # noqa: E402

RULE_BLOCK = re.compile(r"<!--\s*rule:(\w+)\s*-->\n?(.*?)<!--\s*/rule\s*-->\n?", re.S)
WORKSPACE_LINE = "這個工作區管理 prod-eks、stg-eks 兩個 k8s context 和 web1–web3 三台主機；哪些是 prod 見 TRUTH.md。"


def rule_ids():
    with open(os.path.join(TEMPLATE, "AGENTS.md"), encoding="utf-8") as f:
        return [m.group(1) for m in RULE_BLOCK.finditer(f.read())]


def a3_rules(ablate):
    with open(os.path.join(TEMPLATE, "AGENTS.md"), encoding="utf-8") as f:
        agents = f.read()
    agents = RULE_BLOCK.sub(lambda m: "" if m.group(1) in ablate else m.group(2), agents)
    agents = re.sub(r"^<一段話：.*?>$", WORKSPACE_LINE, agents, flags=re.M)
    with open(os.path.join(TEMPLATE, "CLAUDE.md"), encoding="utf-8") as f:
        claude = f.read()
    claude_specific = claude.split("## Claude 專屬", 1)[1] if "## Claude 專屬" in claude else ""
    return agents.rstrip() + "\n\n## Claude 專屬" + claude_specific


def hook(cmd):
    return {"type": "command", "command": cmd, "timeout": 10}


def build(arm, out_root):
    out = os.path.join(out_root, arm)
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, ".claude-plugin"))
    os.makedirs(os.path.join(out, "hooks"))
    os.makedirs(os.path.join(out, "tools"))

    ablate = set(arm.split("a3-no-", 1)[1].split("+")) if arm.startswith("a3-no-") else set()
    if arm == "a1":
        rules = open(os.path.join(EVALS, "arms", "a1-official.md"), encoding="utf-8").read()
    elif arm == "a2":
        rules = open(os.path.join(EVALS, "arms", "a2-agent-context-kit.md"), encoding="utf-8").read()
    elif arm.startswith("a3"):
        rules = a3_rules(ablate)
    else:
        sys.exit(f"未知的 arm：{arm}")
    with open(os.path.join(out, "RULES.md"), "w", encoding="utf-8") as f:
        f.write(rules)

    root = "${CLAUDE_PLUGIN_ROOT}"
    shutil.copy2(os.path.join(EVALS, "arms", "inject.py"), os.path.join(out, "hooks", "inject.py"))
    start = [hook(f'python3 "{root}/hooks/inject.py"')]
    hooks = {"SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": start}]}
    for tool in ("context.py", "guard.py"):
        shutil.copy2(os.path.join(TEMPLATE, "tools", tool), os.path.join(out, "tools", tool))
    if arm == "a2":
        start.append(hook(f'python3 "{root}/tools/context.py" --plain'))
    if arm.startswith("a3"):
        if "K2" not in ablate:
            start.append(hook(f'python3 "{root}/tools/context.py"'))
        if "K1" not in ablate:
            hooks["PreCompact"] = [{"hooks": [hook(f'python3 "{root}/tools/context.py" --remind')]}]
        if not ablate & {"K4", "K4g"}:
            hooks["PreToolUse"] = [{"matcher": "Bash", "hooks": [hook(f'python3 "{root}/tools/guard.py"')]}]
    with open(os.path.join(out, "hooks", "hooks.json"), "w", encoding="utf-8") as f:
        json.dump({"hooks": hooks}, f, indent=2, ensure_ascii=False)

    with open(os.path.join(out, ".claude-plugin", "plugin.json"), "w", encoding="utf-8") as f:
        json.dump({"name": f"opsrules-{arm}", "version": "0.1.0",
                   "description": f"ops-context-kit 評估用規則集：{arm}"}, f, indent=2, ensure_ascii=False)

    shutil.copytree(SUITE, os.path.join(out, "evals"), ignore=shutil.ignore_patterns("__pycache__", "results"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", default="a1,a2,a3")
    ap.add_argument("--ablate", default="", help="要做消融的規則，逗號分隔；all = 每條規則各一組，外加 K4g")
    ap.add_argument("--out", default=os.path.join(EVALS, "build"))
    args = ap.parse_args()

    build_workspace_base()
    arms = [a for a in args.arms.split(",") if a]
    if args.ablate:
        ids = rule_ids() + ["K4g"] if args.ablate == "all" else args.ablate.split(",")
        known = set(rule_ids()) | {"K4g"}
        for rid in ids:
            if rid not in known:
                sys.exit(f"未知的規則編號：{rid}（可用：{', '.join(sorted(known))}）")
            arms.append(f"a3-no-{rid}")
    if os.path.exists(args.out):
        shutil.rmtree(args.out)
    for arm in arms:
        print(build(arm, args.out))


if __name__ == "__main__":
    main()
