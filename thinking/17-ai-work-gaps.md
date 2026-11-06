# 17 大量使用 AI 的工程師：規則層的污染與覆蓋缺口

用 [16](16-model-selection.md) 選出的方式：06 收斂骨架當內容（目標鎖定 → 基準解 → 綁定假設與瓶頸 → 違反預設的差異；找不到就採用基準解 → 功能重述與局部修改 → 接受條件 → 適用範圍），雙向迴圈當動力。基準解逐一上網查證；連續兩組方向沒有新問題才停。查證日期 2026-11-07。

## 目標鎖定

工程師大量使用 AI。現有的規則架構（CLAUDE.md、rules、skills、記憶、提示詞）有污染、有覆蓋不到的地方：找出來，並找出至少在某個範圍內比現有做法好、或改善現有做法的解法。目的是讓整個 AI 工作方式更完善。

使用者的情境（用來找違反的假設）：infra 工作（k8s、遠端主機、prod 權限）、多個平行 session、AI 會讀工單、日誌、訊息等外部文字。

## 轉向紀錄

| # | 方向 | 新問題 | 轉向理由 |
|---|---|---|---|
| 1 | 規則的來源 ↔ 作用範圍 | P1 在一個情境學到的規則被套用到所有情境（全域 ↔ 專案；某次事故的教訓變成所有 session 的規則） | 有新的 → 換方向 |
| 2 | 寫入時 ↔ 讀取時 | P2 寫入時的脈絡（日期、原因、證據）讀取時已經遺失，規則和事實默默過期 | 有新的 |
| 3 | 規則 ↔ 實際行為 | P3 有些行為沒有規則覆蓋，而且看不見；P4 有些規則根本不影響行為，或一直被忽略 | 有新的 |
| 4 | 常駐 ↔ 按需載入 | P5 規則依檔案路徑或關鍵字載入，不依操作目標；P6 必須執行的程序（交接、prod 變更檢查）依賴模型自己決定要不要觸發 skill | 有新的 |
| 5 | 內部規則 ↔ 外部輸入 | P7 讀過外部文字的 session 寫進記憶或規則，讓污染持續到之後的每個 session（記憶中毒） | 有新的 |
| 6 | 單一 ↔ 多 session | 共用狀態、檔案、目標：13、15 和 `workflow` 分支已處理 | **第 1 次空轉** |
| 7 | 新增 ↔ 刪除 | 同 P4 | **第 2 次空轉，停止** |

另外兩個候選（子 agent 角色污染、MCP 工具描述佔 context）在方向 4 一起檢查，見下表。

## 逐一套用 06 骨架

| 問題 | 基準解（查證過的現有做法） | 基準解綁定的假設 | 在使用者情境是否被違反 | 結論 |
|---|---|---|---|---|
| P4 規則被忽略或沒作用 | misfire：從對話紀錄排出哪些規則最常被違反，建議移到 path 規則或改成 hook；agent-backtest：拿掉 CLAUDE.md 重播對話；記憶分析器標出重複、矛盾、無作用的規則 | 對話紀錄可以安全重播 | 部分：infra 指令有副作用，重播要沙盒 | **採用基準解**（misfire、agent-backtest）；重播 infra 指令時用 10 規劃的沙盒 |
| 子 agent 角色污染 | 子 agent 定義檔、`omitClaudeMd` | — | 沒有被違反 | **採用基準解** |
| MCP 工具描述佔 context | Claude Code 的工具搜尋、延遲載入 | — | 沒有被違反 | **採用基準解** |
| P3 看不見的覆蓋缺口 | Claude Code 內建 `/insights`：分析最近 30 天、最多 50 個 session，找出摩擦點並產生 CLAUDE.md 建議 | 50 個 session 能代表使用情況；建議的規則適用於全部工作 | **是**：平行 session 用量大，50 個可能只有幾天；產生的是全域規則，沒有標示是哪個目標、哪類任務學到的 | 局部修改 → 併入 T2 |
| P2 規則與事實過期 | stalebrain：替記憶檔做出處與衰退檢查，對照**目前的程式碼庫**；記憶分析器、agents-lint 等找過期內容 | 「真相」在 repo 裡 | **是**：infra 的事實（版本、節點數、主機設定、誰是 prod）在活的系統上，不在 repo 裡 | **T1** |
| P1 跨範圍污染 | 階層式載入；記憶分析器的「promote」；`/insights` 的建議 | 寫規則的人會選對層級；教訓大多是通用的 | **是**：平行處理多個目標時，很多教訓只適用某台主機或某個叢集 | **T2** |
| P7 記憶中毒 | 原則性防禦：出處標記、只允許指定的寫入者、寫入前檢查、審查關卡；evolveguard 做靜態的漂移檢查。Cisco 實測過讓 Claude Code 的記憶中毒並持續存在；ICML 2026 的研究指出現有提示注入防禦涵蓋不到記憶中毒 | 寫入記憶的 session 是可信的 | **是**：session 會讀工單、日誌、Teams 訊息 | **T2** |
| P6 必須執行的程序依賴觸發 | skill-creator 的描述優化（Anthropic 在 6 個 skill 中 5 個改善了觸發）；描述寫成指令式 | 由模型決定何時使用是對的 | **是**：交接、prod 變更檢查這類程序漏一次就出事，不該由模型決定；而且研究報告 skill 有 56% 的情況沒被叫用 | **T3** |
| P5 依目標載入規則 | SessionStart／UserPromptSubmit hook 依關鍵字注入規則；path 規則 | 從提示詞的關鍵字或檔案路徑推得出相關規則 | **是**：infra 的目標常是間接提到的（「那個 502」）；但 session 綁定的任務已經明確宣告了目標 | **T4**（改善幅度小） |

