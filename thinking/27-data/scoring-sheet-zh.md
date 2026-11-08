# 評分表（2026-11-08）

每題 3 個匿名解法，順序隨機。每個解法打 1–5 分（5 會想馬上用、明顯比現有好；4 比現有好、值得試；3 和現有差不多；2 比現有差或不實用；1 沒有解決問題），並選出每題最好的一個。可以只評一部分。題目的現有做法與已知缺點見 `thinking/27-data/problems-zh.md`（中文版翻譯中）。

回覆格式範例：`P1：S1=4、S2=3、S3=5，最好 S3`

## P1：Agent harness 洩漏工程師的個人身分

問題：讓 agent 在網路上搜尋或抓取資料的工程師發現，harness 會把他們的帳號 email 放進送往任意網站的對外請求標頭，也會在每個 session 把它注入模型的 system prompt，事先沒有詢問。他們的身分流到他們從未選擇的第三方（一位回報者把它和每天收到的詐騙郵件連在一起），所以把網路研究交給 agent，會悄悄付出隱私代價。

### S1
解法：身分對外流量防火牆——一個本機 MITM proxy（mitmproxy addon），所有 agent 流量都必須經過它。對送往模型 API 的請求，它把請求本文中的帳號 email 和使用者列出的識別資訊換成佔位字串（`user@redacted.invalid`），所以模型、subagent 和它們寫的腳本永遠不會知道真實地址。對其他所有對外流量，它解碼標頭、URL 和本文，搜尋任何形式的識別資訊（大小寫折疊、percent/JSON/quoted-printable 跳脫、三種位移的 base64、hex、plus 地址），把標頭中命中的部分改寫成佔位字串，本文命中時則擋下並說明拒絕原因，並記錄每個事件。作業系統規則強制每個 agent 行程都經過它（Linux 上對專用的 agent 使用者設 nftables uid-owner 規則；其他平台用 agent 沙箱的自訂 proxy 連接埠），所以 loopback 呼叫和檔案寫入永遠不會被檢查。一個 commit-msg/pre-push hook 對 git 套用同樣的比對器。
和現有做法的差別：它處理的是實際傳輸中的位元組，不是工具呼叫的文字，所以 Claude 寫的腳本、subagent 和編碼過的形式都會被抓到；只檢查真正的網路對外流量，終結本機的誤判；context 清除在網路層進行，所以 Team/Enterprise 的 mod 限制不適用。
需要：Node 和其他工具信任的本機 CA（NODE_EXTRA_CA_CERTS）；受管理機器上的管理員核准；廠商容許改寫 API 請求本文。廠商：把 email 從 context 拿掉才是真正的解決方法。

### S2
解法：清除身分資訊的對外 proxy——一個本機 TLS 攔截 proxy（mitmproxy addon），harness 和每個子行程透過 HTTPS_PROXY 加上本機 CA（NODE_EXTRA_CA_CERTS、SSL_CERT_FILE）使用它；network namespace 或防火牆規則只允許經由 proxy 對外連線，所以 agent 寫的、忽略 proxy 變數的腳本也無法繞過它。兩條規則：(1) 對送往模型 API 的請求，把 system prompt 中的帳號 email 換成固定的假名，所以模型永遠不會知道這個地址，也無法把它放進標頭、腳本或 commit；(2) 對其他所有對外流量，在 URL、標頭和本文中比對使用者已知的身分字串（email、姓名、git email），涵蓋預先計算好的各種編碼（URL、base64、hex、JSON 跳脫、大小寫變體），然後改寫或擋下，並記錄。判斷依據是真正的目的地；loopback 永遠不經過 proxy。一套外洩測試（curl User-Agent、Python 腳本、subagent、base64 查詢）會回報外洩和誤擋。
和現有做法的差別：hook 和內建的 mod 讀的是工具呼叫的文字：它們會漏掉腳本、編碼和 subagent，還會從字面猜「網路」，造成誤拒。不送 email 的 mod 需要 context hook，而受管理設定會跳過這類 hook。這個做法處理的是實際送出的位元組，包括模型請求；以外洩和誤擋來衡量。
需要：harness 遵守 HTTPS_PROXY 和自訂 CA（Claude Code 有）；作業系統層級的對外流量鎖定；允許 TLS 攔截的組織政策。不需要廠商改動；如果廠商移除 email，規則 1 就不需要了。

### S3
解法：身分對外流量防火牆——由一個 wrapper 啟動 agent，強制所有對外流量都經過本機 TLS 檢查 proxy（每個子行程都設 HTTPS_PROXY 加上 NODE_EXTRA_CA_CERTS/SSL_CERT_FILE/REQUESTS_CA_BUNDLE；Linux 用 netns/nftables 規則，macOS 用 agent 沙箱的 proxy 設定），所以 subagent 和 Claude 自己寫、自己執行的腳本都無法繞過它。啟動時，它從 harness 設定讀取已登入的 email，並預先計算各種變體：大小寫、percent 編碼、JSON 跳脫、base64、hex、拆開的 local part。送往 loopback 和廠商 API 的請求原封不動通過；對其他所有主機，會掃描標頭和本文，命中的部分換成使用者選擇的別名（例如一個轉寄地址，讓 sec.gov 這類要求提供聯絡方式的網站仍然能用）並記錄，永遠不拒絕。也可以選擇在送往廠商 API 的那一段，從 system prompt 移除被注入的 email 區塊。一個 commit-msg hook 會拒絕含有這個地址的 commit。
和現有做法的差別：它檢查的是實際傳輸中的位元組，不是工具呼叫的文字，所以自己寫的腳本、subagent 的 curl 和編碼過的形式都會被抓到；它知道目的地，所以 heredoc 和 127.0.0.1 的呼叫永遠不會被擋；它用替換取代拒絕；在受管理的登入下也能運作。衡量：在外洩測試語料上的漏抓和誤擋。
需要：子工具信任的本機 CA（使用憑證綁定的客戶端會失敗並中斷連線）；作業系統層級的強制對外導流。只有在組織設定允許 API 流量走 proxy 時，才能移除 prompt 內容。廠商：正式支援關閉 email 注入。

