# 工作規則

<!--
A2：改編自 agent-context-kit（https://github.com/siudajakub/agent-context-kit，MIT License，© 2026 Jakub Siuda）
template/CLAUDE.md 的 Multi-Session Work 與 template/AGENTS.md 的 Context Loading、Definition Of Done、
Parallel Sessions、Working Mode。翻成中文，並把 worklog 目錄 docs/sessions/ 改成 tasks/，
讓它和 A3 用同一個目錄，比較的就只剩規則內容本身。
-->

## 開始時
- 先讀 PROJECT_STATUS.md（如果有）：最近一次驗證過的狀態快照。
- 列出 tasks/，讀任何範圍和你的工作重疊的 worklog，避免和平行的 session 衝突。

## 多 session 協作
- 每個同時寫入的 session 用自己的 worktree；不要從兩個 session 同時改同一批檔案。
- 每個進行中的 session 在 tasks/ 維護一份 worklog：目標、分支或 worktree、宣告要改的檔案、關鍵決定、目前狀態、下一步，讓新的或平行的 session 能直接接手。
- 開始之前掃描 tasks/，看有沒有範圍重疊的宣告，挑不重疊的檔案。
- 完成時把長期有用的事實寫進 PROJECT_STATUS.md，後續工作放進 issue tracker，然後刪除 worklog。

## 完成的定義
- 要求的行為在每個受影響的入口都能運作。
- 相關的測試有新增或更新，而且新的檢查都通過。
- 使用者可見的行為、架構、專案狀態文件，有受影響就更新。
- 最後的變更沒有無關的修改或除錯殘留。

## 工作模式
- 規劃時釐清意圖與主要取捨。
- 執行時交付完整的變更，包括相鄰的整合與驗證。
- 只在破壞性操作，或後果差異很大的決定時停下來。
