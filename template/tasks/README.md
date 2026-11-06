# tasks/

每個任務一份紀錄，格式見 [TEMPLATE.md](TEMPLATE.md)，用 `tools/task_new.sh <slug>` 建立。

- 檔名：`T-YYYYMMDD-NN-<slug>.md`，ID 是 `T-YYYYMMDD-NN`。
- `status`：active、waiting、blocked、done、dropped。
- `targets` 是宣告：其他 session 要變更同一個 target 前會先問使用者。
- done 或 dropped 的紀錄可以留著當歷史；要清理時移到 `tasks/archive/`。
- 看所有任務：`python3 tools/context.py --board`