## P2：權限行為和工程師設定的不一致

問題：已經決定 agent 可以做什麼的工程師發現，權限系統不照這個決定執行：allow 和 deny 規則比對不可靠，複合指令會因為無害的 `cd` 跳出確認，一般帶引號的旗標會觸發新的警告，skill 和 subagent 忽略使用者層級的 allow 規則，skip-permissions 或 yolo 模式仍然會跳出確認，每個新專案都需要各自的信任核准，工作區政策檔也會無聲無息地不生效。無人值守的執行會卡在確認提示上，工程師也無法確定自己寫的規則就是實際執行的規則，所以有些人在自己的 hook 裡重新實作強制執行。

### S1
解法：由腳本化模型驅動的權限一致性測試套件——政策只寫一次，寫成意圖加上範例指令（任何地方都允許唯讀 git，包括 git -C；允許在工作區內 cd；拒絕網路寫入）。一個本機的模型 API mock（Claude Code 用 ANTHROPIC_BASE_URL，Codex 用自訂 model provider，Gemini CLI 在允許的地方用對應的方式），在用完即丟的 repo 上以 headless 執行，為每個範例重播腳本化的工具呼叫，包括複合指令、帶引號旗標、subagent 和 skill 的案例。harness 的真實決定，從 mock 接下來收到的 tool_result 和權限拒絕中讀出，再和意圖比較。輸出：一張依 harness、版本和權限模式區分的差異表。CI 在每次 harness 發布和規則變更時執行它；版本鎖定只推出通過的版本；不一致的案例會產生 PreToolUse/PermissionRequest hook 規則，hook 無法覆寫的案例（ExitPlanMode、Remote Control 的確認提示）則變成回報給上游的 bug。
和現有做法的差別：Dippy 這類 hook 重新實作比對，卻不呈現 harness 實際執行的是什麼；內建規則和 auto 模式沒有提供測試。這個做法依 harness、版本和模式，以確定性的方式衡量預期和實際執行之間的不一致，在推出前抓到迴歸，並把自訂 hook 限制在量測到的缺口上。
需要：harness 可覆寫模型端點並有 headless 模式（Claude Code、Codex；Gemini 待確認）；版本鎖定。廠商：修正 hook 無法覆寫的確認提示（ExitPlanMode、Remote Control）。

### S2
解法：權限一致性測試——工程師把預期結果寫成一張表：工具呼叫、情境（主 agent、subagent、skill、離開 plan）、模式（default、auto、bypass）→ allow、ask 或 deny。一個執行器在用完即丟的容器裡，以 headless 方式啟動實際安裝的 CLI，指向本機的 mock 模型端點（ANTHROPIC_BASE_URL；Codex 的自訂 model provider），由它把每個案例重播成腳本化的工具呼叫。結果來自證據：一個會記錄的 --permission-prompt-tool 標記 ask，PATH shim 記錄執行而不產生副作用，回傳的 tool result 裡的拒絕文字標記 deny。它在每次 CLI 版本升級和設定變更時於 CI 執行，擋下出現迴歸的升級，並產生一個最小的 PreToolUse hook，只涵蓋失敗的案例；一旦原生比對器通過，這個 hook 就自動退役。對話紀錄挖掘模式會列出有符合的 allow 規則、卻仍跳出確認的真實指令，並把它們加為案例。
和現有做法的差別：hook 專案用另一個沒人審查過的解析器取代比對器；這個做法拿真正的強制執行點對照工程師自己的預期，在無人值守執行前抓到迴歸（cd 確認提示、bypass、subagent 繼承），並讓變通做法保持最小、自動退役。衡量：每個版本的一致率；每次無人值守執行卡住的次數。
需要：CLI 支援自訂模型端點和 headless 模式（Claude Code、Codex；Gemini CLI 若可覆寫）。不需要廠商改動；如果廠商提供 dry-run 的「解釋決定」指令，就不需要 mock。

### S3
解法：permcheck——一份政策，依每個 agent 編譯，並用真實的 agent 驗證。工程師寫一份政策（依工具、路徑和指令語意設定 allow/ask/deny）。一個真正的 shell 解析器（tree-sitter-bash）在比對前先正規化指令：拆開複合指令和 subshell，去掉切進工作區的 `cd`，拆開 env 前綴、`sh -c`、`xargs` 和 `timeout`，並把全域旗標標準化（`git -C x commit` → `git commit`）。編譯器產生每個 agent 的原生設定（Claude 的 settings.json、Codex 的 rules 加上宣告根目錄下每個 repo 的 `trust_level` 項目、Gemini 的 policy TOML），以及一個安裝在使用者層級和受管理層級的強制執行 hook，讓 subagent 和 skill 也套用到。`permcheck test` 在用完即丟的容器裡，以 headless 方式執行每個已安裝的 agent，跑一組探測語料（複合指令、帶引號旗標、python -c、已知的繞過手法），其中的執行檔都是只記錄呼叫的 shim，並回報預期和實際的 allow/prompt/deny。它在 CI 中執行，也在每次 agent 升級前執行。
和現有做法的差別：現有工具再加一個比對器，卻無法證明它有被套用；這個做法衡量每個 agent 版本實際執行的內容，在無人值守的執行卡住之前抓到迴歸（壞掉的 skip-permissions/yolo、被忽略的工作區政策、沒有被繼承的規則），而且 Claude、Codex 和 Gemini 共用同一個單一事實來源。
需要：每個 agent 的 headless 模式和 hook API；一個容器執行環境。它揭露的缺陷仍需要廠商修正，例如 ExitPlanMode 忽略 hook 的允許，以及行動裝置上的確認提示。

## P3：從 GitHub 以外的程式碼託管平台和工單系統委派工作

問題：程式碼和工單放在 GitLab、Bitbucket、Azure DevOps 或 Linear 的團隊，無法在工作所在的地方把工作交給 agent：雲端 agent session（Claude Code on the web、Codex web）只能連接 GitHub repo，issue 也無法指派給 agent 來啟動 session。工程師要手動複製上下文，自己管理分支和 merge request，這擋住了不使用 GitHub 的組織採用。

