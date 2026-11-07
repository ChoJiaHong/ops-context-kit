# Batch

## F01: Agent harness leaks the engineer's personal identity

- **id:** F01
- **problem:** Engineers who let the agent search or fetch from the web find that the harness puts their account email into outbound request headers sent to arbitrary sites, and also injects it into the model's system prompt every session, without asking. Their identity reaches third parties they never chose (one reporter ties it to daily scam mail), so delegating web research quietly costs privacy.
- **issues:**
  - anthropics/claude-code#107757 (951)
  - anthropics/claude-code#81138 (107)
- **total_reactions:** 1058
- **third_party_solvable:** An egress proxy or wrapper can strip identifying headers and fields from outgoing requests, and a hook can deny the built-in web tools in favour of an MCP fetch server that uses a neutral identity.

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

## F17: No safe way to give cloud sessions credentials

- **id:** F17
- **problem:** Engineers running async agent sessions in the vendor's cloud have no secure way to provide API keys and other credentials; the environment settings field itself warns against putting secrets there. Tasks that need authenticated access either cannot run in the cloud or force engineers to expose secrets.
- **issues:**
  - anthropics/claude-code#32733 (215)
- **total_reactions:** 215
- **third_party_solvable:** A secrets broker (an MCP server or credential-injecting proxy) can hold credentials and attach them at call time, so they never enter the session environment or transcript.

## F21: Parallel sessions in worktrees cannot be set up as needed

- **id:** F21
- **problem:** Engineers running parallel agent sessions in git worktrees cannot choose the base branch or where the worktree is created: the app branches from a default and always places worktrees in a fixed location (a hidden home folder in Codex, a subdirectory of the repository in Claude Code). That breaks workflows that branch from feature branches or depend on project-relative paths and tooling.
- **issues:**
  - anthropics/claude-code#23622 (89)
  - openai/codex#10599 (77)
  - anthropics/claude-code#27282 (73)
- **total_reactions:** 239
- **third_party_solvable:** Worktree-manager wrappers can create worktrees from any base branch and location and start agents inside them.

## F25: Large files and command output overflow or get truncated

- **id:** F25
- **problem:** Engineers working with large files or verbose commands find the agent silently receives truncated content (command output cut at 8,000 characters) or is blocked from reading big files, and an accidental large read can overflow the context with no recovery short of starting a new task. The agent reasons over incomplete data and progress is lost.
- **issues:**
  - cline/cline#13263 (10)
  - cline/cline#4389 (10)
- **total_reactions:** 20
- **third_party_solvable:** Wrappers can write large outputs to files and return summaries with paged or ranged reads, so the agent fetches only what it needs.

## F29: Agent cannot see the web UI it changes

- **id:** F29
- **problem:** Engineers delegating web front-end work find the agent cannot open, inspect or interact with the running page (DOM, screenshots, console output) from the editor integration, so it cannot check that its UI changes work. The engineer has to reload and verify each change by hand and report back.
- **issues:**
  - anthropics/claude-code#57034 (78)
- **total_reactions:** 78
- **third_party_solvable:** Browser-automation MCP servers, for example Playwright-based ones, can give the agent page inspection, screenshots and console output to verify its own changes.
