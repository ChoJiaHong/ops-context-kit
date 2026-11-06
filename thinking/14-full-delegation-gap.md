# 14 工程師把工作全部交給 AI：現有工具覆蓋不了的缺口

情境：一位工程師正在把工作全部交給 AI 做。問題：找出現有工具覆蓋不了的缺口，並提出解法。用兩層雙向迴圈（[13](13-two-layer.md)）。查證日期 2026-11-07。

## 第一層：設計第二層模型

方向：通用模型 ↔ 這個情境。

- 這個情境的對象不是某個任務，而是工程師的整份工作，包括沒寫在任何地方的隱性職責。
- 所以第二層的主軸定為：**工程師原本承擔的職責 ↔ 交給 AI 之後由誰承擔**。正向從職責找接手的工具；反向從工具回頭看它接手時悄悄丟掉了什麼。
- 巢狀用「缺口 ↔ 工具」，每個候選缺口都要先查證現有工具真的沒覆蓋，才算數。

## 第二層：職責 ↔ 承擔者

**正向（職責 → 誰接手）**

| 職責 | 交給 AI 後 |
|---|---|
| 做事（寫程式、改設定、排障） | Claude Code 等 agent |
| 決定做什麼（工單、訊息、口頭請託） | 部分：Jira／Teams 連接器讀得到寫下來的，讀不到沒寫下來的 |
| 把關不合理的需求 | 部分：plan 模式、Spec Kit 的釐清步驟 |
| 審核、核准 | agent 的核准提示 |
| 承擔責任（出事時能解釋、能接手） | 只剩工程師一個人 |
| 從工作中累積對系統的理解 | AI 的記憶（CLAUDE.md、自動記憶） |
| 維持自己的技能 | 沒有 |

**反向（工具 → 悄悄丟掉了什麼）**

- agent 做完事：工程師沒有親手做，也就沒有從中學到東西。
- 記憶和 CLAUDE.md：新學到的現場知識存進 AI 的記憶，沒有回到人身上。
- 稽核紀錄：記下誰做了什麼、誰核准，但沒有確認負責的人看不看得懂。
- 核准提示：一個個彈出，沒有排序，容易變成反射性按同意。

## 查證：哪些其實已經有工具

| 候選缺口 | 現有工具 | 判斷 |
|---|---|---|
| 多個 agent 的核准集中、排序、批次處理 | Gumloop、Beam 的跨 agent 收件匣（可篩選、排序、批次核准）；LangChain Agent Inbox；hoop.dev 在 Slack／Teams 裡做動作層級的核准 | 已覆蓋 |
| 決策可追溯（誰授權、依據什麼） | Gravitee 等 AI gateway 記錄發起者、agent、模型、工具呼叫和政策決定；hoop.dev 的核准紀錄 | 已覆蓋（企業級） |
| agent 的身分與權限委派 | Microsoft Entra Agent ID、Okta for AI Agents（2026-04-30 正式推出） | 已覆蓋 |
| 跨團隊、多人 agent 的協調 | Arxion、Progress Forge 等新工具，但都以程式碼為主 | 部分；infra 目標層級的還沒有 |
| **工程師的理解與技能回流** | 只有文章和個人做法（先自己試 15–30 分鐘；把工作分成 AUTO、REVIEW、COACH、OFF 等檔位） | **沒有工具** |

## 真正的缺口：理解回不到負責的人身上

現有工具都在讓 AI 更懂系統：記憶、CLAUDE.md、context、稽核。沒有工具讓負責的人繼續懂。

工程師把工作全部交出去之後，仍然要負責、要監督、出事時要接手。但：
- **理解債**：他負責的變更越來越多是自己沒看懂的。
- **技能退化**：監督 AI 的品質，受限於自己的專業；而專業不用就會退化。2026 年的文章引用研究指出，在 AI 協助下學習，除錯能力的落差最大。

這個缺口在「全部交給 AI」的情境最尖銳，而且照這次查到的資料，沒有現成工具在處理。