### S1
解法：透過組織自己的 CI runner 進行程式碼託管平台原生派工——一個小型中繼服務（relay），加上適用於 Bitbucket Pipelines、Azure Pipelines、Jenkins（Bitbucket Data Center、Azure DevOps Server）和任何方案等級 GitLab CI 的 pipeline 範本。觸發方式：把 Jira、Linear 或 Azure Boards 的工單指派給「agent」使用者，或在 MR/PR 留言中寫「@agent」。中繼服務（一個可以在防火牆內執行的 webhook 處理程式）根據工單（描述、驗收條件、連結的 MR、留言）建立任務說明，並透過程式碼託管平台的 API 把 pipeline 排入佇列。這個 job 以 headless 方式執行 agent CLI（claude -p、codex exec），使用限定在該 repo 的 CI 憑證，push agent/<ticket-id>，以原生方式開啟 MR/PR，在工單上加上連結，並把 session 對話紀錄存成 artifact；之後的「@agent」review 留言會在同一個分支上接續那個 session。政策（允許的 repo、預算、最長執行時間）放在中繼服務裡。
和現有做法的差別：不需要特定的程式碼託管平台方案等級、功能旗標、GitHub 鏡像或廠商整合：它重複使用組織已有的 runner、憑證、地端網路的連線範圍和稽核軌跡，一個中繼服務就涵蓋每一種程式碼託管平台和工單系統的組合。和 cyrus 不同，不需要常駐主機。衡量：從工單到 MR 的手動步驟（目標為零）；支援的程式碼託管平台和工單系統。
需要：可以對外連到模型 API 的 runner；存成受保護 CI 變數的 API key 或 CLI token；工單系統的 webhook 或自動化規則。不需要廠商改動。

### S2
解法：透過 proxy 注入憑證的程式碼託管平台橋接——一個小型 webhook 服務，監聽 Linear 的 agent 指派，以及 Jira、Azure Boards、GitLab 和 Bitbucket 的提及或指派。觸發時，它在一個空殼 GitHub repo 上啟動廠商的雲端 session（例如 claude --cloud），這個 repo 只放橋接設定，沒有原始碼。環境把程式碼託管平台的 token 存成針對該平台主機的 network secret（basic auth），所以 session 透過 HTTPS 從 GitLab、Bitbucket 或 Azure DevOps clone 真正的 repo 並 push 回去，token 不會進入 VM。空殼 repo 裡有一個不綁定特定平台的 CLI（建分支、push、開 MR/PR、留言、連結工單），包裝各程式碼託管平台的 REST API。agent 在原始的程式碼託管平台上開 MR，並把連結貼到工單；寫給 agent 的 review 留言會在那個分支上啟動後續 session，以留言作為 prompt。自架環境則改用 runner 自己的程式碼託管平台憑證。
和現有做法的差別：原生整合要等廠商逐一支援各平台，處於 beta 或限 Premium 方案，而且不支援 Bitbucket Data Center 和 Azure DevOps Server；cyrus 需要自架運算資源。這個做法重複使用只支援 GitHub 的雲端 session，讓原始碼不放上 GitHub，並且適用於任何 HTTPS git 程式碼託管平台。衡量：從工單到 MR 的手動步驟。
需要：方案中有 Claude Code 的 network secret（Team 方案的缺口在廠商端）；廠商雲端連得到程式碼託管平台（否則用自架環境）；CLI 啟動 session 時接受空殼 repo。

### S3
解法：程式碼託管平台影子橋接——一個服務，為只支援 GitHub 的 agent 提供每個 GitLab、Bitbucket（Cloud 或 Data Center）或 Azure DevOps repo 的私有 GitHub 鏡像，並以原始來源為準。原始來源的 push webhook 把分支鏡像到一個權限鎖緊的 GitHub org，在那裡只有 agent 的分支前綴（`claude/*`、`codex/*`）可以寫入。當 agent 開了鏡像 PR（Claude Code on the web、Codex cloud、Linear coding sessions、Claude Agent for Jira），橋接服務會把分支 push 到原始來源，開對應的 MR 並附上工單連結，再把鏡像 PR 變成一個指標。原始 MR 上的 review 留言會以 `@claude`/`@codex` 提及的形式轉發到鏡像 PR，由廠商的 GitHub 整合處理，新的 commit 再流回去。把 Jira、Linear 或 Azure Boards 的工單指派給「agent」使用者時，橋接服務會透過廠商 CLI，在鏡像上用工單內容啟動雲端 session。
和現有做法的差別：不用等每個廠商支援每個平台，一個橋接服務就讓每個只支援 GitHub 的 agent 能搭配任何程式碼託管平台，包括 Bitbucket Data Center 和 Azure DevOps Server，不受 GitLab Premium 方案限制，也不需要功能旗標或各廠商的 beta 整合。
需要：一個私有 GitHub org，以及把程式碼鏡像到那裡的核准（如有要求，還要處理資料落地）；程式碼託管平台的 webhook 和 API token；廠商的雲端 session CLI。不需要廠商改動。

## P4：不知道長時間執行的 agent 何時完成或需要輸入

問題：把長任務交給 agent 的工程師會切去做其他工作，但在 agent 完成或等待輸入時，收不到明顯的訊號，而且對話中沒有時間戳記，無法看出背景檢查上次是何時執行，或某個指示是何時下的。他們只能盯著終端機，或因 agent 閒置而浪費時間。

