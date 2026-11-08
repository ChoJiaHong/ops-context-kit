# 問題（截至 2026-11-08）

每個問題都來自代理程式（agent）工具儲存庫（repository）上未關閉的 GitHub 議題（issue）。「現有做法」與「已知缺點」由兩位獨立的檢查者收集（thinking/24）；連結均為第三方頁面。

## P1（F01）：代理程式執行框架（harness）洩漏工程師的個人身分

問題：讓代理程式搜尋或擷取網頁的工程師發現，執行框架未經詢問，就把他們的帳號電子郵件放進送往任意網站的對外請求標頭（header）中，而且每個工作階段（session）還會把它注入模型的系統提示詞（system prompt）。他們的身分流向自己從未選擇的第三方（一位回報者把它和每天收到的詐騙郵件連結在一起）。因此，委派網路研究會悄悄付出隱私代價。

需求：未關閉的議題上共有 1058 個反應（reaction）。

現有做法：
- Claude Code 內建 cc-plugin-privacy 模組（mod）（v2.1.317+）（0 顆星，2026-11-05）：預設啟用的內建模組。在含有帳號電子郵件的網頁工具呼叫或 curl 類指令執行前，加以阻擋或先行詢問。官方人員也表示，電子郵件將在即將推出的版本中從模型上下文（context）移除。<https://github.com/anthropics/claude-code/issues/107757>
- klavdiy-core/pii-tripwire（0 顆星，2026-10-24）：Claude Code 鉤子（hook），阻止使用者列出的一組電子郵件、電話號碼與身分證件號碼，經由對外的工具呼叫流出。<https://github.com/klavdiy-core/pii-tripwire>
- Claude Code 內建隱私模組 cc-plugin-privacy（v2.1.317+）（0 顆星，2026-11-04）：官方檢查機制。網頁或 shell 工具呼叫的輸入含有已登入帳號的電子郵件時，在送往網路之前會先詢問（無頭（headless）模式下則直接拒絕）；預設啟用。一位貢獻者在主討論串中確認了這點（https:/ <https://github.com/anthropics/claude-code/issues/107144>
- AlexErrant/claude-code-no-email（71 顆星，2026-10-29）：模組／鉤子，從 Claude Code 傳給模型的上下文中移除 userEmail 區塊，藉此消除標頭洩漏的來源。<https://github.com/AlexErrant/claude-code-no-email>
- NobleCodeSoftware/claude-pii-guard（0 顆星，2026-11-06）：本機 PreToolUse 鉤子，偵測工具呼叫中的電子郵件與其他個人識別資訊（PII），提供阻擋、詢問或警告三種模式。<https://github.com/NobleCodeSoftware/claude-pii-guard>
- princejain756/egressleak（0 顆星，2026-11-06）：稽核工具，針對 Claude Code、Codex CLI 與 MCP 設定，檢查對外 HTTP 流量（egress）、User-Agent 電子郵件洩漏（#107757），以及上下文中的 PII。<https://github.com/princejain756/egressleak>

已知缺點：
- 帳號電子郵件仍會被注入系統提示詞，且無法選擇退出（自 2026-07 起未關閉）。截至最新留言，承諾的移除尚未推出，而穩定版通道仍停在 2.1.311，沒有這個模組。<https://github.com/anthropics/claude-code/issues/81138>
- 留言者回報，在 2.1.317/2.1.318 上，隱私模組並未拒絕一個含有電子郵件的測試指令。官方人員承認，它不涵蓋 Claude 自行撰寫並執行的腳本。<https://github.com/anthropics/claude-code/issues/107757>
- 帳號電子郵件檢查會誤判（false positive）：在無頭模式執行時，它會拒絕只在本機進行的 Bash 呼叫，例如 heredoc 寫入，以及對 127.0.0.1 的 curl。<https://github.com/anthropics/claude-code/issues/107144>
- 子代理程式（subagent）會把電子郵件放進送往 sec.gov 與 bls.gov 的 curl User-Agent 標頭，即使系統提示詞要求它們不要把它傳給無關的服務。<https://github.com/anthropics/claude-code/issues/106012>
- 議題討論串中引用了一位 Claude Code 員工的說法：2.1.317 的檢查並未涵蓋所有情況，例如 Claude 自行撰寫並執行的腳本。從模型上下文移除電子郵件，已承諾在之後的版本推出，而這項檢查 foun <https://github.com/anthropics/claude-code/issues/107757>
- 內建檢查是比對電子郵件地址加上與網路相關的字詞。因此在無頭的略過權限（bypass）模式執行中，它會拒絕只在本機進行的呼叫（heredoc 檔案寫入、對 127.0.0.1 的 curl），而且該次執行仍以成功結束。唯一的關閉方式是停用整個隱私外掛（plugin） <https://github.com/anthropics/claude-code/issues/107144>
- 每個工作階段仍會把帳號電子郵件注入系統提示詞，且沒有官方支援的退出方式。IS_DEMO 只會隱藏顯示介面。模型也曾把這個地址寫進提交（commit）中。<https://github.com/anthropics/claude-code/issues/81138>
- 在 Team/Enterprise 登入或套用受管理設定（managed settings）的機器上，claude-code-no-email 模組沒有任何作用。因為在這些情況下，內建防護會略過使用者模組的 prompt.context 鉤子。<https://github.com/AlexErrant/claude-code-no-email/issues/1>
- 以鉤子實作的權宜做法只比對完全相同的字串，可能漏掉編碼過的形式；而提示詞規則也沒能防止一起已回報的洩漏。<https://explainx.ai/blog/claude-code-leaks-your-email-user-agent-header-how-to-stop-it-2026>

## P2（F11）：權限行為與工程師的設定不符

問題：已經決定代理程式可以做什麼的工程師發現，權限系統並未遵循這個決定：允許與拒絕規則（allow/deny rules）的比對不可靠；複合指令會在無害的 `cd` 上跳出權限詢問（permission prompt）；一般帶引號的旗標（flag）會觸發新的警告；技能（skill）與子代理程式會忽略使用者層級的允許規則；略過權限（skip-permissions）或 yolo 模式仍會跳出詢問；每個新專案都需要各自的信任核准；工作區政策檔則在沒有任何提示的情況下不生效。無人值守的執行會卡在權限詢問上。工程師也無法確定自己寫的規則就是實際執行的規則，因此有些人在自己的鉤子裡重新實作權限控管。

