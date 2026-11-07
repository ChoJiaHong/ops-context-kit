#!/usr/bin/env python3
"""驗證問題界定：用你的 Claude Code 對話紀錄，數出兩種說法各自的訊號。

  A（使用者說過的痛點）：plan 和需求差很多、要一步步確認、session 目的不清楚、多 session 難管理
  B（thinking/18 的推論）：用量大時人審不完、錯誤要到出事才發現；規則和記憶大多是 AI 自己寫的

只在本機讀檔、不上傳任何東西。輸出彙總數字，加上少量遮罩過的摘錄讓判讀的人核對分類。
摘錄可能含主機、叢集、專案名稱：上傳前請自己看過，或加 --no-excerpts。

這支程式只數訊號、不下結論。判讀交給沒看過 18 推論的人或 agent（見 thinking/19）。

用法：
  python3 evals/validate_problem.py                        最近 30 天，輸出 problem-signals.md
  python3 evals/validate_problem.py --since 90 --no-excerpts
  python3 evals/validate_problem.py --root /path/to/projects
"""
import argparse
import glob
import json
import os
import re
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime

BUCKET = 600          # 10 分鐘內有任何紀錄，就算這個 session 在這段時間「活著」
LINK_WINDOW = 72 * 3600

CORRECT = re.compile(
    r"不是這|不是我要|不是要你|不對|錯了|搞錯|弄錯|誤會|誤解|我要的是|我是說|我的意思是|理解錯|"
    r"沒有要你|沒叫你|不是叫你|我沒說|我沒有說|跟我說的不一樣|"
    r"not what i|that'?s wrong|i meant|misunderstood|wrong (?:file|cluster|host|namespace|context)", re.I)
STOP = re.compile(
    r"先不要|不要動|不要做|不要執行|停一下|停下|先停|等一下|等等|別動|先別|"
    r"^stop\b|^wait\b|hold on|don'?t (?:do|run|touch|change)", re.I)
CONFIRM = re.compile(
    r"^(?:好|好的|好啊|可以|可以啊|繼續|請繼續|繼續吧|ok|okay|yes|y|go|行|對|嗯|是|同意|確認|執行|"
    r"做吧|開始|lgtm|continue|proceed|沒問題|就這樣|照做|做|跑|跑吧)[\s。.!！~]*$", re.I)
CONTINUATION = re.compile(r"繼續|接續|延續|接著|交接|handoff|continue|resume", re.I)
INCIDENT = re.compile(
    r"壞了|掛了|掛掉|出事|爆了|炸了|不能用|連不上|起不來|誰改|被改|被刪|回滾|rollback|roll back|revert|"
    r"broke|broken|outage|incident|crashloop", re.I)

INFRA = re.compile(r"\b(kubectl|helm|ssh|scp|terraform|tofu|ansible|ansible-playbook|aws|gcloud|az|docker|"
                   r"systemctl|psql|mysql)\b")
MUTATE = [
    re.compile(r"\bkubectl\b[^|;&\n]*\b(apply|create|delete|patch|edit|scale|replace|set|label|annotate|drain|"
               r"cordon|uncordon|taint|rollout\s+(?:restart|undo))\b"),
    re.compile(r"\bhelm\b[^|;&\n]*\b(install|upgrade|uninstall|delete|rollback)\b"),
    re.compile(r"\b(terraform|tofu)\b[^|;&\n]*\b(apply|destroy|import|taint)\b|\b(terraform|tofu)\s+state\s+(rm|mv)\b"),
    re.compile(r"\bansible-playbook\b(?![^|;&\n]*(--check|\s-C\b))"),
    re.compile(r"\bsystemctl\s+(restart|stop|start|enable|disable|reload|daemon-reload)\b"),
    re.compile(r"\bdocker\b[^|;&\n]*\b(rm|stop|kill|restart|run)\b|docker[- ]compose\b[^|;&\n]*\b(up|down|restart)\b"),
]
REMOTE_MUTATE = re.compile(r"\b(rm|mv|sed\s+-i|tee|chmod|chown|reboot|shutdown|apt|apt-get|yum|dnf)\b")
RULE_NAMES = {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "MEMORY.md", "TRUTH.md"}
RULE_APPEND = re.compile(r"(>>?|tee(\s+-a)?)\s*\S*(CLAUDE|AGENTS|MEMORY|TRUTH)\.md")
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
REJECT = re.compile(r"doesn't want to proceed|user rejected|user has rejected", re.I)

