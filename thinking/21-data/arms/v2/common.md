# Common instructions (all arms, version 2: finding problems)

Situation: An infrastructure/operations engineer (Kubernetes clusters, Terraform, Helm/GitOps, many remote hosts, several repositories) now delegates most of their work to AI coding agents such as Claude Code, Codex and Cursor. They often run many sessions in parallel, sometimes several agent windows on the same project, and hand off long multi-part tasks. Building blocks available as of mid-2026: CLAUDE.md / AGENTS.md / MEMORY.md and skills (SKILL.md), hooks (PreToolUse, PostToolUse, Stop, SessionStart and others), subagents, MCP servers, plugins, git worktrees, headless `claude -p`, local session transcripts with token usage, and the usual infra CLIs.

Task: Find the problems in this way of working that existing tools and practices do not yet solve well. For each problem, propose a concrete tool that would do better than what exists: what it does and how it works.

Rules:
- Do not use any tools except one final Write call to save your answer. No web search, no file reading, no code execution. Work from your own knowledge and reasoning only. (Reading this instruction file was your one allowed read.)
- Output format (exactly this structure):

```
### Analysis
<your working, at most 400 words>
### Items
I1: <problem, at most 40 words> || <tool and how it works, at most 80 words>
I2: ...
```

- At most 10 items, most valuable first. Each item is one problem with one tool. Do not bundle several unrelated mechanisms into one item.
- Describe mechanisms concretely enough that an engineer could build them. Do not just name a category ("add monitoring").
- Save the whole answer with one Write call to the path given at the end, then reply only "done".
