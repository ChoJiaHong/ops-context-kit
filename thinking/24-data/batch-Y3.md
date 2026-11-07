# Batch

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

## F19: Unattended work stops at usage limits

- **id:** F19
- **problem:** When a long delegated task hits the 5-hour or weekly usage limit, the agent stops even though the reset time is known. If the reset falls overnight, the work waits until the engineer returns, finds the session and re-issues the prompt.
- **issues:**
  - openai/codex#21073 (90)
  - openai/codex#28931 (79)
- **total_reactions:** 169
- **third_party_solvable:** A wrapper can detect the limit message, schedule a resume of the same session at the reset time and continue the task.

## F15: Not knowing when a long-running agent finishes or needs input

- **id:** F15
- **problem:** Engineers who hand an agent a long task switch to other work, but get no noticeable signal when it finishes or waits for input, and the conversation shows no timestamps to tell when a background check last ran or an instruction was given. They either watch the terminal or lose time to an agent sitting idle.
- **issues:**
  - openai/codex#3962 (224)
  - anthropics/claude-code#44763 (109)
- **total_reactions:** 333
- **third_party_solvable:** Stop and notification hooks can send desktop or phone alerts, and hooks can log a timestamped record of each turn.

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

## F03: One account per external service in a session

- **id:** F03
- **problem:** Engineers whose agent works with external services (Gmail, Slack, Drive, calendars, GitHub) often have separate personal, employer and client accounts for the same service, but a session can connect only one account per connector. Switching means disconnecting and reconnecting, and the agent can act in the wrong account, crossing privacy boundaries between employers or clients.
- **issues:**
  - anthropics/claude-code#27302 (647)
  - openai/codex#20500 (147)
- **total_reactions:** 794
- **third_party_solvable:** MCP servers can hold several named credentials for the same service and require an explicit account choice on each call, without any change from the vendor.
