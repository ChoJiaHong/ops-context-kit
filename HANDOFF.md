# 交接（2026-11-07）

給接手的 session。先讀這份，再依需要讀 `thinking/README.md` 和下面列的檔案。

## 使用者

- 台灣的 infra 工程師，用繁體中文（語音輸入時偶爾出現簡體與錯字，例如「追踪」=「最終」、「泡」=「跑」）。
- 平行開很多個 Claude 桌面版 session，處理 k8s 叢集和遠端主機。
- 重視可行性和效率；喜歡短答案，常要求「10 秒總結」。
- 每個階段的結論都要放進 git。
- 對模型的定義會要求「先思考、再跟我確認」；說「不要做任何動作」時只回答、不動手。

## repo

`https://github.com/ChoJiaHong/ops-context-kit`（本機曾在 `/home/claude/ops-context-kit`，新 session 要重新 clone）

| 分支 | 內容 | 狀態 |
|---|---|---|
| `main` | 最初版本 | 沒動過；合併等使用者決定 |
| `round2` → `round3` → `v3-merge` | 規則集三輪評估、v3 規則（未驗證） | 已 push |
| `thinking-models` | thinking/00–08 | 已 push |
| `double-loop` | thinking/09 + guard.py 三輪反駁試驗（回歸測試 202 個） | 已 push |
| **`claude-md`** | thinking/10–20 + 本檔 + 問題訊號分析與校準程式；包含以上全部 | **最新** |
| `workflow` | 從 `claude-md` 的 thinking/15 分出：`/start` → `/handoff`、session 綁定任務、guard 依任務 mode／targets 把關（回歸測試 213 個） | 已 push；沒有 thinking/16–19 |

檢查指令：`python3 evals/guard_test.py`、`python3 template/tools/check_kit.py`。

## 目前的結論

**思考模型**
- 使用者的原模型（[thinking/00](thinking/00-original-notes.md)：創新縮窄法、縮窄法、情境對比驅動的問題界定）最適合「找出問題、做出比現有更好的工具」。
- 用原模型時要加三件事：現有解法實際查證、優勢實際量測、連續兩次空轉才停。步驟順序交給 AI，但四種情境差異、向下與向上迴圈、優勢公式、適用範圍 P\*、硬湊檢驗都要做到。
- [11](thinking/11-double-loop-pure.md) 的「雙向迴圈」是使用者確認的最終抽象：兩個相反方向持續移動，其他全由 AI 決定。單獨用不夠，因為沒有判準；它是動力，原模型是內容。
- 06 的收斂骨架拿掉了原模型最需要的部分，已在 [16](thinking/16-model-selection.md) 修正，不要再選它。

**最近一次執行與評估**
- [20](thinking/20-problem-validation.md)：Codex 已在雲端完成量測器校準與可見對話個案核對。48 個事先固定的邊界案例中，25 個符合期望、23 個不符合；不是使用者實際準確率。`guard_test.py` 202/202，kit 結構檢查通過。沒有原電腦 JSONL，完整歷史 A/B 仍未驗證；不要把模擬資料當真實紀錄，或從缺資料推出零事件。詳見 `thinking/20-data/` 和 `evals/probe_problem_signals.py`。
- [18](thinking/18-original-model-run.md)：用原模型處理「大量使用 AI 時規則層的污染與覆蓋缺口」，得到四個解法。
- [19](thinking/19-evaluation-of-18.md)：自我評估。只有「infra 事實查核」站得住，而且應該改成「手寫事實越少越好」；「stg 測 AI 指令」的關鍵主張錯了（任務紀錄沒有初始狀態）；「隔離寫入」有內部矛盾（日誌也是外部文字）；問題的重新界定沒有用使用者的資料驗證。

**其他重要結論**
- guard 試驗（[09](thinking/09-double-loop.md)）：用字串判斷指令的黑名單補不完；隔離要靠權限（每個 session 只拿得到宣告目標的憑證），不是靠規則。
- 規則檔的現況（[10](thinking/10-claude-md.md)）：結構化做法已成熟，但都依檔案路徑觸發；規則有沒有用，社群憑感覺，沒有實測。

## 等使用者決定的事

1. 哪些分支要併進 `main`。
2. guard 的定位與四個細項（[09-data/claims/guard.md](thinking/09-data/claims/guard.md) 最後一節）。
3. 19 的修正建議要做哪幾項。

## 建議的下一步

**最新狀態（20）**：使用者要求由 agent 自主完成實驗，不再反覆把本機執行交回使用者。本輪已完成能自主進行的受控校準。原分析程式在 dry-run／權限查詢、部分寫入、工具失敗、事件時間、去重與專案識別上有量測偏差；正式歷史比較之前先處理這些資料品質問題。下列第 1 項的原始資料前提尚未滿足，不能宣稱已完成；不要以等待上傳作為唯一能做的工作。

1. **先用使用者的實際資料驗證問題**（使用者 11-07 選了這項，進行中）：已寫好 `evals/validate_problem.py`，等使用者在自己電腦跑完、上傳 `problem-signals.md`。它分別數出 A（使用者說過的痛點）和 B（18 的推論）的訊號，只輸出彙總數字和遮罩過的摘錄。`mine_sessions.py` 不適合做這件事：它是挑評估案例用的，只輸出第一句需求和難度分數，量不到糾正、逐步確認、同時開幾個 session、出事前有沒有 AI 改過 infra。`/insights` 最多看 50 個 session，平行用量大時只涵蓋幾天，可當補充。拿到結果後，判讀交給沒看過 18 推論的 agent（避免自己評自己）。這個雲端 session 碰不到使用者的電腦。
2. TRUTH.md 改成「只留查不到的事實」，其他現查或從 IaC 產生。
3. infra 工作區關掉自動記憶，教訓走 `lessons/inbox.md`（`workflow` 分支）。
4. 在原模型的主場測它（[16](thinking/16-model-selection.md) 的實驗設計）：只有雙向迴圈 vs 原模型完整內容，比較找出的方案查證後是否真的勝過現有工具。

## 這一路學到、要避免的錯

- **自己評自己**：產出者評估自己的結果偏差很大；重要的評估交給沒看過推論的 agent，或用實際資料。
- **太早停**：找到第一個看起來不錯的就停（14）；改成連續兩次空轉才停（15）。
- **只在 AI 工具圈子找現有解法**：要同時查使用者所在領域（infra）自己的成熟做法（19）。
- **資源只確認存在、沒確認能用**（19）。
- **誤解需求就動手**：使用者說「做出一個工作流」，其實是要「用模型找問題、做出比現有更好的工具」。不確定時先確認，或先問「你要的產出是什麼」。
- **工具面**：派子 agent 時，要求「寫出推理過程」的提示曾被安全機制擋下，換成只要結果的寫法；WebFetch 的授權提示有時沒人回應，改用搜尋或 `git clone`。11-07 的 session 裡，直接執行 clone 下來的程式（`guard_test.py`、`check_kit.py`）被權限擋下，沒驗證測試現況；自己寫的程式可以跑。

## commit 署名

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
