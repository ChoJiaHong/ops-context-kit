#!/usr/bin/env python3
"""guard.py 的回歸測試：用 template/TRUTH.md（prod-eks、web1–web3 是 prod）判斷每個指令的處理方式。

    python3 evals/guard_test.py

allow = 不攔；fix = 擋下請 agent 自己修正；ask = 要求使用者確認；deny = 直接拒絕。
第 2 輪評分者指出、也實際重現的誤判，標註 (r2)。
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "template")

CASES = [
    # 唯讀：不該打擾任何人
    ("allow", "kubectl get pods -n app --context prod-eks"),
    ("allow", "kubectl --context prod-eks get pods -n app | tee /tmp/pods.txt"),
    ("allow", "kubectl --context prod-eks get deploy api -o yaml > /tmp/api.yaml"),
    ("allow", "ssh -o BatchMode=yes web1 'df -h 2>/dev/null'"),                      # (r2)
    ("allow", "ssh web1 'lsof +L1 2>/dev/null | head'"),                            # (r2)
    ("allow", "ssh web1 'logrotate -d /etc/logrotate.d/orders'"),                   # (r2)
    ("allow", "ssh web1 'cat /etc/nginx/conf.d/app.conf' > /tmp/web1.conf"),       # (r2)
    ("allow", "ssh web1 cat /var/log/x | tee /tmp/x.log"),
    ("allow", "ssh web1 'journalctl -u nginx -n 50 > /tmp/n.log 2>&1'"),
    ("allow", "for h in web1 web2 web3; do ssh -o ConnectTimeout=5 $h 'df -h /'; done"),
    ("allow", "cat <<'EOF' > check_disk.sh\nfor h in web1 web2; do ssh $h df -h /; done\nEOF"),
    ("allow", "ssh -i ~/.ssh/id web1 'ps aux | grep orders-web'"),
    # 非 prod 的變更：K4 R2，hook 不攔
    ("allow", "kubectl --context stg-eks rollout restart deploy/api -n app"),
    ("allow", "kubectl --context stg-eks apply -f k8s/prod-eks/api.yaml"),          # 檔名有 prod 不算
    ("allow", "ssh stg1 'sudo systemctl reload nginx'"),
    # prod 變更：要求確認
    ("ask", "kubectl --context prod-eks rollout restart deploy/api -n app"),
    ("ask", "kubectl apply -f api.yaml --context=prod-eks"),
    ("ask", "helm upgrade api ./chart --kube-context prod-eks"),
    ("ask", "ssh web2 'sudo sed -i s/50MB/50m/ /etc/nginx/conf.d/app.conf'"),
    ("ask", "ssh -o BatchMode=yes deploy@web1 'sudo systemctl restart orders-web'"),
    ("ask", "ssh web1 'echo x | sudo tee /etc/nginx/conf.d/app.conf'"),
    ("ask", "ssh web1 'echo x > /etc/motd'"),
    ("ask", "ssh web1 'sudo logrotate -f /etc/logrotate.d/orders'"),
    ("ask", "ssh -p 2222 web3 'cp app.conf app.conf.bak'"),
    ("ask", "ssh web1 \"sudo kill -HUP $(cat /run/nginx.pid)\""),
    # 不可逆：不論環境都要確認
    ("ask", "kubectl --context stg-eks delete ns tmp"),
    ("ask", "ssh stg1 'truncate -s 0 /var/log/big.log'"),
    ("ask", "find /var/log -name '*.gz' -delete"),
    # 可以自己修正的錯
    ("fix", "kubectl get pods -n app"),
    ("fix", "kubectl config use-context prod-eks"),
    ("fix", "helm upgrade api ./chart"),
    # 災難指令
    ("deny", "rm -rf /"),
    ("deny", "dd if=/dev/zero of=/dev/sda"),
]

# KIT_PROD_CONFIRM=0：prod 上的可回復變更不再要求確認，不可逆操作仍然要
CASES_NO_PROD_CONFIRM = [
    ("allow", "kubectl --context prod-eks rollout restart deploy/api -n app"),
    ("allow", "ssh web2 'sudo sed -i s/50MB/50m/ /etc/nginx/conf.d/app.conf'"),
    ("allow", "helm upgrade api ./chart --kube-context prod-eks"),
    ("ask", "kubectl --context prod-eks delete pvc data-0 -n app"),
    ("ask", "ssh web1 'sudo truncate -s 0 /var/log/big.log'"),
    ("fix", "kubectl get pods -n app"),
]


def decide(cmd, **extra):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=TEMPLATE, **extra)
    env.pop("KIT_PROD_PATTERN", None)
    if "KIT_PROD_CONFIRM" not in extra:
        env.pop("KIT_PROD_CONFIRM", None)
    out = subprocess.run([sys.executable, os.path.join(TEMPLATE, "tools", "guard.py")],
                         input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}),
                         capture_output=True, text=True, env=env, check=True).stdout.strip()
    if not out:
        return "allow"
    hso = json.loads(out)["hookSpecificOutput"]
    if hso["permissionDecision"] == "deny":
        return "fix" if hso["permissionDecisionReason"].startswith("↺") else "deny"
    return hso["permissionDecision"]


def main():
    bad = 0
    runs = [(want, cmd, {}) for want, cmd in CASES]
    runs += [(want, cmd, {"KIT_PROD_CONFIRM": "0"}) for want, cmd in CASES_NO_PROD_CONFIRM]
    for want, cmd, extra in runs:
        got = decide(cmd, **extra)
        if got != want:
            bad += 1
            print(f"FAIL want={want} got={got} {extra}: {cmd!r}")
    print(f"{len(runs) - bad}/{len(runs)} passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
