#!/usr/bin/env python3
"""PreToolUse(Bash) hook：K3、K4 的保證層。三種處理方式：

1. 擋下並請 agent 自己修正（deny + 指示，不打擾使用者）
   - kubectl／helm 沒有明確帶 --context（K3）
   - 修改共用的全域設定：kubectl config use-context、kubectx、gcloud config set、aws eks update-kubeconfig…（K3）
2. 要求使用者確認（ask：桌面版會跳出核准提示，使用者點同意就照常執行；無人值守時等於擋下）
   - 不可逆操作（K4）
   - prod 上的變更（K4）；判斷不出變更目標時也當成 prod。K4 v3 允許「使用者明確要求、可回復」的 prod 變更直接做，
     這個提示是保險：互動使用時只是多點一次核准。設 KIT_PROD_CONFIRM=0 可以關掉這一類，只保留不可逆操作的確認。
3. 直接拒絕（deny）
   - 災難指令：rm -rf /、mkfs、dd 寫入磁碟

prod 名單來自 TRUTH.md「環境」表格中 prod 欄為 yes 的列；也可以用環境變數 KIT_PROD_PATTERN（regex）覆寫。
terraform、ansible 的目標是目錄、變數檔或群組，除了名單也看 prod／production／prd／live 這些字。
設 KIT_REQUIRE_CONTEXT=0 可以關掉「kubectl 一定要帶 --context」這一條。

怎麼判斷：先把指令切成一段段（; && || | 換行 $( ) 反引號），每段認出指令名稱與參數，再依指令套規則。
引號裡的字串、寫進檔案的 heredoc 是資料，不當成指令；會被執行的字串（ssh 的遠端指令、bash -c、
送進遠端 shell 的 heredoc 或腳本檔、kubectl exec、psql -c…）會再拆開檢查。

不涵蓋（已知邊界）：
- 刻意混淆（編碼後 eval、拼接指令名稱）。
- 目標不在 TRUTH.md 名單上的不算 prod：ansible 群組、terraform 環境、資料庫主機要列進 TRUTH.md 才認得。
- 遠端的變更指令是「列出來的才認得」（systemctl、sed -i、重導向、套件管理…），不在清單上的指令會放行。

修改紀錄：method/round1.md、method/round2.md、thinking/09-double-loop.md（雙迴圈試驗 1）。
回歸測試：evals/guard_test.py
"""
import itertools
import json
import os
import re
import shlex
import sys

# ---------------------------------------------------------------- 斷詞

SEPARATORS = {";", "&", "&&", "|", "||", "|&", "(", ")", "\n", "`", ";;"}
OPERATORS = ["&&", "||", "|&", ";;", "&>>", "&>", ">>", ">&", "<&", ">|", "<>", "<<<", "$(",
             ";", "&", "|", "(", ")", "`", ">", "<"]
REDIRECTS = {">", ">>", "<", ">&", "<&", "&>", "&>>", ">|", "<>", "<<<"}
WORD_END = set(" \t\n;&|()<>`")


class Tok:
    __slots__ = ("kind", "raw", "value", "quoted", "body", "adj")

    def __init__(self, kind, raw, value=None, quoted=False, adj=False):
        self.kind, self.raw, self.value, self.quoted, self.adj = kind, raw, value if value is not None else raw, quoted, adj
        self.body = None


def unquote(word):
    try:
        parts = shlex.split(word, posix=True)
    except ValueError:
        return word.strip("'\"")
    return " ".join(parts)


def _read_word(s, i):
    start, n = i, len(s)
    while i < n and s[i] not in WORD_END:
        c = s[i]
        if c == "\\":
            i += 2
        elif c == "'":
            j = s.find("'", i + 1)
            i = n if j < 0 else j + 1
        elif c == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == "\\" else 1
            i += 1
        elif c == "$" and s.startswith("$(", i):
            break
        elif c == "$" and s.startswith("${", i):
            j = s.find("}", i)
            i = n if j < 0 else j + 1
        else:
            i += 1
    return s[start:min(i, n)], min(i, n)


