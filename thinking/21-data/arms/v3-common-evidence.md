# Common instructions (all arms, version 2: finding problems)

Situation: An infrastructure/operations engineer (Kubernetes clusters, Terraform, Helm/GitOps, many remote hosts, several repositories) now delegates most of their work to AI coding agents such as Claude Code, Codex and Cursor. They often run many sessions in parallel, sometimes several agent windows on the same project, and hand off long multi-part tasks. Building blocks available as of mid-2026: CLAUDE.md / AGENTS.md / MEMORY.md and skills (SKILL.md), hooks (PreToolUse, PostToolUse, Stop, SessionStart and others), subagents, MCP servers, plugins, git worktrees, headless `claude -p`, local session transcripts with token usage, and the usual infra CLIs.

Evidence about real pains (titles of the 100 most-reacted issues filed on the Claude Code GitHub repository, January to June 2026). Use it as evidence about what people actually struggle with; it is not a to-do list, and the best problems may be ones the titles only hint at.

- 2026-04-02 | 3286 | [MODEL] Claude Code is unusable for complex engineering tasks with the Feb updates
- 2026-04-09 | 2117 | Bring Back Buddy — A Consolidated Plea from the Community
- 2026-01-09 | 1414 | [Feature Request] Support for OpenCode and Max plan
- 2026-01-15 | 1310 | [FEATURE] Add the ability to manage multiple Claude accounts within the Claude Desktop app with easy switching between profiles.
- 2026-03-19 | 1078 | [FEATURE] Multi-account switching in Claude Mobile app without shared email
- 2026-03-14 | 893 | [BUG] Phone verification
- 2026-01-03 | 728 | [BUG] Instantly hitting usage limits with Max subscription
- 2026-06-05 | 655 | [FEATURE] Official Claude Desktop build for Linux (Ubuntu LTS / Debian)
- 2026-01-11 | 646 | Feature Request: India-Specific Pricing Plans (INR) for Claude & Claude Code
- 2026-02-21 | 647 | [FEATURE] Support multiple Connector accounts (same connector, different accounts) in Claude and Claude Code on the web (claude.ai/code)
- 2026-01-01 | 616 | Add support for Visual Studio 2026 Integration
- 2026-03-05 | 604 | Support for AGENTS.md and .agents/skills/, the community has been asking since August 2025
- 2026-03-24 | 546 | [BUG] Claude Max plan session limits exhausted abnormally fast since March 23, 2026 (CLI usage)
- 2026-04-25 | 532 | HERMES.md in git commit messages causes requests to route to extra usage billing instead of plan quota
- 2026-04-12 | 341 | Cache TTL silently regressed from 1h to 5m around early March 2026, causing quota and cost inflation
- 2026-03-13 | 313 | [FEATURE] VS Code Extension: Diff review UI similar to GitHub Copilot Edits Review
- 2026-01-14 | 303 | Copy/paste from terminal includes unwanted indentation and trailing spaces
- 2026-03-02 | 288 | FEATURE: Multi-window support in Claude Code Desktop
- 2026-02-02 | 278 | Cowork feature creates 10GB VM bundle that severely degrades performance
- 2026-02-10 | 272 | [FEATURE] VS Code extension: add setting to disable auto-attach of open file / selection
- 2026-06-07 | 256 | [MODEL] Claude verbose code comments by default — ignores instructions to stop.
- 2026-04-18 | 255 | Feature Request: Message queue mode — queue messages instead of interrupting active tasks
- 2026-03-10 | 241 | [FEATURE] Support Amazon Bedrock as backend for Claude Desktop / Cowork
- 2026-01-06 | 238 | [BUG] github-actions incorrectly closed a bunch of issues for "60 days of inactivity"
- 2026-03-22 | 227 | Support /btw command in VS Code extension
- 2026-03-29 | 223 | [BUG] Conversation history invalidated on subsequent turns
- 2026-04-12 | 219 | CC v2.1.100+ inflates cache_creation by ~20K tokens vs v2.1.98 — same payload, server-side
- 2026-03-10 | 215 | [FEATURE] Secure secrets injection for Claude Code on the web
- 2026-01-02 | 215 | [FEATURE] Menu Bar Only Mode (Hide Dock Icon Option)
- 2026-02-24 | 209 | [BUG] Permission prompt incorrectly triggers on cd instead of the actual command in compound bash statements
- 2026-04-13 | 198 | feat: Team plan needs a Max 20x equivalent tier for power users
- 2026-04-12 | 197 | [BUG]  API Error: Stream idle timeout - partial response received - multiple time today
- 2026-02-04 | 191 | Feature Request: Option to disable paste text collapse in input field
- 2026-02-11 | 190 | [BUG] Cowork: Folder picker rejects folders outside home directory, symlinks/junctions also blocked
- 2026-04-26 | 185 | [MODEL] Claude Code can not stop using the word "load-bearing"
- 2026-01-27 | 186 | [FEATURE] No indication of WHICH file for READ tool
- 2026-02-26 | 187 | [FEATURE] Sync conversation history between CLI and Claude Code desktop app
- 2026-01-24 | 183 | [Bug] VS Code extension: Tool use concurrency error after Jan 23-24 update
- 2026-01-07 | 177 | [BUG] Invalid Version: 2.1.0 (2026-01-07)
- 2026-01-07 | 176 | Feature: Parse compound Bash commands and match each component against permissions
- 2026-01-25 | 171 | [FEATURE] Sync Skills between Claude Desktop and Claude Code CLI
- 2026-04-08 | 163 | [BUG] Disabling telemetry also disables 1-hour prompt cache TTL
- 2026-02-26 | 165 | Enable Remote Control for Claude Code sessions in Claude Desktop App
- 2026-01-16 | 164 | [FEATURE] VSCode Extension: Display context usage percentage in UI
- 2026-01-06 | 162 | [FEATURE] LaTeX rendering in "Claude Code for VS Code" plugin
- 2026-04-09 | 160 | [BUG] Pro Max 5x Quota Exhausted in 1.5 Hours Despite Moderate Usage
- 2026-03-30 | 159 | [FEATURE] Enable Auto mode support for Amazon Bedrock models
- 2026-02-25 | 159 | [FEATURE] Link a source control repo as the source for organization skills
- 2026-03-09 | 153 | [BUG] GitHub Connector connected in Claude Desktop but not recognized by Claude
- 2026-02-17 | 152 | [BUG] [URGENT!!!] Claude Code is hanging / freezing / stuck on heaps of prompts for 5-20minutes or more.
- 2026-04-01 | 149 | [Feature Request] Buddy customization, progression system & monetization — a paying user's perspective
- 2026-02-11 | 148 | [FEATURE] allow skills to programmatically rename sessions
- 2026-02-28 | 143 | [BUG] Cowork: Cannot use folders outside home directory on Windows (secondary drive)
- 2026-02-06 | 143 | [FEATURE] Support diff comparison against branches other than main
- 2026-01-23 | 142 | Claude.ai MCP servers auto-injected into Claude Code without opt-in — causes OOM crashes on resource-constrained systems
- 2026-02-25 | 138 | [FEATURE] Allow slash command usage over remote-control
- 2026-01-08 | 137 | Feature Request: Add Dart/Flutter LSP support
- 2026-02-26 | 136 | [FEATURE] Support AWS Bedrock + AWS SSO in `claude remote-control`
- 2026-03-20 | 135 | Terminal keeps scrolling to top when conversation gets long
- 2026-03-14 | 135 | Feature request: support AGENTS.md as a native context file alongside CLAUDE.md
- 2026-04-15 | 135 | [FEATURE] Add font size adjustment for Code tab in Claude Desktop
- 2026-02-20 | 131 | [FEATURE] Preview: Allow configurable external URL whitelist for OAuth and other third-party required flows
- 2026-04-01 | 130 | Messages disappear from terminal display during conversation after v2.1.89 update
- 2026-04-06 | 130 | Feature request: Support multiple Slack workspaces in the built-in Slack connector
- 2026-06-06 | 130 | v2.1.150: scroll wheel no longer scrolls conversation — sends arrow keys instead
- 2026-01-13 | 129 | [FEATURE] Support JSONC format for settings files (settings.jsonc)
- 2026-03-23 | 128 | Option to hide inline diffs for Edit/Write tool output
- 2026-01-21 | 124 | [MODEL] Frequently uses Bash tools (sed/grep/etc) when use-case is well aligned to other builtin tools (Read/Grep/etc)
- 2026-01-03 | 124 | [FEATURE] AWS Bedrock authentication support for Chrome extension
- 2026-06-09 | 123 | [FEATURE] Session URL appended to commit messages and PR descriptions by default — should be opt-in
- 2026-03-23 | 122 | RTL (Right-to-Left) Support for Hebrew & Arabic in Claude Desktop / Cowork
- 2026-03-29 | 121 | My automated tool is running git reset --hard origin/main in my project every 10 minutes
- 2026-06-18 | 120 | [BUG] No response from API error when Advisor is triggered
- 2026-05-30 | 116 | Recurring error: "The model's tool call could not be parsed (retry also failed)" interrupts sessions
- 2026-03-13 | 117 | VSCode extension: add font size setting for chat panel
- 2026-01-11 | 117 | [Feature Request] Enhanced /compact with file-backed summaries and selective restoration
- 2026-02-19 | 117 | [FEATURE] Add /delete command to delete current session
- 2026-05-25 | 114 | [Bug] Anthropic API Error: Model's tool call could not be parsed (retry also failed)
- 2026-01-22 | 115 | Feature Request: Multi-Account Profile Support
- 2026-03-14 | 112 | [BUG] Remote Control: automatic reconnection doesn't work -- connection drops silently with no recovery
- 2026-01-27 | 110 | [FEATURE] Option to disable automatic git worktree creation for linked repositories
- 2026-04-07 | 109 | Show timestamps on conversation messages
- 2026-03-27 | 108 | Allow removal of local folders from a Cowork project's context
- 2026-03-18 | 106 | [FEATURE] Auto-continue after subscription rate limit resets
- 2026-01-23 | 105 | Feature Request: Microsoft 365 Connector for Max Plan Individual Users
- 2026-03-04 | 103 | cowork for ARM processor
- 2026-01-26 | 102 | [FEATURE] - Add Setting to Disable Automatic IDE Selection Context
- 2026-02-27 | 102 | Feature request: Allow Claude to programmatically rename sessions
- 2026-03-02 | 100 | Feature Request: Support multiple account login and switching (like `gh auth switch`)
- 2026-02-06 | 100 | [FEATURE] Multi-repository support for remote/web sessions
- 2026-04-08 | 99 | [FEATURE] Add Scala (Metals) to the native LSP plugin lineup
- 2026-04-02 | 98 | [BUG] Claude Code Desktop fails to Relaunch on Windows due to orphaned process file lock
- 2026-06-18 | 98 | [BUG] API Error: Connection closed mid-response ==> frequent enough to make Claude Code unusable for any task
- 2026-04-01 | 97 | [BUG] Critical: Widespread abnormal usage limit drain across all paid tiers since March 23, 2026 — multiple root causes identified, no formal communication issued
- 2026-04-16 | 97 | [BUG] Opus 4.7 doesn't work with bedrock
- 2026-02-08 | 96 | Agent Teams: Add zellij terminal multiplexer support for split-pane mode
- 2026-02-18 | 94 | Migrate Claude Cowork from Electron to Electrobun
- 2026-02-28 | 94 | [BUG] API Error: Rate limit reached despite Claude Max subscription and only 16% usage
- 2026-06-05 | 94 | [BUG] Inline KaTeX math (`$...$`) no longer renders in chat output — only block `$$...$$` works (regression)
- 2026-01-30 | 92 | [BUG] Critical memory regression in 2.1.27 - OOM crash on simple input

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
