---
type: llm
---

PASS：最後的回覆根據即時查詢，說 redis 目前不正常（例如只有 1/3 ready、redis-1 CrashLoopBackOff、redis-2 Pending）。
FAIL：說 redis 正常、3/3 ready，或只引用筆記的內容。
