#!/usr/bin/env python3
"""從你電腦上的 Claude Code 對話紀錄，挑出適合變成評估案例的真實任務。

只在本機讀檔、不上傳任何東西。對話紀錄位置：~/.claude/projects/<專案>/<session>.jsonl
（CLI 與桌面版 Code 分頁共用同一個引擎；如果你的版本存在別處，用 --root 指定）

用法：
  python3 evals/mine_sessions.py                     最近 30 天，輸出 candidates.md
  python3 evals/mine_sessions.py --since 90 --out x.md
  python3 evals/mine_sessions.py --root /path/to/projects

輸出的每一列是一個 session：第一句需求、回合數、工具錯誤次數、被壓縮次數、infra 指令數。
「難度訊號」越高的越值得變成案例——那些就是目前規則集處理不好的地方。
"""
import argparse
import glob
import json
import os
import re
import time
from datetime import datetime

INFRA = re.compile(r"\b(kubectl|helm|ssh|scp|terraform|tofu|ansible|ansible-playbook|aws|gcloud|az|docker|systemctl|psql|mysql)\b")
SECRET = re.compile(r"((?:password|passwd|token|secret|api[-_]?key)\s*[=:]\s*)\S+", re.I)


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_human_prompt(entry):
    msg = entry.get("message") or {}
    if entry.get("type") != "user" or msg.get("role") != "user" or entry.get("isSidechain") or entry.get("isMeta"):
        return False
    content = msg.get("content")
    if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return False
    text = text_of(content).strip()
    return bool(text) and not text.startswith("<") and not entry.get("isCompactSummary")


def parse_ts(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def scan(path):
    s = {"path": path, "prompts": [], "tool_errors": 0, "compactions": 0, "infra_cmds": 0, "tool_calls": 0,
         "cwd": "", "start": None, "end": None}
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            ts = parse_ts(e.get("timestamp", ""))
            if ts:
                s["start"] = s["start"] or ts
                s["end"] = ts
            s["cwd"] = s["cwd"] or e.get("cwd", "")
            if e.get("type") == "summary" or e.get("isCompactSummary"):
                s["compactions"] += 1
            msg = e.get("message") or {}
            content = msg.get("content")
            if is_human_prompt(e):
                s["prompts"].append(text_of(content).strip())
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use":
                        s["tool_calls"] += 1
                        cmd = (b.get("input") or {}).get("command", "")
                        if isinstance(cmd, str) and INFRA.search(cmd):
                            s["infra_cmds"] += 1
                    elif b.get("type") == "tool_result" and b.get("is_error"):
                        s["tool_errors"] += 1
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--since", type=int, default=30, help="只看最近幾天")
    ap.add_argument("--min-prompts", type=int, default=1)
    ap.add_argument("--out", default="candidates.md")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    cutoff = time.time() - args.since * 86400
    files = [p for p in glob.glob(os.path.join(args.root, "**", "*.jsonl"), recursive=True)
             if os.path.getmtime(p) >= cutoff]
    if not files:
        raise SystemExit(f"在 {args.root} 找不到最近 {args.since} 天的對話紀錄（*.jsonl）")

    sessions = [s for s in map(scan, files) if len(s["prompts"]) >= args.min_prompts]
    for s in sessions:
        s["signal"] = s["tool_errors"] * 2 + s["compactions"] * 3 + len(s["prompts"]) + min(s["infra_cmds"], 20) / 2
    sessions.sort(key=lambda s: s["signal"], reverse=True)

    rows = ["# 候選任務（依難度訊號排序）", "",
            f"來源：{args.root}，最近 {args.since} 天，共 {len(sessions)} 個 session。", "",
            "| 訊號 | 日期 | 專案 | 第一句需求 | 回合 | 工具錯誤 | 壓縮 | infra 指令 |",
            "|---|---|---|---|---|---|---|---|"]
    for s in sessions[:args.top]:
        first = SECRET.sub(r"\1***", " ".join(s["prompts"][0].split()))[:120].replace("|", "\\|")
        day = time.strftime("%m-%d", time.localtime(s["start"])) if s["start"] else "?"
        rows.append(f"| {s['signal']:.0f} | {day} | {os.path.basename(s['cwd']) or '-'} | {first} | "
                    f"{len(s['prompts'])} | {s['tool_errors']} | {s['compactions']} | {s['infra_cmds']} |")
    rows += ["", "## 怎麼變成案例", "",
             "1. 挑 10–20 個有代表性的（各種類型都要有：事故、變更、調查、腳本、接續、平行）。",
             "2. 每個寫成 evals/suite/<名稱>/：prompt.md 用那句真實需求；sim.json 依當時的實際輸出改寫（去掉機密）。",
             "3. 想清楚「做對」的可觀察標準，盡量寫成 regex／tool_used grader，llm grader 只用在短回覆。",
             "4. 在 selftest.json 寫一條正確做法與一條錯誤做法，跑 python3 evals/selftest.py 確認有鑑別力。",
             "5. 換了案例集就是新版本，之前的分數不能直接比較。"]
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print(f"已寫入 {args.out}（{min(len(sessions), args.top)} 筆）")


if __name__ == "__main__":
    main()
