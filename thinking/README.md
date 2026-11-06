# thinking/：思考模型的評估與衍生版本

這個資料夾整理從作者的「創新縮窄法」出發的所有分析：原模型適合什麼、怎麼改寫成優化 Claude 和設計 agent 工作流的版本，以及它能抽象到什麼程度。

## 一句話結論

- 原模型是**創意搜尋方法**：適合在已有成熟解法的領域，靠情境裡被忽略的資源做出更好的方案。用在優化、調校、除錯時很弱。
- 寫或調 CLAUDE.md 不需要它：直接用現成的規則集，出錯才改（[02](02-failure-driven-narrowing.md)）。
- 設計 agent 工作流的結構時，它改寫後很好用（[03](03-human-agent-design.md)）。
- 它可以當成範本衍生不同版本，核心是兩層骨架（[04](04-prototype-and-skeleton.md)）。
- 用它來抽象它自己，沒有比直接抽象好（[05](05-self-abstraction-experiment.md)）；但用**抽象後的骨架**再做一次，就勝過 Claude 自己的方式，骨架也接近收斂（[06](06-self-abstraction-2.md)）。
- 拿骨架去解外部問題集（MacGyver、錯誤前提、數學），沒有比一般「先分析再回答」的提示更好；在數學題上不幫忙、只讓輸出變長（[08](08-results.md)）。
- 前面測的都是單次提示。把雙迴圈改寫成「迭代有範圍的主張」，由獨立反駁者搭配能自動判定的評估器多輪執行，第一次用在 guard.py 上：找出大量既有測試漏掉的嚴重問題，三輪沒有收斂，指出 guard 只能當盡力而為的第二層（[09](09-double-loop.md)）。
- 對象換成 claude.md 集後先整理現況：結構化做法已經成熟，但都依檔案路徑觸發，沒有依操作目標觸發；規則有沒有用，社群憑感覺判斷、沒有實測，這正是雙迴圈可以補的地方（[10](10-claude-md.md)）。
- 最終抽象只剩「雙向迴圈」：一定是兩個相反的方向，才能持續移動；方向是什麼、何時轉向、何時停，全部交給執行的 AI 決定（[11](11-double-loop-pure.md)）。
- 對「找出問題、做出比現有更好的工具」這個需求，最好的版本是 06 的收斂骨架（內容與判準），用 11 的雙向迴圈去跑（動力）；模型的意義在具體內容，不在固定程序（[16](16-model-selection.md)）。
- 用它檢視 ops-context-kit：kit 在執行階段很強，入口、出口、學習都缺；任務檔的 targets 可以變成中樞，同時驅動規則載入、憑證隔離和 guard 的目標白名單（[12](12-kit-loop.md)）。

## 文件

