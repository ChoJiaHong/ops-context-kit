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

# 雙迴圈試驗 1（thinking/09-double-loop.md）：兩個反駁者找到、經重現的反例，以及確認不會多打擾的日常指令
CASES_R1 = [
    ('ask', "for h in web1 web2 web3; do ssh -o BatchMode=yes $h 'sudo -n systemctl reload nginx'; done"),
    ('ask', 'for ctx in stg-eks prod-eks; do kubectl --context $ctx -n app rollout restart deploy/api; done'),
    ('ask', "ssh -o BatchMode=yes web1 'sudo -n bash -s' < scripts/fix_nginx.sh"),
    ('ask', "ssh -o BatchMode=yes web1 <<'EOF'\nsudo -n cp /etc/nginx/conf.d/app.conf /etc/nginx/conf.d/app.conf.bak\nsudo -n systemctl restart orders-web\nEOF"),
    ('ask', 'rsync -av --delete ./html/ deploy@web1:/var/www/html/'),
    ('fix', 'aws eks update-kubeconfig --name prod-eks --region ap-northeast-1'),
    ('fix', 'gcloud config configurations activate prod'),
    ('ask', 'terraform -chdir=envs/production apply -auto-approve'),
    ('ask', "ansible web1 -b -m systemd -a 'name=nginx state=restarted'"),
    ('ask', 'ssh web1 "sudo -n sed -ri \'s/^worker_processes .*/worker_processes 4;/\' /etc/nginx/nginx.conf"'),
    ('ask', "ssh web1 'sudo -n nginx -t && sudo -n nginx -s reload'"),
    ('ask', 'ssh web1 "psql -c \'DELETE FROM sessions WHERE expires_at < now()\'"'),
    ('ask', "find /var/log/app -name '*.gz' -mtime +30 -exec rm {} +"),
    ('deny', 'sudo dd if=backup.img of=/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol0abc123 bs=4M'),
    ('allow', 'kubectl --context prod-eks -n app apply -f api.yaml --dry-run=server'),
    ('allow', 'kubectl get pods -n app -o wide \\\n  --context prod-eks'),
    ('allow', "cat >> tasks/T7-api.md <<'EOF'\n- 下一步：kubectl --context prod-eks -n app rollout restart deploy/api（等使用者核准）\nEOF"),
    ('allow', "echo '- 新磁碟要 mkfs.xfs 後掛載，交給使用者在終端機操作' >> tasks/T4-disk.md"),
    ('allow', 'ssh web1 \'sudo -n journalctl --since yesterday | grep -iE "reboot|shutdown|oom"\''),
    ('allow', 'ssh web1 \'sudo -n journalctl -k --since "1 hour ago" | grep -i oom-kill\''),
    ('allow', 'ssh web1 "df -h | awk \'\\$5+0 > 80\'"'),
    ('allow', 'kubectl --context prod-eks auth can-i delete pods -n app'),
    ('allow', "grep -rn 'kubectl config use-context' tasks/ runbooks/"),
    ('ask', 'CTX=prod-eks; kubectl --context $CTX rollout restart deploy/api -n app'),
    ('fix', 'kubectl --context prod-eks -n app logs $(kubectl -n app get pods -l app=api -o name | head -1) --tail=100'),
    ('ask', "ssh -o BatchMode=yes web1 'sudo -n reboot'"),
    ('ask', "ssh -o BatchMode=yes web1 'sudo -n systemctl reboot'"),
    ('ask', "ssh -o BatchMode=yes web1 bash -s <<'EOF'\nsudo -n systemctl restart nginx\nEOF"),
    ('ask', 'scp app.conf web1:/etc/nginx/conf.d/app.conf'),
    ('ask', "ssh -o BatchMode=yes web1 'sudo -n nginx -t && sudo -n nginx -s reload'"),
    ('ask', "ssh -o BatchMode=yes web1 'sudo -n yum update -y openssl'"),
    ('ask', "ansible web1 -b -m service -a 'name=nginx state=restarted'"),
    ('ask', "find /var/log -name '*.gz' -mtime +30 -exec rm {} \\;"),
    ('ask', "ssh stg1 ': > /var/log/big.log'"),
    ('ask', 'ssh -o BatchMode=yes web1 \'mysql app -e "DELETE FROM sessions WHERE expires_at < NOW()"\''),
    ('ask', 'terraform -chdir=envs/stg apply -destroy -auto-approve'),
    ('ask', 'aws s3 rm s3://app-backups-stg/2025/ --recursive'),
    ('allow', 'kubectl --context prod-eks apply -f api.yaml --dry-run=server'),
    ('allow', 'helm diff upgrade api ./chart -n app --kube-context prod-eks'),
    ('allow', 'echo "- 回滾：kubectl --context prod-eks rollout undo deploy/api -n app" >> tasks/T-0042.md'),
    ('allow', 'ssh web1 \'last -x | grep -E "reboot|shutdown"\''),
    ('allow', 'ssh web1 "awk \'\\$9 >= 500\' /var/log/nginx/access.log | wc -l"'),
    ('allow', "ssh web1 'systemctl status logrotate --no-pager'"),
    ('allow', 'grep -rn "DROP TABLE" db/migrations/'),
    ('allow', 'ansible-playbook -i inventory/hosts.ini site.yml --limit web1 --syntax-check'),
    ('allow', 'ssh -o BatchMode=yes web1 "sudo -n grep \'systemctl restart\' /var/log/auth.log | tail -20"'),
    ('ask', "ssh web1 'sudo -n service nginx restart'"),
    ('ask', "ssh web1 'sudo -n docker restart api'"),
    ('ask', "ssh web1 'sudo -n apt-get -y install jq'"),
    ('ask', 'ssh web1 "psql -c \'ALTER TABLE orders DROP COLUMN legacy\'"'),
    ('ask', 'kubectl --context prod-eks taint nodes n1 key=v:NoSchedule'),
    ('ask', 'kubectl --context prod-eks autoscale deploy api --min 2 --max 5'),
    ('ask', 'kubectl --context prod-eks cp ./fix.conf app/api-0:/etc/app/fix.conf'),
    ('ask', 'kubectl --context prod-eks rollout pause deploy/api -n app'),
    ('allow', "ssh stg1 'ls -l /sbin/mkfs*'"),
    ('allow', 'helm repo list'),
    ('allow', 'kubectl --context prod-eks set env deploy/api --list -n app'),
    ('allow', 'kubectl --context prod-eks create cm x --from-file=a.conf --dry-run=client -o yaml'),
    ('allow', 'kubectl --context prod-eks get cronjob delete-old-logs -n app'),
    ('fix', 'kubectl config set current-context prod-eks'),
    ('allow', 'echo hi > out.txt && cp out.txt out2.txt && rm out2.txt'),
    ('allow', "git commit -m 'kubectl delete 改成要確認'"),
    ('allow', 'kubectl --context prod-eks logs api-0 -n app --since=10m | grep -i error > /tmp/err.log'),
    ('allow', 'ssh -o BatchMode=yes web1 \'sudo -n journalctl -u nginx --since "10 min ago" --no-pager | tail -50\''),
    ('allow', 'kubectl --context prod-eks exec api-0 -n app -- cat /etc/app/config.yaml'),
    ('allow', 'python3 tools/report.py > /tmp/report.txt 2>&1'),
    ('allow', 'for h in web1 web2 web3; do echo "== $h"; ssh -o BatchMode=yes $h \'uptime; free -m\'; done'),
    ('ask', 'kubectl --context prod-eks exec api-0 -n app -- rm -rf /var/cache/app'),
    ('ask', "cat fix.sh | ssh -o BatchMode=yes web1 'sudo -n bash -s'"),
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
    runs = [(want, cmd, {}) for want, cmd in CASES + CASES_R1]
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
