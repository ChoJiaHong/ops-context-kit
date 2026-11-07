# Batch

## F28: Scheduled agent automations belong to individuals, not the team

- **id:** F28
- **problem:** Teams that run scheduled remote agents for shared jobs (daily Slack summaries, automated PR checks) find each routine is tied to the account of whoever created it. If that person leaves the team, the team's automations go with them, and there is no shared ownership or visibility.
- **issues:**
  - anthropics/claude-code#48322 (79)
- **total_reactions:** 79
- **third_party_solvable:** Teams can run scheduled agents from their own CI or cron under a service identity, with the definitions kept in a shared repository.

## F24: Agent runs commands in the wrong directory

- **id:** F24
- **problem:** Agents lose track of their current working directory and run commands where they believe they are rather than where they are. In one report a git hard reset ran in the wrong directory and destroyed about 60 hours of work; at best it costs rounds of self-troubleshooting.
- **issues:**
  - anthropics/claude-code#1669 (86)
- **total_reactions:** 86
- **third_party_solvable:** A hook can inject the current directory into each turn and guard destructive commands such as git reset or rm by checking the target path.

## F20: Plans do not persist where the team can reuse them

- **id:** F20
- **problem:** Engineers who use plan files as durable working memory (kept in a plans/ directory under a naming convention and referenced in later prompts) find the agent writes plans to its own location under generated names. Plans become hard to find, version and reuse across sessions and teammates.
- **issues:**
  - anthropics/claude-code#12619 (168)
- **total_reactions:** 168
- **third_party_solvable:** A hook or skill can save each plan into the repository under the team's naming scheme.

## F16: File work done through raw shell commands

- **id:** F16
- **problem:** Agents increasingly read, write and edit files with sed, cat and grep through the shell instead of the dedicated file tools, more so in auto mode. Those changes bypass the file-level permission rules, diff display and edit tracking engineers use to supervise the agent.
- **issues:**
  - anthropics/claude-code#19649 (124)
  - anthropics/claude-code#87971 (104)
- **total_reactions:** 228
- **third_party_solvable:** A pre-tool-use hook can detect shell commands that read or modify files and block them or redirect the agent to the dedicated tools.

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

## F04: Project instructions fragmented across agents and directories

- **id:** F04
- **problem:** Teams that use more than one agent must keep the same project guidance in tool-specific files and folders (CLAUDE.md, AGENTS.md, .agents/skills), and within one repository it is unclear whether nested instruction files in subdirectories load and override the root file. Instructions drift between tools and directories, and engineers cannot tell which rules an agent actually received.
- **issues:**
  - anthropics/claude-code#31005 (604)
  - openai/codex#12115 (127)
- **total_reactions:** 731
- **third_party_solvable:** A generator or sync convention can render one canonical instruction source into each agent's file format, and a linter can show which instruction files apply to a given path.
