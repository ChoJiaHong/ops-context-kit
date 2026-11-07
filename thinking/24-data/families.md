# Problem families: agent-delegation pain points from open issues

Sources: candidates-raw.md (250 entries collected 2026-11-07; C101 to C150 repeated C051 to C100 because of a pagination bug and are ignored) and candidates-addendum.md (C251 to C300, the real ranks 101 to 150 for anthropics/claude-code). That gives 250 unique issues. Kept 85 issues in 29 families; dropped 165. Reactions are as listed in the sources.

Family ids F01 to F25 come from the first pass and are unchanged; F26 to F29 were added with the addendum. Families are sorted by total reactions, descending, so ids are not in numeric order.

## F01: Agent harness leaks the engineer's personal identity

- **id:** F01
- **problem:** Engineers who let the agent search or fetch from the web find that the harness puts their account email into outbound request headers sent to arbitrary sites, and also injects it into the model's system prompt every session, without asking. Their identity reaches third parties they never chose (one reporter ties it to daily scam mail), so delegating web research quietly costs privacy.
- **issues:**
  - anthropics/claude-code#107757 (951)
  - anthropics/claude-code#81138 (107)
- **total_reactions:** 1058
- **third_party_solvable:** An egress proxy or wrapper can strip identifying headers and fields from outgoing requests, and a hook can deny the built-in web tools in favour of an MCP fetch server that uses a neutral identity.

## F02: No way back to the state before an agent turn

- **id:** F02
- **problem:** When an agent deletes untracked files or makes unwanted edits, engineers cannot return to the workspace as it was before a given turn: rewinding the conversation does not revert the files, and editing an earlier message does not undo the edits that followed it. Work not yet committed to git can be lost outright, so engineers commit defensively or hesitate to let the agent run.
- **issues:**
  - openai/codex#9203 (547)
  - openai/codex#11626 (231)
  - openai/codex#2948 (85)
  - openai/codex#11086 (84)
- **total_reactions:** 947
- **third_party_solvable:** Hooks or wrappers can snapshot the working tree, untracked files included, before each turn or edit and restore a chosen snapshot together with its point in the conversation.

## F05: Agents work without code intelligence

- **id:** F05
- **problem:** Agents edit real, often multi-language repositories without language-server diagnostics, symbol information or a codebase index: Codex CLI has no language-server support, Claude Code's native language-server plugins skip languages such as Ruby and Scala, and installed language-server plugins can silently fail to load. The agent produces edits that do not compile or resolve the wrong symbols, and burns tokens searching the codebase for what an index would answer.
- **issues:**
  - openai/codex#8745 (614)
  - anthropics/claude-code#45132 (99)
  - anthropics/claude-code#14818 (75)
  - anthropics/claude-code#15148 (73)
  - anthropics/claude-code#4556 (69)
- **total_reactions:** 930
- **third_party_solvable:** LSP-bridging MCP servers, code-index or semantic-search MCP servers, and post-edit hooks that run type checkers can give the agent diagnostics, symbol lookups and search for any language.

## F03: One account per external service in a session

- **id:** F03
- **problem:** Engineers whose agent works with external services (Gmail, Slack, Drive, calendars, GitHub) often have separate personal, employer and client accounts for the same service, but a session can connect only one account per connector. Switching means disconnecting and reconnecting, and the agent can act in the wrong account, crossing privacy boundaries between employers or clients.
- **issues:**
  - anthropics/claude-code#27302 (647)
  - openai/codex#20500 (147)
- **total_reactions:** 794
- **third_party_solvable:** MCP servers can hold several named credentials for the same service and require an explicit account choice on each call, without any change from the vendor.

## F04: Project instructions fragmented across agents and directories

- **id:** F04
- **problem:** Teams that use more than one agent must keep the same project guidance in tool-specific files and folders (CLAUDE.md, AGENTS.md, .agents/skills), and within one repository it is unclear whether nested instruction files in subdirectories load and override the root file. Instructions drift between tools and directories, and engineers cannot tell which rules an agent actually received.
- **issues:**
  - anthropics/claude-code#31005 (604)
  - openai/codex#12115 (127)
- **total_reactions:** 731
- **third_party_solvable:** A generator or sync convention can render one canonical instruction source into each agent's file format, and a linter can show which instruction files apply to a given path.

## F06: Reviewing agent changes before they land

