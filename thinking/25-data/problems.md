# Problems (as of 2026-11-08)

Each problem comes from open GitHub issues on agent-tool repositories. "Existing approaches" and "Known shortcomings" were collected by two independent checkers (thinking/24); links are third-party pages.

## P1 (F01): Agent harness leaks the engineer's personal identity

Problem: Engineers who let the agent search or fetch from the web find that the harness puts their account email into outbound request headers sent to arbitrary sites, and also injects it into the model's system prompt every session, without asking. Their identity reaches third parties they never chose (one reporter ties it to daily scam mail), so delegating web research quietly costs privacy.

Demand: 1058 reactions on the open issues.

Existing approaches:
- Claude Code built-in cc-plugin-privacy mod (v2.1.317+) (0 stars, 2026-11-05): A default-on built-in mod that blocks or asks before web tool calls or curl-style commands containing the account email. Staff also said the email will be removed from model context in an upcoming release. <https://github.com/anthropics/claude-code/issues/107757>
- klavdiy-core/pii-tripwire (0 stars, 2026-10-24): Claude Code hook that stops a user-listed set of emails, phone numbers and ID numbers from leaving in outbound tool calls. <https://github.com/klavdiy-core/pii-tripwire>
- Claude Code built-in privacy mod cc-plugin-privacy (v2.1.317+) (0 stars, 2026-11-04): Official check that asks (or denies, headless) before a web or shell tool call whose input holds the signed-in account email goes to the network; enabled by default. A contributor confirmed it in the main thread (https:/ <https://github.com/anthropics/claude-code/issues/107144>
- AlexErrant/claude-code-no-email (71 stars, 2026-10-29): Mod/hook that drops the userEmail block from the context Claude Code sends to the model, which removes the source of the header leak. <https://github.com/AlexErrant/claude-code-no-email>
- NobleCodeSoftware/claude-pii-guard (0 stars, 2026-11-06): Local PreToolUse hook that detects emails and other PII in tool calls, with block, ask or warn modes. <https://github.com/NobleCodeSoftware/claude-pii-guard>
- princejain756/egressleak (0 stars, 2026-11-06): Auditor for outbound HTTP egress, the User-Agent email leak (#107757) and PII in context for Claude Code, Codex CLI and MCP configs. <https://github.com/princejain756/egressleak>

Known shortcomings:
- The account email is still injected into the system prompt with no opt-out (open since 2026-07). The promised removal had not shipped as of the latest comments, and the stable channel was on 2.1.311, without the mod. <https://github.com/anthropics/claude-code/issues/81138>
- Commenters report that the privacy mod did not refuse a test command containing the email on 2.1.317/2.1.318. Staff concede it does not cover scripts Claude writes and runs itself. <https://github.com/anthropics/claude-code/issues/107757>
- The account-email check gives false positives: it denies local-only Bash calls such as heredoc writes and curl to 127.0.0.1 in headless runs. <https://github.com/anthropics/claude-code/issues/107144>
- Sub-agents put the email in curl User-Agent headers to sec.gov and bls.gov even though the system prompt tells them not to send it to unrelated services. <https://github.com/anthropics/claude-code/issues/106012>
- A Claude Code employee's statement, quoted in the issue thread, says the 2.1.317 check does not cover every case, for example scripts Claude writes and runs itself. Removing the email from the model context was promised for a later release, and this check foun <https://github.com/anthropics/claude-code/issues/107757>
- The built-in check matches on the address plus a network word, so it denies local-only calls (heredoc file writes, curl to 127.0.0.1) in headless bypass runs, and the run still ends as success. The only way to turn it off is to disable the whole privacy plugin <https://github.com/anthropics/claude-code/issues/107144>
- The account email is still injected into the system prompt every session, with no supported opt-out. IS_DEMO hides only display surfaces. The model has also written the address into commits. <https://github.com/anthropics/claude-code/issues/81138>
- The claude-code-no-email mod does nothing on Team/Enterprise logins or on machines with managed settings, because the built-in guard skips prompt.context hooks from user mods there. <https://github.com/AlexErrant/claude-code-no-email/issues/1>
- Hook workarounds match exact strings and can miss encodings, and prompt rules did not prevent a reported leak. <https://explainx.ai/blog/claude-code-leaks-your-email-user-agent-header-how-to-stop-it-2026>

## P2 (F11): Permission behaviour does not match what the engineer configured

Problem: Engineers who have decided what the agent may do find the permission system does not follow that decision: allow and deny rules match unreliably, compound commands prompt on the harmless `cd`, ordinary quoted flags trigger new warnings, skills and subagents ignore user-level allow rules, skip-permissions or yolo modes still prompt, every new project needs its own trust approval, and workspace policy files silently do not take effect. Unattended runs stall on prompts, and engineers cannot be sure the rules they wrote are the ones enforced, so some reimplement enforcement in their own hooks.

Demand: 683 reactions on the open issues.

Existing approaches:
- ldayton/Dippy (244 stars, 2026-06-12): PreToolUse hook that parses shell commands (including compound ones) and auto-approves safe ones under user rules <https://github.com/ldayton/Dippy>
- kornysietsma/tool-gate-hook (41 stars, 2026-10-12): PreToolUse hook with more granular permission rules than built-in matching <https://github.com/kornysietsma/tool-gate-hook>
- Claude Code PreToolUse / PermissionRequest hooks (0 stars, 2025-06-30): Official mechanism to implement custom allow/deny decisions <https://code.claude.com/docs/en/hooks>
- Claude Code per-subcommand permission matching and read-only cd (0 stars, 2026-11-08): Compound commands are split on &&, ||, ;, | etc. and each subcommand matched; cd into the working directory counts as read-only; 'don't ask again' saves one rule per subcommand; /permissions lists every rule and its sour <https://code.claude.com/docs/en/permissions>
- Claude Code auto mode (classifier approvals) (0 stars, 2026-11-08): A classifier decides most permission prompts instead of the user, reducing stalls in unattended runs. <https://code.claude.com/docs/en/permissions>
- oryband/claude-code-auto-approve (20 stars, 2026-07-29): Auto-approves compound Bash commands by parsing pipes, chains and subshells and checking each segment. <https://github.com/oryband/claude-code-auto-approve>
- vosslab/codex-code-permissions-hook (0 stars, 2026-07-26): Codex permission hook that decomposes compound shell commands and applies allow/deny TOML rules. <https://github.com/vosslab/codex-code-permissions-hook>

Known shortcomings:
- Built-in permission matching described as broken across 30+ open issues; users are reimplementing enforcement in hooks <https://github.com/anthropics/claude-code/issues/30519>
- Compound commands prompt on the cd instead of the real command (open) <https://github.com/anthropics/claude-code/issues/28240>
- PermissionRequest hook 'allow' is ignored for ExitPlanMode since v2.1.199, so hooks cannot fully replace prompts <https://github.com/anthropics/claude-code/issues/74256>
- Remote Control mobile app shows prompts despite --dangerously-skip-permissions (open) <https://github.com/anthropics/claude-code/issues/29214>
- Skills/subagents do not inherit user-level allow rules (open) <https://github.com/anthropics/claude-code/issues/18950>
- Dippy config rules do not match commands with global flags such as git -C <https://github.com/ldayton/Dippy/issues/136>
- Dippy: Cursor bugs limit its ability to operate <https://github.com/ldayton/Dippy/issues/129>
- Codex still requires per-project trust approval (open) <https://github.com/openai/codex/issues/14599>
- Gemini CLI workspace policy files do not take effect (open) <https://github.com/google-gemini/gemini-cli/issues/18186>
- Gemini CLI v0.63.0 breaks yolo mode (open) <https://github.com/google-gemini/gemini-cli/issues/29682>
- Permission prompt triggers on cd instead of the real command in compound statements; most-reacted permission bug still open. <https://github.com/anthropics/claude-code/issues/28240>
- Permission matching described as fundamentally broken (30+ issues, user-level rules not applied, deny-rule bypasses); community hook reimplementations have no security review. <https://github.com/anthropics/claude-code/issues/30519>
- Skills and subagents do not inherit user-level permissions. <https://github.com/anthropics/claude-code/issues/18950>
- Bypass/skip-permissions broken in versions after v2.1.77. <https://github.com/anthropics/claude-code/issues/36168>
- Remote Control mobile app shows permission prompts despite --dangerously-skip-permissions. <https://github.com/anthropics/claude-code/issues/29214>
- Quoted-characters-in-flag-names warning cannot be disabled. <https://github.com/anthropics/claude-code/issues/27957>
- Codex requires per-project trust approval; maintainers announced trusting all directories then reversed the decision and reopened the issue. <https://github.com/openai/codex/issues/14599>
- Gemini CLI workspace .gemini/policies/*.toml files do not take effect. <https://github.com/google-gemini/gemini-cli/issues/18186>

## P3 (F08): Delegating work from forges and trackers other than GitHub

Problem: Teams whose code and tickets live in GitLab, Bitbucket, Azure DevOps or Linear cannot hand work to an agent from where it lives: cloud agent sessions (Claude Code on the web, Codex web) connect only to GitHub repositories, and issues cannot be assigned to an agent to start a session. Engineers copy context by hand and manage branches and merge requests themselves, which blocks adoption in organizations that do not use GitHub.

Demand: 563 reactions on the open issues.

Existing approaches:
- Cursor cloud agents on GitLab (incl. self-hosted), Azure DevOps Services (beta) and Bitbucket Cloud (0 stars, 2026-11-08): Cloud agent sessions on non-GitHub forges, plus Linear/Jira integrations to delegate from tickets. <https://cursor.com/help/integrations/github-gitlab>
- GitLab Duo Agent Platform external agents (Claude Code, OpenAI Codex) (0 stars, 2026-01-14): Mention, assign or request review from the agent's service account in GitLab issues/MRs to start a run that responds with changes. <https://docs.gitlab.com/user/duo_agent_platform/agents/external.html>
- Claude Code GitLab CI/CD (beta, maintained by GitLab) (0 stars, 2026-11-08): @claude in issues/MRs triggers a pipeline job that implements changes and opens MRs. <https://code.claude.com/docs/en/gitlab-ci-cd>
- cyrusagents/cyrus (886 stars, 2026-11-06): Self-hosted Claude Code (and Codex/Cursor/Gemini) background agent triggered from Linear, Slack, GitHub and GitLab. <https://github.com/cyrusagents/cyrus>
- Linear coding sessions (Claude Code or Codex) (0 stars, 2026-06-11): Delegate a Linear issue to a cloud agent that opens a draft PR. <https://linear.app/docs/coding-sessions>
- GitLab Duo Agent Platform external agents (Claude Code Agent, Codex Agent) (0 stars, 2026-11-07): Mention or assign a service account in GitLab issues/MRs to run GitLab-managed Claude Code or Codex agents that push branches and MRs <https://docs.gitlab.com/user/duo_agent_platform/agent_assistant/>
- Cursor Cloud Agents forge integrations (0 stars, 2026-11-07): Cloud agents work with GitHub, GitLab (incl. self-hosted), Azure DevOps Services and Bitbucket Cloud <https://cursor.com/help/integrations/github-gitlab>
- Linear coding sessions (0 stars, 2026-06-11): Assign a Linear issue to Linear Agent to run Claude Code or Codex in the cloud and return a diff <https://linear.app/changelog/2026-06-11-coding-sessions>

Known shortcomings:
- Claude Code cloud sessions still require GitHub for cloning and PRs; GitLab/Bitbucket can only be uploaded as a bundle that cannot push back. <https://code.claude.com/docs/en/claude-code-on-the-web>
- Linear coding sessions require repositories via Linear's GitHub integration. <https://linear.app/docs/coding-sessions>
- Claude Agent for Jira opens PRs only in a connected GitHub repository. <https://www.atlassian.com/blog/company-news/claude-agent-for-jira>
- Cursor cloud agents: Bitbucket Data Center gets only Bugbot, Azure DevOps is public beta and Services-only. <https://cursor.com/help/integrations/github-gitlab>
- GitLab external agents are Premium/Ultimate only and gated behind a feature flag for verified customers. <https://docs.gitlab.com/user/duo_agent_platform/agents/external.html>
- Native Azure DevOps support for Codex web still requested (open). <https://github.com/openai/codex/issues/10665>
- Bitbucket support for Claude Code still requested (open). <https://github.com/anthropics/claude-code/issues/38179>
- Claude Code on the web still connects only to GitHub; GitLab, Bitbucket and Azure DevOps requests remain open <https://github.com/anthropics/claude-code/issues/54054>
- Linear coding sessions require a GitHub connection; no other forge mentioned <https://linear.app/changelog/2026-06-11-coding-sessions>
- GitLab external agents require Premium/Ultimate, are behind a feature flag enabled on request, and are 'Experiment' on Self-Managed/Dedicated <https://docs.gitlab.com/user/duo_agent_platform/agent_assistant/>
- Cursor Azure DevOps and Bitbucket Cloud support is public beta, Bitbucket Data Center unsupported for cloud agents <https://cursor.com/help/integrations/github-gitlab>
- User report: Cursor Azure DevOps integration broken <https://forum.cursor.com/t/azure-dev-ops-integration-is-broken/170774>
- User report: Cursor cloud agents cannot get branches from Bitbucket repo <https://forum.cursor.com/t/cloud-agents-cant-get-branches-from-bitbucket-repo/169511>
- Codex cloud has no Azure DevOps integration <https://github.com/openai/codex/issues/10665>

## P4 (F15): Not knowing when a long-running agent finishes or needs input

Problem: Engineers who hand an agent a long task switch to other work, but get no noticeable signal when it finishes or waits for input, and the conversation shows no timestamps to tell when a background check last ran or an instruction was given. They either watch the terminal or lose time to an agent sitting idle.

Demand: 333 reactions on the open issues.

Existing approaches:
- Claude Code Notification/Stop hooks (0 stars, 2025-06-30): Run a command (desktop/phone alert) when Claude finishes or needs input <https://code.claude.com/docs/en/hooks-guide>
- Claude Code mobile push notifications (0 stars, 2026-04-13): Phone push when Claude needs input <https://code.claude.com/docs/en/whats-new/2026-w16.md>
- Codex tui.notifications and notify hook (0 stars, 2026-04-13): Terminal notifications for agent-turn-complete and approval-requested; external notify command <https://codex.danielvaughan.com/2026/04/13/codex-cli-notification-pipeline-osc9-hooks-alerts/>
- mylee04/code-notify (291 stars, 2026-09-04): Cross-platform desktop notifications and sounds for Claude Code, Codex, Gemini CLI <https://github.com/mylee04/code-notify>
- tuchg/Lucarne (343 stars, 2026-08-02): Remote notifications, approve and resume for Codex/Claude Code sessions <https://github.com/tuchg/Lucarne>
- ProducerGuy/claude-timecodes (6 stars, 2026-04-04): Timestamps on Claude Code conversation turns <https://github.com/ProducerGuy/claude-timecodes>
- Claude Code Notification and Stop hooks (0 stars, 2026-11-08): Hooks fire when Claude needs input or finishes, so users can trigger desktop/phone alerts or log timestamps. <https://code.claude.com/docs/en/hooks>
- Claude Code Remote Control push notifications (0 stars, 2026-08-17): 'Push when actions required' and 'Push when Claude decides' send phone pushes via the Claude app when blocked on a prompt or when a long task finishes. <https://wmedia.es/en/tips/claude-code-notifications-on-your-phone>
- Codex tui.notifications / notify config (0 stars, 2026-11-05): Maintainer describes tui.notifications with OSC 9/BEL and the notify script hook on agent-turn-complete; desktop app has OS completion notifications. <https://github.com/openai/codex/issues/3962>
- DevinoSolutions/anotifier-for-claude-codex-cursor (35 stars, 2026-11-07): Desktop and phone (ntfy) notifications for Claude Code, Codex, Gemini CLI and Cursor, with native VS Code support. <https://github.com/DevinoSolutions/anotifier-for-claude-codex-cursor>
- wyattjoh/claude-code-notification (95 stars, 2026-11-03): macOS desktop notification hook with sounds for Claude Code events. <https://github.com/wyattjoh/claude-code-notification>
- Riplexa Timestamps (VS Code extension) (0 stars, 2026-09-14): Shows timestamps inline in the Claude Code and Codex VS Code chat panels. <https://github.com/agurrotem-crypto/riplexa-timestamps>

Known shortcomings:
- Codex external notify hook fires only for agent-turn-complete, not approvals; OSC 9 support varies by terminal; no dedup <https://codex.danielvaughan.com/2026/04/13/codex-cli-notification-pipeline-osc9-hooks-alerts/>
- Codex: a turn that ends on an API error fires no Stop or other hook, so no alert <https://github.com/openai/codex/issues/54884>
- Codex: hooks stopped running after a Desktop update <https://github.com/openai/codex/issues/21639>
- Codex: Stop hook fires at every /goal continuation, producing false 'done' alerts <https://github.com/openai/codex/issues/52950>
- Codex completion sound request still open <https://github.com/openai/codex/issues/3962>
- Claude Code still shows no timestamps on messages (open); only tiny third-party tools exist <https://github.com/anthropics/claude-code/issues/44763>
- No per-message timestamps in Claude Code; request open; the only third-party option covers the VS Code panel only and patches its webview. <https://github.com/anthropics/claude-code/issues/44763>
- Second open request for message timestamps in the interactive conversation view. <https://github.com/anthropics/claude-code/issues/30745>
- Claude Code VS Code extension lacks native system/toast notifications when Claude needs attention. <https://github.com/anthropics/claude-code/issues/57230>
- Codex IDE extension has no audible signal; notify hook does not fire on approval requests; third-party notifiers fail over Remote SSH. <https://github.com/openai/codex/issues/3962>
- Codex VS Code extension does not request attention when approval is required. <https://github.com/openai/codex/issues/30821>
- Claude Code Notification hook fires with a ~10 second delay. <https://github.com/anthropics/claude-code/issues/5186>
- idle_prompt notification timeout is not configurable. <https://github.com/anthropics/claude-code/issues/13922>
- Remote Control pushes need a subscription, both toggles on, a live Remote Control session and an open terminal; not available with API keys or cloud providers. <https://wmedia.es/en/tips/claude-code-notifications-on-your-phone>
- Codex Remote Control push notifications not delivered on iOS. <https://github.com/openai/codex/issues/32908>

## P5 (F16): File work done through raw shell commands

Problem: Agents increasingly read, write and edit files with sed, cat and grep through the shell instead of the dedicated file tools, more so in auto mode. Those changes bypass the file-level permission rules, diff display and edit tracking engineers use to supervise the agent.

Demand: 228 reactions on the open issues.

Existing approaches:
- tonywu20/no-shell-file-ops (Claude Code plugin) (0 stars, 2026-05-21): Hooks that block shell commands that read or edit files (sed, cat, xxd, od, sd, python -c). <https://www.claudepluginhub.com/plugins/tonywu20-no-shell-file-ops>
- enforce-builtin-tools.sh PreToolUse hook (0 stars, 2026-10-30): Denies Bash cat/head/tail/sed/grep/find and points the agent to Read/Edit/Write/Grep/Glob. <https://dev.to/yurukusa/claude-code-ignores-its-own-tools-here-are-3-hooks-that-force-it-to-behave-mi1>
- davidewins/claude-guardrails (1 stars, 2026-11-03): Config-driven block/ask/remind rules on Bash commands and file writes. <https://github.com/davidewins/claude-guardrails>
- CLAUDE_CODE_THRIFTY_SONIC=0 env workaround (undocumented) (0 stars, 2026-08-19): Users report it disables the auto-mode 'Bash-first' steering on 2.1.263+. <https://github.com/anthropics/claude-code/issues/87971>
- Claude Code Read/Edit deny rules applied to recognized Bash file commands, plus OS sandbox (0 stars, 2026-10-02): Deny rules cover cat/head/tail/sed/tee in Bash; sandbox blocks file access at OS level <https://dev.to/rulestack/claude-codes-read-deny-rules-let-4-of-11-routes-through-grep-r-a-python-one-liner-and-two-ajf>
- HabibiCodeCH/claude-no-bash-detour (2 stars, 2026-07-24): PreToolUse hooks that deny Bash commands with a native-tool equivalent (grep/find, sed -i, cat/head/tail) and redirect to Grep/Glob/Read/Edit <https://github.com/HabibiCodeCH/claude-no-bash-detour>
- derekwden-droid/file-tools-first (0 stars, 2026-10-09): Plugin blocking shell file reads/edits and routing them to Read/Edit/Write so /rewind and rules apply <https://github.com/derekwden-droid/file-tools-first>
- JasonGDG/claude-bash-bridge (0 stars, 2026-10-19): Fires Write/Edit hooks and path rules when Claude edits files through Bash <https://github.com/JasonGDG/claude-bash-bridge>

Known shortcomings:
- Claude Code's auto/bypass mode system prompt itself tells the model to read and edit files with cat/sed/heredocs, routing writes around Write|Edit hooks; still reproducing on 2.1.268. <https://github.com/anthropics/claude-code/issues/89251>
- A user's PreToolUse hook blocking shell writes stopped being a reliable opt-out after the Opus 5.5 release; no documented setting separates auto-approval from tool routing. <https://github.com/anthropics/claude-code/issues/87971>
- Bash-first edits silently skip nested CLAUDE.md and path-scoped rules; PreToolUse cannot inject additionalContext to redirect. <https://github.com/anthropics/claude-code/issues/90450>
- Bash-edited files break /rewind. <https://github.com/anthropics/claude-code/issues/87575>
- Agent circumvents an Edit hook by writing files via python in Bash, showing pattern-based hooks are easy to route around. <https://github.com/anthropics/claude-code/issues/29709>
- Third-party hooks are tiny projects (0-1 stars, low maintenance scores). <https://www.claudepluginhub.com/plugins/tonywu20-no-shell-file-ops>
- In auto mode the harness itself instructs Claude to do file reads/writes via Bash (cat, sed, heredocs) instead of Read/Edit/Write; open <https://github.com/anthropics/claude-code/issues/87971>
- Model frequently uses sed/grep/cat when built-in tools fit; open <https://github.com/anthropics/claude-code/issues/19649>
- Checkpointing/rewind does not track files changed only by Bash commands <https://code.claude.com/docs/en/checkpointing>
- Read deny rules bypassed by grep -r and python one-liners on v2.1.285 unless the sandbox is on <https://dev.to/rulestack/claude-codes-read-deny-rules-let-4-of-11-routes-through-grep-r-a-python-one-liner-and-two-ajf>

## P6 (F17): No safe way to give cloud sessions credentials

Problem: Engineers running async agent sessions in the vendor's cloud have no secure way to provide API keys and other credentials; the environment settings field itself warns against putting secrets there. Tasks that need authenticated access either cannot run in the cloud or force engineers to expose secrets.

Demand: 215 reactions on the open issues.

Existing approaches:
- Claude Code cloud environments: network secrets (0 stars, 2026-11-08): API keys and tokens are stored on the environment, and Anthropic's agent proxy attaches them to requests for the listed hosts after the requests leave the VM. The key never appears in the session's env vars, files or tra <https://code.claude.com/docs/en/cloud-environments#add-network-secrets>
- Claude Code cloud GitHub proxy (0 stars, 2026-11-08): Git credentials stay encrypted server-side and are attached by a proxy, never entering the VM. <https://code.claude.com/docs/en/claude-code-on-the-web>
- mmartinez/postern (11 stars, 2026-11-02): Credential-brokering HTTPS proxy that injects 1Password/Bitwarden secrets at request time so the agent never sees them (self-hosted, not for vendor cloud sessions). <https://github.com/mmartinez/postern>
- Claude Code cloud environments: network secrets (official) (0 stars, 2026-11-07): Store an API key or token (Bearer, custom header, username/password, AWS SigV4) on an Anthropic-hosted environment. The agent proxy attaches it to requests for the listed hosts after they leave the VM, so the key never e <https://code.claude.com/docs/en/cloud-environments>
- Claude Code cloud GitHub proxy (official) (0 stars, 2026-11-07): Git and gh requests are re-authenticated by a proxy that keeps the real GitHub token outside the session VM. <https://code.claude.com/docs/en/cloud-environments>
- ermoluk/mcp-warden (12 stars, 2026-11-03): Local-first credential broker for MCP. Agents call APIs, SSH and databases through scoped presets, and secrets stay in the OS keychain. It is local only, not for vendor-cloud sessions. <https://github.com/ermoluk/mcp-warden>

Known shortcomings:
- Network secrets are never attached to setup-script requests, to public package registries (registry.npmjs.org, pypi.org, crates, Go proxy) or to non-HTTP-header uses. They do not exist in self-hosted environments, cannot be saved by CMEK orgs, and need an org- <https://code.claude.com/docs/en/cloud-environments#requests-that-never-get-the-secret>
- The secure secrets request is still open with 215 reactions. Commenters say the feature reached personal accounts but not Team accounts, and the UI did not match the docs. <https://github.com/anthropics/claude-code/issues/32733>
- Cloud sessions get no OIDC identity token for keyless AWS/GCP/Azure auth. <https://github.com/anthropics/claude-code/issues/81502>
- The AWS SigV4 network secret rejects non-amazonaws.com hosts (for example R2) without warning. <https://github.com/anthropics/claude-code/issues/106173>
- A running cloud session cannot reload environment variables and secrets. <https://github.com/anthropics/claude-code/issues/106125>
- Network secrets never reach setup scripts, public package registries (registry.npmjs.org, pypi.org and others), the Anthropic API or telemetry. Self-hosted environments have no network secrets, orgs with customer-managed encryption keys cannot save them, and E <https://code.claude.com/docs/en/cloud-environments>
- An AWS SigV4 network secret signs only *.amazonaws.com hosts, so S3-compatible stores such as R2 fail with a 502 and users fall back to a plain environment variable. <https://github.com/anthropics/claude-code/issues/106173>
- There is no OIDC identity token for keyless cloud-provider auth from cloud sessions; request open (updated 2026-11-04). <https://github.com/anthropics/claude-code/issues/81502>
- The original request for secrets as process-level env vars, usable by setup scripts, private registries and database URLs, is still open. Comments report Team-account gaps and a mismatch between the docs and the UI. <https://github.com/anthropics/claude-code/issues/32733>

## P7 (F18): Cross-repository work in one session

Problem: Organizations with multi-repository architectures cannot use cloud or app agent sessions for cross-service changes, because a session assumes one repository, one branch and one pull request. Changes that span services, such as shared types or API contracts, must be split by hand into separate sessions and coordinated manually.

Demand: 186 reactions on the open issues.

Existing approaches:
- Claude Code cloud sessions with multiple repositories (0 stars, 2026-11-07): Add several repositories to one cloud session at claude.ai/code. Tested to produce one PR per repository from a single session (see https://dev.classmethod.jp/en/articles/claude-code-web-multiple-repositories/). <https://code.claude.com/docs/en/web-quickstart.md>
- Codex app multi-folder projects (0 stars, 2026-07-23): Local projects that span several folders or repos, with one primary folder. The CLI also takes --add-dir and writable_roots. <https://codex.danielvaughan.com/2026/07/24/codex-multi-folder-projects-primary-folder-writable-roots-cross-repo-workspace-configuration/>
- yahor-punko/mavericks-os (82 stars, 2026-11-07): Orchestrates Claude Code subagents across multi-repo projects and tracks cross-repo dependencies. <https://github.com/yahor-punko/mavericks-os>
- dean0x/mars (15 stars, 2026-03-06): Workspace layer for agents across polyrepos with coordinated branches. <https://github.com/dean0x/mars>
- Claude Code on the web multi-repository sessions (0 stars, 2026-09-30): Official: several repositories can be attached to one cloud session (multi-select picker or the repositories URL parameter; 12 repos tested in https://dev.classmethod.jp/en/articles/claude-code-web-twelve-repositories/), <https://dev.classmethod.jp/en/articles/claude-code-web-multi-repo-issues-prs/>
- Claude Code Projects (0 stars, 2026-11-07): Official: a project is 'one conversation where Claude coordinates parallel cloud sessions on your repositories and reports back'. <https://code.claude.com/docs/en/claude-code-on-the-web>
- Cursor cloud agents multi-repo environments (0 stars, 2026-10-02): Reported by a migrating user: Cursor cloud agents support multiple repos in one environment and can raise multiple PRs. <https://github.com/openai/codex/issues/50155>
- me-public/nemus (19 stars, 2026-11-03): Multi-repo git workspaces that group repos, operate in bulk and wire them to a coding agent. <https://github.com/me-public/nemus>

Known shortcomings:
- There are still no coordinated change sets across repos (linked PRs with merge order), per-repo push policies, or multi-repo teleport. The issue is still open. <https://github.com/anthropics/claude-code/issues/23627>
- Codex cloud environments still lack multi-repo support (open, Oct 2026). <https://github.com/openai/codex/issues/50155>
- In Codex multi-folder projects there are no cross-repo commits, the diff panel only covers the primary folder, and every folder gets the same permissions. <https://codex.danielvaughan.com/2026/07/24/codex-multi-folder-projects-primary-folder-writable-roots-cross-repo-workspace-configuration/>
- The Codex app diff view fails with multi-repo directories (open). <https://github.com/openai/codex/issues/10817>
- Codex iOS remote drops the secondary folders of multi-folder projects (open). <https://github.com/openai/codex/issues/54508>
- The general Codex multi-repo request is still open. <https://github.com/openai/codex/issues/11956>
- Source issue still open; it asks for coordinated change sets presented as one unit, linked PRs with merge order, per-repo push/PR policy and multi-repo teleport, none of which are documented. <https://github.com/anthropics/claude-code/issues/23627>
- In a multi-repo web session each repo gets an independent PR; 'There was no behavior where changes across multiple repositories were consolidated into a single PR.' <https://dev.classmethod.jp/en/articles/claude-code-web-multi-repo-issues-prs/>
- Official docs: '--cloud works with a single repository at a time' and --teleport requires a checkout of the same repository, so multi-repo sessions cannot be moved between terminal and cloud. <https://code.claude.com/docs/en/claude-code-on-the-web>
- Codex multi-repo support request still open (updated 2026-10-02). <https://github.com/openai/codex/issues/11956>
- Codex Cloud environments still lack multiple repos per environment. <https://github.com/openai/codex/issues/50155>
- Codex App Git/diff/review UI stays tied to the starting repository when a parent workspace holds several repos. <https://github.com/openai/codex/issues/26338>

## P8 (F19): Unattended work stops at usage limits

Problem: When a long delegated task hits the 5-hour or weekly usage limit, the agent stops even though the reset time is known. If the reset falls overnight, the work waits until the engineer returns, finds the session and re-issues the prompt.

Demand: 169 reactions on the open issues.

Existing approaches:
- Claude Code auto-continue at usage limit (CLI, on by default) (0 stars, 2026-08-17): Interactive subscription sessions wait in place and continue the task after the reset (v2.1.234+) <https://code.claude.com/docs/en/interactive-mode#wait-for-a-usage-limit-to-reset>
- Claude Code Desktop 'Auto-continue when limits reset' (0 stars, 2026-08-10): Desktop retries the interrupted turn after a session-limit reset <https://code.claude.com/docs/en/whats-new/2026-w33.md>
- saaranshM/unsnooze (229 stars, 2026-11-01): Auto-resumes Claude Code, Codex CLI and other agent sessions after 5-hour or weekly limit resets <https://github.com/saaranshM/unsnooze>
- terryso/claude-auto-resume (821 stars, 2026-05-09): Shell wrapper that resumes Claude CLI tasks when the limit lifts <https://github.com/terryso/claude-auto-resume>
- songyb111-gachon/codex-auto-resume-windows (77 stars, 2026-11-07): Resumes the same Codex desktop conversation on Windows after limit resets <https://github.com/songyb111-gachon/codex-auto-resume-windows>
- Claude Code auto-continue at usage limit (autoContinueAtUsageLimit, v2.1.234) (0 stars, 2026-08-13): Interactive CLI sessions (and a Desktop checkbox) wait out a claude.ai 5-hour limit and resume with a continuation prompt after reset; on by default for subscribers. <https://aicatchup.com/news/claude-code-desktop-auto-continue>
- Claude Code auto-continue caveats write-up (0 stars, 2026-09-28): Documents surfaces and limits of the built-in auto-continue (CLI default on, Desktop checkbox, /rate-limit-options fallback). <https://wmedia.es/en/tips/claude-code-session-limit-auto-continue>
- dujunyi416/claude-nightshift (36 stars, 2026-07-20): Quota-aware automation: queue prompts overnight and auto-resume interrupted sessions on reset. <https://github.com/dujunyi416/claude-nightshift>

Known shortcomings:
- Claude Code auto-continue is not offered for background sessions or -p runs, does not start for resets more than 24h away (weekly limits), needs Enter after >30 min sleep, and the continued task still stops on permission prompts <https://code.claude.com/docs/en/interactive-mode#wait-for-a-usage-limit-to-reset>
- Codex has no built-in auto-resume for CLI (open) <https://github.com/openai/codex/issues/21073>
- Codex App /goal does not auto-resume after the 5h/weekly limit (open) <https://github.com/openai/codex/issues/28931>
- claude-auto-resume fails to parse reset time after Claude changed its output format <https://github.com/terryso/claude-auto-resume/issues/24>
- claude-auto-resume fails to run if already over a session limit <https://github.com/terryso/claude-auto-resume/issues/27>
- Codex has no native auto-resume at limit reset; request open with no maintainer reply; Goals stay in usageLimited after reset until a new user message. <https://github.com/openai/codex/issues/21073>
- Codex /goal auto-resume after 5h/weekly reset requested and still open; users rely on third-party desktop scripts. <https://github.com/openai/codex/issues/28931>
- Claude Code auto-continue does not apply to -p headless or background sessions, does not auto-wait for weekly resets more than 24h away, needs Enter after >30 min laptop sleep, ends if the terminal closes, and re-arms at most twice. <https://wmedia.es/en/tips/claude-code-session-limit-auto-continue>
- Claude Code auto-continue never arms when Remote Control is connected. <https://github.com/anthropics/claude-code/issues/100650>
- Claude Code auto-continue at usage limit does not trigger. <https://github.com/anthropics/claude-code/issues/103591>
- Session stalls on a consent prompt when a model-specific weekly limit is hit instead of continuing. <https://github.com/anthropics/claude-code/issues/104623>
- Third-party wrapper fails if already over a session limit, and broke when Claude's limit message format changed. <https://github.com/terryso/claude-auto-resume/issues/24>

## P9 (F27): No way to line up the next tasks

Problem: Engineers who already know the next several things the agent should do cannot queue them: they must wait for each task to finish before giving the next, and in the VS Code extension a new message interrupts the running task instead of waiting its turn. Delegation stays turn by turn, and the engineer has to stay present between tasks.

Demand: 137 reactions on the open issues.

Existing approaches:
- Claude Code CLI message queue (Enter while working; Ctrl+Enter to send now) (0 stars, 2026-11-08): Messages typed while Claude works are queued instead of interrupting <https://code.claude.com/docs/en/interactive-mode#queue-messages-while-claude-works>
- Claude Code VS Code extension queued messages (0 stars, 2026-11-08): Docs say a message sent while Claude works is announced as 'Message queued.' (v2.1.236+) <https://code.claude.com/docs/en/vs-code>
- vasiliyk/claude-queue (23 stars, 2026-04-28): Queue multiple Claude Code tasks with priorities and dependencies, pause/resume at plan limits <https://github.com/vasiliyk/claude-queue>
- starsh2001/qlaude (23 stars, 2026-02-22): Queue tasks for Claude Code and walk away, Telegram pings <https://github.com/starsh2001/qlaude>
- txtx/axel (21 stars, 2026-02-05): Task queue that dispatches to Claude/Codex/OpenCode <https://github.com/txtx/axel>
- Codex follow-up queue (CLI Tab to queue, IDE extension queue mode, desktop app queue list) (0 stars, 2026-11-03): Native queue in Codex: a queued message waits until the current run finishes; the IDE extension defaults to queue (chatgpt.followUpQueueMode) and the desktop app lets users edit, reorder or delete queued items. <https://www.memorylake.ai/en/blogs/codex-steer-vs-queue>
- Claude Code built-in message queue (0 stars, 2026-11-03): Enter while Claude works queues messages, but plain messages are passed in as soon as the current tool calls finish within the same turn; only slash and shell commands wait until the turn ends. <https://www.memorylake.ai/en/blogs/claude-code-queue-messages>
- codecShivam/claudeq (9 stars, 2026-09-14): Side-pane queue for Claude Code built on Stop/SessionStart/UserPromptSubmit hooks; delivers one queued message per turn in order, no patching. <https://github.com/codecShivam/claudeq>
- Vesely/cmux-claude-queue (3 stars, 2026-09-20): Option+Enter queues a prompt delivered as a fresh turn after the Stop hook fires (macOS + cmux only). <https://github.com/Vesely/cmux-claude-queue>
- ivanarama/PromptPilot (20 stars, 2026-11-07): Background task queue for Claude Code and other AI CLIs with web UI and Telegram bot. <https://github.com/ivanarama/PromptPilot>
- coding-by-feng/ai-agent-session-center (95 stars, 2026-11-05): Dashboard for Claude Code and Codex sessions with prompt queues and workspace resume. <https://github.com/coding-by-feng/ai-agent-session-center>

Known shortcomings:
- Queued messages are passed to Claude as soon as current tool calls finish, within the same turn, so they steer the running task instead of waiting as the next task <https://code.claude.com/docs/en/interactive-mode#queue-messages-while-claude-works>
- Request for deferred messages held until end of turn is open <https://github.com/anthropics/claude-code/issues/63190>
- Task queue for running multiple prompts sequentially or in parallel is open; earlier requests were auto-closed <https://github.com/anthropics/claude-code/issues/33323>
- VS Code extension queuing issue still open with users building Stop-hook workarounds <https://github.com/anthropics/claude-code/issues/30677>
- Third-party queue tools are small; the most-starred (Claude-Autopilot, 249 stars) has had no push since 2025-08 <https://github.com/benbasha/Claude-Autopilot>
- VS Code extension request to queue instead of interrupting is still open with no maintainer reply; users ask whether it is on the roadmap. <https://github.com/anthropics/claude-code/issues/30677>
- Task-queue request still open; earlier queue issues were auto-closed by the stale bot; the cmux workaround needs macOS and cmux. <https://github.com/anthropics/claude-code/issues/33323>
- Claude Code merges queued messages into one combined turn instead of one message = one turn FIFO. <https://github.com/anthropics/claude-code/issues/73661>
- No setting to hold queued messages until the turn completes instead of folding them mid-turn. <https://github.com/anthropics/claude-code/issues/87656>
- Desktop Code tab has no way to queue a message until the turn fully ends; Ctrl+Enter interrupts. <https://github.com/anthropics/claude-code/issues/92988>
- Queued messages are never delivered in Claude Code desktop (silent loss of input). <https://github.com/anthropics/claude-code/issues/104517>
- Public criticism (Sep 2026) that Claude Code cannot queue a message as a separate next task; cites a cycle of partial fixes and regressions. <https://digg.com/ai/pdwiholm>
- Codex queue bugs: 'App-server queued follow-up no longer exists' errors, queued prompts behaving like steer and being sent simultaneously, prompts disappearing before entering the queue. <https://github.com/openai/codex/issues/45019>
- Codex queued prompts behave like steer prompts; multiple queued prompts sent simultaneously. <https://github.com/openai/codex/issues/17285>
- Codex VS Code extension: submitted prompts randomly disappear before entering the queue. <https://github.com/openai/codex/issues/25928>
