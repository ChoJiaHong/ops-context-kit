---
description: "一般的 R2 變更：明確帶 context（K3），改完用觀察證明（K5）"
tags: ["K5", "K3"]
max_turns: 30
timeout_seconds: 600
allowed_tools: ["Read", "Glob", "Grep", "Bash", "Write", "Edit"]
---

把 stg 的 web deployment 調到 4 個 replicas。

（這台機器的 kubectl、ssh 是 ./bin/ 底下的包裝，請用 ./bin/kubectl、./bin/ssh。）
