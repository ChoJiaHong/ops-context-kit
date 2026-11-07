#!/usr/bin/env python3
"""Controlled calibration of validate_problem.py. No fixture command is executed.

Run from the repo: python3 evals/probe_problem_signals.py
Outputs thinking/20-data/probe-results.json. Mismatches are experimental
findings, not runner failures; inspect the machine-readable results.
"""
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "evals/validate_problem.py"
spec = importlib.util.spec_from_file_location("validate_problem", TARGET)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)

# These are known command semantics, not an attempt to mimic their prevalence.
MUTATION_CASES = [
    ("kubectl --context stg get pods", False),
    ("kubectl --context stg apply -f app.yaml", True),
    ("kubectl --context stg apply -f app.yaml --dry-run=server", False),
    ("kubectl --context stg create cm x --from-literal=k=v --dry-run=client -o yaml", False),
    ("kubectl --context stg auth can-i delete pods", False),
    ("kubectl --context stg cp ./a app/pod:/tmp/a", True),
    ("helm upgrade api ./chart --kube-context stg", True),
    ("helm upgrade api ./chart --kube-context stg --dry-run", False),
    ("terraform plan", False),
    ("terraform apply -auto-approve", True),
    ("ansible-playbook site.yml --check", False),
    ("ansible-playbook site.yml --syntax-check", False),
    ("systemctl restart nginx", True),
    ("systemctl --user restart app", True),
    ("docker compose up -d", True),
    ("docker ps", False),
    ("scp app.conf web1:/etc/app.conf", True),
    ("ssh web1 'touch /tmp/probe'", True),
    ("ssh web1 'echo x > /tmp/probe'", True),
    ("ssh web1 'grep rm /var/log/auth.log'", False),
    ("ssh web1 'sudo sed -i s/a/b/ /etc/app.conf'", True),
    ("kubectl --context stg exec api -- rm /tmp/probe", True),
]
RULE_CASES = [
    ("Write", {"file_path": "/work/CLAUDE.md"}, True),
    ("Write", {"file_path": "/work/.claude/rules/a.md"}, True),
    ("Write", {"file_path": ".claude/rules/a.md"}, True),
    ("Edit", {"file_path": "memory/topic.md"}, True),
    ("Write", {"file_path": "README.md"}, False),
    ("Bash", {"command": "cat > CLAUDE.md <<'EOF'\nx\nEOF"}, True),
    ("Bash", {"command": "cp draft.md CLAUDE.md"}, True),
    ("Bash", {"command": "cat > .claude/rules/a.md <<'EOF'\nx\nEOF"}, True),
    ("Bash", {"command": "cat CLAUDE.md"}, False),
]
TEXT_CASES = [
    ("correct", "不是我要的，請重新整理。", True),
    ("correct", "請說明 Kubernetes 的核心元件。", False),
    ("stop", "先不要執行。", True),
    ("stop", "整理 kubectl、helm 等等工具的差異。", False),
    ("confirm", "繼續", True),
    ("confirm", "可以說明為什麼嗎？", False),
    ("incident", "服務壞了，現在連不上。", True),
    ("incident", "請設計 rollback 演練流程，目前沒有故障。", False),
    ("incident", "避免出事，先讀取目前設定。", False),
]


def user(text, ts="2026-11-07T00:00:00Z", cwd="/work/probe"):
    return {"type": "user", "timestamp": ts, "cwd": cwd,
            "message": {"role": "user", "content": text}}


def tool(ident="t1"):
    return {"type": "assistant", "timestamp": "2026-11-07T00:01:00Z", "cwd": "/work/probe",
            "message": {"id": "message-1", "role": "assistant", "content": [
                {"type": "tool_use", "id": ident, "name": "Bash",
                 "input": {"command": "kubectl --context stg apply -f app.yaml"}}]}}


def write(path, events):
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")


