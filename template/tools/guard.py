#!/usr/bin/env python3
"""PreToolUse(Bash) hook：K3、K4 的保證層。三種處理方式：

1. 擋下並請 agent 自己修正（deny + 指示，不打擾使用者）
   - kubectl／helm 沒有明確帶 --context（K3）
   - 修改共用的全域設定：kubectl config use-context、kubectx、gcloud config set…（K3）
2. 要求使用者確認（ask：桌面版會跳出核准提示，使用者點同意就照常執行；無人值守時等於擋下）
   - 不可逆操作（K4）
   - prod 上的變更（K4）。K4 v3 允許「使用者明確要求、可回復」的 prod 變更直接做，
     這個提示是保險：互動使用時只是多點一次核准。設 KIT_PROD_CONFIRM=0 可以關掉這一類，只保留不可逆操作的確認。
3. 直接拒絕（deny）
   - 災難指令：rm -rf /、mkfs、dd 寫入磁碟

prod 名單來自 TRUTH.md「環境」表格中 prod 欄為 yes 的列；也可以用環境變數 KIT_PROD_PATTERN（regex）覆寫。
設 KIT_REQUIRE_CONTEXT=0 可以關掉「kubectl 一定要帶 --context」這一條。
設 KIT_PROD_CONFIRM=0 可以關掉「prod 上的可回復變更要確認」這一條（不可逆操作仍然要確認）。

第 1 輪思想實驗後的修改（method/round1.md）：
- 「沒帶 --context」從「問使用者」改成「擋下讓 agent 自己補上」：這是可以自己修正的錯，不該打斷使用者。
- 補上 truncate、find -delete、logrotate -f 等清除檔案的寫法。

第 2 輪後的修改（method/round2.md）：唯讀指令被誤判成 prod 變更
- ssh 只看送到遠端的那段指令；本機的 pipe、`> /tmp/x` 重導向不算遠端變更。
- `2>/dev/null`、寫到 /tmp、`logrotate -d`（預演）不算變更。
- prod 判斷看實際目標：kubectl／helm 看 --context，ssh 看主機名，不再搜整段指令文字。
回歸測試：evals/guard_test.py
"""
import json
import os
import re
import shlex
import sys

SEG = r"[^;&|\n]*"  # 只在同一段指令內比對，避免跨過 pipe 誤判

CATASTROPHIC = [
    (r"\brm\s+-\w*[rR]\w*\s+(-\w+\s+)*(/|/\*|~|~/|\$HOME/?)(\s|$|['\";])", "rm -r 目標是根目錄或家目錄"),
    (r"--no-preserve-root", "--no-preserve-root"),
    (r"\bmkfs(\.\w+)?\b", "格式化檔案系統"),
    (r"\bdd\b" + SEG + r"\bof=/dev/(sd|nvme|vd|xvd|hd)", "dd 寫入磁碟裝置"),
]

GLOBAL_STATE = [
    (r"\bkubectl\b" + SEG + r"\bconfig\s+(use-context|set-context|delete-context|set-cluster|set-credentials)\b",
     "不要修改共用的 kubeconfig（其他 session 也在用）"),
    (r"(^|[;&|\s])(kubectx|kubens)\s+[^\s|;&-]", "不要切換全域 context／namespace（其他 session 也在用）"),
    (r"\bgcloud\s+config\s+set\b", "不要修改 gcloud 全域設定，改用 --project"),
    (r"\baws\s+configure\s+set\b", "不要修改 aws 全域設定，改用 --profile"),
]

# kubectl 這些子指令不碰叢集，不需要 --context
KUBECTL_LOCAL = r"(config|version\s+--client|completion|plugin|kustomize|explain\s+--help)"
HELM_CLUSTER = r"(install|upgrade|uninstall|delete|rollback|list|ls|status|get|history|test)"

