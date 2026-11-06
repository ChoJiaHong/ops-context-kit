# ops-context-kit

一套給 infra 維運工作用的 Claude 規則集。和一般範本不同的是，它附上**推導規則的思考模型**和**驗證規則的實驗**：每條規則都有編號、假設和測試案例，沒有效果的規則可以用消融實驗找出來刪掉。

方法來自「情境對比驅動的問題重構」：
1. 把需求當成假設。
2. 從一般解（社群範本、官方建議）出發，和你的情境逐項比較差異。
3. 用差異帶來的資源消除一般解的瓶頸，得到候選規則。
4. 再用實驗往下補、往上剪。

```
ops-context-kit/
├── method/
│   ├── README.md        思考模型：形式化定義、推導流程、放置原則、停止條件
│   ├── derivation.md    第 0 輪推導：從你的需求到規則 K1–K10
│   ├── round1.md        第 1 輪：盲測思想實驗的結果與規則修正
│   ├── round1-data/     第 1 輪的原始評分資料
│   ├── round2.md        第 2 輪：修掉不公平之處後重做（獨立案例、獨立專家對手、跨模型評分）
│   ├── round2-data/     第 2 輪的案例、對手規則集與評分資料
│   ├── round3-plan.md   第 3 輪預先登記
│   ├── round3.md        第 3 輪：同一份數據，方法修改 vs. 專家修改
│   └── round3-data/     第 3 輪的新案例、a3′、a4′ 與評分資料
├── concepts.md          概念模型：工作區、環境、任務、session、宣告、事實
├── template/            複製到你的工作區就能用的規則集
│   ├── CLAUDE.md        Claude 入口（@AGENTS.md 自動載入規則）
│   ├── AGENTS.md        規則本體（K1–K8、K10；行數上限 80，由驗證腳本檢查）
│   ├── TRUTH.md         環境清單與查詢指令（不放狀態快照）
│   ├── tasks/           任務紀錄
│   ├── tools/           task_new.sh、context.py（注入／總覽）、guard.py（--context 與 R3 守門）、check_kit.py（驗證）
│   └── .claude/settings.json   SessionStart、PreCompact、PreToolUse hooks
├── install.sh           把 template 複製到你的工作區（不碰 ~/.claude）
└── evals/               實驗：12 個模擬案例、對照組、消融、比較報告、思想實驗模式（thought/）、從真實對話挖案例
```

## 使用

```bash
./install.sh ~/ops            # 或你的 infra repo
```
1. 編輯 `~/ops/TRUTH.md` 的環境表，標出哪些 context 和主機是 prod。
2. 在 Claude 桌面版開啟這個資料夾，開新 session，直接交代任務。

每個 session 會自動：
- 列出進行中的任務。
- 收到非一次性的工作時，建立任務紀錄並把 session 改名成任務 ID。
- prod 變更先停下來確認（第 2 輪發現這條在「使用者明確要求、可回復」的變更上太嚴，候選修改見 method/round2.md）。
- 完成前用觀察證明，做完收尾。

想看所有任務，開一個 hub session 說「看任務總覽」，或在終端機執行 `python3 tools/context.py --board`。

## 驗證規則

```bash
python3 evals/selftest.py                     # 不花錢：檢查案例本身寫得對不對
python3 evals/guard_test.py                   # 不花錢：guard hook 的 33 個回歸測試
evals/run.sh --quick --model sonnet           # 試跑
evals/run.sh --arms a1,a2,a3 --runs 3         # 和官方精簡版、agent-context-kit 改編版比較
evals/run.sh --arms a3 --ablate all           # 找出可以刪的規則
python3 evals/mine_sessions.py                # 從你的真實對話挖案例
```
詳見 [evals/README.md](evals/README.md)。

## 維護
- **改規則**：改 `template/AGENTS.md`（或工作區裡的 AGENTS.md），每條規則包在 `<!-- rule:Kn -->` 標記裡；接著跑 `python3 tools/check_kit.py`。
- **加規則**：只為觀察到的失敗加，並同時加一個會測到它的案例（method/README.md 第 ⑥ 步）。
- **刪規則**：消融結果 c_k < ε 時刪（第 ⑦ 步）。
- **每一輪的結論**寫回 `method/derivation.md`。

## 目前狀態
- **第 3 輪（方法修改 vs. 專家修改）已完成**，詳見 [method/round3.md](method/round3.md)，預先登記見 [method/round3-plan.md](method/round3-plan.md)。
  - 兩邊拿同一份第 2 輪數據修改規則，在 8 個全新案例上：方法修改版 0.82、專家修改版 0.85、無規則 0.67。
  - 修改後兩版都同時比無規則更安全、更有效率，取捨消失。**有效的是「用評估數據迭代」，不是推導方法本身**：依預先登記的標準，專家修得略好（−0.031，剛好越過門檻）。
  - 方法修改版沒有通過放進 template 的條件，template 維持第 2 輪版本；目前表現最好的規則集是 [a4′](method/round3-data/a4p/RULES.md)。
- **第 2 輪（公平條件下的思想實驗）**，詳見 [method/round2.md](method/round2.md)：
  - 案例和 grader 由看不到規則的獨立作者撰寫，對手換成獨立 SRE 寫的規則集，環境資訊對等，評分者混用兩種模型。
  - 本規則集 0.80、獨立 SRE 規則集 0.80、無規則 0.81。**本方法推導的規則沒有比有經驗的人直接寫的更好。**
  - 兩套規則集都是用效率換安全：避免損害的項目變好（失敗率約 10% → 3%），但在該直接做的任務上，停下來問的機率從 0.07 升到約 0.30。
  - 一次事故的代價若超過多確認一次的約 4～8 倍，規則就划算；這要用你的真實紀錄判斷。
  - 修正了 guard hook 的 7 個實際誤判，例如 `2>/dev/null` 被當成寫入、`ssh … | sudo tee /etc/…` 沒被攔到。K4 與 K2 的候選修改等第 3 輪驗證。
- **第 1 輪**的 0.91 對 0.58–0.64 是循環評估造成的（grader 在檢查有沒有照本規則做），保留在 [method/round1.md](method/round1.md) 作為紀錄。
- template 與工具都測過：安裝、建立任務、注入、總覽、guard（33 個回歸測試）、結構驗證。評估案例通過 selftest，格式也能被 `claude plugin eval` 載入。

## 參考
- [agent-context-kit](https://github.com/siudajakub/agent-context-kit)（MIT）：分層記憶、worklog、hooks、驗證腳本；a2 對照組改編自它的規則。
- [showrunner](https://github.com/Bendzae/showrunner)：Project → Task → Session 的概念模型與狀態設計。
- Anthropic〈Claude Code best practices〉：a1 對照組。
- `claude plugin eval`：Claude Code 內建的 plugin 評估工具。