## 局部修改：四個工具

### T1：infra 事實的即時查核

- **基準解的瓶頸**：現有工具把事實對照 repo 查核，infra 的事實不在 repo 裡。
- **差異（可用的資源）**：TRUTH.md 本來就規定每個事實要附「怎麼查」的指令。
- **功能重述**：查詢指令可以變成自動查核器。
- **修改**：排程任務定期執行每個事實的唯讀查詢指令，結果和寫下的值不同就標記；SessionStart 時只顯示和這個 session 目標有關、已經漂移的事實。
- **接受條件**：先在 TRUTH.md 裡故意放入一些已知過期的事實；T1 抓得到，只對照 repo 的工具抓不到。拿掉「依查詢指令實際執行」，優勢就消失。
- **適用範圍**：有唯讀查詢指令可以驗證的 infra 事實。沒有查詢指令的事實不適用，仍用基準解。

### T2：帶出處的教訓流程

- **基準解的瓶頸**：教訓沒有出處和範圍，寫入者被當成可信。
- **差異**：session 已經綁定任務（`workflow` 分支），所以知道這次的目標、模式、有沒有讀過外部文字。
- **修改**：
  1. 每條教訓自動帶出處：任務、目標、日期、證據、這個 session 有沒有讀過外部文字。
  2. 讀過外部文字的 session 寫進記憶或規則檔時，hook 把它轉到隔離區，等人審查。
  3. 依範圍放置：只和某個目標有關的放進 `envs/<目標>/`，通用的才進 AGENTS.md。
  4. 擴大 `/insights` 的視野：把所有 session 的修正、拒絕、guard 的攔截都收進來，不受 50 個 session 的限制。
- **接受條件**：
  - 持續性測試：在一個讀過惡意工單的 session 裡嘗試寫入記憶，下一個新 session 不受影響；基準解（直接寫入記憶）會受影響。
  - 誤用測試：只適用 web1 的教訓，不會出現在處理 stg 的 session。
  - 拿掉出處標記，兩項優勢都消失。
- **適用範圍**：會讀外部輸入、或同時處理多個目標的工作。只有一個專案、不讀外部輸入的人，用基準解就夠。

### T3：必須執行的程序改由 hook 觸發

- **基準解的瓶頸**：skill 是否被叫用由模型決定，優化描述只能提高機率。
- **差異（改變的假設）**：少數程序一定要執行，不需要模型判斷「要不要」。
- **修改**：交接和 prod 變更檢查改由 hook 觸發。Stop hook 在任務仍是進行中、但 Claude 宣告完成時要求執行交接；PreToolUse 在 prod 變更前要求先有備份紀錄。skill 留給可有可無的程序。
- **接受條件**：同一批情境中，必須執行的程序實際被執行的比率：hook 版接近 100%，描述優化版明顯較低。拿掉 hook，比率就回到描述優化的水準。
- **適用範圍**：少數「漏一次就出事」的程序。其他 skill 繼續用描述優化。