- **id:** F06
- **problem:** Engineers who delegate changes need to inspect and accept or reject what the agent wrote, but the IDE surfaces offer no inline per-change review flow and show diffs in different places depending on which internal tool made the edit, so engineers leave the agent panel to diff by hand; the built-in automated review reports only a handful of findings. Changes slip in unreviewed, or problems the review pass could have flagged go unreported.
- **issues:**
  - anthropics/claude-code#33932 (313)
  - openai/codex#2998 (244)
  - openai/codex#5547 (87)
  - anthropics/claude-code#29388 (73)
- **total_reactions:** 717
- **third_party_solvable:** Review tools built on git diffs and staging, and custom review skills or subagents with their own criteria and depth, work independently of the vendor's UI.

## F07: Agent setup cannot be versioned and shared like code

- **id:** F07
- **problem:** Teams that want one shared, version-controlled agent setup cannot manage it as code: org skills must be uploaded one by one in an admin console, plugins cannot bundle rules or subagents, plugin and marketplace settings cannot be scoped to a repository, user config files mix portable preferences with machine-local trust entries, and project settings are not inherited from a monorepo root, so each package needs its own copy. Setups drift between teammates and machines, and every change means manual redistribution.
- **issues:**
  - anthropics/claude-code#28729 (159)
  - anthropics/claude-code#14200 (126)
  - openai/codex#11061 (95)
  - openai/codex#14601 (90)
  - openai/codex#18308 (73)
  - anthropics/claude-code#12962 (72)
  - openai/codex#18115 (68)
- **total_reactions:** 683
- **third_party_solvable:** Sync tools, repo-hosted plugin bundles and config-layering scripts can build, version and distribute skills, rules, subagents and preferences from a git repository.

## F11: Permission behaviour does not match what the engineer configured

- **id:** F11
- **problem:** Engineers who have decided what the agent may do find the permission system does not follow that decision: allow and deny rules match unreliably, compound commands prompt on the harmless `cd`, ordinary quoted flags trigger new warnings, skills and subagents ignore user-level allow rules, skip-permissions or yolo modes still prompt, every new project needs its own trust approval, and workspace policy files silently do not take effect. Unattended runs stall on prompts, and engineers cannot be sure the rules they wrote are the ones enforced, so some reimplement enforcement in their own hooks.
- **issues:**
  - anthropics/claude-code#28240 (209)
  - anthropics/claude-code#29214 (86)
  - anthropics/claude-code#30519 (81)
  - anthropics/claude-code#27957 (74)
  - anthropics/claude-code#18950 (72)
  - openai/codex#14599 (71)
  - anthropics/claude-code#36168 (65)
  - google-gemini/gemini-cli#18186 (16)
  - google-gemini/gemini-cli#29682 (9)
- **total_reactions:** 683
- **third_party_solvable:** Pre-tool-use hooks can implement custom approval policies (parsing compound commands, applying trust lists), and test tools can show which configured rules actually fire.

## F08: Delegating work from forges and trackers other than GitHub

- **id:** F08
- **problem:** Teams whose code and tickets live in GitLab, Bitbucket, Azure DevOps or Linear cannot hand work to an agent from where it lives: cloud agent sessions (Claude Code on the web, Codex web) connect only to GitHub repositories, and issues cannot be assigned to an agent to start a session. Engineers copy context by hand and manage branches and merge requests themselves, which blocks adoption in organizations that do not use GitHub.
- **issues:**
  - anthropics/claude-code#12346 (161)
  - anthropics/claude-code#12925 (154)
  - openai/codex#10665 (94)
  - anthropics/claude-code#38179 (86)
  - anthropics/claude-code#54054 (68)
- **total_reactions:** 563
- **third_party_solvable:** MCP servers for these forges and trackers, plus webhook services that start headless agent runs and open merge requests, can be built outside the vendors.

## F10: No visibility or control over where tokens go

- **id:** F10
- **problem:** Engineers paying for heavy agent use cannot see or steer what consumes their tokens: remaining quota and context usage are not shown in the desktop app or exposed to the CLI and scripts, a usage stats panel was removed, background calls such as subagent spinner summaries take an invisible share (about 18% of weighted tokens in one measured session), spend cannot be labelled by team, and model and effort level must be switched by hand per task. They overspend on simple work and hit limits without warning.
- **issues:**
  - anthropics/claude-code#13585 (133)
  - anthropics/claude-code#86879 (121)
  - anthropics/claude-code#102264 (93)
  - anthropics/claude-code#43326 (82)
  - anthropics/claude-code#41456 (71)
  - google-gemini/gemini-cli#12819 (6)
