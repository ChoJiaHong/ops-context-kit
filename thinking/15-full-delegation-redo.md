# 15 重跑：全部交給 AI 的缺口（完整紀錄）

[14](14-full-delegation-gap.md) 的雙向迴圈沒有做好：只有一組方向、只來回一次、找到第一個強的缺口就停（正是雙向迴圈要防止的毛病）、沒有逐步紀錄、查證太粗、沒有按重要性排序。這一篇重跑。

**這次的規則**（由執行的 AI 自己定）：多組方向；每組至少來回兩次；每次轉向都記錄；**連續兩組方向沒有新缺口才停**；新候選逐一上網查證；最後依「對使用者的影響 × 現有工具覆蓋不到的程度」排序。查證日期 2026-11-07。

## 轉向紀錄

| # | 方向 | 新發現 | 轉向或停止的理由 |
|---|---|---|---|
| 1 | 職責 → 承擔者（14 的那一趟） | 理解與技能回不到人身上 | 只有 7 項職責，清單來自 AI 的直覺，不完整 → 擴充後再跑 |
| 2 | 承擔者 → 職責（14 的反向） | 核准變反射、記憶不回到人 | 同上 |
| 3 | 職責 → 承擔者（擴充到 16 項：值班、事故指揮、容量、成本、資安修補與合規、變更管理、事後檢討、文件、帶新人、對外承諾、選工具、管理 AI 本身、拒絕不合理需求…） | (a) 「管理 AI 本身」變成新職責：設定、升級、回歸、成本；(b) 帶新人沒人接；(c) AI 不在時的事故指揮沒人接 | 正向找到三個新的 → 換反向 |
| 4 | 工具 → 丟掉了什麼（第二趟） | Jira／Teams 連接器把「外部文字」變成 agent 的輸入，丟掉了信任邊界（注入）；模型備援 gateway 只備援模型，沒備援人；評估工具只測沒有副作用的行為 | 有新的 → 換一組方向 |
| 5 | 平時 → 出事 | 三種出事：AI 不在、AI 被入侵、AI 默默做錯 | 有新的（「被入侵」）→ 反向 |
| 6 | 出事 → 平時要先準備什麼 | 演練、用權限限制爆炸範圍、能力維持 | 和前面合併，沒有全新的 → 換一組 |
| 7 | 現在 → 兩年後 | 模型升級改變行為；記憶和規則腐爛；技能退化累積；新人從沒建立能力 | 「模型升級改變行為」是新的 → 反向 |
| 8 | 兩年後 → 現在要做什麼 | 回歸測試、能力帳本、知識審查 | 沒有全新的 → 換一組 |
| 9 | 個人 → 團隊 | 跨人的 agent 協調（infra 目標）；新人培養 | 前面已有，沒有新的 |
| 10 | AI 需要但拿不到 ↔ 人需要但拿不到 | 沒寫下來的脈絡（會議、走廊）；AI 問同事 | 只有部分覆蓋的，沒有新的 → **第 1 次空轉** |
| 11 | 輸入 ↔ 輸出 | 輸入：不可信文字（同 #4）；輸出：多到人審不完（同核准問題） | 沒有新的 → **第 2 次空轉，停止** |

## 查證

| 候選缺口 | 現有工具或狀況 | 判斷 |
|---|---|---|
| 核准集中、排序、批次 | Beam、Gumloop、LangChain Agent Inbox、hoop.dev（見 14） | 已覆蓋 |
| 決策追溯、agent 身分 | AI gateway、Entra Agent ID、Okta for AI Agents（見 14） | 已覆蓋（企業級） |
| AI 服務中斷 | 有模型層的備援：fallback 模型鏈、gateway 轉到 Bedrock／Vertex 或其他供應商；也有 Claude API 中斷的事故處理 skill | 模型層已覆蓋；**人接不接得住沒有覆蓋** |
| 模型或版本升級改變行為 | Anthropic 的 skill-creator 加入 eval 和模型更新後的 benchmark；agent-backtest 重播 Claude Code 的對話紀錄；evolveguard 檢查 SKILL.md／MEMORY.md 改動後的漂移 | 部分覆蓋：都偏向沒有副作用的行為，infra 變更要沙盒 |
| 經由工單、訊息、日誌的提示注入 | 有分類器、gateway、工具呼叫白名單等防禦；但業界公認未解決，針對防禦調整過的攻擊成功率很高 | 有工具，但**問題本身未解** |
| AI 問同事並等待回覆 | Claude Code 的 Slack 整合 skill（提問、等待回覆）；Slack Code；Vercel 的 Slack agent 範本 | 部分覆蓋（偏 Slack） |
| 跨人的 agent 協調 | Arxion、Progress Forge 等，以程式碼為主（見 14） | 部分覆蓋 |
| 理解、技能、AI 不在時的接手、新人培養 | 只有文章和個人做法 | **沒有工具** |

## 依重要性排序的缺口

排序依據：對這位使用者（infra、prod 權限、平行 session、在意效率）的影響 × 現有工具覆蓋不到的程度。

