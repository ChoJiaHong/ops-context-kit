#!/usr/bin/env python3
"""任務總覽與上下文注入（K1、K2）。

用法：
  python3 tools/context.py            SessionStart hook：把進行中的任務與 targets 注入上下文
  python3 tools/context.py --remind   PreCompact hook：提醒在壓縮前更新任務紀錄
  python3 tools/context.py --board    給人看的總覽（hub session 用；加 --all 含已完成）
  python3 tools/context.py --plain    同 SessionStart，但只列任務、不附規則提示

只讀檔案，一律 exit 0，不會擋住 session。
"""
import glob
import json
import os
import sys
import time

OPEN = ("waiting", "blocked", "active")
ORDER = {"waiting": 0, "blocked": 0, "active": 1, "done": 3, "dropped": 4}
STALE_HOURS = 24


def root():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def parse(path):
    task = {"path": os.path.relpath(path, root()), "title": "", "progress": []}
    section = ""
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.startswith("# ") and not task["title"]:
                task["title"] = line[2:].strip()
            elif line.startswith("## "):
                section = line[3:].strip().lower()
            elif not section and ":" in line:
                key, value = line.split(":", 1)
                task[key.strip()] = value.strip()
            elif section == "progress" and line.startswith("- "):
                task["progress"].append(line[2:].strip())
    task.setdefault("status", "active")
    try:
        task["ts"] = time.mktime(time.strptime(task.get("updated", ""), "%Y-%m-%d %H:%M"))
    except ValueError:
        task["ts"] = os.path.getmtime(path)
    task["stale"] = task["status"] in OPEN and time.time() - task["ts"] > STALE_HOURS * 3600
    return task


def load(include_closed=False):
    tasks = []
    for path in glob.glob(os.path.join(root(), "tasks", "T-*.md")):
        try:
            tasks.append(parse(path))
        except OSError:
            continue
    if not include_closed:
        tasks = [t for t in tasks if t["status"] in OPEN]
    tasks.sort(key=lambda t: (ORDER.get(t["status"], 2) + (1.5 if t["stale"] and t["status"] == "active" else 0),
                              -t["ts"]))
    return tasks


def age(ts):
    minutes = int((time.time() - ts) / 60)
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h" if minutes < 2880 else f"{minutes // 1440}d"


def hook_input():
    if sys.stdin.isatty():
        return {}
    try:
        return json.load(sys.stdin)
    except ValueError:
        return {}


def bound_task(session_id):
    if not session_id:
        return None
    try:
        with open(os.path.join(root(), "tasks", ".bind", session_id), encoding="utf-8") as f:
            path = os.path.join(root(), f.read().strip())
        return parse(path) if os.path.exists(path) else None
    except OSError:
        return None


def session_start(plain=False):
    """plain=True 只列任務，不附 K1/K2 的指示（評估時給非 A3 的 arm 用）。"""
    sid = hook_input().get("session_id", "")
    tasks = load()
    lines = []
    if not plain:
        mine = bound_task(sid)
        lines.append(f"[session] id: {sid or '（未知）'}")
        if mine:
            lines.append(f"[session] 這個 session 綁定的任務：{mine['title']}｜mode: {mine.get('mode', '-')}｜"
                         f"targets: {mine.get('targets', '-')}｜next: {mine.get('next', '-')}｜{mine['path']}")
        else:
            lines.append("[session] 還沒有綁定任務：不是一次問答就能結束的工作，先用 /start（接續既有任務用 tools/task.py bind）。")
    if tasks:
        lines.append(f"[tasks] 進行中的任務 {len(tasks)} 個（{os.path.join(root(), 'tasks')}）：")
        for t in tasks:
            lines.append(f"- {t['title']}｜{t['status']}｜targets: {t.get('targets', '-')}｜"
                         f"next: {t.get('next', '-')}｜{age(t['ts'])} 前更新｜{t['path']}")
        if not plain:
            lines.append("變更任何 target 之前，確認它沒有被上面的「其他」任務宣告（使用者要你接續的那個任務不算）；"
                         "有重疊就先告訴使用者，等他決定（K2）。")
    else:
        lines.append("[tasks] 目前沒有進行中的任務。")
    if not plain:
        lines.append("工作流：/start 建立並綁定任務 → 照任務的 mode 與 targets 工作 → /handoff 驗證、交接（K1）。")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": "\n".join(lines)}}, ensure_ascii=False))


def remind():
    print("上下文即將被壓縮：先把目前任務的 progress、next、status 寫進任務紀錄（tasks/），再繼續。")


def board():
    tasks = load(include_closed="--all" in sys.argv)
    if not tasks:
        print("沒有進行中的任務。")
        return
    icon = {"waiting": "⏸ 等你", "blocked": "⛔ 卡住", "active": "▶ 進行", "done": "✅ 完成", "dropped": "✖ 放棄"}
    for t in tasks:
        mark = " ⌛" if t["stale"] else ""
        print(f"{icon.get(t['status'], t['status'])}{mark}  {age(t['ts']):>4}  {t['title']}")
        print(f"            goal: {t.get('goal', '-')}")
        print(f"            mode: {t.get('mode', '-')}｜targets: {t.get('targets', '-')}｜next: {t.get('next', '-')}")


def main():
    if "--remind" in sys.argv:
        remind()
    elif "--board" in sys.argv:
        board()
    else:
        session_start(plain="--plain" in sys.argv)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # 永遠不擋 session
        print(f"context.py error: {exc}", file=sys.stderr)
