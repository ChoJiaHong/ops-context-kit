#!/usr/bin/env python3
"""PreToolUse(Bash) hook：K3、K4 的保證層。三種處理方式：

1. 擋下並請 agent 自己修正（deny + 指示，不打擾使用者）
   - kubectl／helm 沒有明確帶 --context（K3）
   - 修改共用的全域設定：kubectl config use-context、kubectx、gcloud config set、aws eks update-kubeconfig、
     覆寫 ~/.kube/config…（K3）
2. 要求使用者確認（ask：桌面版會跳出核准提示，使用者點同意就照常執行；無人值守時等於擋下）
   - 不可逆操作（K4）
   - prod 上的變更（K4）；判斷不出變更目標時也當成 prod。K4 v3 允許「使用者明確要求、可回復」的 prod 變更直接做，
     這個提示是保險：互動使用時只是多點一次核准。設 KIT_PROD_CONFIRM=0 可以關掉這一類，只保留不可逆操作的確認。
3. 直接拒絕（deny）
   - 災難指令：rm -rf /、mkfs、dd 寫入區塊裝置

prod 名單來自 TRUTH.md「環境」表格中 prod 欄為 yes 的列；也可以用環境變數 KIT_PROD_PATTERN（regex）覆寫。
terraform、ansible、helmfile 的目標是目錄、變數檔或群組，除了名單也看 prod／production／prd／live 這些字。
設 KIT_REQUIRE_CONTEXT=0 可以關掉「kubectl 一定要帶 --context」這一條。

怎麼判斷：先把指令切成一段段（; && || | 換行、子 shell），每段認出指令名稱與參數，再依指令套規則。
- 引號裡的字串、寫進檔案的 heredoc 是資料，不當成指令。
- 會被執行的內容會再拆開檢查：$( ) 與反引號（包括雙引號裡的）、ssh 的遠端指令、bash -c、
  送進 shell／資料庫／容器的 heredoc、here-string、stdin 檔案、腳本檔（包括同一個指令裡剛寫好的）、
  kubectl／docker exec、find -exec、xargs、watch、su -c。
- 目標可以是變數（for h in …、CTX=…）、大括號展開（web{1..3}）、cd 進去的目錄；解不出來的當成判斷不出目標。

不涵蓋（已知邊界）：
- 刻意混淆（編碼後 eval、拼接指令名稱）。
- 目標不在 TRUTH.md 名單上的不算 prod：ansible 群組或 inventory 檔、資料庫主機要列進 TRUTH.md 才認得。
- 遠端的變更指令是「列出來的才認得」（systemctl、sed -i、重導向、套件管理、docker…），清單外的指令會放行。
- 由程式語言間接執行的指令（python subprocess、Makefile 等）與清單外的遠端執行工具（aws ssm、pssh…）。

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

SEPARATORS = {";", "&", "&&", "|", "||", "|&", "(", ")", "\n", ";;"}
OPERATORS = ["&&", "||", "|&", ";;", "&>>", "&>", ">>", ">&", "<&", ">|", "<>", "<<<",
             ";", "&", "|", "(", ")", ">", "<"]
REDIRECTS = {">", ">>", "<", ">&", "<&", "&>", "&>>", ">|", "<>", "<<<"}
WORD_END = set(" \t\n;&|()<>")


class Tok:
    __slots__ = ("kind", "raw", "value", "quoted", "body", "adj", "subs")

    def __init__(self, kind, raw, value=None, quoted=False, adj=False, subs=None):
        self.kind, self.raw, self.quoted, self.adj = kind, raw, quoted, adj
        self.value = value if value is not None else raw
        self.body = None
        self.subs = subs or []


def unquote(word):
    try:
        parts = shlex.split(word, posix=True)
    except ValueError:
        return word.strip("'\"")
    return " ".join(parts)


def _match_paren(s, i):
    """s[i] 是 '('：回傳對應的 ')' 之後的位置。"""
    depth, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            j = s.find("'", i + 1)
            i = n if j < 0 else j + 1
            continue
        if c == '"':
            i = _skip_dq(s, i, [])
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _skip_dq(s, i, subs):
    """s[i] 是 '"'：回傳結束引號之後的位置，順便收集裡面的 $( ) 與反引號。"""
    n = len(s)
    i += 1
    while i < n and s[i] != '"':
        if s[i] == "\\":
            i += 2
            continue
        if s.startswith("$((", i):
            i = _match_paren(s, i + 1)
            continue
        if s.startswith("$(", i):
            j = _match_paren(s, i + 1)
            subs.append(s[i + 2:j - 1])
            i = j
            continue
        if s[i] == "`":
            j = s.find("`", i + 1)
            j = n if j < 0 else j
            subs.append(s[i + 1:j])
            i = j + 1
            continue
        i += 1
    return i + 1


def _read_word(s, i):
    start, n, subs = i, len(s), []
    while i < n and s[i] not in WORD_END:
        c = s[i]
        if c == "\\":
            i += 2
        elif c == "'":
            j = s.find("'", i + 1)
            i = n if j < 0 else j + 1
        elif c == '"':
            i = _skip_dq(s, i, subs)
        elif s.startswith("$((", i):
            i = _match_paren(s, i + 1)
        elif s.startswith("$(", i):
            j = _match_paren(s, i + 1)
            subs.append(s[i + 2:j - 1])
            i = j
        elif c == "`":
            j = s.find("`", i + 1)
            j = n if j < 0 else j
            subs.append(s[i + 1:j])
            i = j + 1
        elif s.startswith("${", i):
            j = s.find("}", i)
            i = n if j < 0 else j + 1
        else:
            i += 1
    return s[start:min(i, n)], min(i, n), subs


def lex(s):
    toks, pending, i, n = [], [], 0, len(s)
    while i < n:
        c = s[i]
        adj = i > 0 and s[i - 1] not in " \t\n"
        if s.startswith("\\\n", i):
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
        if s.startswith("((", i) and not adj:  # 算術 (( … ))
            i = _match_paren(s, i)
            continue
        if s.startswith("<<", i) and not s.startswith("<<<", i):
            strip = s.startswith("<<-", i)
            i += 3 if strip else 2
            while i < n and s[i] in " \t":
                i += 1
            word, i, _ = _read_word(s, i)
            tok = Tok("heredoc", "<<" + word)
            tok.body = ""
            toks.append(tok)
            pending.append((tok, unquote(word), strip))
            continue
        op = next((o for o in OPERATORS if s.startswith(o, i)), None)
        if op:
            toks.append(Tok("op", op, adj=adj))
            i += len(op)
            continue
        word, i2, subs = _read_word(s, i)
        if i2 == i:  # 保險：不會卡住
            i2, word = i + 1, s[i]
        toks.append(Tok("word", word, unquote(word), quoted=word[:1] in "'\"", adj=adj, subs=subs))
        i = i2
    return toks


class Seg:
    """一段指令：words（參數，不含重導向）、redirects、heredocs、從 pipe 接收輸入、$( ) 內容。"""

    def __init__(self, pipe_in):
        self.words, self.redirects, self.heredocs, self.pipe_in, self.subs = [], [], [], pipe_in, []


def segments(toks):
    segs, cur, i = [], Seg(False), 0
    while i < len(toks):
        t = toks[i]
        if t.kind == "op" and t.raw in SEPARATORS:
            if cur.words or cur.redirects or cur.heredocs or cur.subs:
                segs.append(cur)
            cur = Seg(t.raw in ("|", "|&"))
        elif t.kind == "op" and t.raw in REDIRECTS:
            if cur.words and re.fullmatch(r"\d+", cur.words[-1].raw) and t.adj:
                cur.words.pop()  # 2>/dev/null 的 2
            target = toks[i + 1] if i + 1 < len(toks) and toks[i + 1].kind == "word" else None
            cur.redirects.append((t.raw, target.value if target else ""))
            if target:
                cur.subs += target.subs
                i += 1
        elif t.kind == "heredoc":
            cur.heredocs.append(t.body or "")
        else:
            cur.words.append(t)
            cur.subs += t.subs
        i += 1
    if cur.words or cur.redirects or cur.heredocs or cur.subs:
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


def expand_braces(value, limit=50):
    """web{1..3} → web1 web2 web3；{a,b} → a b；web[1-3]（pdsh 寫法）→ web1 web2 web3。"""
    m = re.search(r"\{(-?\d+)\.\.(-?\d+)\}|\{([^{}]*,[^{}]*)\}|\[(\d+)-(\d+)\]", value)
    if not m:
        return [value]
    if m.group(1) is not None:
        a, b = int(m.group(1)), int(m.group(2))
        items = [str(x) for x in range(a, b + (1 if b >= a else -1), 1 if b >= a else -1)]
    elif m.group(3) is not None:
        items = m.group(3).split(",")
    else:
        items = [str(x) for x in range(int(m.group(4)), int(m.group(5)) + 1)]
    out = []
    for it in items[:limit]:
        out += expand_braces(value[:m.start()] + it + value[m.end():], limit)
    return out[:limit]


SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
DB_CODE_FLAGS = {"psql": "c", "mysql": "e", "mariadb": "e", "clickhouse-client": "q"}
DB_CODE_OPTS = {"psql": {"-c", "--command"}, "mysql": {"-e", "--execute"}, "mariadb": {"-e", "--execute"},
                "clickhouse-client": {"-q", "--query"}, "mongosh": {"--eval"}, "mongo": {"--eval"}}
DB_CLIENTS = set(DB_CODE_FLAGS) | {"sqlite3", "redis-cli", "mongosh", "mongo"}
KEYWORDS = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "case", "esac", "!", "{", "}",
            "time", "function", "in"}
WRAPPER_ARGS = {  # 包裝指令：哪些選項後面帶參數
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "--user", "--group"},
    "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "--class", "--classdata"},
    "nohup": set(), "stdbuf": set(), "command": set(), "exec": set(), "caffeinate": set(), "builtin": set(),
    "xargs": {"-I", "-i", "-n", "-P", "-d", "-E", "-L", "-s", "-a", "--max-args", "--max-procs", "--delimiter",
              "--arg-file", "--replace"},
    "watch": {"-n", "--interval", "-d"},
    "su": {"-c", "-s", "--command", "--shell", "-g", "-G"},
    "flock": {"-w", "-E", "--timeout", "-c", "--command"},
    "aws-vault": set(), "sops": set(),
}
SSH_ARG_FLAGS = set("bcDEeFIiJLlmOopQRSWw")
KUBE_FLAG_ARGS = {"-n", "--namespace", "--context", "--kubeconfig", "--cluster", "--user", "-s", "--server",
                  "--token", "--request-timeout", "-v", "--as", "--as-group", "--certificate-authority",
                  "--client-certificate", "--client-key", "--tls-server-name", "--cache-dir", "-c", "--container",
                  "-l", "--selector", "-o", "--output", "-f", "--filename", "-k", "--kustomize",
                  "--field-selector", "--type", "--image", "--replicas", "--from-literal", "--from-file",
                  "--timeout", "--to-revision", "--min", "--max", "--port", "--target-port", "--name", "-p",
                  "--patch", "--overrides", "--since", "--tail", "--sort-by", "-L", "--label-columns", "--cpu-percent"}
KUBE_FLAG_ARGS.discard("-p")
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
                    "package_facts", "fetch", "listen_ports_facts", "mount_facts"}
ANSIBLE_CHECK = {"--check", "-C", "--syntax-check", "--list-hosts", "--list-tasks", "--list-tags"}
SCP_ARGS = {"-P", "-i", "-o", "-F", "-c", "-l", "-S", "-J", "-D"}
RSYNC_ARGS = {"-e", "--rsh", "--exclude", "--include", "--filter", "-f", "--files-from", "--exclude-from",
              "--include-from", "--password-file", "--port", "--chmod", "--chown", "--log-file", "--backup-dir",
              "--suffix", "--compare-dest", "--link-dest", "--copy-dest", "-T", "--temp-dir", "-M",
              "--remote-option"}
DOCKER_GLOBAL_ARGS = {"-H", "--host", "-c", "--context", "--config", "-l", "--log-level"}
DOCKER_COMPOSE_ARGS = {"-f", "--file", "-p", "--project-name", "--env-file", "--profile", "--project-directory",
                       "--ansi", "--progress"}
DOCKER_EXEC_ARGS = {"-e", "--env", "-u", "--user", "-w", "--workdir", "--env-file", "--detach-keys"}
DOCKER_MUTATING = {"restart", "stop", "start", "kill", "rm", "rmi", "run", "update", "pause", "unpause", "create",
                   "prune", "pull", "load", "tag", "push", "rename", "up", "down"}
SAFE_WRITE = re.compile(r"^(/tmp/|/var/tmp/|/dev/(null|stdout|stderr|fd/|tty))")
SAFE_DEVICE = re.compile(r"^/dev/(null|zero|stdout|stderr|tty|u?random|fd/)")
KUBECONFIG_FILE = re.compile(r"(^|/)\.kube/config$")
POWER = {"reboot", "shutdown", "poweroff", "halt"}
UNKNOWN = object()  # 看不到內容的 stdin


def short_flags(a):
    """-avn → {'a','v','n'}；長選項或非選項 → 空集合。"""
    return set(a[1:]) if re.fullmatch(r"-[A-Za-z]+", a) else set()


def positionals(args, takes, clusters=True):
    """去掉選項與選項的參數，回傳位置參數。clusters：-nu 這種合併短選項的最後一個字母可以帶參數（getopt 寫法）；
    kubectl、helm、docker 用 pflag，-oyaml 是把值直接接在後面，要設成 False。"""
    out, k = [], 0
    letters = {t[1] for t in takes if re.fullmatch(r"-[A-Za-z]", t)} if clusters else set()
    while k < len(args):
        a = args[k]
        if a == "--":
            out += args[k + 1:]
            break
        if a.startswith("-") and a != "-":
            k += 2 if (a in takes or (len(a) > 2 and not a.startswith("--") and a[-1] in letters)) else 1
            continue
        out.append(a)
        k += 1
    return out


def sql_effect(text):
    """回傳 (會寫入, 不可逆)。依每個 SQL 敘述的第一個字判斷；也認得 mongo 的寫法。"""
    text = re.sub(r"--[^\n]*|/\*.*?\*/", " ", text, flags=re.S)
    mutating = irreversible = False
    for stmt in text.split(";"):
        words = stmt.strip().split()
        if not words:
            continue
        first = words[0].lower().lstrip("(")
        if first in ("insert", "update", "delete", "drop", "truncate", "alter", "create", "grant", "revoke",
                     "replace", "merge", "rename", "upsert") or (first == "copy" and re.search(r"\bfrom\b", stmt, re.I)):
            mutating = True
        if re.match(r"\s*(drop\s+(database|table|schema|index|view)|truncate\b|delete\s+from"
                    r"|alter\s+table\s+\S+\s+drop)\b", stmt, re.I):
            irreversible = True
    if re.search(r"\.(deleteMany|deleteOne|remove|drop|dropDatabase|findOneAndDelete)\s*\(", text):
        mutating = irreversible = True
    elif re.search(r"\.(insert\w*|update\w*|replace\w*|createIndex|bulkWrite|renameCollection)\s*\(", text):
        mutating = True
    return mutating, irreversible


def redis_effect(text):
    mutating = irreversible = False
    for line in text.splitlines():
        w = line.strip().split()
        if not w:
            continue
        c = w[0].upper()
        if c in ("DEL", "UNLINK", "FLUSHALL", "FLUSHDB"):
            mutating = irreversible = True
        elif c in ("SET", "HSET", "MSET", "LPUSH", "RPUSH", "SADD", "ZADD", "EXPIRE", "INCR", "DECR", "HDEL", "LPOP",
                   "RPOP", "SREM", "ZREM", "RENAME", "PERSIST", "SETEX", "APPEND") or w[:2] == ["CONFIG", "SET"]:
            mutating = True
    return mutating, irreversible


# ---------------------------------------------------------------- 分析

class Result:
    def __init__(self):
        self.deny, self.fix, self.irreversible, self.prod, self.unknown = [], [], [], [], []


class Analyzer:
    def __init__(self):
        self.prod = prod_pattern()
        self.vars = {}
        self.files = {}         # 同一個指令裡剛寫好的檔案：路徑 → 內容
        self.cwd = []           # cd 進去的目錄
        self.tf_workspace = []  # terraform workspace select 的名稱
        self.placeholders = {"{}"}
        self.r = Result()
        self.base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    # ---- 變數與目標

    def collect_vars(self, segs):
        for seg in segs:
            w = [t.value for t in seg.words]
            if len(w) >= 3 and w[0] == "for" and w[2] == "in":
                items = [x for v in w[3:] for x in expand_braces(v)]
                self.vars[w[1]] = items if items and not seg.subs and not any("$" in x for x in items) else None
            for t in seg.words:
                if t.value in ("export", "declare", "local", "readonly"):
                    continue
                m = re.fullmatch(r"([A-Za-z_]\w*)=(.*)", t.value, re.S)
                if not m:
                    break
                val = m.group(2)
                self.vars[m.group(1)] = expand_braces(val) if val and "$" not in val and not t.subs else None

    def resolve(self, value):
        if value is None:
            return None
        out = []
        for v in expand_braces(value):
            if any(p in v for p in self.placeholders):
                return None
            names = re.findall(r"\$\{?(\w+)\}?", v)
            if not names:
                out.append(v)
                continue
            options = []
            for name in names:
                vals = self.vars.get(name)
                if not vals:
                    return None
                options.append(vals)
            for combo in itertools.islice(itertools.product(*options), 50):
                x = v
                for name, val in zip(names, combo):
                    x = re.sub(r"\$\{?" + name + r"\}?", val, x, count=1)
                out.append(x)
        return out

    def hit(self, values, label, generic=False):
        if values is None:
            self.r.unknown.append(label)
            return
        for v in values:
            m = self.prod.search(v) or (generic and GENERIC_PROD.search(v))
            if m:
                self.r.prod.append(m.group(0))
                return

    def remote_change(self, where, why):
        if where[0] == "remote":
            self.hit(where[1], f"判斷不出主機的遠端變更（{why}）")
        elif where[0] == "pod":
            self.hit(where[1], f"判斷不出 context 的 pod 內變更（{why}）")

    def write_change(self, where, why, local_targets=None, generic=False):
        """local：看參數裡的目標名稱；遠端或 pod：看所在主機或 context。"""
        if where[0] == "local":
            if local_targets is not None:
                self.hit(local_targets, why, generic)
        else:
            self.remote_change(where, why)

    def read_script(self, path):
        if path is None:
            return None
        for key in (path, os.path.normpath(path)):
            if key in self.files:
                return self.files[key]
        for base in (os.getcwd(), self.base):
            p = os.path.expanduser(path if os.path.isabs(path) else os.path.join(base, path))
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    return f.read(200_000)
            except OSError:
                continue
        return None

    # ---- 走訪

    def unit(self, text, where=("local",), depth=0, stdin=None):
        if depth > 6 or not text:
            return
        segs = segments(lex(text))
        self.collect_vars(segs)
        for seg in segs:
            self.segment(seg, where, depth, stdin)

    def seg_stdin(self, seg, inherited):
        if seg.heredocs:
            return "\n".join(seg.heredocs)
        for op, val in seg.redirects:
            if op == "<<<":
                return val
            if op == "<":
                body = self.read_script(val)
                return UNKNOWN if body is None else body
        if seg.pipe_in:
            return UNKNOWN
        return inherited

    def segment(self, seg, where, depth, inherited=None):
        for sub in seg.subs:
            self.unit(sub, where, depth + 1)
        values = [t.value for t in seg.words]
        if values[:1] == ["for"]:
            return
        if values[:1] in (["cd"], ["pushd"]):
            self.cwd.append(values[1] if len(values) > 1 else "~")
            return
        i, wrappers, code = command_index(values, self.placeholders)
        if code is not None:
            self.unit(code, where, depth + 1)
        cmd = os.path.basename(values[i]) if i < len(values) else ""
        if cmd.startswith("$"):  # 指令放在變數裡
            vals = self.resolve(values[i])
            for v in vals or []:
                self.unit(" ".join([v] + values[i + 1:]), where, depth + 1, inherited)
            return
        args = values[i + 1:]
        prefix = values[:i]
        stdin = self.seg_stdin(seg, inherited)
        self.record_files(seg, cmd, args, stdin)
        self.redirect_checks(seg, cmd, where)
        if not cmd:
            return
        self.catastrophic(cmd, args)
        self.global_state(cmd, args, seg)
        self.irreversible(cmd, args, wrappers)

        if cmd in SHELLS:
            self.shell(args, where, depth, stdin)
        elif cmd in ("source", ".") or (values[i].startswith(("./", "/")) and values[i].endswith(".sh")):
            body = self.read_script(args[0] if cmd in ("source", ".") and args else values[i])
            if body is not None:
                self.unit(body, where, depth + 1)
        elif cmd == "eval":
            self.unit(" ".join(args), where, depth + 1, stdin)
        elif cmd == "find":
            for k, a in enumerate(args):
                if a in ("-exec", "-execdir", "-ok", "-okdir"):
                    end = next((j for j in range(k + 1, len(args)) if args[j] in (";", "+", "\\;")), len(args))
                    self.unit(shlex.join(args[k + 1:end]), where, depth + 1)
        elif cmd in DB_CLIENTS:
            self.db(cmd, args, seg, where, stdin)
        elif cmd == "kubectl":
            self.kubectl(args, where, depth, stdin)
        elif cmd == "helm":
            self.helm(args, where)
        elif cmd in ("terraform", "tofu", "terragrunt"):
            self.terraform(args, prefix)
        elif cmd == "helmfile":
            self.helmfile(args)
        elif cmd == "eksctl":
            pos = positionals(args, {"-f", "--config-file", "--region", "-r", "--profile", "--name", "-n"},
                              clusters=False)
            if pos[:1] in (["delete"], ["drain"]):
                self.r.irreversible.append(f"eksctl {pos[0]}")
            if pos[:1] in (["create"], ["delete"], ["upgrade"], ["scale"], ["drain"], ["set"], ["unset"]):
                self.hit([" ".join(args)], f"eksctl {pos[0]}")
        elif cmd == "ansible-playbook":
            if not ANSIBLE_CHECK & set(args):
                self.hit([" ".join(args + self.cwd)], "ansible-playbook", generic=True)
        elif cmd == "ansible":
            self.ansible(args, depth)
        elif cmd in ("pdsh", "clush"):
            self.pdsh(args, depth)
        elif cmd == "ssh":
            self.ssh(args, depth, stdin)
        elif cmd in ("scp", "rsync"):
            self.transfer(cmd, args, where)
        elif cmd in ("docker", "podman", "nerdctl"):
            self.docker(cmd, args, where, depth, stdin)
        elif cmd == "docker-compose":
            self.docker("docker", ["compose"] + args, where, depth, stdin)
        elif where[0] != "local":
            why = remote_mutation(cmd, args, stdin)
            if why:
                self.remote_change(where, why)

    def record_files(self, seg, cmd, args, stdin):
        """記下這個指令裡寫出的檔案內容（之後若被執行，才看得到內容）。"""
        content = None
        if cmd in ("cat", "tee") and isinstance(stdin, str):
            content = stdin
        elif cmd in ("echo", "printf"):
            content = " ".join(a for a in args if not re.fullmatch(r"-[neE]+", a)).replace("\\n", "\n")
        if content is None:
            return
        targets = [t for op, t in seg.redirects if op in (">", ">>", ">|", "&>", "&>>")]
        if cmd == "tee":
            targets += [a for a in args if not a.startswith("-")]
        appending = {t for op, t in seg.redirects if op in (">>", "&>>")} | ({a for a in args if not a.startswith("-")}
                                                                           if cmd == "tee" and "-a" in args else set())
        for t in targets:
            body = self.files.get(t, "") + "\n" + content if t in appending else content
            self.files[t] = self.files[os.path.normpath(t)] = body

    def redirect_checks(self, seg, cmd, where):
        for op, target in seg.redirects:
            if op not in (">", ">>", "&>", "&>>", ">|") or not target or target.startswith("&"):
                continue
            if KUBECONFIG_FILE.search(target) or (target.startswith("$KUBECONFIG")):
                self.r.fix.append("不要覆寫共用的 ~/.kube/config（其他 session 也在用）；寫到獨立檔案，再用 --kubeconfig 指定")
            if op in (">", ">|", "&>") and not SAFE_WRITE.match(target) and cmd in ("", ":", "true"):
                self.r.irreversible.append("清空檔案內容")
            if where[0] != "local" and not SAFE_WRITE.match(target):
                self.remote_change(where, "寫入檔案")

    # ---- 規則

    def catastrophic(self, cmd, args):
        if cmd == "rm" and any("r" in short_flags(a) or "R" in short_flags(a) or a == "--recursive" for a in args):
            if any(a in ("/", "/*", "~", "~/", "$HOME", "$HOME/", "/home", "/root") for a in args):
                self.r.deny.append("rm -r 目標是根目錄或家目錄")
        if "--no-preserve-root" in args:
            self.r.deny.append("--no-preserve-root")
        dry = any(a in ("-n", "-N", "--no-act", "--dry-run") for a in args)
        if (re.fullmatch(r"mkfs(\.\w+)?|mke2fs|mkswap|mkdosfs|mkntfs|mkexfatfs", cmd) or cmd in ("wipefs", "blkdiscard")) \
                and not dry:
            self.r.deny.append("格式化或抹除區塊裝置")
        if cmd == "sgdisk" and any(a in ("-Z", "--zap-all", "-o", "--clear") for a in args):
            self.r.deny.append("清除分割表")
        if cmd == "dd" and any(a.startswith("of=/dev/") and not SAFE_DEVICE.match(a[3:]) for a in args):
            self.r.deny.append("dd 寫入區塊裝置")

    def global_state(self, cmd, args, seg):
        own_kubeconfig = any(a.startswith("--kubeconfig") for a in args) or any(
            t.value.startswith("KUBECONFIG=") for t in seg.words)
        pos = [a for a in args if not a.startswith("-")]
        why = None
        if cmd == "kubectl" and pos[:1] == ["config"] and len(pos) > 1 and pos[1] in (
                "use-context", "use", "set-context", "delete-context", "rename-context", "set-cluster",
                "delete-cluster", "set-credentials", "delete-user", "set", "unset") and not own_kubeconfig:
            why = "不要修改共用的 kubeconfig（其他 session 也在用）"
        elif cmd in ("kubectx", "kubens") and any(not a.startswith("-") or a == "-" for a in args):
            why = "不要切換全域 context／namespace（其他 session 也在用）"
        elif cmd == "gcloud" and (pos[:2] in (["config", "set"], ["config", "unset"])
                                  or pos[:3] == ["config", "configurations", "activate"]):
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
        elif cmd in ("cp", "mv", "ln", "install", "tee") and any(KUBECONFIG_FILE.search(a) for a in pos):
            why = "不要覆寫共用的 ~/.kube/config（其他 session 也在用）；寫到獨立檔案，再用 --kubeconfig 指定"
        if why:
            self.r.fix.append(why)

    def irreversible(self, cmd, args, wrappers):
        pos = [a for a in args if not a.startswith("-")]
        if cmd == "rm" and any("r" in short_flags(a) or "R" in short_flags(a) or a == "--recursive" for a in args):
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
        if cmd == "aws" and (any(re.match(r"(delete|terminate)-", a) for a in pos)
                             or pos[:2] in (["s3", "rm"], ["s3", "rb"])):
            self.r.irreversible.append("AWS 刪除／終止資源")
        if cmd in ("gcloud", "az") and "delete" in pos:
            self.r.irreversible.append("雲端刪除資源")
        if cmd == "journalctl" and any(a.startswith("--vacuum") for a in args):
            self.r.irreversible.append("清除系統日誌")

    def shell(self, args, where, depth, stdin):
        k, code, reads_stdin, script = 0, None, False, None
        while k < len(args):
            a = args[k]
            flags = short_flags(a)
            if a == "--":
                break
            if "n" in flags:  # bash -n：只檢查語法
                return
            if a == "-c" or "c" in flags:
                code = args[k + 1] if k + 1 < len(args) else ""
                break
            if "s" in flags:
                reads_stdin = True
            if a in ("-o", "+o", "-O", "+O") or (flags and a.endswith("o")):
                k += 2
                continue
            if not a.startswith(("-", "+")):
                script = a
                break
            k += 1
        if code is not None:
            self.unit(code, where, depth + 1)
        elif script and not reads_stdin:
            body = self.read_script(script)
            if body is not None:
                self.unit(body, where, depth + 1)
            elif where[0] != "local":
                self.remote_change(where, "看不到要執行的腳本內容")
        elif isinstance(stdin, str):
            self.unit(stdin, where, depth + 1)
        elif stdin is UNKNOWN:
            self.remote_change(where, "看不到要執行的腳本內容")

    def db(self, cmd, args, seg, where, stdin):
        code, k, flag = [], 0, DB_CODE_FLAGS.get(cmd)
        files = []
        while k < len(args):
            a = args[k]
            if a in DB_CODE_OPTS.get(cmd, ()) or (flag and len(a) > 2 and short_flags(a) and a.endswith(flag)):
                if k + 1 < len(args):
                    code.append(args[k + 1])
                k += 2
                continue
            if a in ("-f", "--file") and k + 1 < len(args):
                files.append(args[k + 1])
                k += 2
                continue
            m = re.match(r"--(command|execute|eval|query|file)=(.*)", a, re.S)
            if m:
                (files if m.group(1) == "file" else code).append(m.group(2))
            k += 1
        if cmd == "sqlite3":
            code += positionals(args, {"-cmd", "-init", "-separator", "-newline", "-nullvalue"})[1:]
        if cmd == "redis-cli":
            code.append(" ".join(a for a in args if not a.startswith("-")))
        unknown = False
        for f in files:
            body = self.read_script(f)
            if body is None:
                unknown = True
            else:
                code.append(body)
        if not code:
            if isinstance(stdin, str):
                code.append(stdin)
            elif stdin is UNKNOWN:
                unknown = True
        text = "\n".join(code)
        mutating, irreversible = redis_effect(text) if cmd == "redis-cli" else sql_effect(text)
        if irreversible:
            self.r.irreversible.append("刪除資料庫資料")
        if mutating or unknown:
            self.write_change(where, f"{cmd} 寫入" if mutating else f"看不到 {cmd} 要執行的內容", [" ".join(args)])

    def kubectl(self, args, where, depth, stdin):
        ctx, has_ctx = None, False
        before = args[:args.index("--")] if "--" in args else args
        for j, a in enumerate(before):
            if a == "--context" and j + 1 < len(before):
                ctx, has_ctx = before[j + 1], True
            elif a.startswith("--context="):
                ctx, has_ctx = a.split("=", 1)[1], True
        pos = positionals(before, KUBE_FLAG_ARGS, clusters=False)
        if not pos or any(a in ("-h", "--help") for a in before):
            return
        verb, rest = pos[0], pos[1:]
        local = verb in KUBE_LOCAL or (verb == "version" and "--client" in before)
        if not local and not has_ctx and os.environ.get("KIT_REQUIRE_CONTEXT", "1") != "0" and where[0] != "pod":
            self.r.fix.append("missing-context:kubectl " + " ".join(args)[:60])
        targets = self.resolve(ctx) if ctx else None
        if verb in ("exec", "attach") and "--" in args:
            inner = args[args.index("--") + 1:]
            interactive = any(a in ("-i", "--stdin") or "i" in short_flags(a) for a in before)
            self.unit(shlex.join(inner), ("pod", targets), depth + 1, stdin if interactive else None)
            return
        dry = any(a.startswith("--dry-run") and a != "--dry-run=none" for a in before)
        if verb not in KUBE_MUTATING or dry or local:
            return
        if verb == "rollout" and rest[:1] not in (["restart"], ["undo"], ["pause"], ["resume"]):
            return
        if verb in ("set", "label", "annotate") and "--list" in before:
            return
        if verb == "apply" and rest[:1] == ["view-last-applied"]:
            return
        if verb == "cp" and not (rest and ":" in rest[-1]):
            return
        if verb in ("delete", "drain"):
            self.r.irreversible.append(f"kubectl {verb}")
        if verb == "apply" and any(a.startswith("--prune") for a in before):
            self.r.irreversible.append("kubectl apply --prune")
        if where[0] == "local":
            self.hit(targets, f"判斷不出 kubectl 的 context（{ctx}）")
        else:
            self.remote_change(where, f"kubectl {verb}")

    def helm(self, args, where):
        has_ctx, ctx = False, None
        for j, a in enumerate(args):
            if a == "--kube-context" and j + 1 < len(args):
                ctx, has_ctx = args[j + 1], True
            elif a.startswith("--kube-context="):
                ctx, has_ctx = a.split("=", 1)[1], True
        pos = positionals(args, HELM_GLOBAL_ARGS, clusters=False)
        sub = pos[0] if pos else None
        if sub in HELM_CLUSTER and not has_ctx and os.environ.get("KIT_REQUIRE_CONTEXT", "1") != "0":
            self.r.fix.append("missing-context:helm " + " ".join(args)[:60])
        if sub in HELM_MUTATING and not any(a.startswith("--dry-run") for a in args):
            if sub in ("uninstall", "delete"):
                self.r.irreversible.append("helm 移除 release")
            if where[0] == "local":
                self.hit(self.resolve(ctx) if ctx else None, f"判斷不出 helm 的 context（{ctx}）")
            else:
                self.remote_change(where, f"helm {sub}")

    def terraform(self, args, prefix):
        pos = [a for a in args if not a.startswith("-")]
        if pos[:1] == ["run-all"]:
            pos = pos[1:]
        sub = pos[0] if pos else ""
        if pos[:2] in (["workspace", "select"], ["workspace", "new"]) and len(pos) > 2:
            self.tf_workspace.append(pos[2])
            return
        destroy = sub == "destroy" or (sub == "apply" and "-destroy" in args) or pos[:2] == ["state", "rm"] \
            or pos[:2] == ["workspace", "delete"]
        if destroy:
            self.r.irreversible.append("terraform 刪除資源／state")
        if destroy or sub in ("apply", "import", "taint", "untaint") or pos[:2] in (
                ["state", "mv"], ["state", "push"], ["state", "replace-provider"]):
            where_text = args + prefix + self.cwd + self.tf_workspace + [os.environ.get("TF_WORKSPACE", "")]
            self.hit([" ".join(where_text)], "terraform", generic=True)

    def helmfile(self, args):
        pos = positionals(args, {"-e", "--environment", "-f", "--file", "-l", "--selector", "--kube-context",
                                 "-n", "--namespace"}, clusters=False)
        sub = pos[0] if pos else ""
        if sub == "destroy" or sub == "delete":
            self.r.irreversible.append("helmfile 移除 release")
        if sub in ("apply", "sync", "deploy", "destroy", "delete"):
            self.hit([" ".join(args + self.cwd)], "helmfile", generic=True)

    def ansible(self, args, depth):
        pattern, module, margs, limit, inline, k = None, "command", "", None, [], 0
        while k < len(args):
            a = args[k]
            if a in ANSIBLE_ARGS and k + 1 < len(args):
                val = args[k + 1]
                if a in ("-m", "--module-name"):
                    module = val
                elif a in ("-a", "--args"):
                    margs = val
                elif a in ("-l", "--limit"):
                    limit = val
                elif a in ("-i", "--inventory") and "," in val:
                    inline += [h for h in val.split(",") if h]
                k += 2
                continue
            if not a.startswith("-") and pattern is None:
                pattern = a
            k += 1
        hosts = list(inline)
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
        elif short not in ANSIBLE_READONLY:
            self.hit(hosts, f"ansible -m {module}", generic=True)

    def pdsh(self, args, depth):
        hosts, k, rest = [], 0, []
        while k < len(args):
            a = args[k]
            if a in ("-w", "-g", "-x", "-l", "-R", "-f", "-t", "-u") and k + 1 < len(args):
                if a == "-w":
                    hosts += [x for h in args[k + 1].split(",") for x in expand_braces(h)]
                k += 2
                continue
            if a.startswith("-"):
                k += 1
                continue
            rest = args[k:]
            break
        self.unit(" ".join(rest), ("remote", hosts or None), depth + 1)

    def ssh(self, args, depth, stdin):
        k = 0
        while k < len(args) and args[k].startswith("-") and len(args[k]) > 1:
            k += 2 if (len(args[k]) == 2 and args[k][1] in SSH_ARG_FLAGS) else 1
        if k >= len(args):
            return
        host_expr = args[k].split("@")[-1]
        k += 1
        while k < len(args) and re.fullmatch(r"-[A-Za-z]", args[k]):  # ssh host -o X '<cmd>'
            k += 2 if args[k][1] in SSH_ARG_FLAGS else 1
        remote = args[k:]
        if remote[:1] == ["--"]:
            remote = remote[1:]
        where = ("remote", self.resolve(host_expr))
        if remote:
            self.unit(" ".join(remote), where, depth + 1, stdin)
        elif isinstance(stdin, str):
            self.unit(stdin, where, depth + 1)
        elif stdin is UNKNOWN:
            self.remote_change(where, "看不到要執行的腳本內容")

    def transfer(self, cmd, args, where):
        dry = cmd == "rsync" and any("n" in short_flags(a) or a == "--dry-run" for a in args)
        pos = positionals(args, SCP_ARGS if cmd == "scp" else RSYNC_ARGS)
        if len(pos) < 2 or dry:
            return
        dest = pos[-1]
        m = re.match(r"^rsync://(?:[^@/]+@)?([^/:]+)", dest) or re.match(r"^(?:[^@/:]+@)?([^/:]+)::?", dest)
        if m:
            self.hit(self.resolve(m.group(1)), f"判斷不出 {cmd} 的目標主機（{m.group(1)}）")
        elif where[0] != "local" and not SAFE_WRITE.match(dest):
            self.remote_change(where, f"{cmd} 寫入")

    def docker(self, cmd, args, where, depth, stdin):
        pos = positionals(args, DOCKER_GLOBAL_ARGS, clusters=False)
        if not pos:
            return
        verb = pos[0]
        if verb == "compose":
            sub = positionals(args[args.index("compose") + 1:], DOCKER_COMPOSE_ARGS, clusters=False)
            verb = sub[0] if sub else ""
            if verb in ("down",) and any(a in ("-v", "--volumes") for a in args):
                self.r.irreversible.append("docker compose down -v 刪除資料")
        elif verb in ("container", "image", "volume", "network", "system", "builder") and len(pos) > 1:
            if pos[1] in ("prune", "rm") and verb in ("volume", "system"):
                self.r.irreversible.append("docker 刪除資料")
            verb = pos[1]
        if verb == "exec":
            rest = args[args.index("exec") + 1:]
            k = 0
            while k < len(rest) and rest[k].startswith("-"):
                k += 2 if rest[k] in DOCKER_EXEC_ARGS else 1
            inner = rest[k + 1:]
            interactive = any(a in ("-i", "--interactive") or "i" in short_flags(a) for a in rest[:k])
            self.unit(shlex.join(inner), where, depth + 1, stdin if interactive else None)
            return
        if verb in DOCKER_MUTATING and where[0] != "local":
            self.remote_change(where, f"{cmd} {verb}")


def command_index(values, placeholders):
    """跳過關鍵字、變數設定、包裝指令（sudo、env、timeout、xargs…），
    回傳 (指令名稱的位置, 包裝指令, 包裝指令帶的程式碼字串或 None)。"""
    i, wrappers, code = 0, [], None
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
        letters = {t[1] for t in takes if re.fullmatch(r"-[A-Za-z]", t)}
        if name == "aws-vault":
            j = values.index("--", i) if "--" in values[i:] else i + 2
            i = j + 1 if j < len(values) and values[j] == "--" else j
            continue
        if name == "sops":
            i += 2  # exec-env <file>
            continue
        if name == "su":  # su [-] [user] -c '<cmd>'：-c 可以在任何位置
            for j in range(i, len(values)):
                if values[j] in ("-c", "--command") or (short_flags(values[j]) and values[j].endswith("c")):
                    return len(values), wrappers, values[j + 1] if j + 1 < len(values) else ""
            return len(values), wrappers, None
        while i < len(values) and values[i].startswith("-") and values[i] != "-":
            a = values[i]
            if name in ("su", "flock") and (a in ("-c", "--command") or (short_flags(a) and a.endswith("c"))):
                code = values[i + 1] if i + 1 < len(values) else ""
                return len(values), wrappers, code
            if name == "xargs" and (a in ("-I", "-i", "--replace") and i + 1 < len(values)):
                placeholders.add(values[i + 1])
            elif name == "xargs" and re.fullmatch(r"-I.+", a):
                placeholders.add(a[2:])
            takes_arg = a in takes or (len(a) > 2 and not a.startswith("--") and short_flags(a) and a[-1] in letters)
            i += 2 if takes_arg else 1
        if name == "timeout" and i < len(values):
            i += 1  # 時間長度
        if name == "su":
            return len(values), wrappers, None
        if name == "flock" and i < len(values):
            i += 1  # 鎖檔
            if i < len(values) and values[i] in ("-c", "--command"):
                return len(values), wrappers, values[i + 1] if i + 1 < len(values) else ""
        if name == "watch":
            rest = values[i:]
            return len(values), wrappers, rest[0] if len(rest) == 1 else " ".join(rest)
    return i, wrappers, code


def remote_mutation(cmd, args, stdin=None):
    """在遠端主機或 pod 裡會造成變更的指令；回傳原因或 None。"""
    pos = [a for a in args if not a.startswith("-")]
    verb = pos[0] if pos else ""
    if cmd == "systemctl" and verb in ("start", "stop", "restart", "reload", "try-restart", "reload-or-restart",
                                       "try-reload-or-restart", "enable", "disable", "mask", "unmask",
                                       "daemon-reload", "kill", "isolate", "set-property", "edit", "reboot",
                                       "poweroff", "halt", "kexec", "reset-failed", "link", "revert"):
        return f"systemctl {verb}"
    if cmd == "service" and len(pos) >= 2 and pos[1] in ("start", "stop", "restart", "reload", "force-reload"):
        return f"service {pos[1]}"
    if cmd in ("nginx", "openresty") and "-s" in args:
        return "nginx -s"
    if cmd in ("apachectl", "apache2ctl", "httpd") and verb in ("restart", "graceful", "stop", "start",
                                                                "graceful-stop"):
        return f"{cmd} {verb}"
    if cmd == "sed" and any(("i" in short_flags(a) and not a.startswith("--")) or a.startswith("--in-place")
                            for a in args):
        return "sed -i"
    if cmd in ("perl", "ruby") and any(re.fullmatch(r"-\w*i\S*", a) for a in args):
        return f"{cmd} -i"
    if cmd == "tee" and any(not a.startswith("-") and not SAFE_WRITE.match(a) for a in args):
        return "tee 寫入檔案"
    if cmd in {"rm", "rmdir", "unlink", "truncate", "chmod", "chown", "chgrp", "ln", "kill", "pkill", "killall",
               "useradd", "userdel", "usermod", "groupadd", "passwd", "chpasswd", "swapoff", "umount",
               "modprobe", "rmmod", "insmod"} | POWER:
        return cmd
    if cmd == "mount" and (pos or set(args) & {"-a", "--all"} or any("remount" in a for a in args)):
        return "mount"
    if cmd == "swapon" and not set(args) & {"--show", "-s", "--summary"} and args:
        return "swapon"
    if cmd in ("cp", "mv", "install", "mkdir", "touch") and not (pos and SAFE_WRITE.match(pos[-1])):
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
    if cmd == "crontab":
        p = positionals(args, {"-u"})
        if set(args) & {"-r", "-e", "-i"} or p or "-" in args:
            return "crontab"
    if cmd in ("iptables", "ip6tables") and set(args) & {"-A", "-D", "-I", "-R", "-F", "-X", "-P", "-N",
                                                         "--append", "--delete", "--insert", "--flush"}:
        return cmd
    if cmd == "firewall-cmd" and any(re.match(r"--(add|remove|set|new|delete|change|reload|complete-reload"
                                              r"|runtime-to-permanent|lockdown-on|panic-on)", a) for a in args):
        return cmd
    if cmd == "ufw" and verb in ("allow", "deny", "reject", "limit", "delete", "insert", "enable", "disable",
                                 "reset", "reload", "route", "default"):
        return cmd
    if cmd == "sysctl" and ("-w" in args or "-p" in args or any("=" in a for a in pos)):
        return "sysctl"
    if cmd in ("hostnamectl", "timedatectl", "localectl") and verb.startswith("set"):
        return cmd
    if cmd in ("git",) and verb in ("pull", "checkout", "reset", "clean", "merge", "rebase", "stash"):
        return f"git {verb}"
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
