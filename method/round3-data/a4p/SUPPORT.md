# 輔助檔案

路徑皆相對於工作區根目錄（與 RULES.md 中的 `ops/...` 一致）。`ops/sessions/`、`ops/scripts/` 是 agent 執行時自行建立的資料夾，不屬於輔助檔案。

舊版的 `ops/session-template.md` 已刪除：session 檔的格式（固定五行檔頭與內文段落）已直接寫在 RULES.md 第 1 節，agent 不必為了建檔多讀一個檔。

## 1. ops/change-card.md

用途：只在 agent 決定停下、需要使用者決定要不要改正式環境時使用。讓使用者一眼看懂為什麼停、要做什麼、失敗怎麼退，回一句「同意」就能執行。直接做的 prod 變更不需要出卡，只要在 session 檔的變更紀錄記一行。

````markdown
# 正式環境變更卡（停下等使用者決定時附在回覆裡）

【變更卡】<ID>-<序號>
- 為什麼停下：<不可逆／前提不成立／別人正在處理／會讓 prod 整體中斷／超出要求範圍／拿不準能否回復>，附關鍵證據（指令與輸出摘要）
- 目標：<prod-eks / namespace / 資源> 或 <web1 → web2 → web3：服務>
- 指令（逐字、依序）：
  1. 
- 影響：<會不會中斷、動到幾個 pod 或哪台、預計多久>
- 前置：<現況備份路徑 ops/sessions/<ID>/...；stg 是否跑過同樣變更>
- 驗證：<每一步之後跑什麼指令、看到什麼算成功>
- 停止條件：<出現什麼就停>
- 回滾（逐字）：
  1. 
- 不可逆的另附：備份位置，以及如何確認備份可用
- 不做或延後的話：<風險、可替代的作法>

請回覆「同意」執行，或指出要改的地方。

## 使用規則
- 同意只涵蓋這張卡；執行時 context、namespace、主機要和卡上一字不差。
- 一張卡可包含一組有順序的步驟（例：三台逐台 reload），每步之間都要驗證。
- 觸發停止條件：立即照卡回滾（已含在同意範圍內），然後停手回報，不自行改試別的修法。
- 指令、目標、範圍任何一項要改，就出新卡重新取得同意。
- 執行後在 session 檔「變更紀錄」記一行，並更新「更新:」時間。
````

## 2. ops/env-notes.md

用途：所有 session 共用的環境知識庫。每個 session 開場和第一批偵察平行讀，避免重複摸索；驗證過的新事實隨手補上。最後一段是通用陷阱，不是本環境特有，但在這類工作中常見。

````markdown
# 環境備忘（所有 session 共用，只放驗證過的事實）
格式：- 事實｜怎麼確認的｜YYYY-MM-DD
用 Edit 加在對應段落。發現與現況不符就直接更正並改日期。
不放 secret、密碼、token；不放很快會過期的狀態快照（例如「api 目前 3 個 replica」）。

## Kubernetes
- prod-eks＝正式，stg-eks＝測試。kubeconfig 多 session 共用，current-context 不可信，每個指令都帶 --context。
### namespace 與服務對照
- 
### 部署方式（helm release、manifest 目錄、CI pipeline，以及改了叢集要同步哪裡）
- 
### 慣用排查指令
- 

## 正式主機
- web1、web2、web3：正式環境，ssh 直接用主機名。
### 各台跑的服務、設定檔與日誌位置
- 
### 前端 LB 與健康檢查（URL 或指令、預期結果、怎麼看某台是否被摘除）
- 

## 相依服務（DB、快取、外部 API、DNS）
- 

## 工作區慣例（筆記放哪、共用變更紀錄在哪、誰負責什麼）
- 

## 本環境已知坑
- 

## 通用坑（非本環境特有）
- 不帶 --context 的 kubectl 會打到共用的 current-context；文件或筆記裡抄來的指令常漏帶。
- `kubectl create job --from=cronjob/...` 會真的執行那個工作（寄信、同步、扣款），不是演練。
- 沒有 readiness probe 時，`rollout status` 成功不代表穩定；會崩潰的問題要等過原本崩潰的時間點再看 RESTARTS。
- `df` 會列出 squashfs（/snap，永遠 100%）、tmpfs、devtmpfs、overlay；看真實磁碟壓力用 `df -hPT -x squashfs -x tmpfs -x devtmpfs -x overlay`。
- `du` 加總遠小於 `df` 已用量：多半是已刪除但仍被程序開著的檔，用 `sudo lsof +L1` 查；要讓該程序重開檔（重啟）才會真正釋放。
- 沒設 ConnectTimeout 的 ssh 遇到連不上的主機會卡約兩分鐘。
- 設定語法錯誤時 reload 會失敗但舊設定繼續服務；restart 則會停掉後起不來。
````