需求：未關閉的議題上共有 683 個反應。

現有做法：
- ldayton/Dippy（244 顆星，2026-06-12）：PreToolUse 鉤子，解析 shell 指令（包括複合指令），並依使用者規則自動核准安全的指令 <https://github.com/ldayton/Dippy>
- kornysietsma/tool-gate-hook（41 顆星，2026-10-12）：PreToolUse 鉤子，權限規則比內建比對更細緻 <https://github.com/kornysietsma/tool-gate-hook>
- Claude Code PreToolUse/PermissionRequest 鉤子（0 顆星，2025-06-30）：實作自訂允許／拒絕決策的官方機制 <https://code.claude.com/docs/en/hooks>
- Claude Code 逐一子指令的權限比對與唯讀 cd（0 顆星，2026-11-08）：複合指令會依 &&、||、;、| 等符號拆開，再逐一比對每個子指令；cd 進入工作目錄視為唯讀；「不再詢問（don't ask again）」會為每個子指令各存一條規則；/permissions 會列出每條規則及其 sour <https://code.claude.com/docs/en/permissions>
- Claude Code 自動模式（auto mode）（分類器核准）（0 顆星，2026-11-08）：由分類器（classifier）代替使用者決定大多數的權限詢問，減少無人值守執行時卡住的情形。<https://code.claude.com/docs/en/permissions>
- oryband/claude-code-auto-approve（20 顆星，2026-07-29）：解析管線、串接與子 shell，並檢查每個片段，藉此自動核准複合 Bash 指令。<https://github.com/oryband/claude-code-auto-approve>
- vosslab/codex-code-permissions-hook（0 顆星，2026-07-26）：Codex 權限鉤子，拆解複合 shell 指令，並套用 TOML 格式的允許／拒絕規則。<https://github.com/vosslab/codex-code-permissions-hook>

