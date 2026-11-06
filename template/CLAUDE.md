# CLAUDE.md

@AGENTS.md

上面這行讓 Claude Code 每個 session 自動載入 [AGENTS.md](AGENTS.md)（規則本體）。這份只補充 Claude 專屬的部分，不重複那裡的規則。

## Claude 專屬
- 建立任務後，用桌面版的 session 改名工具把 session 改成 `<任務 ID> <短標題>`；任務 done 並經使用者同意後封存 session。沒有這些工具（例如 CLI）時，請使用者自己執行 `/rename`。
- 使用者想看所有任務的狀態時，執行 `python3 tools/context.py --board`。
- hooks（`.claude/settings.json`）：
  - SessionStart：列出進行中的任務與 targets（K2）
  - PreCompact：提醒在上下文被壓縮前更新任務紀錄
  - PreToolUse：沒帶 --context、修改全域設定 → 擋下並請你自己修正（K3）；不可逆操作與 prod 變更 → 跳出核准提示給使用者（K4）。提示是保險，不代表你該先停下來問：符合 K4「直接做」的條件就照常執行，由使用者在提示上核准
- 改了 AGENTS.md、TRUTH.md 或 hooks 之後，執行 `python3 tools/check_kit.py`。
