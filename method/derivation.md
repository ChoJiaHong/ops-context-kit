# 推導紀錄：套用到你的情境

> **第 1 輪已完成**（盲測思想實驗）：K9 移除；K1、K7 縮短；K2、K4 改寫措辭；K3 加上 L0 保證。詳見 [round1.md](round1.md)。
>
> **第 2 輪已完成**（公平條件）：本規則集和獨立 SRE 的規則集表現相當，第 1 輪的領先大多來自循環評估；K4「使用者明確要求也要確認」是主要成本來源，候選修改 K4′、K2′ 待第 3 輪驗證。詳見 [round2.md](round2.md)。
>
> 以下是第 0 輪的原始推導，保留作為紀錄。

## 第 0 輪

這是用 [思考模型](README.md) 第 ①–⑤ 步推導出的**候選規則集 R₁**。第 ⑥⑦ 步要靠 [evals/](../evals/README.md) 的實驗完成；在跑出結果之前，下面每條規則都只是**假設**。

---

## ① 原始問題與需求假設

**P₀（固定）**：讓同時進行的多個 Claude session，在 infra 維運工作裡可靠地完成任務，而且使用者管得動這些 session。

| 編號 | 需求（原文整理） | 狀態 | 指標 |
|---|---|---|---|
| h1 | 每個 session 都自動照同一套工作流程做 | 保留 | 規則遵守率（各案例的 grader） |
| h2 | 對話拉長後還看得出 session 在做什麼 | 保留 | 接續案例（C05）、偏題案例（C06）成功率 |
| h3 | session 多了還管得動 | 保留 | 平行宣告案例（C04）、收尾案例（C12）成功率 |
| h4 | 知道這套東西是什麼、怎麼維護 | 保留 | 非行為指標：結構驗證 `tools/check_kit.py` 通過 |
| h5 | 提示詞包成可呼叫、可控的工具 | **使用者撤回** | — |
| h6 | 控制回覆長度與資訊密度 | **使用者撤回** | — |

h5、h6 是「把一開始的需求當假設」的實例：它們是最早被說出口的需求，但後來的對話顯示瓶頸在 session 管理與多 session 協作，不在單則回覆的長度。推測撤回原因：內建功能（Concise 輸出樣式、skill 的手動觸發設定）已經能涵蓋，再加一層只會增加維護成本。

**使用者情境 C**：大量用 AI 寫腳本、處理 infra、排查錯誤；經常操作叢集與多台遠端主機；用 Claude 桌面版；同時開很多 session；重視可行與效率。

---

## ② 一般問題與一般解

**P_g**：讓多個 coding agent session 能延續上下文、互相協調、不互相干擾。

| 一般解 S_e | 核心元件 |
|---|---|
| S1 官方 best practices | CLAUDE.md 精簡、讓 Claude 能驗證、先探索再規劃、`/clear` 分隔任務 |
| S2 agent-context-kit | 依變化速度分四層的記憶、每個 session 一份 worklog（宣告要改的檔案）、SessionStart/PreCompact hook 注入、驗證腳本防止文件腐化 |
| S3 showrunner | Project → Task → Session 階層、每個任務一個主 session、狀態（執行中／等待／需要你／完成）、worktree 隔離、收尾清理 |
| S4 superpowers | 開發流程 skill（腦力激盪 → 計畫 → TDD）、SessionStart 注入啟動 skill |
| S5 桌面版內建功能 | 側邊欄、改名、封存、依狀態篩選；Claude 可以列出、讀取其他 session，並互傳訊息 |

---

## ③ 情境對比：一般情境（軟體開發）vs C（infra 維運）

| 維度 | 一般情境 | C | 差異 |
|---|---|---|---|
| 事實所在 | git tree | 叢集、主機、雲端帳號的即時狀態 | **D1** 事實在 repo 之外，而且會在你沒動它時改變 |
| 工作單位 | 分支、PR | 事故、變更、調查、腳本 | **D2** 工作單位不是分支 |
| 完成證據 | 測試通過、diff | 觀察到系統達到目標狀態 | **D3** 證據要靠觀察，不是靠測試 |
| 共享狀態 | 同一份 git index、同一批檔案 | kubeconfig 的 current-context、雲端 CLI 的預設 profile、遠端主機本身 | **D4** 衝突發生在全域設定與遠端系統上 |
| 執行環境 | 終端機、tmux、IDE | 桌面版：已有 session 列表、改名、封存、跨 session 工具 | **D5** session 管理功能已內建 |
| 風險 | 大多可以 revert | prod 變更、刪除、資料清除不可逆 | **D6** 爆炸半徑大 |
| 工作區 | 一個 repo | 可能是 infra repo，也可能只是一個工作目錄 | **D7** 不一定有 repo |

---

## ④ 瓶頸 × 差異配對 → 候選規則