SECRET = re.compile(r"((?:password|passwd|token|secret|api[-_]?key)\s*[=:]\s*)\S+", re.I)
IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
LONGTOKEN = re.compile(r"\b[A-Za-z0-9_\-]{24,}\b")


def mask(text, n=60):
    t = " ".join(text.split())
    t = SECRET.sub(r"\1***", t)
    t = IPV4.sub("<ip>", t)
    t = EMAIL.sub("<email>", t)
    t = LONGTOKEN.sub("<token>", t)
    return (t[:n] + ("…" if len(t) > n else "")).replace("|", "\\|")


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def parse_ts(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def is_mutating(cmd):
    if any(r.search(cmd) for r in MUTATE):
        return True
    return bool(re.search(r"\bssh\b", cmd) and REMOTE_MUTATE.search(cmd))


def is_rule_write(name, inp):
    if name in WRITE_TOOLS:
        path = str(inp.get("file_path") or inp.get("notebook_path") or "")
        return os.path.basename(path) in RULE_NAMES or "/.claude/" in path or "/memory/" in path
    if name == "Bash":
        return bool(RULE_APPEND.search(str(inp.get("command", ""))))
    return False


def scan(path):
    s = {"path": path, "cwd": "", "prompts": [], "interrupts": 0, "tool_rejects": 0, "plan_rejects": 0,
         "tool_calls": 0, "infra": 0, "mutations": [], "file_writes": 0, "rule_writes": 0,
         "buckets": set(), "calls_per_turn": [], "first": None}
    plan_ids, rejected_ids, mutations = set(), set(), []
    calls_since_prompt = None
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if not isinstance(e, dict) or e.get("isSidechain"):
                continue
            ts = parse_ts(e.get("timestamp", ""))
            if ts:
                s["buckets"].add(int(ts // BUCKET))
            s["cwd"] = s["cwd"] or e.get("cwd", "")
            msg = e.get("message") or {}
            content = msg.get("content")
            blocks = content if isinstance(content, list) else []

            if e.get("type") == "user" and msg.get("role") == "user" and not e.get("isMeta") \
                    and not e.get("isCompactSummary"):
                if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
                    for b in blocks:
                        if not isinstance(b, dict) or b.get("type") != "tool_result":
                            continue
                        body = text_of(b.get("content")) if not isinstance(b.get("content"), str) else b["content"]
                        # 只認 Claude Code 自己的拒絕訊息；git push 的 "[rejected]" 之類不算
                        rejected = b.get("is_error") and REJECT.search(body or "")
                        if rejected:
                            s["tool_rejects"] += 1
                            rejected_ids.add(b.get("tool_use_id"))
                            if b.get("tool_use_id") in plan_ids:
                                s["plan_rejects"] += 1
                    continue
                text = text_of(content).strip()
                if text.startswith("[Request interrupted by user"):
                    s["interrupts"] += 1
                    continue
                if not text or text.startswith("<"):
                    continue
                if calls_since_prompt is not None:
                    s["calls_per_turn"].append(calls_since_prompt)
                calls_since_prompt = 0
                s["prompts"].append((ts, text))

            for b in blocks:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                s["tool_calls"] += 1
                if calls_since_prompt is not None:
                    calls_since_prompt += 1
                name, inp = b.get("name", ""), b.get("input") or {}
                if name == "ExitPlanMode":
                    plan_ids.add(b.get("id"))
                if name in WRITE_TOOLS:
                    s["file_writes"] += 1
                if is_rule_write(name, inp):
                    s["rule_writes"] += 1
                cmd = inp.get("command", "") if isinstance(inp, dict) else ""
                if isinstance(cmd, str) and cmd:
                    if INFRA.search(cmd):
                        s["infra"] += 1
                    if is_mutating(cmd):
                        mutations.append((ts, b.get("id")))
    if calls_since_prompt is not None:
        s["calls_per_turn"].append(calls_since_prompt)
    # 被使用者拒絕的指令沒有執行，不算改過 infra
    s["mutations"] = [t for t, i in mutations if i not in rejected_ids]
    s["project"] = os.path.basename(s["cwd"].rstrip("/")) or os.path.basename(os.path.dirname(path))
    return s


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "-"


def quantile(xs, q):
    if not xs:
        return "-"
    xs = sorted(xs)
    return str(xs[min(len(xs) - 1, int(q * len(xs)))])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--since", type=int, default=30, help="只看最近幾天")
    ap.add_argument("--out", default="problem-signals.md")
    ap.add_argument("--examples", type=int, default=5, help="每一類最多幾則摘錄")
    ap.add_argument("--no-excerpts", action="store_true", help="只輸出數字，不輸出任何對話內容")
    args = ap.parse_args()

    cutoff = time.time() - args.since * 86400
    files = [p for p in glob.glob(os.path.join(args.root, "**", "*.jsonl"), recursive=True)
             if os.path.getmtime(p) >= cutoff and "subagents" not in p.split(os.sep)]
    if not files:
        raise SystemExit(f"在 {args.root} 找不到最近 {args.since} 天的對話紀錄（*.jsonl）")
    sessions = [s for s in map(scan, files) if s["prompts"]]
    if not sessions:
        raise SystemExit("找到檔案，但沒有任何人類輸入的回合")

    cat = defaultdict(list)          # 類別 → [(session, ts, text)]
    for s in sessions:
        for i, (ts, text) in enumerate(s["prompts"]):
            if i == 0:
                if len(text) < 20 or CONTINUATION.search(text):
                    cat["vague_first"].append((s, ts, text))
                continue
            low = text.lower()
            if CORRECT.search(low):
                cat["correct"].append((s, ts, text))
            if STOP.search(low):
                cat["stop"].append((s, ts, text))
            if CONFIRM.match(low):
                cat["confirm"].append((s, ts, text))
        for ts, text in s["prompts"]:
            if INCIDENT.search(text.lower()):
                cat["incident"].append((s, ts, text))

    mut_by_project = defaultdict(list)
    for s in sessions:
        mut_by_project[s["project"]] += [t for t in s["mutations"] if t]
    linked = [(s, ts, t) for s, ts, t in cat["incident"]
              if ts and any(ts - LINK_WINDOW <= m < ts for m in mut_by_project[s["project"]])]

    n = len(sessions)
    prompts = sum(len(s["prompts"]) for s in sessions)
    later_prompts = prompts - n
    session_hours = sum(len(s["buckets"]) for s in sessions) * BUCKET / 3600
    active = Counter(b for s in sessions for b in s["buckets"])
    wall_hours = len(active) * BUCKET / 3600
    conc = list(active.values()) or [0]
    calls_per_turn = [c for s in sessions for c in s["calls_per_turn"]]
    mutations = sum(len(s["mutations"]) for s in sessions)
    tool_calls = sum(s["tool_calls"] for s in sessions)
    interrupts = sum(s["interrupts"] for s in sessions)
    rejects = sum(s["tool_rejects"] for s in sessions)
    plan_rejects = sum(s["plan_rejects"] for s in sessions)
    rule_writes = sum(s["rule_writes"] for s in sessions)
    file_writes = sum(s["file_writes"] for s in sessions)

    def with_any(key):
        return len({id(s) for s, _, _ in cat[key]})

    def rate(x, h):
        return f"{x / h:.1f}" if h else "-"

    first_ts = min(min(s["buckets"]) for s in sessions if s["buckets"]) * BUCKET if active else None
    last_ts = max(max(s["buckets"]) for s in sessions if s["buckets"]) * BUCKET if active else None
    span = (f"{time.strftime('%Y-%m-%d', time.localtime(first_ts))} ～ "
            f"{time.strftime('%Y-%m-%d', time.localtime(last_ts))}") if first_ts else "?"

    out = ["# 問題界定的訊號", "",
           f"來源：`{args.root}`，最近 {args.since} 天（{span}）。{n} 個 session、{prompts} 個人類回合、"
           f"{len({s['project'] for s in sessions})} 個專案。",
           f"有效時間：各 session 合計 {session_hours:.1f} 小時；牆上時間 {wall_hours:.1f} 小時"
           f"（以 {BUCKET // 60} 分鐘為單位，有紀錄才算）。", "",
           "這份只數訊號、不下結論。關鍵字分類會有誤判"
           + ("。" if args.no_excerpts else "，請用下方摘錄核對。"), "",
           "## A：使用者說過的痛點", "",
           "| 訊號 | 數量 | 比例 |", "|---|---|---|",
           f"| A1 糾正（「不是」「我要的是」…），第 2 句以後 | {len(cat['correct'])} | 佔後續回合 {pct(len(cat['correct']), later_prompts)}；"
           f"{pct(with_any('correct'), n)} 的 session 至少一次 |",
           f"| A1 plan 被拒（ExitPlanMode） | {plan_rejects} | — |",
           f"| A2 只是確認（「好」「繼續」…） | {len(cat['confirm'])} | 佔後續回合 {pct(len(cat['confirm']), later_prompts)} |",
           f"| A2 喊停／先別動手 | {len(cat['stop'])} | {pct(with_any('stop'), n)} 的 session 至少一次 |",
           f"| A2 中斷執行 | {interrupts} | — |",
           f"| A2 拒絕工具呼叫 | {rejects} | 佔全部工具呼叫 {pct(rejects, tool_calls)} |",
           f"| A2 每個人類回合之間的工具呼叫數 | 中位數 {quantile(calls_per_turn, 0.5)}、P90 {quantile(calls_per_turn, 0.9)} | 越小越像逐步確認 |",
           f"| A3 第一句很短（<20 字）或是「繼續／交接」 | {len(cat['vague_first'])} | {pct(len(cat['vague_first']), n)} 的 session |",
           f"| A4 同時活著的 session 數 | 平均 {statistics.mean(conc):.1f}、最多 {max(conc)} | "
           f"≥2 個的時間佔 {pct(sum(c >= 2 for c in conc), len(conc))}、≥3 個佔 {pct(sum(c >= 3 for c in conc), len(conc))} |",
           "", "## B：thinking/18 的推論", "",
           "| 訊號 | 數量 | 比例 |", "|---|---|---|",
           f"| B1 工具呼叫 | {tool_calls} | 每個 session 小時 {rate(tool_calls, session_hours)} 次；每個人類回合 {tool_calls / prompts:.1f} 次 |",
           f"| B1 會改變 infra 的指令（apply、delete、restart…） | {mutations} | 每個 session 小時 {rate(mutations, session_hours)} 次；"
           f"佔 infra 指令 {pct(mutations, sum(s['infra'] for s in sessions))} |",
           f"| B1 檔案寫入（Write／Edit） | {file_writes} | 每個 session 小時 {rate(file_writes, session_hours)} 次 |",
           f"| B2 提到出事（「壞了」「回滾」…） | {len(cat['incident'])} | {pct(with_any('incident'), n)} 的 session |",
           f"| B2 其中，同專案 72 小時內先有 AI 改 infra | {len(linked)} | 佔出事訊號 {pct(len(linked), len(cat['incident']))} |",
           f"| B3 AI 寫規則或記憶檔（CLAUDE.md、AGENTS.md、MEMORY.md、.claude/、memory/） | {rule_writes} | "
           f"{pct(sum(s['rule_writes'] > 0 for s in sessions), n)} 的 session |",
           "", "## 各專案", "",
           "| 專案 | session | 人類回合 | 糾正 | 只是確認 | 改 infra | 出事 | 寫規則 |", "|---|---|---|---|---|---|---|---|"]
    per = defaultdict(Counter)
    for s in sessions:
        p = per[s["project"]]
        p["sessions"] += 1
        p["prompts"] += len(s["prompts"])
        p["mut"] += len(s["mutations"])
        p["rule"] += s["rule_writes"]
    for key, col in (("correct", "correct"), ("confirm", "confirm"), ("incident", "incident")):
        for s, _, _ in cat[key]:
            per[s["project"]][col] += 1
    for name, p in sorted(per.items(), key=lambda kv: -kv[1]["prompts"])[:15]:
        out.append(f"| {mask(name, 30)} | {p['sessions']} | {p['prompts']} | {p['correct']} | {p['confirm']} | "
                   f"{p['mut']} | {p['incident']} | {p['rule']} |")

    out += ["", "## 怎麼讀", "",
            "- A 成立的樣子：糾正、喊停、plan 被拒常見；人類回合之間的工具呼叫很少（逐步確認）；第一句常常很短或在接續；常同時開好幾個 session。",
            "- B 成立的樣子：每小時改 infra 和寫檔的次數多、人類回合之間的工具呼叫多（人沒逐步看）；出事訊號多半在 AI 改過 infra 之後；AI 常寫規則和記憶檔。",
            "- 兩者可以同時成立。判讀時看各專案的差異：infra 專案和其他專案可能很不一樣。"]

    if not args.no_excerpts:
        labels = [("correct", "A1 糾正"), ("stop", "A2 喊停"), ("confirm", "A2 只是確認"),
                  ("vague_first", "A3 第一句"), ("incident", "B2 出事")]
        out += ["", "## 摘錄（核對分類用，已遮罩 IP、email、token；上傳前請再看一次）"]
        for key, label in labels:
            items = cat[key][:args.examples]
            if not items:
                continue
            out += ["", f"**{label}**", ""]
            out += [f"- `{mask(s['project'], 20)}` {mask(text)}" for s, _, text in items]

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"已寫入 {args.out}（{n} 個 session）")


if __name__ == "__main__":
    main()