| 檔案 | 內容 |
|---|---|
| [00-original-notes.md](00-original-notes.md) | 原始筆記整理：創新縮窄法、縮窄法、情境對比驅動的問題界定 |
| [01-evaluation.md](01-evaluation.md) | 原模型評估：換情境的思想實驗、用在 agent 工作流的六個思想實驗、前例、自身貢獻、最有意義的用途 |
| [02-failure-driven-narrowing.md](02-failure-driven-narrowing.md) | 失敗驅動的縮窄法：用真實失敗事件校準 Claude 的設定（事實檔、規則、hook、skill、工作方式） |
| [03-human-agent-design.md](03-human-agent-design.md) | 人機差異設計法：用「工作者從人變成 agent」的差異，設計新的 agent 工作方式 |
| [04-prototype-and-skeleton.md](04-prototype-and-skeleton.md) | 原模型當原型：可替換的槽位、上層骨架（參照、差異、作用、範圍、必要）、下層骨架（綁定假設、功能重述） |
| [05-self-abstraction-experiment.md](05-self-abstraction-experiment.md) | 自我抽象實驗：用原模型抽象原模型 vs. 直接抽象，盲評結果 |
| [self-abstraction-data/](self-abstraction-data/) | 實驗的輸入、六份方案、評分標準與評審紀錄 |
| [06-self-abstraction-2.md](06-self-abstraction-2.md) | 第二次自我抽象：用抽象後的骨架分析原模型，十份方案盲評，以及收斂後的骨架 |
| [self-abstraction-2-data/](self-abstraction-2-data/) | 第二次的預先登記、分析工具、四份新方案與三位評審紀錄 |
| [07-experiment-plan.md](07-experiment-plan.md) | 實驗計畫：拿收斂後的骨架去解 MacGyver、錯誤前提問題、GSM8K 等外部問題集，和 Claude 直接解比較 |
| [08-results.md](08-results.md) | 小規模試驗結果：MacGyver、FalseQA、GSM8K，三組 × 70 題；骨架沒有比一般結構化提示好 |
| [08-data/](08-data/) | 試驗的預先登記、題目、提示、全部答案、評審紀錄與核對紀錄 |
| [09-double-loop.md](09-double-loop.md) | 雙迴圈改寫成「迭代有範圍的主張」：角色、證據等級、觸發與停止；試驗 1（guard.py）的結果 |
| [09-data/](09-data/) | 主張紀錄、三輪反駁者的反例、核對紀錄、評估器與計分腳本 |
| [double-loop/SKILL.md](double-loop/SKILL.md) | 雙迴圈的 skill 草稿（尚未放進 template） |
| [10-claude-md.md](10-claude-md.md) | claude.md 集的現況：各工具的結構、md 在工作流的位置、infra 用的結構、子 agent 控制、社群做法、提示詞正規化、Jira／Teams 自動化、多 session 隔離，以及下一步實驗方向 |
| [11-double-loop-pure.md](11-double-loop-pure.md) | 雙向迴圈的最終抽象、方向的例子、從原模型到最終形式的路徑；skill 草稿在 [double-loop/bidirectional-loop/](double-loop/bidirectional-loop/SKILL.md) |
| [12-kit-loop.md](12-kit-loop.md) | 用雙向迴圈檢視 ops-context-kit：四組方向的紀錄、五個優化方向、kit 的新定位（以任務檔為中心的 session 生命週期系統） |
| [13-two-layer.md](13-two-layer.md) | 兩層雙向迴圈：第一層設計第二層（目標 ↔ 機制，巢狀缺口 ↔ 工具），找出投資和目標錯配、憑證分讀寫、隔離換掉確認 |
| [14-full-delegation-gap.md](14-full-delegation-gap.md) | 工程師把工作全部交給 AI：查證哪些缺口已有工具，找出真正的空白（理解與技能回不到負責的人身上）與解法（接手卡、能力帳本、理解債） |
| [15-full-delegation-redo.md](15-full-delegation-redo.md) | 重跑 14：11 次轉向的完整紀錄、連續兩次空轉才停、逐一查證，得到 5 個依重要性排序的缺口與解法方向 |
| [16-model-selection.md](16-model-selection.md) | 選出最好的版本：需求釐清（找問題、做出比現有好的工具）、固定判準與內容而非程序、「死規則就是意義」的評估；選 06 的收斂骨架，用 11 的雙向迴圈跑 |
| [17-ai-work-gaps.md](17-ai-work-gaps.md) | 用選出的模型找規則層的污染與覆蓋缺口：9 個候選、3 個直接採用現有工具，4 個局部修改的工具（帶出處的教訓流程、infra 事實查核、hook 觸發必須執行的程序、依目標載入規則），各附接受條件 |
| [18-original-model-run.md](18-original-model-run.md) | 用原模型重跑 17：問題重新界定為「人審不完、錯誤出事才知道」，四種情境差異與六維縮窄找出「用 stg 和自己的任務紀錄測試 AI 指令」等四個新解，向上迴圈找出各自的適用範圍 |

## 三個版本怎麼搭配

```
設計新工作方式（創造）       ── 03 人機差異設計法
        │ 實際使用
        ▼
出錯時修正設定（校準）       ── 02 失敗驅動的縮窄法
        │ 同類問題修兩次仍在
        ▼
重新界定問題（重構）         ── 原模型（00）
```

## 和 method/ 的關係

[method/](../method/) 是「用情境對比推導 CLAUDE.md 規則」的思考模型與三輪實驗。三輪的結論是：推導出的規則不比專家直接寫的好，有效的是用評估數據迭代。這個資料夾接著回答兩個問題：這個方法到底適合什麼，以及怎麼改寫才適合優化 Claude 和設計工作流。