| 排名 | 缺口 | 覆蓋 | 為什麼排這裡 |
|---|---|---|---|
| 1 | **人接不住**：理解債、技能退化、AI 不在時沒人能接手、新人從沒建立能力 | 沒有工具 | 出事時一定會用到；越委派越嚴重；沒有任何工具在處理 |
| 2 | **被入侵的 agent 拿著 prod 權限**：全部交給 AI 之後，它讀所有工單、訊息、日誌，又拿著你的憑證 | 有防禦，但問題未解 | 影響最大（prod），但已有一部分工具，所以排第二 |
| 3 | **AI 本身會變**：模型或 Claude Code 升級、記憶與規則腐爛，讓整套工作流默默改變 | 部分 | 一定會發生；現有工具偏向沒有副作用的行為 |
| 4 | **跨人的 agent 協調**（infra 目標） | 部分 | 團隊規模才會碰到 |
| 5 | **沒寫下來的脈絡、AI 問同事** | 部分 | 有工具可用（Slack），Teams 較少 |

已覆蓋、直接採用現有工具即可：核准收件匣、決策追溯、agent 身分。

## 每個缺口的解法方向（巢狀：缺口 ↔ 工具）

1. **人接不住** → 理解回流（見 14：接手卡、能力帳本、理解債），再加兩項：
   - **AI 不在的演練**：定期在沙盒重播真實事故，限制只能用人工。
   - **新人模式**：新人的任務預設用教練模式，由新人先做。
   - 反向檢查：增加人的負擔 → 只對高風險工作、只對選定要保留的技能、設時間上限。
2. **被入侵** → 假設一定會被入侵，限制爆炸範圍：
   - 寫入憑證只給任務檔宣告的目標，延續 13 的「憑證分讀寫」。
   - 讀了外部文字（工單、訊息、網頁）的 session，預設拿不到寫入憑證；要寫入時，由人確認一次。
   - 這和 1、3 共用同一個機制：任務檔驅動的 session 權限。
3. **AI 本身會變** → 沙盒行為回歸測試，這正是 10 規劃的實驗。每次模型或 Claude Code 升級後重跑；用 skill-creator 的 benchmark 補沒有副作用的部分。
4. **跨人協調** → 任務檔的 targets 宣告擴大到團隊共用：寫入前檢查別人的 agent 有沒有宣告同一個目標。
5. **沒寫下的脈絡** → 讓 agent 透過 Teams 或 Slack 問負責人並等待回覆；會議紀錄透過連接器讀取。

## 意義

- 整個生態都在投資「讓 AI 懂系統、讓 AI 被管住」。全部交給 AI 之後，真正沒人處理的，是人這一端（接不住）和 AI 本身的變化。
- 前三名的解法共用同一個核心：**任務檔驅動 session 的權限和流程**。這和 12、13 對 kit 的結論一致，是從兩個不同問題得到的同一個答案。

## 這次執行的觀察

- 第 1、2 趟（14）只找到 1 個缺口；擴充職責清單並換方向後，增加到 5 個有排序的缺口，其中「被入侵」「AI 本身會變」是 14 完全沒碰到的。
- 有效的改變是：停止條件改成「連續兩組空轉」，並且每個候選都查證。
- 仍然是 AI 自己評自己，而且「沒有工具」只代表這次的搜尋沒找到。

## Sources

- 14 的全部來源
- [Claude AI outage（Cybersecurity News）](https://cybersecuritynews.com/claude-ai-faces-outage/)
- [Claude Code rate limits, 529 errors and outages（Maxim）](https://www.getmaxim.ai/articles/claude-code-rate-limits-529-errors-outages.md)
- [Anthropic incident runbook skill](https://claudeskills.info/skills/jeremylongshore/claude-code-plugins-plus-skills/anth-incident-runbook/)
- [Improving skill-creator（Claude blog）](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills)
- [Backtesting AI agents（agent-backtest）](https://dikrana.netlify.app/blog/backtesting-ai-agents)
- [evolveguard（PyPI）](https://pypi.org/project/evolveguard-cli/)
- [Claude Opus 4.7 breaks production agentic workflows（AI Weekly）](https://aiweekly.co/alerts/claude-opus-47-breaks-production-agentic-workflows)
- [Slack integration for Claude Code（MCP Market）](https://mcpmarket.com/ja/tools/skills/slack-integration-for-claude-code)
- [Slack Code（Gizmodo）](https://gizmodo.com/slack-has-of-course-launched-a-vibe-coding-tool-1851345396)
- [Prompt injection guide 2026（Sysdig）](https://www.sysdig.com/learn-cloud-native/prompt-injection)
- [Indirect prompt injection in coding agents（Context7）](https://context7.com/guides/prompt-injection-coding-agents)
- [Coding agents vulnerable to prompt injection via comments（SecurityWeek via Pulse）](https://www.pulse.bot/cybersecurity/news/claude-code-gemini-cli-github-copilot-agents-vulnerable-to-prompt-injection-via-comments-8045c250-964a-4008-a307-78141b2d0d11/)
