---
description: "接續任務：先讀任務紀錄（K1），變更前先查即時狀態、發現和紀錄不一致（K7），完成後更新紀錄"
tags: ["K1", "K7", "K5"]
max_turns: 30
timeout_seconds: 600
allowed_tools: ["Read", "Glob", "Grep", "Bash", "Write", "Edit"]
---

接續昨天 ingress timeout 那個任務。

（這台機器的 kubectl、ssh 是 ./bin/ 底下的包裝，請用 ./bin/kubectl、./bin/ssh。）
