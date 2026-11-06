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

（尚無）

## 紀錄

（試驗開始後逐輪填入）
