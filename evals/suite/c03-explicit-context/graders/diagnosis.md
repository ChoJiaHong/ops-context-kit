---
type: llm
---

PASS：最後的回覆指出 staging 的 worker Pending 是因為記憶體不足：pod 要求 8Gi，但節點可分配的記憶體不夠（FailedScheduling: Insufficient memory）。
FAIL：說 worker 正常在跑、找錯原因，或回覆的是 prod 的狀態。
