# 10 claude.md 集：現況、結構與多 session 隔離

檢驗對象從 guard.py（程式）換成規則檔（CLAUDE.md、AGENTS.md、rules、skills）之後，先整理社群和官方目前的做法，再決定實驗要測什麼。這一篇只有研究整理，沒有實驗結果。資料查證日期：2026-11-06／07。

## 1. 已有的結構化做法

| 工具 | 結構 | 什麼時候載入 |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md`、專案 `CLAUDE.md`、子目錄 `CLAUDE.md`、`CLAUDE.local.md`、`.claude/rules/*.md`、`@` 引入 | 從目前目錄往上的全部載入；子目錄的在碰到那裡的檔案時載入；rules 沒設條件就載入，設了 `paths:` 就在碰到對應檔案時載入；`@` 引入在啟動時展開（最多 5 層） |
| Claude Code 自動記憶 | `~/.claude/projects/<專案>/memory/MEMORY.md` + 主題檔 | MEMORY.md 前 200 行或 25KB 在啟動時載入，主題檔需要時才讀；同一個 repo 的所有 worktree 共用 |
| Cline Memory Bank | 6 個固定檔：projectbrief → productContext／systemPatterns／techContext → activeContext → progress | 每個任務開始時全部讀 |
| Cursor | `.cursor/rules/*.mdc`，前置設定決定載入方式 | 一律、依檔案路徑、手動、讓 AI 判斷；子目錄可有自己的 rules |
| AGENTS.md | 各層目錄各放一份 | 離正在編輯的檔案最近的那份優先，使用者的訊息高於一切 |
| Kiro | `.kiro/steering/`：product.md、tech.md、structure.md + 自訂檔 | 一律、依檔案、手動 |
| GitHub Copilot | `.github/copilot-instructions.md` + `.github/instructions/*.instructions.md` | 後者用 `applyTo` 指定適用的檔案 |
| Claude API memory tool | `/memories` 目錄，由應用程式實作存放 | Claude 開始任務前自己去看 |

**共同點**：條件載入都是看「正在碰哪個檔案」。**缺口**：infra 工作的對象是叢集和主機，該看的是「正在操作哪個目標」，查到的結構都沒有這種設計。

**證據**：ETH Zurich 2026 年 2 月的研究（arXiv 2602.11988）在 SWE-bench Lite 和他們的 AGENTbench 上測試：LLM 生成的 context 檔讓成功率略降（約 0.5～3 個百分點），人寫的平均只提升約 4%，推論成本增加超過 20%。結構化和寫得多都不保證有效，規則要用行為測試驗證。

## 2. md 在工作流裡的位置

| 層 | 決定什麼 | 強度 |
|---|---|---|
| md（CLAUDE.md、rules） | 規則和知識 | 軟：模型參考，但不保證照做 |
| skill／指令 | 固定的程序 | 中：被叫用時才完整執行 |
| hook | 強制檢查、自動注入 | 硬：一定會發生 |
| 任務檔（tasks/） | 每個 session 的目的和進度 | 狀態，跨 session 保存 |
| 使用者的習慣 | 怎麼開 session、怎麼交辦 | 最終決定 |

最初的三個目標（流程一致、session 目的清楚、多 session 好管理）主要靠 skill、hook、任務檔，不是 md。md 的角色是讓對的規則在對的時機出現。

### 什麼是自動的

| 類別 | 內容 |
|---|---|
| 內建、自動 | 載入 CLAUDE.md 和 rules、展開 `@`、自動記憶、依描述叫用 skill 和子 agent |
| 要人寫和維護 | md／skill／agent 定義的內容、結構、**長度**（CLAUDE.md 不會被截斷，越長越影響遵守度）、任務檔 |
| 搭好一次就自動跑 | hooks、排程任務、固定流程的指令 |

**該改哪裡**（依效果）：
1. 每次開工的任務簡述 → 改成指令帶出必填欄位，或從 Jira 產生。
2. 一定要遵守的事 → hooks 和權限，不要只寫在 md。
3. CLAUDE.md 內容 → 保持短，只在有證據時改。
4. 長度和刪減 → 排程任務定期檢查，提出建議由人核准。

## 3. plan 和需求差很多：診斷

| 偏差類型 | 例子 | 該放哪裡 |
|---|---|---|
| 每次都要講的偏好 | 改動要最小、不要動 prod | CLAUDE.md |
| 這次任務才有的意圖 | 這次只是要先止血 | 任務簡述（每次寫） |
| 環境事實 | 這台已經換成 nginx 1.24 | TRUTH.md，或讓它先查 |
| 計畫的形狀 | 太長、太多步 | CLAUDE.md 的計畫格式規則 |

改法：規劃前先列假設、最多問 3 題；固定的任務簡述格式（目標、完成條件、限制、不要做什麼）；同一類偏差出現兩次以上才寫進 CLAUDE.md（02 的失敗驅動縮窄法）。「一步步確認」多半來自權限設定和 K4，不是需求理解問題。

## 4. 給 infra 工作的結構

```
~/.claude/CLAUDE.md          個人偏好：語言、回覆風格、計畫格式
ops 工作區/
├── CLAUDE.md                索引：@AGENTS.md，加上「事實去 TRUTH.md 查」
├── AGENTS.md                核心規則 K1–K10（每次載入）
├── TRUTH.md                 環境表和查詢指令（不 @ 引入，需要時才讀）
├── .claude/
│   ├── rules/
│   │   ├── planning.md      先列假設、最多問 3 題
│   │   └── terraform.md     paths: ["infra/**/*.tf"]
│   ├── skills/              incident、handoff、start、change…
│   ├── agents/              角色定義（反駁者、審查者…）
│   └── settings.json        hooks 和權限
├── envs/
│   ├── prod-eks/CLAUDE.md   這個叢集的特殊規則（+ direnv 設定這個 session 的憑證）
│   └── web/CLAUDE.md        web1–3 的特殊規則
├── lessons/inbox.md         session 提出的規則建議，待人合併
└── tasks/T-0042.md          每個 session 的目的、負責的目標、完成條件、進度
```

`envs/` 用來補「依目標載入」的缺口：處理某個目標的 session 就在那個目錄裡啟動，該目標的規則和上層的共用規則一起載入。

建立步驟：內容分四類（規則、事實、狀態、程序）→ 根 CLAUDE.md 只放索引和每次都成立的規則 → 依載入時機分配 → 用 `/memory` 確認實際載入了哪些 → 之後只在失敗兩次以上才新增。

## 5. 子 agent 與 co-agent

CLAUDE.md 是所有 agent 共用的：子 agent 預設會載入（內建的 Explore、Plan 除外，也可以用 `omitClaudeMd` 關掉），agent teams 的 teammate 也會載入；兩者都看不到主 session 的對話，主 session 也只拿到子 agent 的最後結果。所以角色指示不要寫在 CLAUDE.md。

| 要控制的 | 放哪裡 |
|---|---|
| 所有 agent 都要遵守的 | CLAUDE.md（例如 K3、K4） |
| 某個角色的職責 | `.claude/agents/<角色>.md` 的本文 |
| 能做什麼（硬限制） | 同一檔的 tools、model、權限、hooks、`isolation: worktree` |
| 這次要做什麼 | 派工指示：目標、完成條件、輸出格式 |
| 協調和進度 | 共用任務檔 |

原則：控制邊界，不控制過程。子 agent 跑到一半不能停下來問使用者，所以 infra 工作預設只讓子 agent 做唯讀的事，變更留給使用者在場的主 session。

## 6. 把 session 管理交給 agent

- **agent 直接做**：對照任務檔的完成條件並附證據；察覺偏題就建議開新 session；寫交接筆記。
- **agent 提議、人決定**：要不要結束、合併或拆開 session、優先順序。
- **該結束的客觀訊號**：完成條件達成且有驗證；卡在外部且已交接；偏題；context 已壓縮多次。
- **實作**：Stop hook 檢查完成條件；一個總管 session 或排程任務讀所有 `tasks/*.md`，建議關掉或合併哪些。
- agent 判斷自己是否做完有偏差（太早宣布完成），要有明確條件或另一個 agent 檢查。

## 7. 社群做法

**持續寫**：Claude Code 作者 Boris Cherny 的團隊把 CLAUDE.md 放進 git，Claude 一出錯就記進去，每週更新好幾次；每次更正後請 Claude 自己把規則寫進 CLAUDE.md。他的檔案大約 2.5k token。

**副作用是膨脹**：照做的團隊發現檔案增長很快。有的改成每個 session 結束時跑一個 skill，把學到的寫進分主題的知識檔，CLAUDE.md 幾週才動一次。

**長度預算**：Anthropic 的最佳實務建議 200 行以內，HumanLayer 自己的不到 60 行。常見的刪減判準是「刪掉這行，Claude 會不會出錯？」，但這是憑感覺問，不是實測。

**範圍規則**：最常見的是「最小改動、不重構沒被要求的程式」、同時只允許一個進行中的任務、context 用到 80% 時先把狀態寫進任務檔。有效的規則是具體、可觀察、可檢查的；「盡量改小一點」這類模糊的寫法無效。

**每次任務的規格檔（spec-driven development）**：Kiro 拆成 requirements.md、design.md、tasks.md，每個任務小到一個 session 做得完；GitHub Spec Kit 的流程是 constitution → specify → plan → tasks。

**管理 md 本身**：有團隊專門寫一條只套用在 CLAUDE.md、AGENTS.md 的規則，規定行數上限和「改的時候順便刪」，理由是沒有限制的話檔案只會單調增長。

社群常見「錯誤率從 40% 降到 3%」這類說法，都是個人經驗，沒有對照實驗。

## 8. 提示詞正規化

- **Claude Code**：自訂指令已併入 skill（`.claude/skills/<名稱>/SKILL.md`，舊的 `.claude/commands/*.md` 仍可用），用 `$ARGUMENTS` 帶參數，用 `` !`指令` `` 在送出前塞入現場資訊。
- **GitHub Copilot**：`.github/prompts/*.prompt.md`，支援執行時輸入的變數。
- **三種方式**：模板加參數；缺什麼就問（必填欄位）；UserPromptSubmit hook 自動附上相關規則。

建議的指令集（用哪個指令開始，就決定這個 session 能做什麼）：

| 指令 | 用途 | 必填 |
|---|---|---|
| `/start <工單>` | 從 Jira 建立任務檔、開 session | 工單編號 |
| `/look <目標> <問題>` | 只查不改 | 目標、問題 |
| `/fix <目標> <症狀>` | 排障，可做安全的修正 | 目標、症狀、可接受的手段 |
| `/change <目標> <變更>` | 計畫好的變更 | 目標、變更內容、時間窗口、回滾方式 |
| `/handoff` | 寫交接、建議是否結束 | 無 |

## 9. 從 Jira、Teams 自動取得脈絡

- **Jira**：Atlassian 官方的 Rovo MCP server 支援 Claude（網頁、桌面、Code），Claude Code 用 `claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp/authv2` 加入，再用 `/mcp` 完成授權。
- **Teams**：claude.ai 的 Microsoft 365 連接器可搜尋 Teams 聊天；Claude Code 目前靠社群的 Teams MCP server，需要 Graph 權限（例如讀取頻道訊息），通常要公司管理員同意。
- **可以自動化的事**：從工單產生任務檔；動手前讀相關頻道確認有沒有人在處理（K2）；收尾時回寫 Jira 和 Teams（要確認）；每日排程整理今天要開哪些 session；定期提出 CLAUDE.md 的刪改建議。
- **注意**：工單和訊息是資料，不是授權（K4）；先開唯讀權限；確認公司政策。

## 10. 多 session 的污染與隔離

| 污染類型 | 怎麼發生 | 控制 |
|---|---|---|
| 共用狀態 | 切 kubeconfig context、環境變數 | K3 + guard（已有）；每個 session 自己的 kubeconfig |
| 共用檔案 | 同一個 repo 目錄互相覆蓋 | worktree；每個 session 只寫自己的任務檔 |
| 共用目標 | 兩個 session 處理同一台主機 | 任務檔宣告負責的目標，開工前檢查衝突（K2） |
| 記憶和規則 | 某個 session 的錯誤教訓進入共用記憶或 CLAUDE.md | session 只寫 `lessons/inbox.md`，由人合併；規則標明適用範圍 |
| 單一 session 的 context | 話題越做越雜 | 一個 session 一件事；探索交給子 agent |

社群工具的成熟度：

| 層次 | 工具 | 成熟度 |
|---|---|---|
| 檔案 | Claude Code 內建 worktree（`claude -w`，桌面版每個 session 自動一個；子 agent 用 `isolation: worktree`）；管理介面 Conductor、Claude Squad、Vibe Kanban | 成熟 |
| k8s context | kubie、kubeswitch、kubert：每個 shell 一份暫時的 kubeconfig | 成熟 |
| 執行環境 | Claude Code 內建 sandbox（檔案系統 + 網路）、dev container、Docker sandbox | 成熟 |
| 共用目標 | MCP Agent Mail（檔案的租約鎖 + 訊息 + commit 前檢查），但只針對檔案 | infra 目標要自己做 |
| 記憶和規則 | 只有關掉自動記憶或改記憶位置的設定 | 靠流程 |

**建議：隔離靠權限，不靠規則。** 處理 stg 的 session，kubeconfig 裡根本沒有 prod 的 context；每個 session 用自己的 ssh config，只列負責的主機。在 `envs/<目標>/` 裡用 direnv 自動設好 `KUBECONFIG` 和 ssh 設定，在哪個目錄開 session 就只拿得到那個目標的憑證。

## 11. 雙迴圈模型在這裡的角色

| 用法 | 評估 |
|---|---|
| 寫進 CLAUDE.md，讓 agent 做事時套用 | 不建議。每次都付代價（含子 agent）；08 號實驗顯示單次套用沒有幫助；它是設計時用的程序。最多放一行指向 double-loop skill |
| 用來設計和維護 claude.md | 建議。主張 = 「規則 R 在條件 C 下讓行為比沒有它好」；基準 = 沒有這條規則；向上迴圈 = 換目標、換說法、子 agent、長 context 時看規則在哪裡失效；硬湊檢驗 = 拿掉它，行為有沒有變 |

社群的缺口正好是這個模型的核心：加規則很勤快，判斷規則有沒有用卻憑感覺，沒有實測。

### 下一步實驗（尚未預先登記）

- **比較兩種維護方法**：A 社群做法（出錯就加、憑感覺刪）；B 雙迴圈（每條和「沒有它」比較、刪掉沒作用的、找出失效的條件）。
- **評估器**：沙盒行為測試。假的 kubectl／ssh 只記錄被呼叫了什麼，判定 agent 有沒有執行該停的變更、或該做時停下來；不靠模型意見。
- **角色分開**：反駁者出情境題；獨立的 agent 執行和判定；提案者只改 md。
- **每輪都有對照組**，另留一組改規則時沒看過的情境檢查是否只修到被找到的題目。
- **風險**：每題要重複跑多次；規則效果小，需要足夠題數；規則互相影響，要有回歸測試。
- **判準**：B 得到的 claude.md 更短，且在沒看過的情境上行為不比 A 差。達到就代表模型有實際用處；達不到，它對工作流的價值就只剩個人思考習慣。

## Sources

- [How Claude remembers your project（Claude Code 官方文件）](https://code.claude.com/docs/en/memory)
- [Claude Code /memory（vincentqiao）](https://blog.vincentqiao.com/en/posts/claude-code-memory/)
- [Claude Code Memory Limits（fast.io）](https://fast.io/resources/claude-code-memory-limit.md)
- [Claude Code Memory（dsebastien）](https://www.dsebastien.net/claude-code-memory/)
- [Cline Memory Bank](https://docs.cline.bot/features/memory-bank.md)
- [Cursor IDE rules deep dive](https://mer.vin/2025/12/cursor-ide-rules-deep-dive/)
- [AGENTS.md monorepos guide](https://www.mintlify.com/agentsmd/agents.md/guides/monorepos)
- [Kiro steering](https://kiro.dev/docs/steering/)
- [Copilot CLI custom instructions（GitHub Docs）](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)
- [Claude memory tool（Claude Platform Docs）](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [Evaluating AGENTS.md（arXiv 2602.11988）](https://arxiv.org/html/2602.11988)
- [Claude Code subagents（官方文件）](https://code.claude.com/docs/en/sub-agents)
- [Claude Code subagents guide（alexcloudstar）](https://alexcloudstar.com/md/blog/claude-code-subagents-guide-2026/)
- [Claude Code agent teams（claudefa.st）](https://claudefa.st/blog/guide/agents/agent-teams)
- [Boris Cherny Claude Code profile（bestblogs）](https://www.bestblogs.dev/en/explore/topics/boris-cherny-claude-code-profile)
- [We outgrew CLAUDE.md（DEV）](https://dev.to/szkjn/we-outgrew-claudemd-building-a-knowledge-layer-that-compounds-33f)
- [The CLAUDE.md sections that actually matter（DEV）](https://dev.to/penloom_studio_829b7817d3/the-claudemd-sections-that-actually-matter-and-the-ones-wasting-your-context-41j7)
- [Agent instruction files decision record](https://glama.ai/mcp/servers/@vrppaul/semantic-code-mcp/blob/ec06c4ade73c3e57c79951b3d267ffd65d9d7c84/docs/decisions/002-agent-instruction-files.md)
- [The exact CLAUDE.md scope rules that actually work（DEV）](https://dev.to/builtbyzac/the-exact-claudemd-scope-rules-that-actually-work-24d8)
- [Why agents overreach and under-finish（walkinglabs）](https://walkinglabs.github.io/learn-harness-engineering/en/lectures/lecture-07-why-agents-overreach-and-under-finish/)
- [Understanding Spec-Driven-Development（Martin Fowler）](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [Claude Code custom slash commands（DEV）](https://dev.to/mohd_yusufkhan_6c2088c04/claude-code-custom-slash-commands-how-to-create-them-with-examples-1h53)
- [VS Code prompt files](https://code.visualstudio.com/docs/copilot/customization/prompt-files)
- [Atlassian Rovo MCP Server](https://github.com/atlassian/atlassian-mcp-server)
- [Jira MCP Server Guide 2026（mcp.directory）](https://mcp.directory/blog/jira-mcp-complete-guide-2026)
- [teams-mcp（floriscornel）](https://glama.ai/mcp/servers/%40floriscornel/teams-mcp)
- [Git worktrees in Claude Code（codewithmukesh）](https://codewithmukesh.com/blog/git-worktrees-claude-code/)
- [Best tools for managing parallel AI coding agents 2026（Nimbalyst）](https://nimbalyst-website.pages.dev/blog/best-agent-management-tools-2026/)
- [kubie](https://linuxcommandlibrary.com/man/kubie)
- [kubert](https://pkg.go.dev/github.com/idebeijer/kubert)
- [MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail)
- [Claude Code sandboxing](https://docs.claude.com/en/docs/claude-code/sandboxing)