- **total_reactions:** 506
- **third_party_solvable:** Usage trackers that parse local logs or OpenTelemetry data, status-line scripts, request-labelling proxies and model-routing wrappers can provide attribution, budgets and routing without the vendor.

## F09: Keeping many agent sessions organized

- **id:** F09
- **problem:** Engineers who run many sessions across projects cannot keep them organized: histories from different repositories appear in one list, sessions keep generic names that skills cannot change, and there is no command to delete old, test or sensitive sessions. Finding the session that holds a piece of work means scanning lists, and sensitive transcripts linger on disk.
- **issues:**
  - openai/codex#25319 (189)
  - anthropics/claude-code#25045 (148)
  - anthropics/claude-code#26904 (117)
- **total_reactions:** 454
- **third_party_solvable:** Session indexers that read local transcripts, hooks that record a label per session, and cleanup scripts can group, search and prune sessions.

## F13: Agent ignores standing instructions and installed skills

- **id:** F13
- **problem:** Engineers who write standing rules in instruction files (no verbose code comments, run scripts directly instead of writing new ones, a delegation policy) or install skills for their stack find the agent ignores them: it does not notice available skills and searches the codebase by hand instead, and in one update a vendor system-prompt section silently overrode the user's configured delegation policy. They repeat corrections every session and cannot rely on configuration to shape behaviour.
- **issues:**
  - anthropics/claude-code#65961 (256)
  - anthropics/claude-code#80988 (91)
  - anthropics/claude-code#9716 (75)
  - google-gemini/gemini-cli#13852 (18)
- **total_reactions:** 440
- **third_party_solvable:** Hooks can check output against the rules (for example linting comment density), re-inject rules or point the agent to matching skills, and tools can diff the vendor system prompt across versions to flag overriding changes.

## F12: OAuth to remote MCP servers is fragile

- **id:** F12
- **problem:** Engineers connecting agents to authenticated remote MCP servers (GitHub, Slack and others) hit OAuth failures: the client cannot connect, rejects the issuer, lacks dynamic client registration, or never refreshes a stored token. Tool access breaks mid-session or in scheduled automations, and the only recovery is a manual browser re-login.
- **issues:**
  - anthropics/claude-code#3433 (154)
  - openai/codex#31573 (76)
  - openai/codex#17265 (69)
  - openai/codex#13200 (67)
- **total_reactions:** 366
- **third_party_solvable:** Auth-bridging proxies can run the OAuth flow and token refresh themselves and expose the remote server to the agent locally, or local servers can use long-lived tokens.

## F14: Long sessions lose working context at compaction

- **id:** F14
- **problem:** In long, code-heavy sessions, auto-compaction triggers at a fixed threshold without consent and replaces working context with a lossy summary, with no way to restore the detail later, and the pre-compaction conversation cannot be viewed in the UI even though the transcript is on disk. The agent loses details it needed mid-task, and the engineer cannot see what was dropped.
- **issues:**
  - openai/codex#4106 (138)
  - anthropics/claude-code#17428 (117)
  - anthropics/claude-code#27242 (91)
- **total_reactions:** 346
- **third_party_solvable:** Pre-compaction hooks can save state and references to files for later reload, and transcript viewers can browse the full history on disk.

## F15: Not knowing when a long-running agent finishes or needs input

- **id:** F15
- **problem:** Engineers who hand an agent a long task switch to other work, but get no noticeable signal when it finishes or waits for input, and the conversation shows no timestamps to tell when a background check last ran or an instruction was given. They either watch the terminal or lose time to an agent sitting idle.
- **issues:**
  - openai/codex#3962 (224)
  - anthropics/claude-code#44763 (109)
- **total_reactions:** 333
- **third_party_solvable:** Stop and notification hooks can send desktop or phone alerts, and hooks can log a timestamped record of each turn.

## F21: Parallel sessions in worktrees cannot be set up as needed

- **id:** F21
- **problem:** Engineers running parallel agent sessions in git worktrees cannot choose the base branch or where the worktree is created: the app branches from a default and always places worktrees in a fixed location (a hidden home folder in Codex, a subdirectory of the repository in Claude Code). That breaks workflows that branch from feature branches or depend on project-relative paths and tooling.
- **issues:**
  - anthropics/claude-code#23622 (89)
  - openai/codex#10599 (77)
  - anthropics/claude-code#27282 (73)
