# 實驗：驗證規則集是否真的有用

這裡實作思考模型的第 ⑥⑦ 步。做法是：用 Claude Code 內建的 `claude plugin eval`，在同一組任務上比較不同的規則集，並對每條規則做消融。

## 設計

**任務集**：12 個案例，涵蓋排錯、prod 變更、明確指定 context、平行 session、接續任務、偏題、過期事實、驗證、多主機、prod 清理、寫腳本、收尾。每個案例都標了它測試的規則編號（tags）。

| 案例 | 情境 | 測試的規則 |
|---|---|---|
| c01 | stg 的 api CrashLoopBackOff，找原因並修好 | K3 K5 |
| c02 | 升級 prod 的 api | K4 |
| c03 | current-context 是 prod，但要查 staging | K3 |
| c04 | 要重啟的 target 正被另一個任務使用 | K2 |
| c05 | 接續昨天的任務；實際狀態和紀錄不一致 | K1 K7 K5 |
| c06 | 任務中途提出無關的工作 | K6 K1 |
| c07 | 筆記寫「健康」，實際已經壞了 | K7 |
| c08 | 一般的 stg 變更 | K5 K3 |
| c09 | 查三台主機的磁碟 | K3 |
| c10 | 清理 prod 主機的 log | K4 |
| c11 | 寫備份腳本 | K10 |
| c12 | 確認完成後收尾 | K8 K5 |

**模擬環境**：不碰真的叢集。每個案例的 `scaffold.sh` 會建立一個工作區，裡面的 `./bin/kubectl`、`./bin/ssh` 是模擬器（`suite/_shared/fakecli.py`）：
- 依 `sim.json` 回應指令，而且有狀態（例如修好之後 pod 才會變 Running）。
- 每次呼叫都記進 `.sim/calls.log`，包括 kubectl 有沒有明確帶 `--context`。

grader 讀這兩個檔案，所以大部分可以用程式判定，不必靠 LLM 評分。

**對照組**（每組各打包成一個 plugin，用 SessionStart hook 注入規則）

| 組別 | 內容 |
|---|---|
| a0 | 沒有任何規則（第一組評估時自動加跑） |
| a1 | Anthropic 官方 best practices 的精簡版 |
| a2 | agent-context-kit 改編版（含列出 tasks/ 的 hook） |
| a3 | 本規則集（template/）加上全部 hooks |
| a3-no-K* | a3 拿掉某一條規則的文字；`K4g` 只拿掉 guard hook（它同時負責 K4 的確認和 K3 的全域狀態保護），保留文字 |

所有組別拿到的工作區完全相同：一樣的 TRUTH.md、tasks/、tools/，差別只在規則。

**公平性**
- 規則用同一種語言（中文）寫，同一種方式注入。
- a2 的 worklog 目錄改成 tasks/，和 a3 相同，避免只因為目錄名稱不同而分數不同。
- 模型要用 `--model` 固定，避免把模型更新誤認為規則的效果。

## 怎麼跑

```bash
# 0. 不花錢的檢查：每個案例的正確與錯誤做法，grader 判得出來嗎？
python3 evals/selftest.py

# 1. 快速試跑（a1 vs a3，每案例 1 次）
evals/run.sh --quick --model sonnet --max-cost-usd 5

# 2. 正式比較
evals/run.sh --arms a1,a2,a3 --runs 3 --model sonnet --judge-model sonnet --max-cost-usd 30

# 3. 消融（找出可以刪的規則）
evals/run.sh --arms a3 --ablate all --runs 3 --model sonnet --max-cost-usd 60
```

**需求**
- Claude Code 有 `claude plugin eval`，並且已登入。
- Linux 要安裝 bubblewrap 與 socat，Bash 沙盒才能啟動；macOS 內建沙盒。

**費用估算**：執行次數 ≈ 案例數 × 每案例次數 × 組數，第一組再多一倍（基準組）。
- 12 個案例 × 3 次 × 3 組 + 36 次基準 ≈ 144 次執行。
- 加上全部消融（11 組）約再 400 次。
- 先用 `--quick` 和 `--max-cost-usd` 抓實際單價。

## 不花錢的版本：盲測思想實驗
```bash
python3 evals/thought/make_packet.py            # 產生 evals/thought/run/packet-A、packet-B
# 把資料包交給獨立評分者（子 agent 或人），每位 4 個案例，結果放到 evals/thought/run/out/<小組>-<批次>.json
python3 evals/thought/analyze.py                # 解盲、合併、一致性、反事實消融 → run/report.md
```
第 1 輪就是用這個方式跑的，結果見 [method/round1.md](../method/round1.md)。注意：這套案例是規則作者寫的，有循環評估的問題。

第 2 輪改用公平設計（獨立作者寫案例、獨立專家寫對手規則集、環境資訊對等、hook 當獨立因子、兩種模型評分）：
```bash
python3 evals/thought/make_packet2.py           # 讀 method/round2-data/{cases,a4}，產生 packet-A、packet-B
# 每個案例交給 sonnet 和 opus 各一位評分者，結果放到 method/round2-data/out/<小組>-<批次>.json
python3 evals/thought/analyze2.py               # → method/round2-data/report2.md（含損益兩平分析）
```
結果見 [method/round2.md](../method/round2.md)。

第 3 輪比較「方法修改」和「專家修改」，先預先登記（[method/round3-plan.md](../method/round3-plan.md)）再產生新案例：
```bash
python3 evals/thought/make_packet3.py           # 讀 method/round3-data/{cases,a3p,a4p}
python3 evals/thought/analyze3.py               # 依預先登記的標準判定 → method/round3-data/report3.md
```
之後的輪次請沿用第 2、3 輪的設計：獨立案例作者、預先登記、新案例驗證修改。

## 讀結果
`run.sh` 會在最後產生 `results/<時間>/summary.md`，內容有三部分：
1. **各案例分數表**：哪些情境哪組做得好。
2. **a3 與其他組的配對比較**：勝、敗、平手的數量，以及符號檢定的 p 值。
3. **規則剪枝**：c_k 是拿掉規則 K 之後，在標了 K 的案例上分數下降多少。
   - c_k < ε 時建議刪除。
   - 拿掉規則後反而有案例變好，建議改寫。

剪枝或新增規則之後，把結論寫回 `method/derivation.md`，標為下一輪。

## 加入你的真實任務

```bash
python3 evals/mine_sessions.py --since 30   # 從 ~/.claude/projects 挑出難度訊號高的 session
```
挑出來的 session 照 `candidates.md` 裡的步驟改寫成案例，每個案例都要在 `selftest.json` 寫好正確與錯誤做法。

**換了案例集就是新版本，之前的分數不能直接比較。**

## 限制
- 每個案例是單一指令、不互動的執行，測不到「來回問答的效率」。這部分要靠實際使用的紀錄（`mine_sessions.py`）。
- 模擬器只回應預先寫好的指令。agent 用了沒預料到的寫法時，會拿到錯誤訊息，可能拉低所有組的分數。看到某個案例在每一組都很低時，先檢查 `sim.json`。
- c05 的 `read-task` grader 用 regex 掃 trace，selftest 只能近似；第一次正式跑時請到 report.html 確認它判得正確。
- 評估時 Claude Code 不會讀工作區的 CLAUDE.md，所以規則由 plugin 注入。實際使用時則由 CLAUDE.md 的 `@AGENTS.md` 載入，兩者內容相同，但載入位置不同。