### S1
解法：監看對話紀錄的提醒 daemon——一個小型 daemon，在 agent 執行的機器上（包括 Remote SSH 主機）持續讀取 Claude Code、Codex 和 Gemini CLI 本來就會寫的、帶時間戳記的 session 對話紀錄，並檢查行程是否存活。它根據證據推斷狀態，而不是信任 hook：工作中、等待核准、提出問題、已完成、API 錯誤、停滯（行程還活著，但在可設定的 N 分鐘內沒有寫入）、已結束。它只在狀態轉換時通知，並做防抖處理（「已完成」之後幾秒內就有自動的 /goal 接續時，這個通知會被抑制），而且會逐步升級：先是桌面彈出通知和聲音，M 分鐘後仍未確認，再透過 ntfy 通知手機。沉默本身就是一種訊號，所以沒有 hook 涵蓋的錯誤，或因更新而壞掉的 hook，仍然會產生「停滯」警示。一個狀態列腳本（它會收到 transcript_path）顯示狀態、最後一次指示的時間和距離上次活動的時間，在終端機畫面中提供時間戳記。
和現有做法的差別：以 hook 為基礎的通知工具依賴 harness 發出的事件，所以 API 錯誤、因更新而壞掉的 hook、缺少的核准事件、約 10 秒的延遲，以及 /goal 誤報的「完成」警示，不是沒被看到，就是出錯。這個做法獨立推斷狀態。衡量：在錄下的 session 上的漏報、誤報和警示延遲。
需要：對話紀錄格式（沒有文件；需要逐版本的轉接器）；ntfy 或作業系統通知。廠商：在對話畫面本身顯示時間戳記。