- **total_reactions:** 239
- **third_party_solvable:** Worktree-manager wrappers can create worktrees from any base branch and location and start agents inside them.

## F16: File work done through raw shell commands

- **id:** F16
- **problem:** Agents increasingly read, write and edit files with sed, cat and grep through the shell instead of the dedicated file tools, more so in auto mode. Those changes bypass the file-level permission rules, diff display and edit tracking engineers use to supervise the agent.
- **issues:**
  - anthropics/claude-code#19649 (124)
  - anthropics/claude-code#87971 (104)
- **total_reactions:** 228
- **third_party_solvable:** A pre-tool-use hook can detect shell commands that read or modify files and block them or redirect the agent to the dedicated tools.

## F17: No safe way to give cloud sessions credentials

- **id:** F17
- **problem:** Engineers running async agent sessions in the vendor's cloud have no secure way to provide API keys and other credentials; the environment settings field itself warns against putting secrets there. Tasks that need authenticated access either cannot run in the cloud or force engineers to expose secrets.
- **issues:**
  - anthropics/claude-code#32733 (215)
- **total_reactions:** 215
- **third_party_solvable:** A secrets broker (an MCP server or credential-injecting proxy) can hold credentials and attach them at call time, so they never enter the session environment or transcript.

## F18: Cross-repository work in one session

- **id:** F18
- **problem:** Organizations with multi-repository architectures cannot use cloud or app agent sessions for cross-service changes, because a session assumes one repository, one branch and one pull request. Changes that span services, such as shared types or API contracts, must be split by hand into separate sessions and coordinated manually.
- **issues:**
  - anthropics/claude-code#23627 (100)
  - openai/codex#11956 (86)
- **total_reactions:** 186
- **third_party_solvable:** Wrappers can assemble multi-repo workspaces, and orchestrators can coordinate per-repo sessions and linked pull requests.

## F19: Unattended work stops at usage limits

- **id:** F19
- **problem:** When a long delegated task hits the 5-hour or weekly usage limit, the agent stops even though the reset time is known. If the reset falls overnight, the work waits until the engineer returns, finds the session and re-issues the prompt.
- **issues:**
  - openai/codex#21073 (90)
  - openai/codex#28931 (79)
- **total_reactions:** 169
- **third_party_solvable:** A wrapper can detect the limit message, schedule a resume of the same session at the reset time and continue the task.

## F20: Plans do not persist where the team can reuse them

- **id:** F20
- **problem:** Engineers who use plan files as durable working memory (kept in a plans/ directory under a naming convention and referenced in later prompts) find the agent writes plans to its own location under generated names. Plans become hard to find, version and reuse across sessions and teammates.
- **issues:**
  - anthropics/claude-code#12619 (168)
- **total_reactions:** 168
- **third_party_solvable:** A hook or skill can save each plan into the repository under the team's naming scheme.

## F22: No audit trail of what subagents were told and did

- **id:** F22
- **problem:** Engineers who delegate to multi-agent setups lost the readable record of what the orchestrator sent each subagent once those messages were encrypted. They can no longer audit or debug delegated tasks after the fact, which undermines accountability for multi-agent work.
- **issues:**
  - openai/codex#28058 (152)
- **total_reactions:** 152
- **third_party_solvable:** Hooks or a recording wrapper can log each subagent's task and result into an independent audit trail.

## F26: Built-in sandbox blocks legitimate work

- **id:** F26
- **problem:** Engineers who turn on the agent's built-in sandbox to contain its actions find it blocks ordinary development work: connections to localhost are refused even when listed as allowed, so integration tests against local Docker services fail, and on macOS it breaks TLS verification for Go-based tools such as gh, terraform and kubectl. They must choose between containment and getting the task done, and the sandbox does not honour settings they configured.
- **issues:**
  - anthropics/claude-code#28018 (80)
  - anthropics/claude-code#23416 (70)
- **total_reactions:** 150
- **third_party_solvable:** Engineers can run agents inside their own containers, devcontainers or VMs with network and filesystem policies they control, instead of relying on the built-in sandbox.

## F27: No way to line up the next tasks

