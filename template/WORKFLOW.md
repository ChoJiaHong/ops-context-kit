# 工作流

每個 session 都走同一條路：**/start → 做事 → /handoff**。

## 你要做的

| 時機 | 你打的 | 會發生什麼 |
|---|---|---|
| 開新 session、交辦工作 | `/start 幫我查 web1 為什麼 502` | Claude 先查一下現況，建立任務紀錄（目的、完成條件、模式、會寫入的目標），把這個 session 綁上去、改名，回你一個畫面的摘要。缺的資訊最多問 3 題 |
| 從工單開始 | `/start PROJ-123` | 有連 Jira 時讀工單來填 |
| 接續昨天的任務 | 「接續 T-20261106-02」 | Claude 綁定那份任務，從 next 繼續 |
| 做完、卡住、要交出去 | `/handoff` | 驗證完成條件並附證據、寫結果；有 prod 變更就寫接手卡；教訓放進 `lessons/inbox.md`；建議要不要結束 session |
| 想看全部任務 | `python3 tools/context.py --board`，或開一個 session 說「看任務總覽」 | 列出每個任務的狀態、模式、目標、下一步 |
| 偶爾 | 打開 `lessons/inbox.md` | 審查 session 提出的教訓，值得的合併進 AGENTS.md 或 TRUTH.md |

## 模式

| 模式 | 什麼時候 | guard 怎麼把關 |
|---|---|---|
| `look` | 「看一下」「查」「為什麼」 | 擋下所有會改變狀態的指令，Claude 只能回報發現 |
| `fix` | 「處理」「修好」 | 寫入任務沒宣告的目標會先問你 |
| `change` | 明確的變更 | 同上 |

不論模式：prod 變更和不可逆操作都會跳確認（K4）；沒帶 `--context`、改全域設定會被擋下讓 Claude 自己修正（K3）。

## 為什麼這樣設計

- **每個 session 照同一流程**：開始和結束都是指令，不靠 Claude 記得規則。
- **目的清楚**：每個 session 綁一份任務，模式和目標由 guard 實際把關，不只是寫在紀錄裡。
- **多 session 好管理**：開始時檢查其他任務有沒有宣告同樣的目標；`--board` 一眼看全部。
- **你的負擔小**：需求不用寫完整，Claude 先查再問；收尾和交接由 `/handoff` 做。

## 還沒做的（之後可加）

- 依任務的 targets 自動產生這個 session 專用的 kubeconfig 和 ssh 設定，讓隔離由權限保證（[thinking/13](../thinking/13-two-layer.md)、[15](../thinking/15-full-delegation-redo.md)）。
- Stop hook 自動檢查完成條件。
- 用沙盒行為測試驗證這套流程的效果。
