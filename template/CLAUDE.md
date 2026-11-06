# CLAUDE.md

@AGENTS.md

上面這行讓 Claude Code 每個 session 自動載入 [AGENTS.md](AGENTS.md)（規則本體）。這份只補充 Claude 專屬的部分，不重複那裡的規則。

## Claude 專屬
- 工作流：不是一次問答就能結束的工作，用 `/start` 開始（建立任務、綁定 session、改名）；做完、卡住或要交出去時用 `/handoff`。session id 在開頭 `[session] id:` 那一行。
- 使用者想看所有任務的狀態時，執行 `python3 tools/context.py --board`。
- hooks（`.claude/settings.json`）：
  - SessionStart：session id、這個 session 綁定的任務、所有進行中的任務與 targets（K2）
  - PreCompact：提醒在上下文被壓縮前更新任務紀錄
  - PreToolUse：沒帶 --context、修改全域設定 → 擋下並請你自己修正（K3）；不可逆操作與 prod 變更 → 跳出核准提示給使用者（K4）。綁定任務後還會依任務把關：`look` 模式擋下所有變更；`fix`／`change` 寫入任務沒宣告的目標會跳確認。提示是保險，不代表你該先停下來問：符合 K4「直接做」的條件就照常執行，由使用者在提示上核准
- 改了 AGENTS.md、TRUTH.md 或 hooks 之後，執行 `python3 tools/check_kit.py`。
