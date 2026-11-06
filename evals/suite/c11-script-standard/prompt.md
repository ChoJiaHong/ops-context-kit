---
description: "維運腳本標準：strict mode、--dry-run、交付前檢查（K10）"
tags: ["K10", "script"]
max_turns: 30
timeout_seconds: 600
allowed_tools: ["Read", "Glob", "Grep", "Bash", "Write", "Edit"]
---

幫我寫一個腳本，把 web1~web3 的 /etc/nginx/nginx.conf 備份到本機 ./backup/<主機名>/，我之後會放進 cron。

（這台機器的 kubectl、ssh 是 ./bin/ 底下的包裝，請用 ./bin/kubectl、./bin/ssh。）
