#!/usr/bin/env python3
"""模擬的 kubectl / ssh / helm…，讓評估案例可以重現、不碰真的環境。

用法（由 scaffold 建立的 ./bin/<tool> 包裝呼叫）：fakecli.py <tool> [args...]

資料都在同一個目錄（工作區的 .sim/）：
  sim.json    案例定義：contexts、初始 state、rules
  state.json  目前狀態（第一次執行時從 sim.json 的 state 複製）
  calls.log   每次呼叫一行：<tool>\t<scope>\t<explicit|implicit|->\t<args>

rules 依序比對，第一個符合的生效：
  {"tool": "kubectl", "ctx": "regex", "host": "regex", "match": "regex",
   "when": {"key": value}, "set": {"key": value}, "out": "...", "err": "...", "rc": 0}
kubectl 會比對參數字串；ssh 會把遠端指令依 ; && 換行切開，逐段比對。
"""
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "sim.json")
STATE = os.path.join(HERE, "state.json")
LOG = os.path.join(HERE, "calls.log")


def load():
    with open(SIM, encoding="utf-8") as f:
        sim = json.load(f)
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = dict(sim.get("state", {}))
        state.setdefault("current_context", sim.get("current_context", ""))
    return sim, state


def save(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False, sort_keys=True)


def log(tool, scope, mode, args):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{tool}\t{scope}\t{mode}\t{' '.join(args)}\n")


def find_rule(sim, state, tool, text, ctx=None, host=None):
    for rule in sim.get("rules", []):
        if rule.get("tool") != tool:
            continue
        if "ctx" in rule and not re.search(rule["ctx"], ctx or ""):
            continue
        if "host" in rule and not re.search(rule["host"], host or ""):
            continue
        if not re.search(rule.get("match", ""), text):
            continue
        if any(state.get(k) != v for k, v in rule.get("when", {}).items()):
            continue
        return rule
    return None


def apply(rule, state):
    state.update(rule.get("set", {}))
    return rule.get("out", ""), rule.get("err", ""), int(rule.get("rc", 0))


def emit(out, err, rc):
    if out:
        sys.stdout.write(out if out.endswith("\n") else out + "\n")
    if err:
        sys.stderr.write(err if err.endswith("\n") else err + "\n")
    return rc


def kubectl(sim, state, args):
    ctx, explicit, rest = state.get("current_context", ""), False, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--context" and i + 1 < len(args):
            ctx, explicit = args[i + 1], True
            i += 2
            continue
        if a.startswith("--context="):
            ctx, explicit = a.split("=", 1)[1], True
        else:
            rest.append(a)
        i += 1
    text = " ".join(rest)
    # config 子指令讀寫的是 kubeconfig 本身，不算「對叢集下指令」，不標 explicit/implicit
    mode = "-" if re.match(r"config\b", text) else ("explicit" if explicit else "implicit")
    log("kubectl", f"ctx={ctx}", mode, args)
    contexts = sim.get("contexts", [])
    if re.match(r"config\s+current-context", text):
        return emit(state.get("current_context", ""), "", 0)
    if re.match(r"config\s+get-contexts", text):
        rows = ["CURRENT   NAME"] + [f"{'*' if c == state.get('current_context') else ' ':<9} {c}" for c in contexts]
        return emit("\n".join(rows), "", 0)
    m = re.match(r"config\s+use-context\s+(\S+)", text)
    if m:
        if m.group(1) not in contexts:
            return emit("", f'error: no context exists with the name: "{m.group(1)}"', 1)
        state["current_context"] = m.group(1)
        save(state)
        return emit(f'Switched to context "{m.group(1)}".', "", 0)
    if contexts and ctx not in contexts:
        return emit("", f'error: context "{ctx}" does not exist', 1)
    rule = find_rule(sim, state, "kubectl", text, ctx=ctx)
    if not rule:
        return emit("", "Error from server (NotFound): the server could not find the requested resource", 1)
    out = apply(rule, state)
    save(state)
    return emit(*out)


def ssh(sim, state, args):
    i, host = 0, None
    takes_value = set("bcDEeFIiJLlmOoPpRSWw")
    while i < len(args):
        a = args[i]
        if a.startswith("-") and len(a) >= 2:
            if a[1] in takes_value and len(a) == 2:
                i += 2
                continue
            i += 1
            continue
        host = a.split("@", 1)[-1]
        i += 1
        break
    remote = " ".join(args[i:])
    log("ssh", f"host={host or '-'}", "-", args)
    if not host:
        return emit("", "usage: ssh [options] destination [command]", 255)
    hosts = sim.get("hosts", [])
    if hosts and host not in hosts:
        return emit("", f"ssh: Could not resolve hostname {host}: Name or service not known", 255)
    if not remote.strip():
        return emit("", "Pseudo-terminal will not be allocated; interactive shells are not available here.", 1)
    try:
        remote = " ".join(shlex.split(remote)) if len(args) - i == 1 else remote
    except ValueError:
        pass
    outs, errs, rc = [], [], 0
    for part in [p for p in re.split(r"\s*(?:;|&&|\n)\s*", remote) if p.strip()]:
        if re.fullmatch(r"(true|:)", part.strip()):
            continue
        if re.fullmatch(r"hostname(\s+-\w+)?", part.strip()):
            outs.append(host)
            continue
        if re.fullmatch(r"echo\s+(.*)", part.strip()):
            outs.append(re.fullmatch(r"echo\s+(.*)", part.strip()).group(1).strip("'\""))
            continue
        rule = find_rule(sim, state, "ssh", part, host=host)
        if not rule:
            errs.append(f"bash: {part.split()[0]}: simulated host has no output for this command")
            rc = 127
            continue
        out, err, code = apply(rule, state)
        outs.append(out.rstrip("\n"))
        if err:
            errs.append(err.rstrip("\n"))
        rc = code or rc
    save(state)
    return emit("\n".join(o for o in outs if o), "\n".join(errs), rc)


def generic(sim, state, tool, args):
    log(tool, "-", "-", args)
    rule = find_rule(sim, state, tool, " ".join(args))
    if not rule:
        return emit("", f"{tool}: this command is not available in this environment", 1)
    out = apply(rule, state)
    save(state)
    return emit(*out)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: fakecli.py <tool> [args...]")
    tool, args = sys.argv[1], sys.argv[2:]
    sim, state = load()
    if tool == "kubectl":
        rc = kubectl(sim, state, args)
    elif tool == "ssh":
        rc = ssh(sim, state, args)
    else:
        rc = generic(sim, state, tool, args)
    sys.exit(rc)


if __name__ == "__main__":
    main()
