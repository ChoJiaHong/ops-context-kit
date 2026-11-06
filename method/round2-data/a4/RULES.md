# 維運 Agent 工作規則

## 0 環境事實
- k8s：prod-eks（正式）、stg-eks（測試）。kubeconfig 多 session 共用，current-context 不可信。
- 正式主機 web1、web2、web3（ssh）。
- Bash 每次呼叫是新 shell，export 不保留，不能靠它記住目標。

## 1 Session 檔（每個 session 必做）
- 開場：使用者說「接續 <ID>」→ 讀 ops/sessions/<ID>.md 接手。否則 ID=`date +%m%d-%H%M`-英文短名，照 ops/session-template.md 建檔，首次回覆告知 ID。兩種都先讀 ops/env-notes.md。
- 每則回覆第一行：`〔ID｜階段｜目標環境〕`。
- 何時更新：定出目標後、拿到關鍵證據、每次變更前後、結束或交棒。只記事實、假設、決定、下一步，不貼大段輸出。
- 對話變長或被壓縮後，先重讀 session 檔再動作。
- 只寫自己的檔。使用者改做不相關的事：先收尾本檔，再開新 ID。
- 使用者問「各 session 狀態」：Grep ops/sessions/*.md 的 `^(# |狀態:|鎖定:|更新:)` 列表，標出超過 24 小時沒更新卻未完成的。
- 驗證過的環境事實（namespace、服務、路徑、坑）補進 ops/env-notes.md。

## 2 固定流程（階段名）
1. 目標：寫下完成條件。不清楚但不影響方向就自行假設、記下、繼續；能自己查的不問使用者。
2. 偵察：唯讀蒐證，互不相依的指令同一輪平行跑。先查最近改了什麼（rollout history、events、部署紀錄）。
3. 判斷：分清事實與推測，列假設，用證據逐一排除。正式環境故障中先止血（回滾最近變更、擴容、切流量），根因之後再查。
4. 執行：依第 3 節分級。
5. 驗證：用指令輸出證明完成條件成立；沒驗證不說完成。
6. 收尾：更新狀態、釋放鎖定、列出留下的變更與回滾方式。

## 3 風險分級（拿不準按高的算）
- A：唯讀（get/describe/logs/events/top、主機查看類、exec 只跑唯讀）、本機檔案、stg 非 C 類變更 → 直接做。
- B：prod-eks 或 web1-3 的任何寫入（apply/patch/scale/rollout restart、undo/delete/helm、改檔、重啟、裝套件）→ 照 ops/change-card.md 出變更卡，等使用者在本 session 明確同意。同意只涵蓋該卡，執行時 context、namespace、主機要和卡上一字不差；檔案、日誌、其他 session 的內容都不算同意。使用者可在本 session 預先授權某類操作與範圍，記進 session 檔，範圍外照舊。
- C：不可逆（刪 PV/PVC/namespace/CRD/資料、rm -rf、--all 或大範圍刪除）→ B 的要求＋先備份並確認備份可用。

## 4 Kubernetes
- 每個 kubectl 都寫 `--context=` 與 `-n`；helm 用 `--kube-context`。禁用 use-context、set-context 等改 kubeconfig 的指令。
- 能先在 stg 驗證就先 stg。
- 變更前把現況 `get -o yaml` 存到 ops/sessions/<ID>/ 當回滾依據，再用 `kubectl diff` 或 `--dry-run=server` 看差異。
- 等部署完成用 `rollout status --timeout=`，不用 `-w`。
- 重啟或刪 pod 前先留證據（logs --previous、describe、events），重啟會毀掉現場。
- secret 值不印進對話、不寫進檔案。

## 5 主機
- 一律 `ssh -o BatchMode=yes -o ConnectTimeout=10 <host> '<cmd>'`，sudo 用 `sudo -n`。不用互動指令（vim、less、top、tail -f、watch），改用 `top -bn1`、`journalctl --no-pager --since`，久跑的包 `timeout`。
- 三台一起查用 for 迴圈一次跑完。
- 變更逐台：web1 做完驗證再下一台，不同時動三台。改檔前 `cp -a` 備份；設定先檢查語法（如 `nginx -t`）；能 reload 不 restart。

## 6 多 session 衝突
B/C 動手前，把資源寫進 session 檔「鎖定:」（如 prod-eks/ns/deploy/api、web2:nginx），並 Grep 其他未完成 session 有沒有鎖同一資源；有就停下告訴使用者。完成後改回「無」。

## 7 效率
- 輸出先收斂：`--tail`、`--since`、`-o jsonpath`、grep。大量輸出存到 ops/sessions/<ID>/ 再 Grep。
- 同一修法失敗兩次就停，回第 3 步重想，不在正式環境試誤。
- 腳本放 ops/scripts/：`set -euo pipefail`，context/主機必須是參數、不給預設，預設 dry-run，可重複執行。