- **id:** F27
- **problem:** Engineers who already know the next several things the agent should do cannot queue them: they must wait for each task to finish before giving the next, and in the VS Code extension a new message interrupts the running task instead of waiting its turn. Delegation stays turn by turn, and the engineer has to stay present between tasks.
- **issues:**
  - anthropics/claude-code#30677 (72)
  - anthropics/claude-code#33323 (65)
- **total_reactions:** 137
- **third_party_solvable:** A wrapper or task runner can hold a queue of prompts and feed them to the agent, interactive or headless, one after another or in parallel.

## F23: Interactive and long-running commands stall the agent

- **id:** F23
- **problem:** Agents run shell commands without a terminal, so commands that prompt for input, open REPLs or need interaction stall, and there is no setting to cap how long a tool call may run. Sessions hang on a stuck command until the engineer notices and intervenes.
- **issues:**
  - anthropics/claude-code#9881 (90)
  - google-gemini/gemini-cli#3375 (9)
- **total_reactions:** 99
- **third_party_solvable:** PTY- or tmux-backed MCP servers can let the agent drive interactive programs, and command wrappers can enforce timeouts.

## F24: Agent runs commands in the wrong directory

- **id:** F24
- **problem:** Agents lose track of their current working directory and run commands where they believe they are rather than where they are. In one report a git hard reset ran in the wrong directory and destroyed about 60 hours of work; at best it costs rounds of self-troubleshooting.
- **issues:**
  - anthropics/claude-code#1669 (86)
- **total_reactions:** 86
- **third_party_solvable:** A hook can inject the current directory into each turn and guard destructive commands such as git reset or rm by checking the target path.

## F28: Scheduled agent automations belong to individuals, not the team

- **id:** F28
- **problem:** Teams that run scheduled remote agents for shared jobs (daily Slack summaries, automated PR checks) find each routine is tied to the account of whoever created it. If that person leaves the team, the team's automations go with them, and there is no shared ownership or visibility.
- **issues:**
  - anthropics/claude-code#48322 (79)
- **total_reactions:** 79
- **third_party_solvable:** Teams can run scheduled agents from their own CI or cron under a service identity, with the definitions kept in a shared repository.

## F29: Agent cannot see the web UI it changes

- **id:** F29
- **problem:** Engineers delegating web front-end work find the agent cannot open, inspect or interact with the running page (DOM, screenshots, console output) from the editor integration, so it cannot check that its UI changes work. The engineer has to reload and verify each change by hand and report back.
- **issues:**
  - anthropics/claude-code#57034 (78)
- **total_reactions:** 78
- **third_party_solvable:** Browser-automation MCP servers, for example Playwright-based ones, can give the agent page inspection, screenshots and console output to verify its own changes.

## F25: Large files and command output overflow or get truncated

- **id:** F25
- **problem:** Engineers working with large files or verbose commands find the agent silently receives truncated content (command output cut at 8,000 characters) or is blocked from reading big files, and an accidental large read can overflow the context with no recovery short of starting a new task. The agent reasons over incomplete data and progress is lost.
- **issues:**
  - cline/cline#13263 (10)
  - cline/cline#4389 (10)
- **total_reactions:** 20
- **third_party_solvable:** Wrappers can write large outputs to files and return summaries with paged or ranged reads, so the agent fetches only what it needs.

## Dropped

| Reason | Issues |
|---|---|
| UI, rendering and cosmetic features | 39 |
| Only the vendor can change it (model availability, provider and model-format support, product bugs, internal roadmap or eval work, vendor-side settings) | 36 |
| Platform, IDE, OS, terminal, shell-environment and network-proxy support | 35 |
| Accounts, login and verification | 16 |
| Billing, plans, pricing and quota-drain complaints | 16 |
| Outages, connectivity and API errors | 14 |
| Parity or sync between the vendor's own surfaces | 7 |
| Model writing style | 2 |
| **Total dropped (unique issues)** | **165** |

Not counted: the 50 duplicate entries C101 to C150 in candidates-raw.md, replaced by the addendum. Borderline calls: reports of quotas draining abnormally fast were dropped as plan or quota issues even when measured, because only the vendor's metering can change; feature requests for the vendor's IDE diff review were kept (F06) because the underlying need, reviewing agent changes, can be met outside the IDE; requests for usage or context visibility were kept in F10 even when they ask for a display, while general status-line and indicator requests were dropped as UI.
