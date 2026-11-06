#!/usr/bin/env python3
"""任務與 session 的綁定（工作流：/start → 執行 → /handoff）。

用法：
  python3 tools/task.py start --session <id> --slug <slug> --mode look|fix|change \\
      --goal "<一句話>" --done-when "<可觀察的條件>" --targets "<會寫入的目標，或 ->" \\
      [--type change] [--out-of-scope "<這次不做的事>"] [--next "<下一步>"]
      建立任務紀錄、把這個 session 綁到它，並檢查有沒有其他進行中的任務宣告了同樣的目標。
  python3 tools/task.py bind --session <id> <任務檔路徑>     把 session 綁到既有的任務（接續工作時）
  python3 tools/task.py current --session <id>               印出這個 session 綁定的任務

綁定存在 tasks/.bind/<session id>，guard.py 依它知道這個 session 的模式與目標。
"""
import argparse
import glob
import os
import re
import subprocess
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks")
BIND = os.path.join(TASKS, ".bind")
MODES = ("look", "fix", "change")
OPEN = ("active", "waiting", "blocked")


def fields(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                break
            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def target_names(text):
    """「ctx=stg-eks ns=api；host=web1,web2」→ {stg-eks, api, web1, web2}；「-」→ 空集合。"""
    names = set()
    for part in re.split(r"[;；,，\s]+", text or ""):
        if not part or part == "-":
            continue
        value = part.split("=", 1)[1] if "=" in part else part
        names.update(v for v in value.split(",") if v and v != "-")
    return names


def bound(session):
    """回傳 session 綁定的任務檔絕對路徑，沒有就回傳 None。"""
    if not session:
        return None
    p = os.path.join(BIND, re.sub(r"[^\w.-]", "_", session))
    try:
        with open(p, encoding="utf-8") as f:
            rel = f.read().strip()
    except OSError:
        return None
    path = os.path.join(ROOT, rel)
    return path if os.path.exists(path) else None


def bind(session, path):
    os.makedirs(BIND, exist_ok=True)
    with open(os.path.join(BIND, re.sub(r"[^\w.-]", "_", session)), "w", encoding="utf-8") as f:
        f.write(os.path.relpath(os.path.abspath(path), ROOT) + "\n")


def overlaps(path, names):
    hits = []
    for other in glob.glob(os.path.join(TASKS, "T-*.md")):
        if os.path.abspath(other) == os.path.abspath(path):
            continue
        f = fields(other)
        if f.get("status", "active") not in OPEN:
            continue
        common = names & target_names(f.get("targets"))
        if common:
            hits.append(f"{os.path.relpath(other, ROOT)}（{'、'.join(sorted(common))}）")
    return hits


def set_field(text, key, value):
    if re.search(rf"^{re.escape(key)}:.*$", text, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", lambda m: f"{key}: {value}", text, count=1, flags=re.M)
    return re.sub(r"^(status:.*)$", lambda m: f"{m.group(1)}\n{key}: {value}", text, count=1, flags=re.M)


def cmd_start(a):
    if a.mode not in MODES:
        sys.exit(f"mode 只能是 {'、'.join(MODES)}")
    out = subprocess.run(["bash", os.path.join(ROOT, "tools", "task_new.sh"), a.slug, a.type],
                         capture_output=True, text=True)
    if out.returncode:
        sys.exit(out.stderr.strip())
    path = out.stdout.strip()
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for key, value in (("mode", a.mode), ("goal", a.goal), ("done-when", a.done_when), ("targets", a.targets),
                       ("out-of-scope", a.out_of_scope or "-"), ("next", a.next or "-")):
        text = set_field(text, key, value)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if a.session:
        bind(a.session, path)
    print(f"任務：{os.path.relpath(path, ROOT)}")
    print(f"模式：{a.mode}｜targets：{a.targets}")
    print("已綁定這個 session" if a.session else "沒有 session id，未綁定（guard 不會依任務限制）")
    hits = overlaps(path, target_names(a.targets))
    if hits:
        print("⚠ 其他進行中的任務也宣告了同樣的目標，變更前先告訴使用者（K2）：")
        for h in hits:
            print(f"  - {h}")


def cmd_bind(a):
    if not os.path.exists(a.path):
        sys.exit(f"找不到 {a.path}")
    bind(a.session, a.path)
    f = fields(a.path)
    print(f"已綁定：{os.path.relpath(os.path.abspath(a.path), ROOT)}｜模式：{f.get('mode', '-')}｜targets：{f.get('targets', '-')}")
    hits = overlaps(a.path, target_names(f.get("targets")))
    for h in hits:
        print(f"⚠ 目標重疊：{h}")


def cmd_current(a):
    path = bound(a.session)
    if not path:
        print("這個 session 還沒有綁定任務。用 /start 開始，或用 bind 接續既有任務。")
        return
    f = fields(path)
    print(f"任務：{os.path.relpath(path, ROOT)}")
    for k in ("mode", "status", "goal", "done-when", "targets", "out-of-scope", "next"):
        print(f"{k}: {f.get(k, '-')}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--session", default="")
    s.add_argument("--slug", required=True)
    s.add_argument("--type", default="change")
    s.add_argument("--mode", required=True)
    s.add_argument("--goal", required=True)
    s.add_argument("--done-when", required=True)
    s.add_argument("--targets", required=True)
    s.add_argument("--out-of-scope", default="")
    s.add_argument("--next", default="")
    b = sub.add_parser("bind")
    b.add_argument("--session", required=True)
    b.add_argument("path")
    c = sub.add_parser("current")
    c.add_argument("--session", required=True)
    a = p.parse_args()
    {"start": cmd_start, "bind": cmd_bind, "current": cmd_current}[a.cmd](a)


if __name__ == "__main__":
    main()