IRREVERSIBLE = [
    (r"\bkubectl\b" + SEG + r"\s(delete|drain)\b", "kubectl 刪除／排空"),
    (r"\bhelm\b" + SEG + r"\s(uninstall|delete)\b", "helm 移除 release"),
    (r"\b(terraform|tofu)\b" + SEG + r"\s(destroy|state\s+rm)\b", "terraform 刪除資源／state"),
    (r"\brm\s+-\w*[rR]", "遞迴刪除檔案"),
    (r"\btruncate\s+-", "清空檔案內容"),
    (r"\bfind\b" + SEG + r"\s-delete\b", "find -delete 刪除檔案"),
    (r"\b(drop\s+(database|table|schema)|truncate\s+(table\s+)?[a-z_\"`])", "SQL 刪除資料"),
    (r"\bflush(all|db)\b", "Redis 清空資料"),
    (r"(^|[;&|'\"]\s*|\bsudo\s+|\bssh\s+(-\S+\s+(\S+\s+)?)*[\w.@-]+\s+)(reboot|shutdown|poweroff|halt)\b", "重開機／關機"),
    (r"\bdocker\s+(system|volume)\s+prune\b", "docker prune"),
    (r"\baws\b" + SEG + r"\s(delete|terminate)-[\w-]+", "AWS 刪除／終止資源"),
    (r"\bjournalctl\b" + SEG + r"--vacuum", "清除系統日誌"),
]

KUBE_MUTATING = (r"\s(apply|create|replace|patch|edit|set|scale|annotate|label|delete|drain|cordon|uncordon"
                 r"|rollout\s+(restart|undo))\b")
HELM_MUTATING = r"\s(install|upgrade|rollback|uninstall)\b"
OTHER_MUTATING = [
    r"\b(terraform|tofu)\b" + SEG + r"\s(apply|destroy|import)\b",
    r"\bansible-playbook\b(?!" + SEG + r"\s(--check|-C)\b)",
]
# 只套用在 ssh 送到遠端執行的那段指令上（本機的 pipe、重導向不算）。
# 寫到 /tmp、/dev/null 不算變更；logrotate -d 是預演。
REMOTE_MUTATING = (r"(systemctl\s+(start|stop|restart|reload|enable|disable)\b|\bsed\s+(-\w+\s+)*-i|\bsed\s+--in-place"
                   r"|\btee\s+(-a\s+)?(?!/tmp/|/dev/null)\S|\brm\s|\bmv\s|\bcp\s|\b(kill|pkill|killall)\b|\btruncate\b"
                   r"|(?<![/\w.-])logrotate(?![\w.-])(?![^;&|]*\s(-d|--debug)\b)|\b(apt|apt-get|yum|dnf)\s+(install|remove|upgrade)\b"
                   r"|(?<![0-9&])>>?\s*(?!/tmp/|/dev/null|&)\S)")
SSH_ARG_FLAGS = set("bcDEeFIiJLlmOopQRSWw")


def prod_pattern():
    custom = os.environ.get("KIT_PROD_PATTERN")
    if custom:
        return re.compile(custom, re.I)
    names = []
    truth = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(), "TRUTH.md")
    try:
        with open(truth, encoding="utf-8") as f:
            for line in f:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 4 and cells[-1].lower() in ("yes", "y", "true", "✅"):
                    names.extend(_expand(cells[0]))
    except OSError:
        pass
    if names:
        return re.compile(r"(?<![\w-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w-])")
    return re.compile(r"(?<![a-z])(prod|prd|production|live)(?![a-z])", re.I)


def _expand(name):
    """web1–web3 → web1 web2 web3；其他原樣。"""
    m = re.fullmatch(r"([A-Za-z][\w-]*?)(\d+)\s*[–~-]\s*(?:\1)?(\d+)", name)
    if m:
        return [f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(3)) + 1)]
    return [n for n in re.split(r"[\s,、]+", name) if n]


def missing_context(cmd):
    """回傳沒帶 --context 的 kubectl／helm 片段（只看會碰叢集的子指令）。"""
    if os.environ.get("KIT_REQUIRE_CONTEXT", "1") == "0":
        return None
    for seg in re.split(r"[;&|\n]+", cmd):
        if re.search(r"\bkubectl\b", seg) and not re.search(r"--context[= ]", seg):
            sub = re.sub(r"^.*?\bkubectl\b\s*", "", seg)
            sub = re.sub(r"^(-\S+\s+(\S+\s+)?)*", "", sub)  # 跳過放在動詞前面的旗標
            if sub and not re.match(KUBECTL_LOCAL, sub):
                return seg.strip()
        if re.search(r"\bhelm\b" + SEG + r"\s" + HELM_CLUSTER + r"\b", seg) and not re.search(r"--kube-context[= ]", seg):
            return seg.strip()
    return None