def lex(s):
    toks, pending, i, n = [], [], 0, len(s)
    while i < n:
        c = s[i]
        adj = i > 0 and s[i - 1] not in " \t\n"
        if c == "\\" and s.startswith("\\\n", i):
            i += 2
            continue
        if c in " \t":
            i += 1
            continue
        if c == "\n":
            toks.append(Tok("op", "\n"))
            i += 1
            for tok, delim, strip in pending:  # 讀 heredoc 內容
                lines = []
                while i < n:
                    j = s.find("\n", i)
                    line = s[i:] if j < 0 else s[i:j]
                    i = n if j < 0 else j + 1
                    if (line.lstrip("\t") if strip else line).strip() == delim:
                        break
                    lines.append(line)
                tok.body = "\n".join(lines)
            pending = []
            continue
        if c == "#" and not adj:  # 註解
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if s.startswith("<<", i) and not s.startswith("<<<", i):
            strip = s.startswith("<<-", i)
            i += 3 if strip else 2
            while i < n and s[i] in " \t":
                i += 1
            word, i = _read_word(s, i)
            tok = Tok("heredoc", "<<" + word)
            tok.body = ""
            toks.append(tok)
            pending.append((tok, unquote(word), strip))
            continue
        op = next((o for o in OPERATORS if s.startswith(o, i)), None)
        if op:
            toks.append(Tok("op", "(" if op == "$(" else op, adj=adj))
            i += len(op)
            continue
        word, i2 = _read_word(s, i)
        if i2 == i:  # 保險：不會卡住
            i2 = i + 1
            word = s[i]
        toks.append(Tok("word", word, unquote(word), quoted=word[:1] in "'\"", adj=adj))
        i = i2
    return toks


class Seg:
    """一段指令：words（參數，不含重導向）、redirects、heredocs、是否從 pipe 接收輸入。"""

    def __init__(self, pipe_in):
        self.words, self.redirects, self.heredocs, self.pipe_in = [], [], [], pipe_in


def segments(toks):
    segs, cur, pipe_in, i = [], Seg(False), False, 0
    while i < len(toks):
        t = toks[i]
        if t.kind == "op" and t.raw in SEPARATORS:
            if cur.words or cur.redirects or cur.heredocs:
                segs.append(cur)
            pipe_in = t.raw in ("|", "|&")
            cur = Seg(pipe_in)
        elif t.kind == "op" and t.raw in REDIRECTS:
            if cur.words and re.fullmatch(r"\d+", cur.words[-1].raw) and t.adj:
                cur.words.pop()  # 2>/dev/null 的 2
            target = toks[i + 1] if i + 1 < len(toks) and toks[i + 1].kind == "word" else None
            cur.redirects.append((t.raw, target.value if target else ""))
            i += 1 if target else 0
        elif t.kind == "heredoc":
            cur.heredocs.append(t.body or "")
        else:
            cur.words.append(t)
        i += 1
    if cur.words or cur.redirects or cur.heredocs:
        segs.append(cur)
    return segs


# ---------------------------------------------------------------- 名單與規則

GENERIC_PROD = re.compile(r"(?<![a-z])(prod|prd|production|live)(?![a-z])", re.I)


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
    return GENERIC_PROD


def _expand(name):
    """web1–web3 → web1 web2 web3；其他原樣。"""
    m = re.fullmatch(r"([A-Za-z][\w-]*?)(\d+)\s*[–~-]\s*(?:\1)?(\d+)", name)
    if m:
        return [f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(3)) + 1)]
    return [n for n in re.split(r"[\s,、]+", name) if n]


SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
DB_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "redis-cli", "mongosh", "mongo", "clickhouse-client"}
KEYWORDS = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "case", "esac", "!", "{", "}",
            "time", "function"}
WRAPPER_ARGS = {  # 包裝指令：哪些選項後面帶參數
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "--user", "--group"},
    "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "--class", "--classdata"},
    "nohup": set(), "stdbuf": set(), "command": set(), "exec": set(), "caffeinate": set(),
    "xargs": {"-I", "-n", "-P", "-d", "-E", "-L", "-s", "-a", "--max-args", "--max-procs", "--delimiter",
              "--arg-file", "--replace"},
    "watch": {"-n", "--interval", "-d"},
    "flock": {"-w", "-E", "--timeout"},
}
SSH_ARG_FLAGS = set("bcDEeFIiJLlmOopQRSWw")
SQL_IRREVERSIBLE = re.compile(r"\b(drop\s+(database|table|schema|index|view)|truncate\s+(table\s+)?[\w\"`]|"
                              r"delete\s+from|alter\s+table\s+\S+\s+drop)\b", re.I)
SQL_MUTATING = re.compile(r"\b(insert\s+into|update\s+[\w\"`.]+\s+set|delete\s+from|drop|truncate|alter|create|grant"
                          r"|revoke|flushall|flushdb|del|set|hset|expire)\b", re.I)
KUBE_GLOBAL_ARGS = {"-n", "--namespace", "--context", "--kubeconfig", "--cluster", "--user", "-s", "--server",
                    "--token", "--request-timeout", "-v", "--as", "--as-group", "--certificate-authority",
                    "--client-certificate", "--client-key", "--tls-server-name", "--cache-dir"}
