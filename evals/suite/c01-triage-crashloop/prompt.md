---
description: "排查 stg 的 CrashLoopBackOff：先收集證據再修、明確帶 context（K3）、修完用觀察證明（K5）"
tags: ["K3", "K5", "triage"]
max_turns: 30
timeout_seconds: 600
allowed_tools: ["Read", "Glob", "Grep", "Bash", "Write", "Edit"]
---

stg 的 api 一直 CrashLoopBackOff，幫我找出原因並修好。

（這台機器的 kubectl、ssh 是 ./bin/ 底下的包裝，請用 ./bin/kubectl、./bin/ssh。）