### T4：依任務目標載入規則

- **修改**：SessionStart 和綁定任務時，依任務宣告的目標注入 `envs/<目標>/` 的規則，依模式注入對應的規則；不靠關鍵字猜。
- **接受條件**：間接提到目標的提示詞（「那個 502」）下，正確的規則有出現、無關的規則沒有出現的比率，高於關鍵字注入。
- **適用範圍**：目標已宣告的 infra 工作。優勢可能不大，優先順序最低。

## 優先順序

| 順序 | 工具 | 理由 |
|---|---|---|
| 1 | T2 帶出處的教訓流程 | 同時處理三個問題（P1、P3、P7）；記憶中毒有實證、現有防禦涵蓋不到 |
| 2 | T1 infra 事實查核 | 優勢最明確、最容易量測；TRUTH.md 已經有一半 |
| 3 | T3 hook 觸發必須執行的程序 | 實作小、效果可以直接量 |
| 4 | T4 依目標載入 | 改善幅度可能小 |
| — | 採用基準解 | misfire、agent-backtest、skill-creator、`/insights`、`omitClaudeMd`、工具搜尋、worktree、kubie |

T2、T4 建立在 `workflow` 分支的「session 綁定任務」上，那個分支因此有了用途。

## 這次執行的觀察

- 06 骨架的「找不到違反的假設就採用基準解」實際發揮了作用：9 個候選裡有 3 個直接採用現有工具，其他的也都只做局部修改。和 14、15 比，這次得到的是「要做什麼、不做什麼」都有理由的清單。
- 每個解法都寫出了接受條件和拿掉差異的檢驗，可以實際量測；但都還沒量，所以目前仍是假設。

## Sources

- [Claude Code /insights（Pasquale Pillitteri）](https://pasqualepillitteri.it/en/news/408/claude-code-insights-workflow-command)
- [/insights（angelo-lima）](https://angelo-lima.fr/en/claude-code-insights-command/)
- [/insights（wmedia）](https://wmedia.es/en/tips/claude-code-insights-command)
- [misfire（PyPI）](https://pypi.org/project/misfire/)
- [stalebrain（PyPI）](https://pypi.org/project/stalebrain/0.1.1/)
- [Analyze memory with Claude（nikiforovall）](https://nikiforovall.blog/claude-code-memory/guides/analyze/)
- [Keep CLAUDE.md and AGENTS.md from lying to your agent（mcp.directory）](https://mcp.directory/blog/claude-md-agents-md-maintenance-2026)
- [Claude Code auto memory audit（aident）](https://aident.ai/blog/audit-claude-code-auto-memory)
- [Persistent memory compromise in Claude Code（Cisco）](https://blogs.cisco.com/ai/identifying-and-remediating-a-persistent-memory-compromise-in-claude-code)
- [From Untrusted Input to Trusted Memory（ICML 2026）](https://icml.cc/virtual/2026/67964)
- [Memory and State Poisoning in Long-Running Agents（Arthur）](https://www.arthur.ai/column/memory-and-state-poisoning-in-long-running-agents)
- [Your Agent's Memory Is a Liability（Level Up Coding）](https://levelup.gitconnected.com/your-agents-memory-is-a-liability-defending-against-context-poisoning-in-persistent-ai-systems-d9df735244ba)
- [Smart context injection（CodeSignal）](https://codesignal.com/learn/courses/automating-workflows-with-hooks/lessons/smart-context-injection)
- [Claude Code hooks guide（MLOps Community）](https://mlops.community/blog/the-complete-guide-to-claude-code-hooks-automating-your-ai-coding-workflow)
- [Skills without evals are just markdown and hope（DEV）](https://dev.to/danielsogl/skills-without-evals-are-just-markdown-and-hope-3a71)
- [Why Claude Code skills don't trigger（DEV）](https://dev.to/lizechengnet/why-claude-code-skills-dont-trigger-and-how-to-fix-them-in-2026-o7h)
- [skill-creator run_eval issue](https://claudeissues.com/issue/87915-skill-creator-run-eval-py-writes-skills-to-claude-commands-so-description-optimi)
- 10、14、15 的來源（agent-backtest、evolveguard、worktree、kubie、子 agent 文件等）