已知缺點：
- 在 30 多個未關閉的議題中，內建權限比對被形容為已經失效；使用者正在鉤子中重新實作權限控管 <https://github.com/anthropics/claude-code/issues/30519>
- 複合指令會針對 cd 跳出詢問，而不是針對真正的指令（仍未關閉）<https://github.com/anthropics/claude-code/issues/28240>
- 自 v2.1.199 起，PermissionRequest 鉤子的 'allow' 對 ExitPlanMode 會被忽略，因此鉤子無法完全取代權限詢問 <https://github.com/anthropics/claude-code/issues/74256>
- 即使使用 --dangerously-skip-permissions，Remote Control 行動應用程式仍會顯示權限詢問（仍未關閉）<https://github.com/anthropics/claude-code/issues/29214>
- 技能／子代理程式不會繼承使用者層級的允許規則（仍未關閉）<https://github.com/anthropics/claude-code/issues/18950>
- Dippy 的設定規則無法比對帶有全域旗標的指令，例如 git -C <https://github.com/ldayton/Dippy/issues/136>
- Dippy：Cursor 的錯誤限制了它的運作能力 <https://github.com/ldayton/Dippy/issues/129>
- Codex 仍需要逐一專案的信任核准（仍未關閉）<https://github.com/openai/codex/issues/14599>
- Gemini CLI 的工作區政策檔不生效（仍未關閉）<https://github.com/google-gemini/gemini-cli/issues/18186>
- Gemini CLI v0.63.0 讓 yolo 模式失效（仍未關閉）<https://github.com/google-gemini/gemini-cli/issues/29682>
- 在複合語句中，權限詢問是針對 cd 觸發，而不是針對真正的指令；這個反應數最多的權限錯誤仍未關閉。<https://github.com/anthropics/claude-code/issues/28240>
- 權限比對被形容為根本上已經失效（30 多個議題、使用者層級規則未套用、拒絕規則可被繞過）；社群以鉤子重新實作的版本沒有經過安全審查。<https://github.com/anthropics/claude-code/issues/30519>
- 技能與子代理程式不會繼承使用者層級的權限。<https://github.com/anthropics/claude-code/issues/18950>
- 在 v2.1.77 之後的版本中，bypass/skip-permissions 失效。<https://github.com/anthropics/claude-code/issues/36168>
- 即使使用 --dangerously-skip-permissions，Remote Control 行動應用程式仍會顯示權限詢問。<https://github.com/anthropics/claude-code/issues/29214>
- 「旗標名稱中含引號字元」的警告無法關閉。<https://github.com/anthropics/claude-code/issues/27957>
- Codex 需要逐一專案的信任核准；維護者曾宣布信任所有目錄，之後又撤回決定，並重新開啟議題。<https://github.com/openai/codex/issues/14599>
- Gemini CLI 工作區的 .gemini/policies/*.toml 檔案不生效。<https://github.com/google-gemini/gemini-cli/issues/18186>

## P3（F08）：從 GitHub 以外的程式碼託管平台（forge）與議題追蹤系統（tracker）委派工作

問題：程式碼和工單放在 GitLab、Bitbucket、Azure DevOps 或 Linear 的團隊，無法在工作所在的地方把工作交給代理程式：雲端代理程式工作階段（Claude Code on the web、Codex web）只能連接 GitHub 儲存庫，而且無法把議題指派給代理程式來啟動工作階段。工程師得手動複製上下文，並自行管理分支與合併請求（merge request）。這阻礙了不使用 GitHub 的組織導入。

需求：未關閉的議題上共有 563 個反應。

現有做法：
- Cursor 雲端代理程式支援 GitLab（含自架）、Azure DevOps Services（測試版）與 Bitbucket Cloud（0 顆星，2026-11-08）：在非 GitHub 的程式碼託管平台上執行雲端代理程式工作階段，另有 Linear/Jira 整合，可從工單委派工作。<https://cursor.com/help/integrations/github-gitlab>
- GitLab Duo Agent Platform 外部代理程式（Claude Code、OpenAI Codex）（0 顆星，2026-01-14）：在 GitLab 議題／MR 中提及或指派代理程式的服務帳號，或請它審查，即可啟動一次執行，並以變更作為回應。<https://docs.gitlab.com/user/duo_agent_platform/agents/external.html>
- Claude Code GitLab CI/CD（測試版，由 GitLab 維護）（0 顆星，2026-11-08）：在議題／MR 中使用 @claude，會觸發一個管線工作（pipeline job），由它實作變更並開啟 MR。<https://code.claude.com/docs/en/gitlab-ci-cd>
- cyrusagents/cyrus（886 顆星，2026-11-06）：自架的 Claude Code（以及 Codex/Cursor/Gemini）背景代理程式，可由 Linear、Slack、GitHub 與 GitLab 觸發。<https://github.com/cyrusagents/cyrus>
- Linear 程式撰寫工作階段（coding sessions）（Claude Code 或 Codex）（0 顆星，2026-06-11）：把 Linear 議題委派給雲端代理程式，由它開啟草稿 PR。<https://linear.app/docs/coding-sessions>
- GitLab Duo Agent Platform 外部代理程式（Claude Code Agent、Codex Agent）（0 顆星，2026-11-07）：在 GitLab 議題／MR 中提及或指派服務帳號，即可執行由 GitLab 管理的 Claude Code 或 Codex 代理程式，由它們推送分支與 MR <https://docs.gitlab.com/user/duo_agent_platform/agent_assistant/>
- Cursor Cloud Agents 的程式碼託管平台整合（0 顆星，2026-11-07）：雲端代理程式可搭配 GitHub、GitLab（含自架）、Azure DevOps Services 與 Bitbucket Cloud 使用 <https://cursor.com/help/integrations/github-gitlab>
- Linear 程式撰寫工作階段（0 顆星，2026-06-11）：把 Linear 議題指派給 Linear Agent，就會在雲端執行 Claude Code 或 Codex，並傳回差異（diff）<https://linear.app/changelog/2026-06-11-coding-sessions>

已知缺點：
- Claude Code 雲端工作階段在複製（clone）與 PR 上仍需要 GitHub；GitLab/Bitbucket 只能以打包檔（bundle）上傳，且無法推送回去。<https://code.claude.com/docs/en/claude-code-on-the-web>
- Linear 程式撰寫工作階段需要透過 Linear 的 GitHub 整合來取得儲存庫。<https://linear.app/docs/coding-sessions>
- Claude Agent for Jira 只會在已連接的 GitHub 儲存庫中開啟 PR。<https://www.atlassian.com/blog/company-news/claude-agent-for-jira>
- Cursor 雲端代理程式：Bitbucket Data Center 只能使用 Bugbot；Azure DevOps 為公開測試版，且僅支援 Services。<https://cursor.com/help/integrations/github-gitlab>
- GitLab 外部代理程式僅限 Premium/Ultimate，且受功能旗標（feature flag）管控，只開放給經驗證的客戶。<https://docs.gitlab.com/user/duo_agent_platform/agents/external.html>
- 仍有人要求 Codex web 原生支援 Azure DevOps（仍未關閉）。<https://github.com/openai/codex/issues/10665>
- 仍有人要求 Claude Code 支援 Bitbucket（仍未關閉）。<https://github.com/anthropics/claude-code/issues/38179>
- Claude Code on the web 仍只能連接 GitHub；GitLab、Bitbucket 與 Azure DevOps 的請求仍未關閉 <https://github.com/anthropics/claude-code/issues/54054>
- Linear 程式撰寫工作階段需要連接 GitHub；未提及其他程式碼託管平台 <https://linear.app/changelog/2026-06-11-coding-sessions>
- GitLab 外部代理程式需要 Premium/Ultimate，受需申請才會開啟的功能旗標管控，而且在 Self-Managed/Dedicated 上屬於「實驗（Experiment）」階段 <https://docs.gitlab.com/user/duo_agent_platform/agent_assistant/>
- Cursor 對 Azure DevOps 與 Bitbucket Cloud 的支援為公開測試版；雲端代理程式不支援 Bitbucket Data Center <https://cursor.com/help/integrations/github-gitlab>
- 使用者回報：Cursor 的 Azure DevOps 整合故障 <https://forum.cursor.com/t/azure-dev-ops-integration-is-broken/170774>
- 使用者回報：Cursor 雲端代理程式無法從 Bitbucket 儲存庫取得分支 <https://forum.cursor.com/t/cloud-agents-cant-get-branches-from-bitbucket-repo/169511>
- Codex cloud 沒有 Azure DevOps 整合 <https://github.com/openai/codex/issues/10665>

## P4（F15）：不知道長時間執行的代理程式何時完成或需要輸入

問題：把長任務交給代理程式的工程師會轉去做其他工作。但在代理程式完成或等待輸入時，他們收不到明顯的訊號；對話中也沒有時間戳記，無法得知背景檢查上次是何時執行、指令是何時下達的。他們要嘛一直盯著終端機，要嘛因代理程式閒置而浪費時間。

需求：未關閉的議題上共有 333 個反應。

現有做法：
- Claude Code Notification/Stop 鉤子（0 顆星，2025-06-30）：在 Claude 完成或需要輸入時執行指令（桌面／手機提醒）<https://code.claude.com/docs/en/hooks-guide>
- Claude Code 行動推播通知（0 顆星，2026-04-13）：Claude 需要輸入時推播到手機 <https://code.claude.com/docs/en/whats-new/2026-w16.md>
- Codex tui.notifications 與 notify 鉤子（0 顆星，2026-04-13）：針對 agent-turn-complete 與 approval-requested 的終端機通知；外部 notify 指令 <https://codex.danielvaughan.com/2026/04/13/codex-cli-notification-pipeline-osc9-hooks-alerts/>
- mylee04/code-notify（291 顆星，2026-09-04）：為 Claude Code、Codex、Gemini CLI 提供跨平台的桌面通知與音效 <https://github.com/mylee04/code-notify>
- tuchg/Lucarne（343 顆星，2026-08-02）：為 Codex/Claude Code 工作階段提供遠端通知、核准與繼續執行 <https://github.com/tuchg/Lucarne>
- ProducerGuy/claude-timecodes（6 顆星，2026-04-04）：在 Claude Code 的對話回合上加上時間戳記 <https://github.com/ProducerGuy/claude-timecodes>
- Claude Code Notification 與 Stop 鉤子（0 顆星，2026-11-08）：鉤子會在 Claude 需要輸入或完成時觸發，讓使用者可以觸發桌面／手機提醒，或記錄時間戳記。<https://code.claude.com/docs/en/hooks>
- Claude Code Remote Control 推播通知（0 顆星，2026-08-17）：'Push when actions required' 與 'Push when Claude decides' 會在卡在權限詢問上或長任務完成時，透過 Claude 應用程式推播到手機。<https://wmedia.es/en/tips/claude-code-notifications-on-your-phone>
- Codex tui.notifications/notify 設定（0 顆星，2026-11-05）：維護者說明了使用 OSC 9/BEL 的 tui.notifications，以及在 agent-turn-complete 時觸發的 notify 腳本鉤子；桌面應用程式則有作業系統層級的完成通知。<https://github.com/openai/codex/issues/3962>
- DevinoSolutions/anotifier-for-claude-codex-cursor（35 顆星，2026-11-07）：為 Claude Code、Codex、Gemini CLI 與 Cursor 提供桌面與手機（ntfy）通知，並原生支援 VS Code。<https://github.com/DevinoSolutions/anotifier-for-claude-codex-cursor>
- wyattjoh/claude-code-notification（95 顆星，2026-11-03）：macOS 桌面通知鉤子，會針對 Claude Code 事件播放音效。<https://github.com/wyattjoh/claude-code-notification>
- Riplexa Timestamps（VS Code 擴充功能）（0 顆星，2026-09-14）：在 Claude Code 與 Codex 的 VS Code 聊天面板中，直接在訊息旁顯示時間戳記。<https://github.com/agurrotem-crypto/riplexa-timestamps>

已知缺點：
- Codex 的外部 notify 鉤子只在 agent-turn-complete 時觸發，核准請求時不會；OSC 9 的支援程度因終端機而異；沒有去除重複的機制 <https://codex.danielvaughan.com/2026/04/13/codex-cli-notification-pipeline-osc9-hooks-alerts/>
- Codex：因 API 錯誤而結束的回合不會觸發 Stop 或任何其他鉤子，因此沒有提醒 <https://github.com/openai/codex/issues/54884>
- Codex：Desktop 更新後，鉤子停止執行 <https://github.com/openai/codex/issues/21639>
- Codex：每次 /goal 接續執行時都會觸發 Stop 鉤子，產生錯誤的「完成」提醒 <https://github.com/openai/codex/issues/52950>
- Codex 完成音效的請求仍未關閉 <https://github.com/openai/codex/issues/3962>
- Claude Code 的訊息仍未顯示時間戳記（仍未關閉）；只有極小型的第三方工具 <https://github.com/anthropics/claude-code/issues/44763>
- Claude Code 沒有逐則訊息的時間戳記；請求仍未關閉；唯一的第三方選項只涵蓋 VS Code 面板，而且會修補（patch）它的 webview。<https://github.com/anthropics/claude-code/issues/44763>
- 第二個未關閉的請求，要求在互動式對話畫面中顯示訊息時間戳記。<https://github.com/anthropics/claude-code/issues/30745>
- Claude Code VS Code 擴充功能在 Claude 需要注意時，缺少原生的系統／彈出式（toast）通知。<https://github.com/anthropics/claude-code/issues/57230>
- Codex IDE 擴充功能沒有聲音訊號；notify 鉤子在核准請求時不會觸發；第三方通知工具透過 Remote SSH 使用時會失效。<https://github.com/openai/codex/issues/3962>
- Codex VS Code 擴充功能在需要核准時，不會提醒使用者注意。<https://github.com/openai/codex/issues/30821>
- Claude Code Notification 鉤子觸發時有約 10 秒的延遲。<https://github.com/anthropics/claude-code/issues/5186>
- idle_prompt 通知的逾時時間無法設定。<https://github.com/anthropics/claude-code/issues/13922>
- Remote Control 推播需要訂閱、兩個開關都開啟、一個進行中的 Remote Control 工作階段，以及一個開著的終端機；使用 API 金鑰或雲端供應商時無法使用。<https://wmedia.es/en/tips/claude-code-notifications-on-your-phone>
- Codex Remote Control 推播通知在 iOS 上無法送達。<https://github.com/openai/codex/issues/32908>

## P5（F16）：透過原始 shell 指令進行檔案操作

問題：代理程式越來越常透過 shell 使用 sed、cat 和 grep 來讀取、寫入和編輯檔案，而不是使用專用的檔案工具，在自動模式下更是如此。這些變更會繞過工程師用來監督代理程式的檔案層級權限規則、差異顯示與編輯追蹤。

需求：未關閉的議題上共有 228 個反應。

現有做法：
- tonywu20/no-shell-file-ops（Claude Code 外掛）（0 顆星，2026-05-21）：以鉤子阻擋會讀取或編輯檔案的 shell 指令（sed、cat、xxd、od、sd、python -c）。<https://www.claudepluginhub.com/plugins/tonywu20-no-shell-file-ops>
- enforce-builtin-tools.sh PreToolUse 鉤子（0 顆星，2026-10-30）：拒絕 Bash 的 cat/head/tail/sed/grep/find，並引導代理程式改用 Read/Edit/Write/Grep/Glob。<https://dev.to/yurukusa/claude-code-ignores-its-own-tools-here-are-3-hooks-that-force-it-to-behave-mi1>
- davidewins/claude-guardrails（1 顆星，2026-11-03）：以設定檔驅動、針對 Bash 指令與檔案寫入的阻擋／詢問／提醒規則。<https://github.com/davidewins/claude-guardrails>
- CLAUDE_CODE_THRIFTY_SONIC=0 環境變數權宜做法（未列入文件）（0 顆星，2026-08-19）：使用者回報，它能在 2.1.263+ 上關閉自動模式的「Bash 優先（Bash-first）」導向。<https://github.com/anthropics/claude-code/issues/87971>
- Claude Code 的 Read/Edit 拒絕規則套用到可辨識的 Bash 檔案指令，並搭配作業系統沙箱（0 顆星，2026-10-02）：拒絕規則涵蓋 Bash 中的 cat/head/tail/sed/tee；沙箱（sandbox）會在作業系統層級阻擋檔案存取 <https://dev.to/rulestack/claude-codes-read-deny-rules-let-4-of-11-routes-through-grep-r-a-python-one-liner-and-two-ajf>
- HabibiCodeCH/claude-no-bash-detour（2 顆星，2026-07-24）：PreToolUse 鉤子，拒絕有原生工具可替代的 Bash 指令（grep/find、sed -i、cat/head/tail），並改導向 Grep/Glob/Read/Edit <https://github.com/HabibiCodeCH/claude-no-bash-detour>
- derekwden-droid/file-tools-first（0 顆星，2026-10-09）：外掛，阻擋 shell 的檔案讀取／編輯，並改走 Read/Edit/Write，讓 /rewind 與規則能夠生效 <https://github.com/derekwden-droid/file-tools-first>
- JasonGDG/claude-bash-bridge（0 顆星，2026-10-19）：當 Claude 透過 Bash 編輯檔案時，觸發 Write/Edit 鉤子與路徑規則 <https://github.com/JasonGDG/claude-bash-bridge>

已知缺點：
- Claude Code 自動／bypass 模式的系統提示詞本身，就要求模型用 cat/sed/heredoc 讀取與編輯檔案，使寫入繞過 Write|Edit 鉤子；在 2.1.268 上仍可重現。<https://github.com/anthropics/claude-code/issues/89251>
- Opus 5.5 發布後，一位使用者用來阻擋 shell 寫入的 PreToolUse 鉤子，不再是可靠的退出方式；沒有任何列入文件的設定，能把自動核准與工具路由分開。<https://github.com/anthropics/claude-code/issues/87971>
- 以 Bash 優先的編輯會悄悄略過巢狀的 CLAUDE.md 與以路徑為範圍的規則；PreToolUse 無法注入 additionalContext 來改變導向。<https://github.com/anthropics/claude-code/issues/90450>
- 透過 Bash 編輯的檔案會讓 /rewind 失效。<https://github.com/anthropics/claude-code/issues/87575>
- 代理程式在 Bash 中透過 python 寫入檔案，規避了 Edit 鉤子。這顯示以模式比對為基礎的鉤子很容易被繞過。<https://github.com/anthropics/claude-code/issues/29709>
- 第三方鉤子都是極小型專案（0-1 顆星，維護分數低）。<https://www.claudepluginhub.com/plugins/tonywu20-no-shell-file-ops>
- 在自動模式下，執行框架本身會指示 Claude 透過 Bash（cat、sed、heredoc）讀寫檔案，而不是使用 Read/Edit/Write；仍未關閉 <https://github.com/anthropics/claude-code/issues/87971>
- 在內建工具適用的情況下，模型仍經常使用 sed/grep/cat；仍未關閉 <https://github.com/anthropics/claude-code/issues/19649>
- 檢查點（checkpointing）／rewind 不會追蹤只由 Bash 指令變更的檔案 <https://code.claude.com/docs/en/checkpointing>
- 在 v2.1.285 上，除非開啟沙箱，否則 Read 拒絕規則會被 grep -r 與 python 單行指令繞過 <https://dev.to/rulestack/claude-codes-read-deny-rules-let-4-of-11-routes-through-grep-r-a-python-one-liner-and-two-ajf>

## P6（F17）：沒有安全的方式為雲端工作階段提供憑證

問題：在廠商雲端執行非同步代理程式工作階段的工程師，沒有安全的方式提供 API 金鑰和其他憑證（credentials）；環境設定欄位本身就警告不要把機密（secrets）放在那裡。需要經過驗證才能存取的任務，要嘛無法在雲端執行，要嘛逼工程師暴露機密。

需求：未關閉的議題上共有 215 個反應。

現有做法：
- Claude Code 雲端環境：網路機密（network secrets）（0 顆星，2026-11-08）：API 金鑰與權杖（token）儲存在環境上。請求離開虛擬機（VM）之後，Anthropic 的代理程式代理（agent proxy）會把它們附加到送往所列主機的請求上。金鑰從不出現在工作階段的環境變數、檔案或 tra <https://code.claude.com/docs/en/cloud-environments#add-network-secrets>
- Claude Code 雲端 GitHub 代理（proxy）（0 顆星，2026-11-08）：Git 憑證在伺服器端保持加密，由代理附加，從不進入 VM。<https://code.claude.com/docs/en/claude-code-on-the-web>
- mmartinez/postern（11 顆星，2026-11-02）：負責仲介憑證的 HTTPS 代理，在發出請求時注入 1Password/Bitwarden 的機密，讓代理程式永遠看不到它們（自架，不適用於廠商雲端工作階段）。<https://github.com/mmartinez/postern>
- Claude Code 雲端環境：網路機密（官方）（0 顆星，2026-11-07）：在 Anthropic 託管的環境上儲存 API 金鑰或權杖（Bearer、自訂標頭、使用者名稱／密碼、AWS SigV4）。請求離開 VM 之後，代理程式代理會把它附加到送往所列主機的請求上，因此金鑰從不 e <https://code.claude.com/docs/en/cloud-environments>
- Claude Code 雲端 GitHub 代理（官方）（0 顆星，2026-11-07）：Git 與 gh 請求由代理重新驗證，真正的 GitHub 權杖則保留在工作階段 VM 之外。<https://code.claude.com/docs/en/cloud-environments>
- ermoluk/mcp-warden（12 顆星，2026-11-03）：以本機為優先的 MCP 憑證仲介工具。代理程式透過限定範圍的預設組合呼叫 API、SSH 與資料庫，機密則留在作業系統的鑰匙圈（keychain）中。它只能在本機使用，不適用於廠商雲端工作階段。<https://github.com/ermoluk/mcp-warden>

已知缺點：
- 網路機密從不會附加到設定腳本（setup script）的請求、公開套件登錄庫（package registry）（registry.npmjs.org、pypi.org、crates、Go proxy），或非 HTTP 標頭的用途上。它們在自架環境中不存在，使用 CMEK 的組織無法儲存，而且需要 org- <https://code.claude.com/docs/en/cloud-environments#requests-that-never-get-the-secret>
- 安全機密的請求仍未關閉，有 215 個反應。留言者表示，這項功能已推出到個人帳號，但 Team 帳號還沒有，而且使用者介面與文件不符。<https://github.com/anthropics/claude-code/issues/32733>
- 雲端工作階段拿不到 OIDC 身分權杖（identity token），無法進行免金鑰的 AWS/GCP/Azure 驗證。<https://github.com/anthropics/claude-code/issues/81502>
- AWS SigV4 網路機密會在沒有警告的情況下，拒絕非 amazonaws.com 的主機（例如 R2）。<https://github.com/anthropics/claude-code/issues/106173>
- 執行中的雲端工作階段無法重新載入環境變數與機密。<https://github.com/anthropics/claude-code/issues/106125>
- 網路機密從不會送到設定腳本、公開套件登錄庫（registry.npmjs.org、pypi.org 等）、Anthropic API 或遙測（telemetry）。自架環境沒有網路機密，使用客戶自管加密金鑰的組織無法儲存它們，而且 E <https://code.claude.com/docs/en/cloud-environments>
- AWS SigV4 網路機密只會為 *.amazonaws.com 主機簽章。因此，像 R2 這類相容 S3 的儲存服務會以 502 失敗，使用者只好退回使用一般的環境變數。<https://github.com/anthropics/claude-code/issues/106173>
- 雲端工作階段沒有 OIDC 身分權杖可用於免金鑰的雲端供應商驗證；請求仍未關閉（更新於 2026-11-04）。<https://github.com/anthropics/claude-code/issues/81502>
- 最初的請求希望把機密做成行程層級的環境變數，供設定腳本、私有登錄庫與資料庫 URL 使用，這個請求仍未關閉。留言回報了 Team 帳號的缺口，以及文件與使用者介面之間的不一致。<https://github.com/anthropics/claude-code/issues/32733>

## P7（F18）：在單一工作階段中進行跨儲存庫的工作

問題：採用多儲存庫架構的組織，無法用雲端或應用程式中的代理程式工作階段進行跨服務的變更，因為一個工作階段預設只有一個儲存庫、一個分支和一個拉取請求（pull request）。跨越多個服務的變更，例如共用型別或 API 合約，必須手動拆成不同的工作階段，再以人工協調。

需求：未關閉的議題上共有 186 個反應。

現有做法：
- Claude Code 多儲存庫雲端工作階段（0 顆星，2026-11-07）：在 claude.ai/code 把多個儲存庫加入同一個雲端工作階段。經測試，單一工作階段會為每個儲存庫各產生一個 PR（見 https://dev.classmethod.jp/en/articles/claude-code-web-multiple-repositories/）。<https://code.claude.com/docs/en/web-quickstart.md>
- Codex 應用程式的多資料夾專案（0 顆星，2026-07-23）：跨越多個資料夾或儲存庫的本機專案，並有一個主要資料夾。CLI 也接受 --add-dir 與 writable_roots。<https://codex.danielvaughan.com/2026/07/24/codex-multi-folder-projects-primary-folder-writable-roots-cross-repo-workspace-configuration/>
- yahor-punko/mavericks-os（82 顆星，2026-11-07）：在多儲存庫專案中協調 Claude Code 子代理程式，並追蹤跨儲存庫的相依關係。<https://github.com/yahor-punko/mavericks-os>
- dean0x/mars（15 顆星，2026-03-06）：供代理程式跨多個獨立儲存庫（polyrepo）使用的工作區層，提供協調一致的分支。<https://github.com/dean0x/mars>
- Claude Code on the web 多儲存庫工作階段（0 顆星，2026-09-30）：官方：可以把多個儲存庫附加到同一個雲端工作階段（透過多選選擇器或 repositories URL 參數；https://dev.classmethod.jp/en/articles/claude-code-web-twelve-repositories/ 測試了 12 個儲存庫）， <https://dev.classmethod.jp/en/articles/claude-code-web-multi-repo-issues-prs/>
- Claude Code Projects（0 顆星，2026-11-07）：官方：專案是「一段對話，Claude 在其中協調你各個儲存庫上平行進行的雲端工作階段，並回報結果」。<https://code.claude.com/docs/en/claude-code-on-the-web>
- Cursor 雲端代理程式的多儲存庫環境（0 顆星，2026-10-02）：一位正在轉移的使用者回報：Cursor 雲端代理程式支援在一個環境中使用多個儲存庫，並可以開出多個 PR。<https://github.com/openai/codex/issues/50155>
- me-public/nemus（19 顆星，2026-11-03）：多儲存庫 git 工作區，可以把儲存庫分組、批次操作，並把它們接到程式撰寫代理程式上。<https://github.com/me-public/nemus>

已知缺點：
- 目前仍沒有跨儲存庫的協調變更集（具合併順序的連結 PR）、逐一儲存庫的推送政策，也沒有多儲存庫的 teleport。這個議題仍未關閉。<https://github.com/anthropics/claude-code/issues/23627>
- Codex 雲端環境仍缺少多儲存庫支援（仍未關閉，2026 年 10 月）。<https://github.com/openai/codex/issues/50155>
- 在 Codex 多資料夾專案中，沒有跨儲存庫的提交；差異面板只涵蓋主要資料夾；每個資料夾都套用相同的權限。<https://codex.danielvaughan.com/2026/07/24/codex-multi-folder-projects-primary-folder-writable-roots-cross-repo-workspace-configuration/>
- Codex 應用程式的差異檢視在多儲存庫目錄下會失敗（仍未關閉）。<https://github.com/openai/codex/issues/10817>
- Codex iOS 遠端會遺漏多資料夾專案的次要資料夾（仍未關閉）。<https://github.com/openai/codex/issues/54508>
- Codex 一般性的多儲存庫請求仍未關閉。<https://github.com/openai/codex/issues/11956>
- 來源議題仍未關閉。它要求以單一單位呈現的協調變更集、具合併順序的連結 PR、逐一儲存庫的推送／PR 政策，以及多儲存庫的 teleport，這些都沒有列入文件。<https://github.com/anthropics/claude-code/issues/23627>
- 在多儲存庫的網頁版工作階段中，每個儲存庫各自得到獨立的 PR；「沒有出現把多個儲存庫的變更合併成單一 PR 的行為。」<https://dev.classmethod.jp/en/articles/claude-code-web-multi-repo-issues-prs/>
- 官方文件：「--cloud 一次只能搭配單一儲存庫使用」，而 --teleport 需要同一個儲存庫的簽出（checkout）。因此，多儲存庫工作階段無法在終端機與雲端之間移動。<https://code.claude.com/docs/en/claude-code-on-the-web>
- Codex 多儲存庫支援請求仍未關閉（更新於 2026-10-02）。<https://github.com/openai/codex/issues/11956>
- Codex Cloud 環境仍無法在一個環境中使用多個儲存庫。<https://github.com/openai/codex/issues/50155>
- 當上層工作區包含多個儲存庫時，Codex App 的 Git／差異／審查介面仍綁定在起始的儲存庫上。<https://github.com/openai/codex/issues/26338>

## P8（F19）：無人值守的工作在用量上限時停止

問題：當長時間的委派任務碰到 5 小時或每週用量上限時，即使已經知道重置時間，代理程式仍會停止。如果重置時間落在夜間，工作就得等到工程師回來、找到工作階段並重新送出提示詞。

需求：未關閉的議題上共有 169 個反應。

現有做法：
- Claude Code 用量上限自動繼續（CLI，預設開啟）（0 顆星，2026-08-17）：互動式訂閱工作階段會原地等待，並在重置後繼續任務（v2.1.234+）<https://code.claude.com/docs/en/interactive-mode#wait-for-a-usage-limit-to-reset>
- Claude Code Desktop 'Auto-continue when limits reset'（0 顆星，2026-08-10）：工作階段上限重置後，Desktop 會重試被中斷的回合 <https://code.claude.com/docs/en/whats-new/2026-w33.md>
- saaranshM/unsnooze（229 顆星，2026-11-01）：在 5 小時或每週上限重置後，自動恢復 Claude Code、Codex CLI 與其他代理程式工作階段 <https://github.com/saaranshM/unsnooze>
- terryso/claude-auto-resume（821 顆星，2026-05-09）：Shell 包裝腳本，在上限解除時恢復 Claude CLI 任務 <https://github.com/terryso/claude-auto-resume>
- songyb111-gachon/codex-auto-resume-windows（77 顆星，2026-11-07）：在 Windows 上，於上限重置後恢復同一段 Codex 桌面版對話 <https://github.com/songyb111-gachon/codex-auto-resume-windows>
- Claude Code 用量上限自動繼續（autoContinueAtUsageLimit，v2.1.234）（0 顆星，2026-08-13）：互動式 CLI 工作階段（以及 Desktop 的一個核取方塊）會等候 claude.ai 的 5 小時上限結束，並在重置後以接續提示詞恢復；訂閱者預設開啟。<https://aicatchup.com/news/claude-code-desktop-auto-continue>
- Claude Code 自動繼續注意事項整理文章（0 顆星，2026-09-28）：記錄內建自動繼續適用的介面與限制（CLI 預設開啟、Desktop 核取方塊、/rate-limit-options 備援）。<https://wmedia.es/en/tips/claude-code-session-limit-auto-continue>
- dujunyi416/claude-nightshift（36 顆星，2026-07-20）：能感知配額的自動化：在夜間把提示詞排入佇列（queue），並在重置時自動恢復被中斷的工作階段。<https://github.com/dujunyi416/claude-nightshift>

已知缺點：
- Claude Code 自動繼續不支援背景工作階段或 -p 執行；重置時間在 24 小時以後（每週上限）時不會啟動；睡眠超過 30 分鐘後需要按 Enter；而且繼續執行的任務仍會停在權限詢問上 <https://code.claude.com/docs/en/interactive-mode#wait-for-a-usage-limit-to-reset>
- Codex 的 CLI 沒有內建自動恢復（仍未關閉）<https://github.com/openai/codex/issues/21073>
- Codex App 的 /goal 在 5 小時／每週上限後不會自動恢復（仍未關閉）<https://github.com/openai/codex/issues/28931>
- Claude 變更輸出格式後，claude-auto-resume 無法解析重置時間 <https://github.com/terryso/claude-auto-resume/issues/24>
- 如果已經超過工作階段上限，claude-auto-resume 會無法執行 <https://github.com/terryso/claude-auto-resume/issues/27>
- Codex 在上限重置時沒有原生的自動恢復；請求仍未關閉，且沒有維護者回覆；重置後 Goals 會一直停在 usageLimited，直到使用者送出新訊息。<https://github.com/openai/codex/issues/21073>
- 有人要求 Codex /goal 在 5 小時／每週重置後自動恢復，請求仍未關閉；使用者只能依賴第三方桌面腳本。<https://github.com/openai/codex/issues/28931>
- Claude Code 自動繼續不適用於 -p 無頭模式或背景工作階段；不會自動等待 24 小時以後的每週重置；筆電睡眠超過 30 分鐘後需要按 Enter；終端機關閉就會結束；而且最多只會重新啟用兩次。<https://wmedia.es/en/tips/claude-code-session-limit-auto-continue>
- 連接 Remote Control 時，Claude Code 自動繼續永遠不會啟用。<https://github.com/anthropics/claude-code/issues/100650>
- Claude Code 用量上限自動繼續不會觸發。<https://github.com/anthropics/claude-code/issues/103591>
- 碰到特定模型的每週上限時，工作階段會卡在同意詢問上，而不是繼續執行。<https://github.com/anthropics/claude-code/issues/104623>
- 如果已經超過工作階段上限，第三方包裝腳本會失敗；而且在 Claude 的上限訊息格式變更時就壞了。<https://github.com/terryso/claude-auto-resume/issues/24>

## P9（F27）：無法排好接下來的任務

問題：已經知道代理程式接下來該做哪幾件事的工程師，無法把它們排入佇列：他們必須等每個任務完成，才能交代下一個；而在 VS Code 擴充功能中，新訊息會中斷正在執行的任務，而不是排隊等候。委派工作只能一回合一回合地進行，工程師必須在任務之間一直在場。

需求：未關閉的議題上共有 137 個反應。

現有做法：
- Claude Code CLI 訊息佇列（工作中按 Enter；按 Ctrl+Enter 立即送出）（0 顆星，2026-11-08）：Claude 工作時輸入的訊息會排入佇列，而不會中斷工作 <https://code.claude.com/docs/en/interactive-mode#queue-messages-while-claude-works>
- Claude Code VS Code 擴充功能的排隊訊息（0 顆星，2026-11-08）：文件指出，在 Claude 工作時送出的訊息會顯示 'Message queued.'（v2.1.236+）<https://code.claude.com/docs/en/vs-code>
- vasiliyk/claude-queue（23 顆星，2026-04-28）：將多個 Claude Code 任務排入佇列，支援優先順序與相依關係，並在方案上限時暫停／恢復 <https://github.com/vasiliyk/claude-queue>
- starsh2001/qlaude（23 顆星，2026-02-22）：為 Claude Code 排好任務後就能離開，並透過 Telegram 通知 <https://github.com/starsh2001/qlaude>
- txtx/axel（21 顆星，2026-02-05）：把任務分派給 Claude/Codex/OpenCode 的任務佇列 <https://github.com/txtx/axel>
- Codex 後續訊息佇列（CLI 按 Tab 排入佇列、IDE 擴充功能的佇列模式、桌面應用程式的佇列清單）（0 顆星，2026-11-03）：Codex 的原生佇列：排入佇列的訊息會等到目前的執行結束；IDE 擴充功能預設為佇列模式（chatgpt.followUpQueueMode），桌面應用程式則讓使用者編輯、重新排序或刪除佇列中的項目。<https://www.memorylake.ai/en/blogs/codex-steer-vs-queue>
- Claude Code 內建訊息佇列（0 顆星，2026-11-03）：在 Claude 工作時按 Enter 會把訊息排入佇列。但一般訊息會在目前的工具呼叫完成後，於同一回合內立即傳入；只有斜線指令與 shell 指令會等到回合結束。<https://www.memorylake.ai/en/blogs/claude-code-queue-messages>
- codecShivam/claudeq（9 顆星，2026-09-14）：以 Stop/SessionStart/UserPromptSubmit 鉤子打造的 Claude Code 側邊窗格佇列；每個回合依序送出一則排隊訊息，不需要修補程式。<https://github.com/codecShivam/claudeq>
- Vesely/cmux-claude-queue（3 顆星，2026-09-20）：按 Option+Enter 可把提示詞排入佇列，在 Stop 鉤子觸發後以新回合送出（僅限 macOS + cmux）。<https://github.com/Vesely/cmux-claude-queue>
- ivanarama/PromptPilot（20 顆星，2026-11-07）：Claude Code 與其他 AI CLI 的背景任務佇列，附網頁介面與 Telegram 機器人。<https://github.com/ivanarama/PromptPilot>
- coding-by-feng/ai-agent-session-center（95 顆星，2026-11-05）：Claude Code 與 Codex 工作階段的儀表板，提供提示詞佇列與工作區恢復功能。<https://github.com/coding-by-feng/ai-agent-session-center>

已知缺點：
- 排入佇列的訊息會在目前的工具呼叫完成後，於同一回合內立即傳給 Claude。因此它們會引導（steer）正在執行的任務，而不是等著成為下一個任務 <https://code.claude.com/docs/en/interactive-mode#queue-messages-while-claude-works>
- 要求把訊息延後保留到回合結束的請求仍未關閉 <https://github.com/anthropics/claude-code/issues/63190>
- 用來依序或平行執行多個提示詞的任務佇列請求仍未關閉；先前的請求已被自動關閉 <https://github.com/anthropics/claude-code/issues/33323>
- VS Code 擴充功能的排隊議題仍未關閉，使用者自行以 Stop 鉤子打造權宜做法 <https://github.com/anthropics/claude-code/issues/30677>
- 第三方佇列工具規模都很小；星數最多的（Claude-Autopilot，249 顆星）自 2025-08 以來就沒有推送過 <https://github.com/benbasha/Claude-Autopilot>
- VS Code 擴充功能「排隊而非中斷」的請求仍未關閉，且沒有維護者回覆；使用者詢問這是否在路線圖上。<https://github.com/anthropics/claude-code/issues/30677>
- 任務佇列請求仍未關閉；先前的佇列議題被 stale bot 自動關閉；cmux 權宜做法需要 macOS 與 cmux。<https://github.com/anthropics/claude-code/issues/33323>
- Claude Code 會把排隊的訊息合併成一個回合，而不是以「一則訊息 = 一個回合」的先進先出（FIFO）方式處理。<https://github.com/anthropics/claude-code/issues/73661>
- 沒有設定可以把排隊訊息保留到回合完成，而不是在回合中途併入。<https://github.com/anthropics/claude-code/issues/87656>
- Desktop 的 Code 分頁無法把訊息排到回合完全結束之後；Ctrl+Enter 會中斷執行。<https://github.com/anthropics/claude-code/issues/92988>
- 在 Claude Code 桌面版中，排隊的訊息從未送達（輸入在沒有任何提示的情況下遺失）。<https://github.com/anthropics/claude-code/issues/104517>
- 公開批評（2026 年 9 月）指出，Claude Code 無法把訊息排成獨立的下一個任務；並提到部分修正與功能退化反覆循環。<https://digg.com/ai/pdwiholm>
- Codex 佇列錯誤：出現 'App-server queued follow-up no longer exists' 錯誤；排隊的提示詞表現得像引導提示詞，並被同時送出；提示詞在進入佇列前就消失。<https://github.com/openai/codex/issues/45019>
- Codex 排隊的提示詞表現得像引導提示詞；多個排隊的提示詞被同時送出。<https://github.com/openai/codex/issues/17285>
- Codex VS Code 擴充功能：送出的提示詞會在進入佇列前隨機消失。<https://github.com/openai/codex/issues/25928>
