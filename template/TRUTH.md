# TRUTH：怎麼查目前的事實

這裡只放兩種東西：**查詢方法**，以及**長期不變、附查證日期的事實**。
狀態快照（例如「api 有 3 個 replica、全部正常」）不要寫在這裡，它很快就會過期。

## 環境

<!-- 填入你的環境。prod 欄位是 guard hook 和 K4 判斷 R3 的依據。 -->
| 名稱 | 類型 | 怎麼指定 | prod |
|---|---|---|---|
| prod-eks | k8s context | `--context prod-eks` | yes |
| stg-eks | k8s context | `--context stg-eks` | no |
| web1–web3 | 主機 | `ssh -o BatchMode=yes web1` | yes |

## 查詢指令

| 想知道 | 指令 |
|---|---|
| 叢集總覽 | `kubectl get nodes,deploy -A --context <ctx>` |
| 某個服務的 pod | `kubectl get pods -n <ns> -l app=<app> -o wide --context <ctx>` |
| 最近的事件 | `kubectl get events -n <ns> --sort-by=.lastTimestamp --context <ctx> \| tail -20` |
| 主機狀態 | `ssh -o BatchMode=yes <h> 'uptime; df -h /; free -m'` |
| 服務狀態 | `ssh -o BatchMode=yes <h> 'systemctl status <svc> --no-pager -l \| head -20'` |

## 長期事實

<!-- 格式：- <事實>（查證：<指令>，<YYYY-MM-DD>） -->