KUBE_LOCAL = {"config", "completion", "plugin", "kustomize", "help", "options"}
KUBE_MUTATING = {"apply", "create", "replace", "patch", "edit", "set", "scale", "autoscale", "annotate", "label",
                 "taint", "delete", "drain", "cordon", "uncordon", "expose", "run", "cp", "rollout", "certificate",
                 "debug"}
HELM_GLOBAL_ARGS = {"--kube-context", "-n", "--namespace", "--kubeconfig", "--repository-config",
                    "--repository-cache", "--registry-config", "--kube-apiserver", "--kube-token", "--kube-as-user"}
HELM_CLUSTER = {"install", "upgrade", "uninstall", "delete", "rollback", "list", "ls", "status", "get", "history",
                "test", "diff"}
HELM_MUTATING = {"install", "upgrade", "rollback", "uninstall", "delete"}
ANSIBLE_ARGS = {"-i", "--inventory", "-m", "--module-name", "-a", "--args", "-u", "--user", "-f", "--forks", "-e",
                "--extra-vars", "-l", "--limit", "-T", "--timeout", "-M", "--module-path", "--become-user", "-c",
                "--connection", "-P", "--poll", "-B", "--background", "--private-key", "--vault-password-file"}
ANSIBLE_READONLY = {"ping", "setup", "gather_facts", "stat", "slurp", "find", "debug", "service_facts",
                    "package_facts", "ansible.builtin.ping", "ansible.builtin.setup", "ansible.builtin.stat"}
ANSIBLE_CHECK = {"--check", "-C", "--syntax-check", "--list-hosts", "--list-tasks", "--list-tags"}
SCP_ARGS = {"-P", "-i", "-o", "-F", "-c", "-l", "-S", "-J", "-D"}
RSYNC_ARGS = {"-e", "--rsh", "--exclude", "--include", "--filter", "-f", "--files-from", "--exclude-from",
              "--include-from", "--password-file", "--port", "--chmod", "--chown", "--log-file", "--backup-dir",
              "--suffix", "--compare-dest", "--link-dest", "--copy-dest", "-T", "--temp-dir", "-M",
              "--remote-option"}
SAFE_WRITE = re.compile(r"^(/tmp/|/var/tmp/|/dev/(null|stdout|stderr|fd/))")
DISK_DEVICE = re.compile(r"^/dev/(sd|nvme|vd|xvd|hd|mmcblk|md\d|dm-|disk/|mapper/)")
POWER = {"reboot", "shutdown", "poweroff", "halt"}


# ---------------------------------------------------------------- 分析

class Result:
    def __init__(self):
        self.deny, self.fix, self.irreversible, self.prod, self.unknown = [], [], [], [], []