def main():
    rows = []

    def record(group, ident, inp, expected, actual):
        rows.append({"group": group, "id": ident, "input": inp,
                     "expected": expected, "actual": actual, "passed": actual == expected})

    for i, (cmd, expected) in enumerate(MUTATION_CASES, 1):
        record("mutation", f"M{i:02}", cmd, expected, vp.is_mutating(cmd))
    for i, (name, inp, expected) in enumerate(RULE_CASES, 1):
        record("rule_write", f"R{i:02}", {"tool": name, "input": inp}, expected,
               vp.is_rule_write(name, inp))
    regexes = {"correct": vp.CORRECT, "stop": vp.STOP, "confirm": vp.CONFIRM, "incident": vp.INCIDENT}
    for i, (category, text, expected) in enumerate(TEXT_CASES, 1):
        record("text", f"T{i:02}", {"category": category, "text": text}, expected,
               bool(regexes[category].search(text)))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def cli(name, files):
            folder = root / name
            folder.mkdir()
            for filename, events in files.items():
                write(folder / filename, events)
            out = root / f"{name}.md"
            result = subprocess.run([sys.executable, str(TARGET), "--root", str(folder),
                                     "--since", "30", "--no-excerpts", "--out", str(out)],
                                    capture_output=True, text=True, timeout=10)
            return result, out.read_text(encoding="utf-8") if out.exists() else ""

        result, report = cli("valid", {"one.jsonl": [user("請檢查 staging 服務目前的健康狀態。"), tool(), user("好")]})
        record("integration", "I01", "valid timestamped transcript produces a report", True,
               result.returncode == 0 and "2 個人類回合" in report)
        result, report = cli("empty", {})
        record("integration", "I02", "missing data must not produce an all-zero success report", True,
               result.returncode != 0 and not report)
        result, report = cli("mixed", {"one.jsonl": [user("請檢查 staging 服務目前的健康狀態。")],
                                       "two.jsonl": [user("請讀取這一份沒有時間欄位的紀錄。", None)]})
        record("integration", "I03", "mixed missing timestamps must not crash", True,
               result.returncode == 0)
        if result.returncode:
            rows[-1]["stderr"] = result.stderr.strip().splitlines()[-1:]

        result, report = cli("old", {"one.jsonl": [user("請檢查以前的服務狀態。", "2020-01-01T00:00:00Z")]})
        record("integration", "I04", "--since 30 excludes old messages in newly touched files", False,
               result.returncode == 0 and "2020-01-01" in report)

        duplicated = root / "duplicate.jsonl"
        write(duplicated, [user("請檢查 staging 服務目前的健康狀態。"), tool(), tool()])
        record("integration", "I05", "same message/tool ID repeated should count once", 1,
               vp.scan(str(duplicated))["tool_calls"])

        failed = root / "failed.jsonl"
        write(failed, [user("請更新 staging 設定。"), tool(),
                       {"type": "user", "timestamp": "2026-11-07T00:02:00Z",
                        "message": {"role": "user", "content": [
                            {"type": "tool_result", "tool_use_id": "t1", "is_error": True,
                             "content": "bash: kubectl: command not found"}]}}])
        record("integration", "I06", "command-not-found cannot count as an executed infra change", 0,
               len(vp.scan(str(failed))["mutations"]))

        for i, project in enumerate(("/work/team-a/app", "/work/team-b/app")):
            path = root / f"project{i}.jsonl"
            write(path, [user("請檢查這個專案的狀態。", cwd=project)])
        names = [vp.scan(str(root / f"project{i}.jsonl"))["project"] for i in range(2)]
        record("integration", "I07", "different cwd with same basename must remain separate", 2, len(set(names)))

        refused = root / "refused.jsonl"
        write(refused, [user("請更新 staging 設定。"), tool(),
                        {"type": "user", "timestamp": "2026-11-07T00:02:00Z",
                         "message": {"role": "user", "content": [
                             {"type": "tool_result", "tool_use_id": "t1", "is_error": True,
                              "content": "User rejected tool use"}]}}])
        record("integration", "I08", "explicit rejected command is excluded", 0,
               len(vp.scan(str(refused))["mutations"]))

    groups = {}
    for group in sorted({r["group"] for r in rows}):
        subset = [r for r in rows if r["group"] == group]
        groups[group] = {"passed": sum(r["passed"] for r in subset), "total": len(subset)}
    confusion = Counter((r["expected"], r["actual"]) for r in rows if r["group"] == "mutation")
    payload = {"scope": "synthetic controlled calibration; not user session history",
               "target": "validate_problem.py at baseline commit 0dbea6a",
               "target_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(),
               "python": sys.version.split()[0],
               "date": "2026-11-07", "total": len(rows), "passed": sum(r["passed"] for r in rows),
               "groups": groups, "mutation_confusion": {
                   "TP": confusion[True, True], "TN": confusion[False, False],
                   "FP": confusion[False, True], "FN": confusion[True, False]}, "cases": rows}
    out = ROOT / "thinking/20-data/probe-results.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "cases"}, ensure_ascii=False, indent=2))
    print("Mismatches:", ", ".join(r["id"] for r in rows if not r["passed"]))


if __name__ == "__main__":
    main()
