# 概念模型

這套規則集只用六個概念：工作區、環境、任務、session、宣告、事實。

```
Workspace（工作區）
 ├── TRUTH.md ──── 定義 Environments（環境）：哪些 context／主機／帳號、哪些是 prod、怎麼查
 ├── AGENTS.md ─── 規則（K1–K10）
 └── tasks/
      ├── T-20261106-01-api-502.md ──── Task：goal、done-when、targets、status
      │        └── Session（主 session，名稱以 T-20261106-01 開頭）
      ├── T-20261106-02-ingress-upgrade.md
      │        └── Session
      └── …
 hub session（不綁任務）──── 看總覽：python3 tools/context.py --board
```

## 概念定義

**Workspace（工作區）**
你在 Claude 開啟的資料夾，可以是 infra repo，也可以只是一個工作目錄。裡面放 AGENTS.md、CLAUDE.md、TRUTH.md、tasks/、tools/。

**Environment（環境）**
任務要操作的對象：k8s context + namespace、一台主機、一個雲端帳號。定義在 TRUTH.md，並標明是不是 prod。

**Task（任務）**
一件有目標、有完成條件的工作，用 `tasks/` 裡的一份紀錄表示。

| 類型 | 例子 |
|---|---|
| incident | api 間歇 502 |
| change | ingress-nginx 升級 |
| investigation | 盤點 node 資源 |
| script | DB 備份腳本 |
| learning | 了解 eBPF 怎麼用在監控 |

**Session**
一個 Claude 對話。**一個 session 只做一個任務**，名稱以任務 ID 開頭，例如 `T-20261106-01 api 502`。
- **主 session**：負責一個任務。
- **輔助 session**：大任務拆出的子任務，自己也有一份任務紀錄，在 `parent` 欄位指向原任務。
- **hub session**：不綁任務，只用來看總覽、決定下一步做什麼；對話可以隨時 `/clear`。

**Claim（宣告）**
任務紀錄的 `targets` 欄位，表示這個任務可能會變更哪些環境。兩個進行中的任務宣告同一個 target 時，任何一方要變更前都必須先問使用者。

**Truth（事實）**
系統當下的實際狀態。只能用 TRUTH.md 裡的查詢指令取得，不能從文件、任務紀錄、對話記憶推斷。

## 任務狀態

| status | 意義 | 桌面版側邊欄 |
|---|---|---|
| `active` | 進行中 | 開著 |
| `waiting` | 等使用者決定或外部事件 | 開著，hub 會優先列出 |
| `blocked` | 卡住，需要換方向 | 開著，hub 會優先列出 |
| `done` | 完成，已用觀察驗證 | 封存 |
| `dropped` | 放棄，原因寫在 result | 封存 |

## 生命週期

```
建立任務（tools/task_new.sh <slug>）
  │  寫 goal、done-when、targets；session 改名為任務 ID
  ▼
檢查宣告衝突（SessionStart hook 列出進行中任務）
  │  有衝突 → 問使用者
  ▼
工作（R0 直接做 → R2 快照＋預覽 → R3 停下確認）
  │  里程碑更新 progress、next；被壓縮前 PreCompact hook 提醒更新紀錄
  ▼
驗證（用觀察證明 done-when）
  ▼
收尾：寫 result、status=done；長期事實寫回 TRUTH.md；後續工作另建任務
  ▼
封存 session
```

## 和參考專案的對應

| 這裡 | agent-context-kit | showrunner |
|---|---|---|
| Workspace | repository | Project |
| Task 紀錄 | session worklog | Task（綁分支） |
| targets 宣告 | worklog 宣告的檔案 | 一個 session 一個 worktree |
| TRUTH.md（查詢方法） | PROJECT_STATUS.md（狀態快照） | — |
| hub + `context.py --board` | — | TUI 主畫面 |
| 桌面版 session 改名、封存 | — | session 建立、刪除、封存 |
