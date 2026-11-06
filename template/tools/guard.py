#!/usr/bin/env python3
"""PreToolUse(Bash) hook：K3、K4 的保證層。三種處理方式：

1. 擋下並請 agent 自己修正（deny + 指示，不打擾使用者）
   - kubectl／helm 沒有明確帶 --context（K3）
   - 修改共用的全域設定：kubectl config use-context、kubectx、gcloud config set…（K3）
2. 要求使用者確認（ask；無人值守時等於擋下）
   - R3：prod 上的變更、不可逆操作（K4）
3. 直接拒絕（deny）
   - 災難指令：rm -rf /、mkfs、dd 寫入磁碟

prod 名單來自 TRUTH.md「環境」表格中 prod 欄為 yes 的列；也可以用環境變數 KIT_PROD_PATTERN（regex）覆寫。
設 KIT_REQUIRE_CONTEXT=0 可以關掉「kubectl 一定要帶 --context」這一條。

第 1 輪思想實驗後的修改（method/round1.md）：
- 「沒帶 --context」從「問使用者」改成「擋下讓 agent 自己補上」：這是可以自己修正的錯，不該打斷使用者。
- 補上 truncate、find -delete、logrotate -f 等清除檔案的寫法。
"""
import json
import os
import re
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

MUTATING = [
    r"\bkubectl\b" + SEG + r"\s(apply|create|replace|patch|edit|set|scale|annotate|label|delete|drain|cordon|uncordon"
    r"|rollout\s+(restart|undo))\b",
    r"\bhelm\b" + SEG + r"\s(install|upgrade|rollback|uninstall)\b",
    r"\b(terraform|tofu)\b" + SEG + r"\s(apply|destroy|import)\b",
    r"\bansible-playbook\b(?!" + SEG + r"\s(--check|-C)\b)",
    r"\bssh\b" + SEG + r"(systemctl\s+(start|stop|restart|reload|enable|disable)|sed\s+-i|\btee\b|\brm\s|\bmv\s|\bcp\s"
    r"|\bkill|\btruncate\b|\blogrotate\b|\b(apt|apt-get|yum|dnf)\s+(install|remove|upgrade)|>\s*/)",
]


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
    if any(re.search(p, cmd) for p in MUTATING):
        hit = prod_pattern().search(cmd)
        if hit:
            reasons.insert(0, f"prod 變更（{hit.group(0)}）")
    if reasons:
        return "ask", (f"⚠ R3 需要使用者確認：{'；'.join(dict.fromkeys(reasons))}。不要換寫法繞過；"
                       f"停下來說明「做什麼、影響範圍、怎麼回滾」，讓使用者決定（K4）。")
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