def ssh_calls(cmd):
    """回傳 [(主機, 遠端指令)]。解析失敗（例如 heredoc、引號不成對）時回傳 None，改用保守的全文比對。"""
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        return None
    calls, i = [], 0
    while i < len(toks):
        if os.path.basename(toks[i]) != "ssh":
            i += 1
            continue
        i += 1
        while i < len(toks) and toks[i].startswith("-") and len(toks[i]) > 1:
            flag = toks[i]
            i += 2 if (len(flag) == 2 and flag[1] in SSH_ARG_FLAGS) else 1
        if i >= len(toks):
            break
        host = toks[i].split("@")[-1]
        i += 1
        remote = []
        while i < len(toks) and not re.fullmatch(r"[;&|<>()]+", toks[i]):
            remote.append(toks[i])
            i += 1
        calls.append((host, " ".join(remote)))
    return calls


def prod_changes(cmd):
    """回傳這個指令裡會變更 prod 的目標名稱。"""
    prod = prod_pattern()
    hits = []
    for seg in re.split(r"[;&|\n]+", cmd):
        kube = re.search(r"\bkubectl\b", seg) and re.search(KUBE_MUTATING, seg)
        helm = re.search(r"\bhelm\b", seg) and re.search(HELM_MUTATING, seg)
        if kube or helm:
            ctx = re.search(r"--(?:kube-)?context[= ](\S+)", seg)
            target = ctx.group(1) if ctx else seg  # 沒帶 context 的情況前面已經擋下
            m = prod.search(target)
            if m:
                hits.append(m.group(0))
    if any(re.search(p, cmd) for p in OTHER_MUTATING):
        m = prod.search(cmd)
        if m:
            hits.append(m.group(0))
    calls = ssh_calls(cmd)
    if calls is None:  # 解析不了：保守地看整段
        if re.search(r"\bssh\b", cmd) and re.search(REMOTE_MUTATING, cmd):
            m = prod.search(cmd)
            if m:
                hits.append(m.group(0))
    else:
        for host, remote in calls:
            if re.search(REMOTE_MUTATING, remote) and prod.search(host):
                hits.append(host)
    return list(dict.fromkeys(hits))


def classify(cmd):
    for pat, why in CATASTROPHIC:
        if re.search(pat, cmd, re.I):
            return "deny", f"⛔ 已拒絕：{why}。這個指令不能由 agent 執行；若真的需要，請使用者自己在終端機操作。"
    for pat, why in GLOBAL_STATE:
        if re.search(pat, cmd, re.I):
            return "deny", f"↺ 請修正後重試：{why}；在每個指令上明確帶目標（--context／--project／--profile）。這不需要問使用者（K3）。"
    seg = missing_context(cmd)
    if seg:
        return "deny", (f"↺ 請修正後重試：這段指令沒有明確指定叢集「{seg[:80]}」。加上 --context <ctx>（helm 用 --kube-context），"
                        f"可用的 context 見 TRUTH.md。這不需要問使用者（K3）。")
    reasons = [why for pat, why in IRREVERSIBLE if re.search(pat, cmd, re.I)]
    hits = prod_changes(cmd) if os.environ.get("KIT_PROD_CONFIRM", "1") != "0" else []
    if hits:
        reasons.insert(0, f"prod 變更（{'、'.join(hits)}）")
    if reasons:
        # ask 的說明是給使用者看的（核准提示），不是給 agent 的指示
        return "ask", f"⚠ 需要你確認：{'；'.join(dict.fromkeys(reasons))}（K4）。同意才會執行。"
    return None, ""


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    decision, reason = classify((data.get("tool_input") or {}).get("command") or "")
    if not decision:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"guard.py error: {exc}", file=sys.stderr)
        sys.exit(1)