| 一般解元件 | 在 C 的瓶頸 L | 可用的差異／資源 | 調整後 → 規則 |
|---|---|---|---|
| S2 PROJECT_STATUS（狀態快照） | D1：快照很快過期，agent 會相信舊資料 | 系統本身可以查詢 | 文件只記「怎麼查」，不記快照 → **K7**、TRUTH.md |
| S2 worklog 宣告「檔案」 | D4：真正的衝突在叢集與主機上 | 任務紀錄可以宣告「目標」 | 宣告 targets（ctx/ns、主機）→ **K1**、**K2** |
| S2 SessionStart 注入 worklog | 本身可用 | — | 保留，改成注入進行中任務的 targets → **K2** |
| S2 CLAUDE.md 寫「先讀 AGENTS.md」 | 要模型自己去讀，實際上只是 L2，可能沒讀到 | Claude Code 的 CLAUDE.md 支援 `@path` 匯入 | CLAUDE.md 用 `@AGENTS.md` 匯入，保證規則每次都載入（L1） |
| S3 Task = 分支 | D2：維運任務不是分支 | 任務紀錄檔 | 任務 = 一份紀錄，有 goal／done-when／targets → **K1** |
| S3 orchestrator（tmux／TUI） | D5：和桌面版重複 | 桌面版內建 session 工具 | 不做 orchestrator，只定命名慣例：session 名稱以任務 ID 開頭（資源重新詮釋）→ **K1**、CLAUDE.md |
| S3 狀態「需要你」 | 可用 | 任務紀錄的 status 欄位 | waiting／blocked 狀態，hub 用 `context.py --board` 總覽 |
| S1/S2 完成定義（測試通過） | D3：infra 沒有單元測試 | 唯讀查詢指令 | 用觀察證明 done-when → **K5** |
| S1「`/clear` 分隔任務」 | 使用者在對話中途提出新需求時沒有機制 | 任務紀錄的 goal | 偏題時另建任務、建議另開 session → **K6** |
| （無對應） | D4：切換全域 context 會影響其他 session | 每個指令都能帶目標參數 | 不改全域狀態、每個指令明確帶目標 → **K3** |
| （無對應） | D6：不可逆操作 | hook 可強制確認 | 風險分級；R3 停下確認；hook 保證 → **K4** |
| S4 systematic-debugging | 可用，但原版偏程式碼 | infra 的證據來源（logs --previous、events、journal） | 先證據後修改、兩次失敗就停 → **K9** |
| S4 TDD、worktree | D2、D7：多數任務不適用 | — | **不採用** |
| （使用者工作的一大類） | 腳本缺乏 dry-run、不能重跑 | — | 腳本標準 → **K10** |
| S2 收尾（寫回長期記憶、刪 worklog） | 可用 | TRUTH.md、任務紀錄 | 完成時寫 result、status=done、長期事實寫回 TRUTH → **K8** |

---

## ⑤ 規則集 R₁ 與放置

| ID | 規則摘要 | 層級 | 假設 | 測試案例 |
|---|---|---|---|---|
| K1 | 非一次性工作建任務紀錄；一個 session 一個任務；session 以任務 ID 命名 | L1 + L3 | 能維持 session 的目的，接續時不會迷路 | C05、C06、C12 |
| K2 | session 開始時注入進行中任務的 targets；變更前檢查宣告衝突 | L0（SessionStart hook）+ L1 | 減少平行 session 互相干擾 | C04 |
| K3 | 不改全域狀態；每個指令明確帶目標；遠端指令非互動並批次執行 | L1 | 減少打錯環境 | C01、C03、C09 |
| K4 | 風險分級 R0–R3；R3 停下等確認 | L1 + L0（PreToolUse guard） | 減少未經確認的不可逆變更 | C02、C10 |
| K5 | 用觀察證明完成 | L1 | 減少「說完成但其實沒完成」 | C01、C08 |
| K6 | 偏題時另建任務、建議另開 session | L1 | session 保持單一目的 | C06 |
| K7 | 事實要查，不要記 | L1 + L3（TRUTH.md） | 減少相信過期資訊 | C05、C07 |
| K8 | 收尾：寫 result、status=done、長期事實寫回 TRUTH | L1 + L3 | 任務狀態保持正確，session 可以安心封存 | C12 |
| K9 | 先證據後修改；兩次修正失敗就停 | L1 | 減少盲目修改 | C01、C10 |
| K10 | 腳本標準：strict mode、dry-run、可重跑、交付前檢查 | L1 | 腳本品質提升 | C11 |

**刻意不放進規則集的東西**（以及原因）

| 項目 | 原因 |
|---|---|
| 回覆長度控制、提示詞工具化 | 使用者撤回（h5、h6） |
| session orchestrator、status line | 桌面版已內建 session 管理；status line 在桌面版不一定顯示 |
| 大量的危險指令清單 | guard 只管 R3 與全域狀態變更；完整清單維護成本高，交給權限設定 |
| TDD、worktree 流程 | 多數維運任務沒有程式碼測試，也不一定在 repo 裡 |
| 變更紀錄（journal） | 和 K2 的任務宣告功能重疊；先測 K2 是否足夠，不夠再加 |

---

## ⑦ 預期的適用範圍 P*（待驗證）

**假設**：這組規則的優勢不限於 k8s，而是適用於「**事實存在 repo 之外、會被多個 session 同時讀寫的共享可變狀態**」的 agent 工作，例如資料庫維運、雲端帳號管理、資料管線。

**驗證方式**：在任務集加入非 k8s 的案例（例如 C09、C10 的 SSH 主機操作），比較 A3 與 A2 的差距是否仍為正。

---

## 下一輪要做的事
1. 跑 evals：A0（無規則）、A1（官方精簡版）、A2（agent-context-kit 調整版）、A3（R₁）、A3 的消融。
2. 依 c_k 刪除貢獻不足的規則（⑦），依失敗歸因新增規則（⑥）。
3. 用 `evals/mine_sessions.py` 從你的真實對話紀錄補任務，取代部分模擬案例，提高外部效度。
4. 把結果寫回這份文件，標為第 1 輪。