### S2
解法：存活監看器——一個 daemon，在 agent 實際執行的機器上（包括 Remote SSH 主機）持續讀取 CLI 本來就會寫的對話紀錄檔（~/.claude/projects/*.jsonl、~/.codex/sessions/），並取樣 agent 的行程樹。一個狀態機推斷出：工作中；等待核准（有未完成的工具呼叫、沒有子行程、CPU 閒置）；已完成（最後一則 assistant 訊息、沒有未完成的事項、在防抖時間窗內保持閒置，所以 /goal 接續不會觸發警示）；出錯（有錯誤紀錄，或行程還活著但 N 分鐘沒有進展）；已結束。每次轉換都推送到 ntfy、Slack 或 Pushover，並逐步升級重送，直到被確認；hook 事件如果真的有到，只用來讓時間更精準。`pulse log` 從對話紀錄印出指示、工具執行和背景檢查的時間軸，附上時間戳記；在第二個窗格執行 `pulse` 則即時顯示。
和現有做法的差別：以 hook 為基礎的通知工具，只要 harness 沒觸發就保持沉默；這個做法在沒有進展時發出警示，涵蓋以 API 錯誤結束、因更新而壞掉的 hook、未回報的 Codex 核准和 Remote SSH，而且不必修改任何 UI 就能提供時間戳記。衡量：在注入的故障上，漏報閒置的比率和警示延遲。
需要：本機對話紀錄檔的讀取權限（格式沒有文件；解析器必須跟上 CLI 版本）和一個推播服務。不需要廠商改動；有文件的事件串流會有幫助。

### S3
解法：Agent 狀態監看器——一個 daemon，從不依賴 hook 的證據推斷每個 session 的狀態，然後逐步升級地發出警示。輸入：每個介面都會寫的對話紀錄（Claude Code 的 `~/.claude/projects/**/*.jsonl`、Codex 的 `~/.codex/sessions` rollout）和 agent 的行程樹。規則：回合結束，且在防抖時間窗內沒有接續 → 完成（過濾掉 /goal 接續）；有錯誤紀錄，或行程在回合中途結束 → 失敗；有待處理的工具呼叫、沒有子行程，且對話紀錄 N 秒沒有增長 → 需要核准；工作中卻 M 分鐘沒有增長 → 停滯。門檻可以設定；警示會去重複。傳送方式依輸入閒置時間逐步升級：先是終端機鈴聲或作業系統彈出通知，X 分鐘後仍未確認，就透過 ntfy 推播到手機。使用 Remote SSH 時，它在遠端主機上執行。同樣的資料也驅動 `agentlog`，一個為每則訊息、每次工具呼叫和每次背景檢查標上實際時間戳記的時間軸。
和現有做法的差別：它讀取狀態，而不是等待 hook，所以能抓到以 API 錯誤結束和 Codex 等待核准的情況，在更新後 hook 壞掉或延遲時仍能運作，忽略 /goal 的假完成，在 CLI、IDE 和 SSH 中運作方式相同，而且不必修改 webview 就能加上時間戳記。
需要：讀取格式沒有文件的本機對話紀錄的權限（依版本區分的解析器）；一個推播服務，例如 ntfy。要在廠商自己的聊天 UI 裡顯示時間戳記，需要廠商處理。

## P5：透過原始 shell 指令進行的檔案操作

問題：agent 越來越常透過 shell 用 sed、cat 和 grep 讀取、寫入和編輯檔案，而不是使用專用的檔案工具，在 auto 模式下更是如此。這些變更會繞過工程師用來監督 agent 的檔案層級權限規則、diff 顯示和編輯追蹤。

### S1
解法：以效果為依據的 shell 檔案防護——它不從指令文字猜測意圖，而是檢查每次 Bash 呼叫實際改了什麼。一個 PreToolUse hook 把工作目錄快照到一個影子 git repo（git 的 stat 快取讓這一步很快），一個檔案系統監看器（inotify/FSEvents）記錄寫入，包括寫到被 git 忽略的路徑。一個 PostToolUse hook 對結果做 diff，並對每個變更的路徑套用現有的 Edit/Write 規則：不符合政策的變更會從快照還原，並告訴模型套用了哪條規則。允許的變更會以 unified diff 顯示，並記錄為檢查點，讓 `guard rewind` 可以復原 Bash 的編輯；當某個路徑落在巢狀 CLAUDE.md 或限定路徑的規則範圍內時，該規則的文字會以 additionalContext 注入。讀取保護仍交給作業系統沙箱。
和現有做法的差別：比對樣式的 hook 會漏掉 python、perl 和 heredoc 這些途徑，還和 harness 優先用 Bash 的引導互相拉扯，浪費被拒絕的回合；這個做法讓任何途徑都能執行，依效果強制執行，並為 Bash 編輯找回路徑規則、diff、rewind 和巢狀規則。衡量：在一組途徑語料上偵測到的寫入；被拒絕後重試的回合數。
需要：能回饋給模型的 PreToolUse/PostToolUse hook、本機 git、inotify/FSEvents。屬於事後處理：硬性的寫入邊界仍要保留沙箱。廠商（選用）：一個把自動核准和優先用 Bash 的路由分開的設定。

### S2
解法：以效果為依據的 Bash 檔案防護——用 hook 判斷 shell 指令改了什麼，而不是它怎麼寫。Bash 的 PreToolUse 把工作區快照到一個私有的 git index（`GIT_INDEX_FILE=.git/agent-idx git add -A; git write-tree`，再加上對被忽略路徑的 mtime 掃描）；PostToolUse 再快照一次，並對兩個 tree 做 diff。對每個變更的檔案，它會檢查 Edit/Write 權限規則和限定路徑的政策，從執行前的快照還原被拒絕的檔案，並告訴模型改用 Edit；透過 systemMessage 把 diff 顯示給工程師；把被動到的目錄的巢狀 CLAUDE.md 和路徑規則以 additionalContext 回傳；並把每個執行前快照存成 `refs/agent-checkpoints` 底下的 commit，讓 `agent-undo` 可以還原任何 Bash 編輯。對 Bash 而言，讀取的 deny 規則和工作區外的寫入，由根據同一套規則產生的作業系統沙箱設定檔（bubblewrap/Seatbelt）強制執行。一則 SessionStart 提示請模型優先使用 Edit，但沒有任何機制依賴它。
和現有做法的差別：比對樣式的阻擋工具會漏掉 python、heredoc 和新工具，還和 harness 優先用 Bash 的 prompt 互相拉扯；這個做法依效果抓到每一種寫入途徑，並為 Bash 編輯找回 diff、路徑規則和復原功能，而不只是拒絕它們。
需要：一個 git 工作區；支援 additionalContext 的 PreToolUse/PostToolUse hook；處理讀取的作業系統沙箱。原生的 /rewind 追蹤，以及取消優先用 Bash 的引導，需要廠商處理。

### S3
解法：以效果為依據的 Bash 檔案防護——一個 PreToolUse(Bash) hook 把工作區快照到影子 git repo（獨立的 GIT_DIR 和 index，遵守 .gitignore，使用 stat 快取所以保持快速）；一個 PostToolUse(Bash) hook 再快照一次並做 diff。指令實際改動的每個檔案，不論是透過 sed、heredoc、python、make 還是腳本，接著都會像 Edit 一樣處理：(1) 對照 Edit/Write 的 deny 和路徑規則檢查，違規的路徑從快照還原，並把原因回饋給模型；(2) 以合成的 payload 傳給使用者的 Write/Edit hook（formatter、linter）；(3) 以 diff 顯示，並把被動到的目錄的巢狀 CLAUDE.md 和限定路徑的規則以 additionalContext 回傳；(4) 保留為每次呼叫的還原點（bash-rewind <call>）。讀取仍交給作業系統沙箱的讀取 deny，沙箱的寫入 deny 則硬性保護機密和設定檔路徑。
和現有做法的差別：比對樣式的 hook 和 deny 規則讀的是指令文字，python、heredoc 或腳本都能繞過；阻擋也會和 harness 優先用 Bash 的引導互相拉扯。這個做法依檔案系統的效果偵測變更，所以走哪條途徑都沒關係，並加上還原點。衡量：寫入途徑（例如 rulestack 的 11 種）中被檢查、做 diff 且可還原的比例。
需要：工作區在 git 管理下（或是可以快照的目錄樹）；PreToolUse/PostToolUse hook；處理讀取的作業系統沙箱。廠商：把還原點整合進 /rewind。

## P6：沒有安全的方式把憑證交給雲端 session

問題：在廠商雲端執行非同步 agent session 的工程師，沒有安全的方式提供 API key 和其他憑證；環境設定欄位本身就警告不要把機密放在那裡。需要驗證存取的任務，要嘛無法在雲端執行，要嘛逼工程師暴露機密。

### S1
解法：單一金鑰的憑證 broker——團隊在自己的雲端帳號中，以該帳號的 workload identity 執行一個小型 HTTPS broker，所以不存在長期有效的雲端金鑰。雲端環境只存一個 network secret：給 broker.example.com 用的 bearer token，由廠商的 proxy 在流量離開 VM 之後附上，所以 session 本身不持有任何機密。broker 提供：為 AWS 和任何相容 S3 的主機（例如 R2）重新做 SigV4 簽章（例如 aws-sigv4-proxy）；私有的 npm/PyPI proxy（Verdaccio、devpi），透過 SessionStart hook 在 session 內安裝，而不是在 setup script 裡安裝；透過 HTTPS SQL 端點或通往 PgBouncer 的 WebSocket 通道存取資料庫，密碼由 PgBouncer 持有，所以 VM 不用憑證就能連 localhost；以及為其他任何 API 注入標頭。權限範圍、稽核紀錄和撤銷都放在 broker 裡，可以在 session 進行中變更，不必重新載入。
和現有做法的差別：單靠 network secret，只能用於以標頭驗證的 HTTP API，SigV4 也只支援 amazonaws；broker 把那一個標頭變成對 registry、資料庫、R2 和雲端的存取，金鑰仍然留在 VM 外，還能即時輪替。postern 和 mcp-warden 只能在本機使用。衡量：在 VM 內機密位元組為零的情況下，可以使用的憑證類型。
需要：帳號上有 network secret（Team 方案的推出和使用 CMEK 的組織是廠商端的缺口）；一個從廠商對外流量連得到的 broker，最好設 IP 允許清單。廠商（選用）：OIDC token 可以取代 bearer token。

### S2
解法：串接在 network secret proxy 後面的憑證 broker——存一個 network secret：給你自己託管的 broker 用的 bearer token，並把 broker 主機加進允許清單。廠商的 proxy 在請求離開 VM 之後附上它，所以 session 不用持有長期有效的金鑰就能連到 broker。接著 broker 會：(1) 轉送並簽署廠商 proxy 做不到的請求（R2 或 MinIO 的 SigV4、HMAC 簽章的 API）；(2) 作為公開 registry 上私有套件的 pull-through 中介（把 .npmrc 或 pip index 指向 broker 的路徑）；(3) 為非 HTTP 的用途核發短期、限定範圍的憑證：Vault 動態資料庫使用者、SSH 憑證，以及取代缺少的 OIDC token 的 AWS/GCP/Azure session 憑證，搭配分鐘級的 TTL、每個環境各自的政策，以及以 session ID 為鍵的紀錄。私有套件的安裝從 setup script 移到 SessionStart hook，因為在那裡請求會帶上機密。輪替在 broker 中進行，所以執行中的 session 不需要重新載入。
和現有做法的差別：network secret 只涵蓋送往清單上主機的 HTTP 標頭：不涵蓋 registry、setup script、R2、資料庫或免金鑰的雲端驗證；postern 和 mcp-warden 只能在本機使用。這個做法把自架的 broker 放在廠商唯一能注入的那個憑證後面。衡量：在環境變數、檔案或對話紀錄中長期機密為零的情況下，可以使用的憑證類型。
需要：network secret（Team 方案的可用性和 CMEK 支援需要廠商處理）；一個託管的 broker 加上 Vault/STS；短期憑證仍會進入 VM，但受 TTL 和權限範圍限制。

### S3
解法：以 attestation 驗證的憑證 broker——一個由客戶自己執行的服務（容器或 Cloudflare Worker），持有所有真正的機密；雲端 session 只向它驗證身分，使用一個限定給 broker 主機的 network secret；在無法使用 network secret 的情況下（Team、CMEK），則使用 GitHub attestation：session 透過廠商的 GitHub proxy 把一個 nonce ref push 到指定的 repo，broker 驗證 push 的人和 repo 之後，才核發一個綁定該 repo、有效 15 分鐘的 token。broker 以任何驗證機制反向代理 HTTP（R2 和其他相容 S3 主機的 SigV4、私有 registry）；作為 AWS、GCP 和 Azure 信任的 OIDC 簽發者，讓 session 用 token 換取短期的雲端角色；透過 WebSocket 建立 Postgres、MySQL 和 SSH 通道，在伺服器端注入憑證；並以稽核紀錄執行每個 repo 各自的政策。機密在 broker 輪替，立即套用到執行中的 session。相依套件的安裝從 setup script 移到 SessionStart hook。
和現有做法的差別：涵蓋 network secret 做不到的部分：非 HTTP 協定、非 AWS 的 SigV4、免金鑰的雲端聯合身分、Team 和 CMEK 組織、session 中途的變更。和 postern 或 mcp-warden 不同，它從廠商雲端連得到，而且不需要任何工程師的機器保持上線。
需要：session 能對外連到 broker 主機；廠商的 GitHub proxy 允許 push；agent proxy 支援 WebSocket（未驗證）。要讓 setup script 本身取得憑證，需要廠商處理。

## P7：在單一 session 中進行跨 repo 工作

問題：採用多 repo 架構的組織，無法用雲端或 app 的 agent session 進行跨服務的變更，因為一個 session 預設只有一個 repo、一個分支和一個 pull request。跨服務的變更，例如共用型別或 API 契約，必須手動拆成不同的 session，再人工協調。

### S1
解法：由 agent 撰寫的 changeset manifest，加上聯合 CI 和依序合併——一個 skill 讓 agent 每次跨 repo 開 PR 時都寫一份 manifest：changeset ID、PR 清單、相依關係的邊（共用型別 → API → 客戶端）、合併順序，以及每個 repo 的連結步驟（go.mod replace、npm override、pip -e）。manifest 會嵌入每個 PR 的內文。一個可重複使用的 GitHub Actions/GitLab CI 範本讀取它，把同組的其他 PR checkout 到各自的 head SHA，把它們連結起來，測試合起來的狀態，並發布一個必要的狀態「changeset N/M green」。一個小型 GitHub App 會先擋住下游 PR，直到上游 PR 合併；在全部核准且通過後，依拓撲順序合併，針對新的 main 重新測試下游，如果後面的合併失敗，就開 revert PR。一個 PreToolUse hook 在 session 期間強制執行每個 repo 各自的 push 政策（只能開 PR、分支前綴、唯讀）。
和現有做法的差別：多 repo session 和 Projects 產生的是沒有互相連結的 PR，每個都是針對其他 repo 的 main 分支測試；Zuul 或 Gerrit topic 需要龐大的基礎設施和手寫的相依關係。agent 本來就知道相依關係圖，所以 manifest 不需要額外成本。衡量：在合併前做過聯合測試的 changeset；main 被弄壞的事件。
需要：能讀取同組其他 repo 的 CI token；有合併權限的 GitHub App；分支保護。廠商：在 session UI 中把 changeset 顯示成一個單位，以及多 repo 的 teleport。

### S2
解法：change-set 閘門——一個 session 的 Stop hook（或 skill），在 session 於多個 repo 開了 PR 之後，寫出一份 manifest：change-set ID、成員 PR、從相依檔推導出的合併順序（如果 repo B 的 package.json、go.mod 或 pyproject 引用了 repo A 的套件，就先合併 A），以及動到的契約。它在每個 PR 內文中標上「Change-Set: <id>」和「Depends-On: org/repo#n」，並開一個追蹤 issue，連結所有的 diff。接著每個 repo 裡一個可重複使用的 GitHub Action 會：(1) 透過 npm overrides、go replace 或 pip git URL，針對同組其他 PR 的 head 建置和測試，讓契約破壞在合併前就失敗；(2) 提供一個必要的「changeset-order」檢查，在前面的 PR 合併前一直保持 pending，如果同組的其他 PR 在核准後有變更，就重設。每個 repo 各自的 .agent-policy.yml（只能開草稿、不能 push 到受保護分支、禁止的路徑）由掛在 git push 和 gh pr create 上的 PreToolUse hook 強制執行。
和現有做法的差別：現在的多 repo session 產生的是互相獨立的 PR，而 Zuul 式的 Depends-On 閘門需要自己的 CI 基礎設施。這個做法用一般的 GitHub Actions，加上 session 自己知道改了什麼，來提供互相連結的 PR、強制的合併順序、跨 repo 測試和每個 repo 各自的 push 政策。衡量：因為合併順序錯誤而弄壞 main 的事件。
需要：GitHub Actions 和分支保護；各生態系的 override 做法；在雲端 session 中執行的 hook（repo 設定）。廠商：多 repo 的 teleport 和原生的 change-set 檢視。

### S3
解法：change-set 協調器——一個 GitHub/GitLab app 加上 CLI，把各 repo 的 PR 變成一個可以審查、可以合併的單位。任何 agent（多 repo 的網頁 session、Codex 多資料夾、本機）在各 repo 使用同一個分支名稱或 PR 標籤 `cs/<id>`，並 commit 一個 `changeset.yaml`（repo、相依順序、契約說明）。app 會找出這組裡的每個 PR，發布一則共用的狀態留言和一個整合的 diff 頁面，並執行一個聯合 CI job，把所有分支一起 checkout，透過 workspace override（pnpm overrides、go.work、Cargo [patch]、Maven snapshots）讓下游 repo 針對上游分支建置。一個必要的 `changeset` 檢查會擋下部分合併；核准後，它以依序的合併列車方式合併，把下游鎖定的版本更新到上游已發布的版本，如果某一步失敗就暫停。每個 repo 各自的 `.agent-policy` 檔會編譯成分支 ruleset（可寫入的前綴、受保護的路徑）。`cs checkout <id>` 把這組變更重建成本機的 worktree：透過 git 做到多 repo 的 teleport。
和現有做法的差別：現有工具產生互相獨立的 PR，或是協調 session；沒有一個會把整組一起測試，或強制合併順序。這個做法加上原子化審查、聯合 CI、依序合併、每個 repo 各自的 push 政策，以及以 git 為基礎的 teleport，不論分支是哪個 agent 產生的。
需要：app 要有讀取、檢查和合併 PR 的權限；CI 要能 clone 多個 repo；套件管理工具的 override。不需要廠商改動；要在 agent UI 中顯示 change set，需要廠商處理。

## P8：無人值守的工作在用量上限時停止

問題：當一個長時間的委派任務碰到 5 小時或每週用量上限時，即使已經知道重置時間，agent 還是會停下來。如果重置時間落在半夜，工作就要等到工程師回來，找到 session，再重新下 prompt。

### S1
解法：能感知上限的持久 job 執行器——任務以 job 的形式在作業系統排程器（systemd user unit、launchd、Task Scheduler）下執行，而不是在終端機裡。每筆 job 紀錄包含 session ID、目錄、目標，以及只適用於該 job 的權限設定檔。執行器以 JSON 輸出啟動 claude -p 或 codex exec；碰到上限時，它從機器可讀的資料取得重置時間（result 事件，或透過本機直通 proxy 取得的 rate-limit 回應標頭），退而求其次用低成本的探測呼叫，絕不讀螢幕文字。它設定一個喚醒計時器，即使是超過 24 小時的每週重置、筆電在睡眠中也一樣，然後用 --resume <id> 或 codex exec resume 接續，並給一個固定的 prompt：檢查 git status 和你的待辦清單，然後繼續。不在清單上的動作會被拒絕並記錄，而不是跳出確認，所以接續的 job 永遠不會卡住；拒絕和完成都會觸發通知。每個 job 可選的政策：等待，或改用 API key 繼續，最多花 $X。
和現有做法的差別：內建的自動繼續需要一個開著的互動式終端機，不支援 -p、背景執行、超過 24 小時的重置和 Remote Control，而且仍會卡在確認提示上；wrapper 擷取會變動的輸出，在已經達到上限時會失敗。衡量：在不需要人工操作的情況下，於重置後五分鐘內接續的上限停止比例。
需要：依 session ID 進行 headless 接續（Claude Code、codex exec resume）；支援喚醒的作業系統排程器。廠商：有文件的重置時間欄位，就不需要 proxy 和探測。

### S2
解法：持久的接續排程器——一個 wrapper 把每個無人值守的任務當作一筆 job 紀錄（session ID、cwd、目標、權限設定檔）來執行，以 headless 方式和 stream-json 輸出啟動 agent。上限是從結構化的 result/error 事件辨識；如果啟動時就已經超過上限，則從探測呼叫辨識，絕不從 TUI 文字辨識。碰到上限時，它計算重置時間（5 小時或每週，不論多久之後），commit 一個 WIP 檢查點，並註冊一個作業系統喚醒 job：macOS 用 pmset/launchd，Linux 用設了 WakeSystem=true 的 systemd timer，Windows 用 Task Scheduler 的「wake to run」。在重置時間加兩分鐘時，機器會喚醒，保持 caffeinate/systemd-inhibit，並在預先核准的允許清單下執行 `claude --resume <id> -p continue` 或 `codex exec resume <id>`；其他權限請求會交給一個 prompt 工具，它會附上理由拒絕並發出通知，而不是卡住。如果接續失敗，就從目標、WIP diff 和對話紀錄的最後幾個回合開始一個新的 session。
和現有做法的差別：內建的自動繼續需要一個開著且醒著的互動式行程；claude-auto-resume 解析畫面上的文字。這個做法在終端機關閉、睡眠和重新開機後仍能運作，涵蓋 -p、背景執行和每週重置，而且永遠不會卡在確認提示上。衡量：在無人值守的情況下，於重置後五分鐘內接續的上限停止比例。
需要：作業系統喚醒計時器（筆電要接電源；闔上螢幕時能否喚醒因硬體而異）、依 session ID 進行 headless 接續。廠商（選用）：在結構化輸出中提供重置時間戳記，就不需要探測。

### S3
解法：接續排程器——把接續變成一個排程 job，而不是一個等待中的行程。委派的任務在一個監督程式下以 headless 方式執行（`claude -p --output-format stream-json`、`codex exec --json`），監督程式會記錄 session id、cwd 和目標，並指示 agent 持續更新 `progress.md`。當一次執行因上限而結束時，監督程式讀取結構化的錯誤和其中的重置時間，絕不讀給人看的訊息；如果沒有重置時間，就排程低成本的探測執行。接著它註冊一個能從睡眠喚醒的作業系統計時器（systemd WakeSystem timer；launchd 加上 `pmset schedule wake`），不論多久之後都可以，包括每週重置，計時器會執行 `claude -p --resume <id>` 或 `codex exec resume <id>`，並附上「已重置上限；從 progress.md 繼續」。接續的執行使用預先核准的權限設定檔，加上一個拒絕並說明原因的 hook，所以不會有任何東西卡在確認提示上；遇到特定模型的上限時，會切換到設定好的備援模型。選用：接近截止期限時，改用有花費上限的 API key 繼續。
和現有做法的差別：沒有任何東西在行程內等待，所以睡眠、關閉的終端機和 Remote Control 都不影響；它涵蓋 -p、背景執行和每週重置，在已經超過上限時也能啟動，訊息格式改變也不受影響，而且接續的工作不會卡在權限確認提示上。
需要：headless 接續（Claude Code 和 Codex 都有）；具喚醒功能的作業系統排程器。如果 headless 輸出中有文件化、機器可讀的重置時間，排程就能精確（廠商）。

## P9：沒辦法排好接下來的任務

問題：已經知道 agent 接下來該做哪幾件事的工程師，無法把它們排進佇列：他們必須等每個任務完成才能交代下一個，而在 VS Code 擴充功能中，新訊息會打斷正在執行的任務，而不是等輪到它。委派仍然是一回合一回合進行，工程師必須在任務之間一直在場。

### S1
解法：放在 repo 檔案中、設有放行條件的任務佇列——接下來的任務放在 .agent/queue.md，這是一份有順序的檢查清單，可以在任何編輯器中編輯和重新排序，並納入版本控制，所以沒有任何聊天輸入框能打斷或弄丟它們。項目可以帶有 done-when:（一個指令，例如 npm test）和 fresh: true。一個 Stop hook 在回合結束時動作。注入的任務會要求 agent 以一行標記結尾，DONE 或 NEEDS-INPUT: <question>；遇到 NEEDS-INPUT 或有待回答的問題時，hook 會暫停佇列並發出通知。遇到 DONE 時，它執行 done-when 檢查：失敗就把輸出回饋回去（最多重試 N 次，然後暫停）；通過就勾選該項目，標上時間和 commit SHA，並把下一個項目當作新指示注入，或者對 fresh 項目啟動新的 session，以取得乾淨的 context。在聊天中輸入仍然是用來引導方向；檔案只放接下來的任務。
和現有做法的差別：內建的佇列會把訊息併入正在執行的回合，或把它們合併、打斷、弄丟；claudeq 這類 FIFO 即使上一個任務失敗或 agent 提出了問題，仍會推送下一個任務。這個做法讓每次取出都以驗證過的結果為放行條件。衡量：每個無人值守小時完成的任務數；錯誤的取出次數。
需要：Stop hook（Claude Code；Codex hooks）；為 fresh 項目啟動 session 的啟動器。不需要廠商改動；原生的「等到回合結束才送出」模式會讓它更簡單。

### S2
解法：佇列檔加上 Stop hook 派發器——佇列是工作區中的一份純 markdown 檢查清單（.agent/queue.md），工程師可以在任何編輯器中編輯（新增、重新排序、刪除行），或從另一個終端機用 `q add "…"` 追加；agent 工作時，不會在聊天中輸入任何東西。當 agent 即將停止時，一個 Stop hook 會檢查暫停條件：最後一則訊息向使用者提問、有權限被拒絕、任務的檢查指令失敗，或有 PAUSE 這一行。如果都不成立，它就把目前的項目標記為完成並附上 commit SHA，認領下一個未勾選的項目，並回傳 decision「block」，以該項目作為理由，讓同一個 session 在保有完整 context 的情況下，把它當作下一個任務開始。一個項目就是一個任務，嚴格依序，絕不在回合中途注入。佇列清空時正常結束，並發出通知。
和現有做法的差別：因為執行中不會有任何東西進入聊天輸入框，所以避開了 VS Code 的打斷、回合中途併入、回合被合併和桌面版訊息遺失；和 claudeq 或 cmux-claude-queue 不同，它不需要側邊窗格或特定的終端機，而且佇列會保存下來、可以編輯。衡量：排入佇列的任務以獨立任務執行、依序、沒有遺失。
需要：一個能附上理由繼續執行的 Stop hook（Claude Code；Codex 在有支援的地方），並有防止無限迴圈的保護；在每個使用的介面中 hook 都要啟用。廠商（選用）：原生的「等到回合結束才送出」佇列。

### S3
解法：佇列檔加上 Stop hook 派發器。任務放在 `.agent/queue.md`，每個任務一個區塊，可選擇加上 `verify:` 指令、`after:` 相依和 `fresh: true`，可以在任何編輯器中編輯，或透過 CLI（`q add`）或一個小型 VS Code 面板編輯。Stop hook（Claude Code Stop、Codex Stop、Gemini AfterAgent）只在回合真正結束時觸發；如果回合正常結束且還有剩下的任務，派發器就執行已完成任務的 `verify:` 指令，可選擇 commit 一個檢查點，然後以下一個任務作為理由擋下停止，讓每個排入佇列的任務在前一個完成後成為下一個指示。檢查失敗時會重新提示一次，然後暫停佇列並發出通知。`fresh` 任務在 worktree 中以獨立的 headless session 執行，以取得乾淨的 context。輸入永遠不經過聊天框，所以不會發生回合中途併入、VS Code 打斷和桌面版訊息遺失。
和現有做法的差別：內建的佇列會在回合中途併入訊息、把它們合併或弄丟；第三方佇列綁定特定 UI 或平台，而且沒有驗證。這個做法可以持久保存，不綁定特定 agent 或介面，嚴格做到每個完成的回合一個任務，並以驗證成功作為放行條件。
需要：具有 block 加理由語意的 Stop hook（Claude Code、Codex、Gemini）；佇列清空時迴圈就結束。原生的「等到回合結束才送出」設定需要廠商處理。
