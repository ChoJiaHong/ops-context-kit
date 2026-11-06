# tasks/

每個任務一份紀錄，格式見 [TEMPLATE.md](TEMPLATE.md)。用 `tools/task.py start`（Claude 用 `/start`）建立並綁定 session；只要檔案不要綁定時用 `tools/task_new.sh <slug>`。

- 檔名：`T-YYYYMMDD-NN-<slug>.md`，ID 是 `T-YYYYMMDD-NN`。
- `status`：active、waiting、blocked、done、dropped。
- `mode`：look（只查）、fix（排障）、change（變更）。綁定後 guard 依它把關：look 擋下所有變更。
- `targets` 是宣告：寫入沒宣告的目標會跳確認；其他 session 要變更同一個 target 前會先問使用者。
- `.bind/`：session 和任務的綁定（本機狀態，不進 git）。
- done 或 dropped 的紀錄可以留著當歷史；要清理時移到 `tasks/archive/`。
- 看所有任務：`python3 tools/context.py --board`