class Analyzer:
    def __init__(self):
        self.prod = prod_pattern()
        self.vars = {}
        self.r = Result()
        self.base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    # 變數：for h in …、CTX=…；解不出來的是 None
    def collect_vars(self, segs):
        for seg in segs:
            w = [t.value for t in seg.words]
            if len(w) >= 3 and w[0] == "for" and w[2] == "in":
                items = w[3:]
                self.vars[w[1]] = items if items and not any("$" in x for x in items) else None
            for t in seg.words:
                if t.kind != "word":
                    break
                m = re.fullmatch(r"(?:export\s+)?([A-Za-z_]\w*)=(.*)", t.value, re.S)
                if t.value in ("export", "declare", "local", "readonly"):
                    continue
                if not m:
                    break
                self.vars[m.group(1)] = [m.group(2)] if m.group(2) and "$" not in m.group(2) else None

    def resolve(self, value):
        names = re.findall(r"\$\{?(\w+)\}?", value)
        if not names:
            return [value]
        options = []
        for name in names:
            vals = self.vars.get(name)
            if not vals:
                return None
            options.append(vals)
        out = []
        for combo in itertools.islice(itertools.product(*options), 50):
            v = value
            for name, val in zip(names, combo):
                v = re.sub(r"\$\{?" + name + r"\}?", val, v, count=1)
            out.append(v)
        return out

    def is_prod(self, values, generic=False):
        """values：可能的目標名稱；None 表示判斷不出來。回傳 (命中的 prod 名稱, 是否判斷不出)。"""
        if values is None:
            return None, True
        for v in values:
            m = self.prod.search(v) or (generic and GENERIC_PROD.search(v))
            if m:
                return m.group(0), False
        return None, False

    def hit(self, values, label, generic=False):
        name, unknown = self.is_prod(values, generic)
        if unknown:
            self.r.unknown.append(label)
        elif name:
            self.r.prod.append(name)

    def read_script(self, path):
        for base in (os.getcwd(), self.base):
            p = os.path.expanduser(path if os.path.isabs(path) else os.path.join(base, path))
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    return f.read(200_000)
            except OSError:
                continue
        return None

    # where: ("local",) / ("remote", 主機列表或 None) / ("pod", context 列表或 None)
    def unit(self, text, where=("local",), depth=0):
        if depth > 4 or not text:
            return
        segs = segments(lex(text))
        self.collect_vars(segs)
        for seg in segs:
            self.segment(seg, where, depth)

    def segment(self, seg, where, depth):
        words = seg.words
        values = [t.value for t in words]
        if values[:1] == ["for"]:
            return
        i, wrappers = command_index(values)
        if "watch" in wrappers:
            rest = words[i:]
            self.unit(rest[0].value if len(rest) == 1 else " ".join(t.value for t in rest), where, depth + 1)
            return
        cmd = os.path.basename(words[i].value) if i < len(words) else ""
        args = [t.value for t in words[i + 1:]]
        arg_toks = words[i + 1:]
        self.redirect_checks(seg, cmd, where)
        if not cmd:
            return
        self.catastrophic(cmd, args)
        self.global_state(cmd, args, seg)
        self.irreversible(cmd, args, wrappers)

        if cmd in SHELLS:
            if "-c" in args:
                k = args.index("-c")
                if k + 1 < len(args):
                    self.unit(args[k + 1], where, depth + 1)
            else:
                script = next((a for a in args if not a.startswith("-")), None)
                if script:
                    body = self.read_script(script)
                    if body is not None:
                        self.unit(body, where, depth + 1)
                elif seg.heredocs:
                    self.unit("\n".join(seg.heredocs), where, depth + 1)
                else:
                    src = next((t for op, t in seg.redirects if op == "<"), None)
                    body = self.read_script(src) if src else None
                    if body is not None:
                        self.unit(body, where, depth + 1)
                    elif where[0] != "local" and (src or seg.pipe_in):
                        self.remote_change(where, "看不到要執行的腳本內容")
            return
        if cmd in ("source", ".") or (words[i].value.startswith("./") and words[i].value.endswith(".sh")):
            body = self.read_script(args[0] if cmd in ("source", ".") and args else words[i].value)
            if body is not None:
                self.unit(body, where, depth + 1)
        if cmd == "eval":
            self.unit(" ".join(args), where, depth + 1)
        if cmd == "find":
            for k, a in enumerate(args):
                if a in ("-exec", "-execdir", "-ok", "-okdir"):
                    end = next((j for j in range(k + 1, len(args)) if args[j] in (";", "+", "\\")), len(args))
                    self.unit(" ".join(args[k + 1:end]), where, depth + 1)
        if cmd in DB_CLIENTS:
            self.db(cmd, args, arg_toks, seg, where)
        if cmd == "kubectl":
            self.kubectl(args, where, depth)
        elif cmd == "helm":
            self.helm(args, where)
        elif cmd in ("terraform", "tofu"):
            self.terraform(args)
        elif cmd == "ansible-playbook":
            if not ANSIBLE_CHECK & set(args):
                self.hit([" ".join(args)], "ansible-playbook", generic=True)
        elif cmd == "ansible":
            self.ansible(args, depth)
        elif cmd == "ssh":
            self.ssh(args, arg_toks, seg, depth)
        elif cmd in ("scp", "rsync"):
            self.transfer(cmd, args)
        elif where[0] != "local":
            why = remote_mutation(cmd, args, seg)
            if why:
                self.remote_change(where, why)

    def remote_change(self, where, why):
        if where[0] == "remote":
            self.hit(where[1], f"判斷不出主機的遠端變更（{why}）")
        elif where[0] == "pod":
            self.hit(where[1], f"判斷不出 context 的 pod 內變更（{why}）")

    def redirect_checks(self, seg, cmd, where):
        for op, target in seg.redirects:
            if op in (">", ">|", "&>") and target and not SAFE_WRITE.match(target) and cmd in ("", ":", "true"):
                self.r.irreversible.append("清空檔案內容")
            if where[0] != "local" and op in (">", ">>", "&>", "&>>", ">|") and target \
                    and not SAFE_WRITE.match(target) and not target.startswith("&"):
                self.remote_change(where, "寫入檔案")

    def catastrophic(self, cmd, args):
        if cmd == "rm" and any(re.match(r"^-\w*[rR]", a) or a == "--recursive" for a in args):
            if any(a in ("/", "/*", "~", "~/", "$HOME", "$HOME/", "/home", "/root") for a in args):
                self.r.deny.append("rm -r 目標是根目錄或家目錄")
        if "--no-preserve-root" in args:
            self.r.deny.append("--no-preserve-root")
        if re.fullmatch(r"mkfs(\.\w+)?", cmd) or cmd in ("wipefs",):
            self.r.deny.append("格式化檔案系統")
        if cmd == "dd" and any(a.startswith("of=") and DISK_DEVICE.match(a[3:]) for a in args):
            self.r.deny.append("dd 寫入磁碟裝置")

    def global_state(self, cmd, args, seg):
        own_kubeconfig = "--kubeconfig" in " ".join(args) or any(
            t.value.startswith("KUBECONFIG=") for t in seg.words)
        pos = [a for a in args if not a.startswith("-")]
        why = None
        if cmd == "kubectl" and pos[:1] == ["config"] and len(pos) > 1 and pos[1] in (
                "use-context", "use", "set-context", "delete-context", "rename-context", "set-cluster",
                "delete-cluster", "set-credentials", "delete-user", "set", "unset") and not own_kubeconfig:
            why = "不要修改共用的 kubeconfig（其他 session 也在用）"
        elif cmd in ("kubectx", "kubens") and any(not a.startswith("-") or a == "-" for a in args):
            why = "不要切換全域 context／namespace（其他 session 也在用）"
        elif cmd == "gcloud" and (pos[:2] == ["config", "set"] or pos[:3] == ["config", "configurations", "activate"]
                                  or pos[:2] == ["config", "unset"]):
            why = "不要修改 gcloud 全域設定，改用 --project／--configuration"
        elif cmd == "gcloud" and pos[:3] == ["container", "clusters", "get-credentials"] and not own_kubeconfig:
            why = "get-credentials 會改寫共用的 kubeconfig 並切換 current-context；改用 KUBECONFIG=<獨立檔案>"
        elif cmd == "aws" and pos[:2] == ["configure", "set"]:
            why = "不要修改 aws 全域設定，改用 --profile"
        elif cmd == "aws" and pos[:2] == ["eks", "update-kubeconfig"] and not own_kubeconfig \
                and "--dry-run" not in args:
            why = "update-kubeconfig 會改寫共用的 kubeconfig 並切換 current-context；改用 --kubeconfig <獨立檔案>"
        elif cmd == "az" and pos[:2] == ["account", "set"]:
            why = "不要修改 az 全域設定，改用 --subscription"
        elif cmd == "az" and pos[:2] == ["aks", "get-credentials"] and "--file" not in args and "-f" not in args:
            why = "get-credentials 會改寫共用的 kubeconfig；改用 --file <獨立檔案>"
        if why:
            self.r.fix.append(why)

    def irreversible(self, cmd, args, wrappers):
        pos = [a for a in args if not a.startswith("-")]
        if cmd == "rm" and any(re.match(r"^-\w*[rR]", a) or a == "--recursive" for a in args):
            self.r.irreversible.append("遞迴刪除檔案")
        if cmd == "rm" and "xargs" in wrappers:
            self.r.irreversible.append("xargs rm 刪除檔案")
        if cmd == "truncate":
            self.r.irreversible.append("清空檔案內容")
        if cmd == "cp" and args[:1] == ["/dev/null"]:
            self.r.irreversible.append("清空檔案內容")
        if cmd == "find" and ("-delete" in args or any(
                a in ("-exec", "-execdir") and k + 1 < len(args) and os.path.basename(args[k + 1]) in ("rm", "unlink")
                for k, a in enumerate(args))):
            self.r.irreversible.append("find 刪除檔案")
        if cmd in POWER or (cmd == "systemctl" and pos[:1] and pos[0] in POWER | {"kexec"}) \
                or (cmd in ("init", "telinit") and pos[:1] in (["0"], ["6"])):
            self.r.irreversible.append("重開機／關機")
        if cmd == "docker" and len(pos) >= 2 and pos[0] in ("system", "volume", "image", "container", "network") \
                and pos[1] in ("prune", "rm"):
            self.r.irreversible.append("docker 刪除資料")
        if cmd == "aws" and (any(re.match(r"(delete|terminate)-", a) for a in pos)
                             or pos[:2] in (["s3", "rm"], ["s3", "rb"])):
            self.r.irreversible.append("AWS 刪除／終止資源")
        if cmd in ("gcloud", "az") and "delete" in pos:
            self.r.irreversible.append("雲端刪除資源")
        if cmd == "journalctl" and any(a.startswith("--vacuum") for a in args):
            self.r.irreversible.append("清除系統日誌")

    def db(self, cmd, args, arg_toks, seg, where):
        code = []
        for k, a in enumerate(args):
            if a in ("-c", "-e", "--command", "--execute", "--eval") and k + 1 < len(args):
                code.append(args[k + 1])
            elif re.match(r"--(command|execute|eval)=", a):
                code.append(a.split("=", 1)[1])
        if cmd == "sqlite3":
            code += [t.value for t in arg_toks[1:] if t.quoted]
        if cmd == "redis-cli":
            code.append(" ".join(a for a in args if not a.startswith("-")))
        code += seg.heredocs
        text = "\n".join(code)
        if SQL_IRREVERSIBLE.search(text) or (cmd == "redis-cli" and re.search(r"\bflush(all|db)\b", text, re.I)):
            self.r.irreversible.append("刪除資料庫資料")
        if SQL_MUTATING.search(text):
            if where[0] == "local":
                self.hit([" ".join(args)], f"{cmd} 寫入")
            else:
                self.remote_change(where, f"{cmd} 寫入")

    def kubectl(self, args, where, depth):
        ctx, has_ctx, verb, rest, k = None, False, None, [], 0
        for j, a in enumerate(args):
            if a == "--context" and j + 1 < len(args):
                ctx, has_ctx = args[j + 1], True
            elif a.startswith("--context="):
                ctx, has_ctx = a.split("=", 1)[1], True
        while k < len(args):
            a = args[k]
            if a == "--":
                break
            if a.startswith("-"):
                k += 2 if a in KUBE_GLOBAL_ARGS else 1
                continue
            verb, rest = a, args[k + 1:]
            break
        if verb is None or any(a in ("-h", "--help") for a in args):
            return
        positional = [a for a in rest if not a.startswith("-")]
        local = verb in KUBE_LOCAL or (verb == "version" and "--client" in rest)
        if not local and not has_ctx and os.environ.get("KIT_REQUIRE_CONTEXT", "1") != "0" and where[0] != "pod":
            self.r.fix.append("missing-context:kubectl " + " ".join(args)[:60])
        targets = self.resolve(ctx) if ctx else None
        dry = any(a.startswith("--dry-run") and a != "--dry-run=none" for a in rest)
        if verb == "exec":
            if "--" in args:
                inner = args[args.index("--") + 1:]
                self.unit(inner[0] if len(inner) == 1 else " ".join(inner), ("pod", targets), depth + 1)
            return
        if verb not in KUBE_MUTATING or dry or local:
            return
        if verb == "rollout" and positional[:1] not in (["restart"], ["undo"], ["pause"], ["resume"]):
            return
        if verb in ("set", "label", "annotate") and "--list" in rest:
            return
        if verb == "apply" and positional[:1] == ["view-last-applied"]:
            return
        if verb == "cp" and not (positional and ":" in positional[-1]):
            return
        if verb in ("delete", "drain"):
            self.r.irreversible.append(f"kubectl {verb}")
        if where[0] == "local":
            self.hit(targets, f"判斷不出 kubectl 的 context（{ctx}）")
        else:
            self.remote_change(where, f"kubectl {verb}")

    def helm(self, args, where):
        has_ctx, ctx, sub, k = False, None, None, 0
        for j, a in enumerate(args):
            if a == "--kube-context" and j + 1 < len(args):
                ctx, has_ctx = args[j + 1], True
            elif a.startswith("--kube-context="):
                ctx, has_ctx = a.split("=", 1)[1], True
        while k < len(args):
            a = args[k]
            if a.startswith("-"):
                k += 2 if a in HELM_GLOBAL_ARGS else 1
                continue
            sub = a
            break
        if sub in HELM_CLUSTER and not has_ctx and os.environ.get("KIT_REQUIRE_CONTEXT", "1") != "0":
            self.r.fix.append("missing-context:helm " + " ".join(args)[:60])
        if sub in HELM_MUTATING and not any(a.startswith("--dry-run") for a in args):
            if sub in ("uninstall", "delete"):
                self.r.irreversible.append("helm 移除 release")
            if where[0] == "local":
                self.hit(self.resolve(ctx) if ctx else None, f"判斷不出 helm 的 context（{ctx}）")
            else:
                self.remote_change(where, f"helm {sub}")

    def terraform(self, args):
        pos = [a for a in args if not a.startswith("-")]
        sub = pos[0] if pos else ""
        destroy = sub == "destroy" or (sub == "apply" and "-destroy" in args) or pos[:2] == ["state", "rm"] \
            or pos[:2] == ["workspace", "delete"]
        if destroy:
            self.r.irreversible.append("terraform 刪除資源／state")
        if destroy or sub in ("apply", "import", "taint", "untaint") or pos[:2] in (
                ["state", "mv"], ["state", "push"], ["state", "replace-provider"]):
            self.hit([" ".join(args) + " " + os.environ.get("TF_WORKSPACE", "")], "terraform", generic=True)

    def ansible(self, args, depth):
        pattern, module, margs, limit, k = None, "command", "", None, 0
        while k < len(args):
            a = args[k]
            if a in ANSIBLE_ARGS and k + 1 < len(args):
                if a in ("-m", "--module-name"):
                    module = args[k + 1]
                elif a in ("-a", "--args"):
                    margs = args[k + 1]
                elif a in ("-l", "--limit"):
                    limit = args[k + 1]
                k += 2
                continue
            if not a.startswith("-") and pattern is None:
                pattern = a
            k += 1
        hosts = []
        for expr in filter(None, (pattern, limit)):
            vals = self.resolve(expr)
            if vals is None:
                hosts = None
                break
            hosts += [h for v in vals for h in re.split(r"[:,&!]+", v) if h]
        if ANSIBLE_CHECK & set(args):
            return
        short = module.split(".")[-1]
        if short in ("command", "shell", "raw"):
            self.unit(margs, ("remote", hosts), depth + 1)
        elif module not in ANSIBLE_READONLY and short not in ANSIBLE_READONLY:
            self.hit(hosts, f"ansible -m {module}", generic=True)

    def ssh(self, args, arg_toks, seg, depth):
        k = 0
        while k < len(args) and args[k].startswith("-") and len(args[k]) > 1:
            k += 2 if (len(args[k]) == 2 and args[k][1] in SSH_ARG_FLAGS) else 1
        if k >= len(args):
            return
        host_expr = args[k].split("@")[-1]
        hosts = self.resolve(host_expr)
        remote = args[k + 1:]
        if remote[:1] == ["--"]:
            remote = remote[1:]
        text = " ".join(remote)
        where = ("remote", hosts)
        first = lex(text)
        rsegs = segments(first)
        reads_stdin = not remote or (len(rsegs) == 1 and _is_stdin_shell(rsegs[0]))
        if reads_stdin:
            if seg.heredocs:
                self.unit("\n".join(seg.heredocs), where, depth + 1)
                return
            src = next((t for op, t in seg.redirects if op == "<"), None)
            if src:
                body = self.read_script(src)
                if body is None:
                    self.remote_change(where, "看不到要執行的腳本內容")
                else:
                    self.unit(body, where, depth + 1)
                return
            if seg.pipe_in:
                self.remote_change(where, "看不到要執行的腳本內容")
            return
        self.unit(text, where, depth + 1)

    def transfer(self, cmd, args):
        takes = SCP_ARGS if cmd == "scp" else RSYNC_ARGS
        pos, k = [], 0
        while k < len(args):
            a = args[k]
            if a.startswith("-"):
                k += 2 if a in takes else 1
                continue
            pos.append(a)
            k += 1
        if len(pos) < 2:
            return
        dest = pos[-1]
        m = re.match(r"^(?:rsync://)?(?:[^@/:]+@)?([^/:]+)(?::|/)", dest) if dest.startswith("rsync://") else \
            re.match(r"^(?:[^@/:]+@)?([^/:]+):", dest)
        if m:
            self.hit(self.resolve(m.group(1)), f"判斷不出 {cmd} 的目標主機（{m.group(1)}）")


