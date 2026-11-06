# thinking/：思考模型的評估與衍生版本

這個資料夾整理從作者的「創新縮窄法」出發的所有分析：原模型適合什麼、怎麼改寫成優化 Claude 和設計 agent 工作流的版本，以及它能抽象到什麼程度。

## 一句話結論

- 原模型是**創意搜尋方法**：適合在已有成熟解法的領域，靠情境裡被忽略的資源做出更好的方案。用在優化、調校、除錯時很弱。
- 寫或調 CLAUDE.md 不需要它：直接用現成的規則集，出錯才改（[02](02-failure-driven-narrowing.md)）。
- 設計 agent 工作流的結構時，它改寫後很好用（[03](03-human-agent-design.md)）。
- 它可以當成範本衍生不同版本，核心是兩層骨架（[04](04-prototype-and-skeleton.md)）。
- 用它來抽象它自己，沒有比直接抽象好（[05](05-self-abstraction-experiment.md)）。

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
