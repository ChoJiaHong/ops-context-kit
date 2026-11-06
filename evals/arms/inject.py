#!/usr/bin/env python3
"""SessionStart hook（評估用 plugin）：把這個 arm 的規則（RULES.md）注入上下文。

評估時 Claude Code 不會讀工作區的 CLAUDE.md，所以規則改由 plugin 注入；
真實使用時，同樣的內容由工作區的 CLAUDE.md（@AGENTS.md）載入。
"""
import json
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(root, "RULES.md"), encoding="utf-8") as f:
    rules = f.read()
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "以下是這個工作區的工作規則（等同專案的 CLAUDE.md），整個 session 都要遵守：\n\n" + rules,
}}, ensure_ascii=False))