def command_index(values):
    """跳過關鍵字、變數設定、包裝指令（sudo、env、timeout、xargs…），回傳 (指令名稱的位置, 包裝指令)。"""
    i, wrappers = 0, []
    while i < len(values):
        v = values[i]
        if v in KEYWORDS or v in ("export", "declare", "local") or re.fullmatch(r"[A-Za-z_]\w*=.*", v, re.S):
            i += 1
            continue
        name = os.path.basename(v)
        if name not in WRAPPER_ARGS:
            break
        wrappers.append(name)
        i += 1
        takes = WRAPPER_ARGS[name]
        while i < len(values) and values[i].startswith("-") and values[i] != "-":
            i += 2 if values[i] in takes else 1
        if name == "timeout" and i < len(values):
            i += 1  # 時間長度
        if name == "watch":
            break
    return i, wrappers


def _is_stdin_shell(seg):
    values = [t.value for t in seg.words]
    i, _ = command_index(values)
    if i >= len(values) or os.path.basename(values[i]) not in SHELLS:
        return False
    rest = values[i + 1:]
    return "-c" not in rest and not any(not a.startswith("-") for a in rest)


def remote_mutation(cmd, args, seg):
    """在遠端主機或 pod 裡會造成變更的指令；回傳原因或 None。"""
    pos = [a for a in args if not a.startswith("-")]
    verb = pos[0] if pos else ""
    if cmd == "systemctl" and verb in ("start", "stop", "restart", "reload", "try-restart", "reload-or-restart",
                                       "try-reload-or-restart", "enable", "disable", "mask", "unmask",
                                       "daemon-reload", "kill", "isolate", "set-property", "edit", "reboot",
                                       "poweroff", "halt", "kexec"):
        return f"systemctl {verb}"
    if cmd == "service" and len(pos) >= 2 and pos[1] in ("start", "stop", "restart", "reload", "force-reload"):
        return f"service {pos[1]}"
    if cmd in ("nginx", "openresty") and "-s" in args:
        return "nginx -s"
    if cmd in ("apachectl", "apache2ctl", "httpd") and verb in ("restart", "graceful", "stop", "start",
                                                                "graceful-stop"):
        return f"{cmd} {verb}"
    if cmd == "sed" and any(re.match(r"^-[a-zA-Z]*i", a) or a.startswith("--in-place") for a in args):
        return "sed -i"
    if cmd == "tee" and any(not a.startswith("-") and not SAFE_WRITE.match(a) for a in args):
        return "tee 寫入檔案"
    if cmd in {"rm", "rmdir", "unlink", "truncate", "chmod", "chown", "chgrp", "ln", "kill", "pkill", "killall",
               "useradd", "userdel", "usermod", "passwd", "mount", "umount", "swapoff", "swapon"} | POWER:
        return cmd
    if cmd in ("cp", "mv", "install") and not (pos and SAFE_WRITE.match(pos[-1])):
        return cmd
    if cmd == "logrotate" and not ({"-d", "--debug"} & set(args)):
        return "logrotate"
    if cmd in ("apt", "apt-get", "aptitude") and verb in ("install", "remove", "purge", "upgrade", "dist-upgrade",
                                                          "full-upgrade", "autoremove", "reinstall"):
        return f"{cmd} {verb}"
    if cmd in ("yum", "dnf", "zypper", "apk") and verb in ("install", "remove", "erase", "update", "upgrade",
                                                           "downgrade", "reinstall", "autoremove", "add", "del"):
        return f"{cmd} {verb}"
    if cmd in ("pip", "pip3", "npm", "gem") and verb in ("install", "uninstall"):
        return f"{cmd} {verb}"
    if cmd in ("docker", "podman", "nerdctl", "crictl") and verb in (
            "restart", "stop", "start", "kill", "rm", "rmi", "run", "update", "pause", "unpause", "create",
            "prune", "pull", "load", "tag", "push", "compose", "rename"):
        if verb == "compose" and not (set(pos[1:2]) & {"up", "down", "restart", "stop", "start", "rm", "pull",
                                                         "kill", "create"}):
            return None
        return f"{cmd} {verb}"
    if cmd in ("docker-compose",) and verb in ("up", "down", "restart", "stop", "start", "rm", "pull", "kill"):
        return f"{cmd} {verb}"
    if cmd == "crontab" and (set(args) & {"-r", "-e"} or pos):
        return "crontab"
    if cmd in ("iptables", "ip6tables") and set(args) & {"-A", "-D", "-I", "-R", "-F", "-X", "-P", "-N",
                                                         "--append", "--delete", "--insert", "--flush"}:
        return cmd
    if cmd in ("ufw", "firewall-cmd") and verb not in ("status", "") and "--list-all" not in args \
            and "--state" not in args:
        return cmd
    if cmd == "sysctl" and ("-w" in args or "-p" in args or any("=" in a for a in pos)):
        return "sysctl"
    if cmd in ("hostnamectl", "timedatectl", "localectl") and verb.startswith("set"):
        return cmd
    return None


def classify(cmd):
    a = Analyzer()
    a.unit(cmd)
    r = a.r
    if r.deny:
        return "deny", f"⛔ 已拒絕：{r.deny[0]}。這個指令不能由 agent 執行；若真的需要，請使用者自己在終端機操作。"
    state = [w for w in r.fix if not w.startswith("missing-context:")]
    if state:
        return "deny", f"↺ 請修正後重試：{state[0]}；在每個指令上明確帶目標（--context／--project／--profile）。這不需要問使用者（K3）。"
    missing = [w.split(":", 1)[1] for w in r.fix if w.startswith("missing-context:")]
    if missing:
        return "deny", (f"↺ 請修正後重試：這段指令沒有明確指定叢集「{missing[0]}」。加上 --context <ctx>（helm 用 --kube-context），"
                        f"可用的 context 見 TRUTH.md。這不需要問使用者（K3）。")
    reasons = list(r.irreversible)
    if os.environ.get("KIT_PROD_CONFIRM", "1") != "0":
        if r.prod:
            reasons.insert(0, f"prod 變更（{'、'.join(dict.fromkeys(r.prod))}）")
        reasons += r.unknown
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
