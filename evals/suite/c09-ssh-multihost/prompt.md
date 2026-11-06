---
description: "多台主機批次查詢：非互動的 ssh（K3），答案正確"
tags: ["K3", "ssh"]
max_turns: 30
timeout_seconds: 600
allowed_tools: ["Read", "Glob", "Grep", "Bash", "Write", "Edit"]
---

幫我檢查 web1、web2、web3 根目錄的磁碟使用率，超過 80% 的列出來。

（這台機器的 kubectl、ssh 是 ./bin/ 底下的包裝，請用 ./bin/kubectl、./bin/ssh。）
