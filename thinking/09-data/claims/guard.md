# 主張：guard.py

- **G（不准改）**：多個平行的 agent session 在執行 Bash 指令前，
  1. prod 上的變更與不可逆操作要經使用者確認（ask）；
  2. 修改共用全域狀態、kubectl／helm 沒指定叢集，要擋下讓 agent 自己修正（fix）；
  3. 災難指令直接拒絕（deny）；
  4. 唯讀工作與非 prod 的可回復變更不打擾（allow）。
  完整定義見 template/AGENTS.md 的 K3、K4。
- **Sₑ**：Claude Code 內建的權限規則（settings.json 依指令前綴 allow／ask／deny），沒有 guard。前綴規則看不到參數，分不出 prod 與非 prod，也分不出唯讀與變更，只能「全部問」或「全部放」。
- **S**：template/tools/guard.py（PreToolUse hook），v3。
- **C（目前假設成立的條件）**：
  1. 指令由善意 agent 在 Bash 工具呼叫裡寫出；
  2. 變更內容直接寫在指令字串裡看得到；
  3. 目標用 TRUTH.md 的名稱指定（`--context prod-eks`、`ssh web1`）；
  4. 使用 kubectl、helm、terraform、ansible-playbook、ssh 與常見 shell 指令。
- **評估器**：`python3 thinking/09-data/check.py '<指令>'`（E4，直接執行 guard.py）。
- **威脅模型**：粗心但善意的 agent。刻意混淆（編碼後 eval、拼接指令名稱來躲規則）不在範圍內，只記為邊界。

## 嚴重度

- **S1**：該攔沒攔。
- **S2**：唯讀或非 prod 的工作被打擾。

## 不涵蓋（縮 C 的累積）

1. 刻意混淆（編碼後 eval、拼接指令名稱）。
2. 目標不在 TRUTH.md 名單上的不算 prod：ansible 群組、terraform 環境、資料庫主機要列進 TRUTH.md 才認得（terraform／ansible 另外看 prod、production、prd、live 這些字）。
3. 遠端的變更指令是「列出來的才認得」，不在清單上的會放行。
4. 由程式語言間接執行的指令（python subprocess、Makefile 等）與清單外的遠端執行工具（aws ssm、pssh…）。

## 紀錄

### 第 1 輪

- 反駁者：A 組（主張框架）、B 組（一般審查），各交 25 個，全部重現。核對後 49 個成立；1 個（`kubectl --kubeconfig <單一叢集檔> get pods` 被要求補 --context）判定為符合 K3，交給使用者決定是否改判。
- 在範圍內的 S1：A 組 15 個（13 類），B 組 16 個（14 類），重疊 8 類，合計 19 類。既有 39 個測試和 method/ 三輪審查都沒涵蓋。
- 處理：
  - 修 S：改成逐段切指令、認出指令名稱再判斷（引號裡的資料、寫進檔案的 heredoc 不再當成指令）；解析迴圈與變數的目標；heredoc、`bash -s < 腳本`、pipe 進遠端 shell；scp／rsync；ansible ad-hoc；kubectl exec；補上多種變更與不可逆寫法。19 類裡 18 類修好。
  - 縮 C：ansible 群組名稱不在 TRUTH.md（不涵蓋第 2 條）。
  - 回歸測試：evals/guard_test.py 新增 69 個（CASES_R1），共 108 個全過。
- 交給使用者：(1) 單一叢集 kubeconfig 是否改判；(2) TRUTH.md 沒列的名稱是否一律當 prod（K4 寫「不確定就當成 prod」，guard 目前當成非 prod）。

### 第 2 輪

- 反駁者：1 個（A 組形式，拿到更新後的主張紀錄），交 25 個，全部重現、成立、在範圍內、未被測試涵蓋：S1 21 個、S2 4 個。
- 其中 9 個（S1 5、S2 4）是第 1 輪的修正本身引入的：舊版對整段文字比對，粗糙但寧可多攔；新版精準，但解析漏掉的地方會直接放行（雙引號裡的 `$( )`、kubectl exec 參數重組、新加的規則寫錯）。
- 處理（全部修 S）：
  - 原則：內容會流向執行者、但解析不確定時，當成指令而不是資料。
  - `$( )`、反引號（包括雙引號裡的）拆開檢查；stdin（heredoc、here-string、`<` 檔案、pipe）一路傳到遠端、pod、容器、資料庫；同一個指令裡剛寫好的腳本，執行時讀剛寫的內容。
  - SQL 依敘述第一個字判斷；合併短選項（`psql -tAc`、`sudo -nu`）；xargs 佔位符當成判斷不出目標；大括號展開；cd 進去的目錄與 terraform workspace；覆寫 ~/.kube/config；dd 寫入任何區塊裝置、mke2fs 等。
  - 回歸測試新增 51 個（CASES_R2，含反駁者提到但沒交出的 21 個），共 159 個全過。