## 巢狀：缺口 ↔ 工具

**缺口 → 工具：理解回流**

1. **接手卡**：AI 完成一項工作時，不只寫紀錄，而是產出一張讓負責的人在凌晨被叫醒時能接手的卡：改了什麼、為什麼、怎麼看出它壞了、怎麼回滾，再附一兩個檢查理解的問題。答不出來的，就記為理解債。
2. **能力帳本**：記錄工程師最近親手做過、真正理解過哪些類型的工作。某類工作太久沒碰，下次同類任務改成教練模式：工程師先做，AI 在旁邊提示。或者用真實事故在沙盒裡重播演練。
3. **理解債指標**：負責但沒理解的變更有多少。超過自己設的門檻，就放慢委派或安排複盤。

**工具 → 缺口（反向檢查）**

- **順便補到的**：承擔責任（人能解釋）、隱性知識（接手卡審過後變成團隊知識）、核准品質（帳本顯示哪類工作人已經看不懂，那類核准就該找別人或放慢）。
- **會弄壞的**：增加人的負擔，和「效率」衝突。對策：
  - 只對 prod、高風險、不可逆的工作出接手卡。
  - 教練模式只用在工程師自己選定要保留的技能。
  - 設每天的時間上限。
- **風險**：檢查問題變成考背誦。對策：只問「怎麼看出壞了、怎麼回滾」這類操作性問題。

**放進 ops-context-kit 的方式**：`/handoff` 產出接手卡；`tasks/` 旁加一份能力帳本；排程任務每週整理理解債，並從真實事故出一題演練。

## 次要缺口

**infra 目標層級的跨人協調**：多位工程師各自把工作交給 AI 時，他們的 agent 可能同時動同一個叢集或主機。現有的協調工具以程式碼檔案為主，人類用的變更管理系統（ServiceNow 等）又不是為 agent 設計的。這個缺口存在，但證據較少，先記下。

## 意義

「把工作全部交給 AI」真正的缺口不在 AI 那邊，而在人這邊。整個生態都在投資「讓 AI 懂系統」，幾乎沒有人投資「讓負責的人繼續懂」。這也是今晚所有討論都沒碰到的方向：前面優化的全是 AI 的 context。

## 限制

缺口是 AI 推理加上網路查證；「沒有工具」是指這次的搜尋沒找到，不保證完全不存在。解法還沒試過。

## Sources

- [Gumloop：Human in the Loop](https://docs.gumloop.com/core-concepts/human_in_the_loop)
- [Beam：Automation modes and Inbox](https://docs.beam.ai/03-running-operations/task-management/automation-modes/automation-modes)
- [LangChain Agent Inbox（agentmail）](https://ai.agentmail.to/langchain-agent-inbox-what-it-is-when-to-use-it-and-how-the-workflow-works)
- [hoop.dev：Action-Level Approvals](https://hoop.dev/blog/why-action-level-approvals-matter-for-ai-audit-trail-ai-enhanced-observability)
- [Gravitee：Provenance and Audit Trails for AI Agents](https://gravitee.io/corpus/gen-2245/neoserica-malaccana/provenance-and-audit-trails.html)
- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/what-are-agent-identities)
- [Okta for AI Agents（AI Magicx）](https://www.aimagicx.com/blog/okta-ai-agents-identity-permissions-2026)
- [Arxion：coordination for AI coding agents](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon/arxion/arxion-coordination-for-ai-coding-agents)
- [Telerik：Multi-agent orchestration](https://www.telerik.com/blogs/multi-agent-orchestration-software-delivery-patterns-multi-repository-workflows)
- [The Skill Atrophy Trap（tianpan.co）](https://tianpan.co/blog/2026-04-19-skill-atrophy-ai-augmented-engineering)
- [Renting Competence（ludentes）](https://ludentes.ru/posts/2026-05-03-renting-competence)
- [Stack Underflow: Losing the Craft of Coding（The New Atlantis）](https://thenewatlantis.com/publications/stack-underflow-losing-the-craft-of-coding)
