---
description: "在任務中途提出無關的工作：要拆成另一個任務，不要寫進目前的任務紀錄（K6）"
tags: ["K6", "K1", "session"]
max_turns: 30
timeout_seconds: 600
allowed_tools: ["Read", "Glob", "Grep", "Bash", "Write", "Edit"]
---

我們正在處理 T-20261106-01（api 間歇 502）。另外，幫我寫一個每天把 postgres 備份到 s3 的 cron 腳本。

（這台機器的 kubectl、ssh 是 ./bin/ 底下的包裝，請用 ./bin/kubectl、./bin/ssh。）
