#!/usr/bin/env python3
"""驗證這套規則集沒有壞掉（對應 agent-context-kit 的 check_agent_docs.py）。

檢查：必要檔案、AGENTS.md 行數上限、規則編號標記、內部連結、hooks 接線、TRUTH.md 環境表、任務紀錄欄位。
用法：python3 tools/check_kit.py      全部通過 exit 0，否則 exit 1
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_AGENTS_LINES = int(os.environ.get("KIT_AGENTS_MAX_LINES", "80"))
REQUIRED = ["AGENTS.md", "CLAUDE.md", "TRUTH.md", "tasks/TEMPLATE.md", "tools/task_new.sh",
            "tools/context.py", "tools/guard.py", ".claude/settings.json"]
STATUSES = {"active", "waiting", "blocked", "done", "dropped"}
TASK_FIELDS = ["status", "goal", "done-when", "targets"]

errors = []


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def check_files():
    for rel in REQUIRED:
        if not os.path.exists(os.path.join(ROOT, rel)):
            errors.append(f"缺少 {rel}")


def check_agents():
    text = read("AGENTS.md")
    n = len(text.splitlines())
    if n > MAX_AGENTS_LINES:
        errors.append(f"AGENTS.md 有 {n} 行，超過上限 {MAX_AGENTS_LINES}；細節請移到其他文件")
    ids, open_id = [], None
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"\s*<!--\s*rule:(\w+)\s*-->", line)
        if m:
            if open_id:
                errors.append(f"AGENTS.md:{i} 規則 {m.group(1)} 開始時，{open_id} 還沒結束")
            open_id = m.group(1)
            if open_id in ids:
                errors.append(f"AGENTS.md:{i} 規則編號重複：{open_id}")
            ids.append(open_id)
        elif re.match(r"\s*<!--\s*/rule\s*-->", line):
            if not open_id:
                errors.append(f"AGENTS.md:{i} 多出一個 <!-- /rule -->")
            open_id = None
    if open_id:
        errors.append(f"AGENTS.md 規則 {open_id} 沒有結束標記")


def check_links():
    for rel in ("AGENTS.md", "CLAUDE.md"):
        for target in re.findall(r"\]\(([^)#\s]+)\)", read(rel)):
            if re.match(r"\w+://", target):
                continue
            if not os.path.exists(os.path.join(ROOT, os.path.dirname(rel), target)):
                errors.append(f"{rel} 的連結找不到：{target}")
    if "AGENTS.md" not in read("CLAUDE.md"):
        errors.append("CLAUDE.md 沒有指向 AGENTS.md")


def check_hooks():
    try:
        hooks = json.loads(read(".claude/settings.json")).get("hooks", {})
    except (OSError, ValueError) as exc:
        errors.append(f".claude/settings.json 無法解析：{exc}")
        return

    def commands(event, matcher=None):
        return [h.get("command", "") for e in hooks.get(event, [])
                if matcher is None or e.get("matcher") == matcher for h in e.get("hooks", [])]

    if not any("context.py" in c and "--" not in c.split("context.py", 1)[1] for c in commands("SessionStart")):
        errors.append("SessionStart hook 沒有接 tools/context.py")
    if not any("context.py" in c and "--remind" in c for c in commands("PreCompact")):
        errors.append("PreCompact hook 沒有接 tools/context.py --remind")
    if not any("guard.py" in c for c in commands("PreToolUse", "Bash")):
        errors.append("PreToolUse(Bash) hook 沒有接 tools/guard.py")


def check_truth():
    text = read("TRUTH.md")
    if not re.search(r"^\|[^\n]*prod[^\n]*\|\s*$", text, re.M | re.I):
        errors.append("TRUTH.md 缺少含 prod 欄位的環境表")


def check_tasks():
    for path in sorted(glob.glob(os.path.join(ROOT, "tasks", "T-*.md"))):
        rel = os.path.relpath(path, ROOT)
        text = open(path, encoding="utf-8").read()
        header = text.split("\n## ", 1)[0]
        fields = dict(re.findall(r"^([\w-]+):\s*(.*)$", header, re.M))
        for key in TASK_FIELDS:
            if not fields.get(key) or fields[key].startswith("<"):
                errors.append(f"{rel} 缺少 {key}")
        status = fields.get("status", "")
        if status not in STATUSES:
            errors.append(f"{rel} 的 status 不合法：{status!r}")
        result = text.split("## Result", 1)[1] if "## Result" in text else ""
        result = re.sub(r"<!--.*?-->", "", result, flags=re.S).strip()
        if status in ("done", "dropped") and not result:
            errors.append(f"{rel} 已經 {status}，但 Result 是空的（K8）")


def main():
    check_files()
    if errors:
        report()
    check_agents()
    check_links()
    check_hooks()
    check_truth()
    check_tasks()
    report()


def report():
    if errors:
        for e in errors:
            print(f"❌ {e}")
        sys.exit(1)
    print("✅ 規則集結構正確")
    sys.exit(0)


if __name__ == "__main__":
    main()
