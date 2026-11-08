# Judge checklists, P1–P9

Derived only from `problems.md` (problem statements and known shortcomings, as of 2026-11-08).

How to score: rate each item **met / partly met / not met** from the written solution description alone. Items describe outcomes, not designs; any mechanism that achieves the outcome counts. "Partly met" means the description achieves the item only for some of the cases, surfaces or paths the item names, or claims it without saying how. "SC:" names the known shortcoming of existing approaches that the item comes from, with its source.

## P1

**Agent harness leaks the engineer's personal identity**

- **R1 (core).** The engineer's identity (account email) no longer reaches sites or services they did not choose through anything the agent sends out (web search and fetch, shell commands, request headers such as User-Agent). This holds by default from the first session, with no per-session effort, and the agent can still do web research. Partly: only some outbound paths or tools are covered, or the protection works by giving up web tools.
- **R2. Identity in model context.** The engineer decides whether their email is given to the model at all. It is withheld by default or through a supported, durable opt-out, so the model cannot copy it into headers, commits or files. A solution that only filters outbound calls while the address stays in context is at most partly met. SC: the email is injected into the system prompt every session with no opt-out, the promised removal has not shipped, IS_DEMO hides only display surfaces, and the model has written the address into commits (claude-code #81138).
- **R3. Indirect egress paths.** Covers traffic from code the agent writes and later runs (scripts, programs, child processes) and from sub-agents, not only the text of the tool call at the moment it is checked. SC: the built-in check does not cover scripts Claude writes and runs itself, and it did not refuse a test command on 2.1.317/2.1.318 (claude-code #107757). Sub-agents put the email in curl User-Agent headers to sec.gov and bls.gov (claude-code #106012).
- **R4. Independent of exact strings and model obedience.** Catches the identity when it is encoded, split, re-cased or otherwise reformatted, and does not depend on the model following a prompt instruction. SC: hook workarounds match exact strings and miss encodings, and prompt rules did not prevent a leak (explainx write-up). Sub-agents sent the email despite a system-prompt instruction not to (claude-code #106012).
- **R5. No false positives on local work, and tunable.** Allows actions that do not leave the machine (file writes including heredocs, requests to localhost/127.0.0.1) even when they contain the address. When it does block during a headless run, the run reports the block instead of ending as success. It can be tuned or scoped without switching off all privacy protection. SC: the built-in check matches on the address plus a network word, denies heredoc writes and curl to 127.0.0.1 in headless runs, and lets the run end as success; the only way to turn it off is to disable the whole privacy plugin (claude-code #107144).
- **R6. Works for every account type and release channel.** Works on Team/Enterprise logins, on machines with managed settings and on the stable channel engineers actually run, or says plainly which of these it excludes. SC: claude-code-no-email does nothing on Team/Enterprise or managed-settings machines, because the built-in guard skips prompt.context hooks from user mods (AlexErrant/claude-code-no-email #1). The stable channel was on 2.1.311, which lacks the built-in mod (claude-code #81138).

**Feasibility constraint:** Third parties can use these today:
- PreToolUse hooks and mods that inspect and block tool calls. These see only the call text, not scripts that run later.
- A local egress proxy or OS-level filter that sees traffic from all agent child processes. Reading HTTPS headers requires TLS interception.
- A user mod that drops the email from context, on personal logins only.

These require the vendor to change the product:
- Stopping the harness from injecting the email.
- Keeping the email out of context on Team/Enterprise/managed machines.
- Fixing the built-in check or making it configurable at a finer grain.

## P2

**Permission behaviour does not match what the engineer configured**

- **R1 (core).** For every action the agent attempts, the decision that takes effect (allow, deny, ask) is the one the engineer's written configuration implies. Allowed actions run without prompts, denied actions never run, and only actions the configuration leaves open produce a prompt. Unattended runs therefore do not stall on prompts the configuration already answered, and for any action the engineer can see which rule decided it. Partly: correct for common cases but some stray prompts or bypasses remain, or there is no way to see which rule applied.
- **R2. Compound and variant commands.** Judges each part of a compound command (&&, ||, ;, |, subshells) separately, so a harmless part such as `cd` does not cause a prompt. Rules still match when commands carry global flags, options in other positions (for example `git -C <dir>`) or ordinary quoting. Any built-in warning, such as the one for quoted characters in flag names, can be governed by configuration. SC: compound commands prompt on the `cd` (claude-code #28240). Dippy rules miss `git -C` (Dippy #136). The quoted-characters warning cannot be disabled (claude-code #27957).
- **R3. Same rules in every execution context.** User-level rules apply inside skills and subagents, at plan-mode exit and on remote or mobile control surfaces. An "allow" from a rule or hook is honoured in all of these contexts. SC: skills and subagents do not inherit user-level allow rules (claude-code #18950). A PermissionRequest hook "allow" has been ignored for ExitPlanMode since v2.1.199 (claude-code #74256). The Remote Control mobile app prompts despite --dangerously-skip-permissions (claude-code #29214).
- **R4. Every configuration scope and mode takes effect.** User-level rules, workspace or project policy files and skip-permissions/yolo/bypass modes apply as written. Trust for new projects can be granted through configuration instead of one interactive approval per project. SC: user-level rules are not applied (claude-code #30519). Gemini CLI `.gemini/policies/*.toml` files do not take effect (gemini-cli #18186), and Gemini CLI v0.63.0 broke yolo mode (gemini-cli #29682). Bypass has been broken since v2.1.77 (claude-code #36168). Codex requires per-project trust, and the decision to trust all directories was reversed (codex #14599).
- **R5. Deny rules hold and enforcement can be verified.** Denied actions cannot be reached by rewording, chaining or wrapping. Commands the solution cannot understand are treated as not allowed (ask or deny), not as allowed. The solution comes with evidence a reviewer can check, such as tests, a security review or a way to dry-run a command against the rules. SC: deny-rule bypasses, and community hook reimplementations with no security review (claude-code #30519).
- **R6. Detects regressions.** When an agent update stops honouring the configured decision (a rule or hook result is ignored, or a mode breaks), the engineer is told or a check fails visibly. They should not find out from a stalled run or an unexpected action. SC: hook "allow" ignored since v2.1.199 (claude-code #74256). Bypass broken after v2.1.77 (claude-code #36168). Yolo broken by Gemini CLI v0.63.0 (gemini-cli #29682). Dippy limited by Cursor bugs (Dippy #129).

**Feasibility constraint:** Third parties can use these today:
- PreToolUse/PermissionRequest hooks, or the Codex and Gemini equivalents, that parse commands and return allow or deny.
- Rule and settings files.
- CI or self-tests that check the agent honours hook decisions.

These require the vendor to change the product:
- Prompts the harness raises outside hook control: ExitPlanMode, Remote Control mobile prompts, the quoted-flag warning, Codex per-project trust and broken bypass/yolo modes.
- Gemini CLI loading its policy files.
- Rule inheritance into skills and subagents. A hook helps there only if it fires in those contexts.

## P3

**Delegating work from forges and trackers other than GitHub**

- **R1 (core).** From an issue or ticket in GitLab, Bitbucket, Azure DevOps or Linear, the engineer can hand the work to an agent and get back a branch and a merge/pull request in the forge where the code lives. The ticket's context is passed in automatically. The engineer does not copy context by hand, manage the branch or MR, or need a GitHub account or mirror. Partly: works for only some of these forges or trackers, or one step (start, context, push back) stays manual.
- **R2. Writes back to the source forge.** The result lands as a pushed branch and an MR/PR in the non-GitHub forge itself, and can be updated after review. An uploaded copy that cannot push back does not count. SC: Claude Code cloud sessions accept GitLab/Bitbucket only as a bundle that cannot push back (claude-code-on-the-web docs). GitLab, Bitbucket and Azure DevOps requests remain open (claude-code #54054, #38179).
- **R3. No hidden GitHub dependency when starting from a tracker.** When work starts in a tracker such as Linear or Jira, the link from ticket to repository works with non-GitHub repositories. SC: Linear coding sessions require Linear's GitHub integration (Linear docs and changelog). Claude Agent for Jira opens PRs only in a connected GitHub repository (Atlassian blog).
- **R4. Self-hosted and server editions.** Covers self-hosted and on-prem editions (GitLab Self-Managed/Dedicated, Bitbucket Data Center, Azure DevOps Server) as well as cloud, or states exactly which it covers. SC: Cursor gives Bitbucket Data Center only Bugbot, and its Azure DevOps support covers Services only (Cursor docs). GitLab external agents are "Experiment" on Self-Managed/Dedicated (GitLab docs).
- **R5. Usable without special gating.** An ordinary team can use it without a top pricing tier or a feature flag the vendor must switch on, and its plan or licence prerequisites are stated. SC: GitLab external agents are Premium/Ultimate only and sit behind a feature flag enabled on request (GitLab docs).
- **R6. Reliable basic repository operations.** On each forge it claims, it reliably authenticates, fetches any branch and pushes, and it gives evidence of maturity such as GA status, tests or reported use. A beta that fails at these basics does not count. SC: Cursor's Azure DevOps and Bitbucket Cloud support is public beta (Cursor docs). Users report the Azure DevOps integration broken and cloud agents unable to get branches from Bitbucket (Cursor forum).

**Feasibility constraint:** Third parties can use these today:
- Forge or tracker webhooks and mentions wired to CI pipelines or a self-hosted runner that runs the agent CLI with a forge token and opens MRs through the forge API.
- MCP servers that give the agent access to forge and tracker APIs.

These require the vendor to change the product:
- Making the vendors' own cloud sessions (Claude Code on the web, Codex web) clone from and push to non-GitHub forges.
- Making tracker integrations (Linear coding sessions, Claude Agent for Jira) accept non-GitHub repositories.

## P4

**Not knowing when a long-running agent finishes or needs input**

- **R1 (core).** Whenever the agent finishes, or stops to wait for the engineer (approval, question, idle), the engineer gets a signal they will notice while doing other work away from the terminal. They neither have to watch the terminal nor lose time to an idle agent. Partly: covers only finishing or only input requests, or works only while the terminal is in view.
- **R2. Every idle state, without false alarms.** Signals approval and permission requests as well as completion, and also runs that end abnormally (API error, crash). It does not report "done" at intermediate continuations and does not send duplicates. SC: the Codex notify hook fires only for agent-turn-complete and has no dedup (notification-pipeline write-up; codex #3962). A turn ending on an API error fires no hook (codex #54884). The Stop hook fires at every /goal continuation (codex #52950).
- **R3. Reaches the engineer on the surfaces they use.** Works in IDE extensions and desktop apps as well as the terminal, regardless of a terminal's escape-sequence support, over Remote SSH and on the phone, with an audible or OS-level attention signal. SC:
  - OSC 9 support varies by terminal (notification-pipeline write-up).
  - The Codex IDE extension has no audible signal, and third-party notifiers fail over Remote SSH (codex #3962).
  - The Claude Code VS Code extension lacks native notifications (claude-code #57230).
  - The Codex VS Code extension does not request attention for approvals (codex #30821).
  - Codex Remote Control pushes are not delivered on iOS (codex #32908).
- **R4. Timely and tunable.** The signal arrives within seconds of the event, and the engineer can set how long the agent may sit idle before a reminder. SC: the Notification hook fires about 10 s late (claude-code #5186). The idle_prompt timeout is not configurable (claude-code #13922).
- **R5. Timestamps in the conversation.** Each message, instruction and background check shows when it happened, in both terminal and IDE views, without patching the vendor's UI. SC: Claude Code shows no per-message timestamps, and the only third-party option covers the VS Code panel only and patches its webview (claude-code #44763, #30745).
- **R6. Few prerequisites, and survives updates.** Works with API keys and cloud providers, without a particular subscription or a live remote-control session, and keeps working (or warns) after client updates. SC: Remote Control pushes need a subscription, both toggles, a live Remote Control session and an open terminal, and are unavailable with API keys or cloud providers (wmedia write-up). Codex hooks stopped running after a Desktop update (codex #21639).

**Feasibility constraint:** Third parties can use these today:
- Claude Code Notification/Stop hooks.
- The Codex notify script (fires on turn-complete only).
- Wrappers that watch the agent's process or output.
- Push services and IDE extensions.

These require the vendor to change the product:
- Codex hook events for approvals and for turns that end on an error.
- Removing the Notification hook delay.
- A configurable idle timeout.
- Native IDE attention signals.
- Timestamps in the conversation view without patching the webview.

## P5

**File work done through raw shell commands**

- **R1 (core).** Every file read and change the agent makes, in every mode including auto mode, is subject to the engineer's file-level permission rules and appears in the diff display and edit tracking they supervise with. This can come from the agent using the dedicated file tools or from bringing shell-made file access under the same supervision. Partly: covers only reads or only writes, or applies the rules but not diff display and tracking.
- **R2. Cannot be routed around.** Holds against any program that can touch files, such as interpreters (python -c), grep -r, heredocs, redirects and other utilities, not only a fixed list of command names. SC: the agent bypassed an Edit hook by writing files with python in Bash (claude-code #29709). Read deny rules are bypassed by grep -r and python one-liners unless the sandbox is on (dev.to rulestack).
- **R3. Works in auto mode, separately from auto-approval.** Still works while the harness's auto or bypass prompt steers the model toward cat/sed/heredocs. The engineer can keep auto-approval and still control how files are touched, through a supported, documented control rather than an undocumented switch. SC: the auto/bypass system prompt tells the model to read and edit files with cat/sed/heredocs (claude-code #89251, #87971). No documented setting separates auto-approval from tool routing, and the only reported switch is an undocumented environment variable (claude-code #87971).
- **R4. Path-scoped instructions and rules still apply.** Nested CLAUDE.md files and path-scoped rules reach the agent and are enforced for files it touches through the shell. When an action is blocked or redirected, the agent gets enough guidance to finish the task correctly. SC: Bash-first edits silently skip nested CLAUDE.md and path-scoped rules, and PreToolUse cannot inject additionalContext to redirect (claude-code #90450).
- **R5. Rewind and change tracking.** Changes made through the shell can be seen as diffs and undone with the same checkpoint and rewind the engineer uses for tool edits. SC: Bash-edited files break /rewind (claude-code #87575), and checkpointing does not track files changed only by Bash (checkpointing docs).
- **R6. Durable and maintained.** Keeps working across model and harness releases, has a way to detect when it has stopped working, and has a maintenance story beyond a one-off script. SC: a PreToolUse hook that blocked shell writes stopped being reliable after the Opus 5.5 release (claude-code #87971). Third-party hooks are tiny projects with low maintenance scores (claudepluginhub).

**Feasibility constraint:** Third parties can use these today:
- PreToolUse hooks on Bash (pattern-based, can deny with a message).
- PostToolUse hooks or wrappers that detect file changes after shell commands and replay Write/Edit hooks and path rules.
- Git or filesystem snapshots.
- Settings deny rules and the OS sandbox.

These require the vendor to change the product:
- Changing the auto-mode system prompt.
- A documented setting that separates auto-approval from tool routing.
- Letting PreToolUse inject context.
- Making the built-in diff display and /rewind track shell changes.

## P6

**No safe way to give cloud sessions credentials**

- **R1 (core).** Engineers can give async sessions in the vendor's cloud the credentials their tasks need, through a channel meant for secrets. Tasks that need authenticated access then run in the cloud without the secret being exposed: it is not typed into a field marked unsafe, and it does not appear in the repository, transcripts or logs. Partly: covers only some credential types or tasks, or keeps the secret safe in storage but leaks it in output.
- **R2. Every place a credential is needed.** Setup scripts, private package registries, database connection strings and other uses outside HTTP headers (SSH, tools that read environment variables) can all use the credential, not only HTTP requests to listed hosts. SC: network secrets never reach setup scripts, package registries or non-header uses (cloud-environments docs). The request for process-level environment variables usable by setup scripts, private registries and database URLs is still open (claude-code #32733).
- **R3. Cloud-provider access without long-lived keys.** Sessions can authenticate to AWS, GCP and Azure without storing long-lived static keys, for example through federated identity tokens. SC: cloud sessions get no OIDC identity token for keyless auth (claude-code #81502).
- **R4. Works with compatible third-party endpoints, and fails loudly.** Signing and credential schemes work with compatible non-vendor hosts, such as S3-compatible stores like R2. A credential that cannot apply produces a clear error when it is configured, not a silent 502 that pushes users back to plain environment variables. SC: the SigV4 secret signs only *.amazonaws.com, and R2 fails with a 502 without warning (claude-code #106173).
- **R5. Available to every account and environment type.** Works for Team/Enterprise accounts, organisations using customer-managed encryption keys and self-hosted environments, and behaves as documented. SC: the feature reached personal accounts but not Team accounts, and the UI did not match the docs (claude-code #32733). Self-hosted environments have no network secrets, and CMEK organisations cannot save them (cloud-environments docs).
- **R6. Change credentials in a running session.** Credentials can be added, rotated or revoked for a running session without starting over. SC: a running cloud session cannot reload environment variables and secrets (claude-code #106125).

**Feasibility constraint:** Inside the vendor's cloud, third parties can use only what the environment exposes today:
- Network secrets for listed hosts.
- Environment variables, which the UI warns against.
- Setup scripts.
- Network access to services the team runs elsewhere, such as a credential broker or MCP server it hosts. The session still has to authenticate to that service.

Credential-brokering proxies and local MCP brokers work only where the team controls the runtime.

These require the vendor to change the product:
- Process-level secret environment variables.
- OIDC tokens.
- SigV4 signing for non-AWS hosts.
- Reloading secrets in a running session.
- Availability for Team accounts, CMEK organisations and self-hosted environments.

## P7

**Cross-repository work in one session**

- **R1 (core).** One cloud or app session can take a change that spans several repositories, such as a shared type or API contract and its consumers, work on all of them together and deliver the change. The engineer does not split it into separate sessions or coordinate those sessions by hand. Partly: several repositories are visible but only one can be changed or delivered, or it works only locally and not in cloud or app sessions.
- **R2. Coordinated change set.** The pull requests in the different repositories are delivered as one linked unit: each refers to the others, and dependencies and merge order are stated and either enforced or checked. Reviewers can treat the set as a whole. SC: there are no coordinated change sets with linked PRs and merge order (claude-code #23627). Each repository gets an independent PR and nothing is consolidated (classmethod write-up). Codex multi-folder projects have no cross-repo commits (multi-folder write-up).
- **R3. Review covers every repository.** Diff, review and git views show changes in every repository in the session and work for all of them, not only the primary or starting one. SC: the Codex diff panel covers only the primary folder (multi-folder write-up). The diff view fails with multi-repo directories (codex #10817). The Git/diff/review UI stays tied to the starting repository (codex #26338).
- **R4. Per-repository policy.** Push, PR and permission settings can differ from one repository to another in the same session. SC: there are no per-repo push policies (claude-code #23627), and every folder gets the same permissions (multi-folder write-up).
- **R5. Moves between surfaces intact.** A multi-repo session can move between terminal and cloud, and be opened from remote and mobile clients, without losing repositories. SC: `--cloud` works with one repository at a time, and `--teleport` needs a checkout of the same repository (claude-code-on-the-web docs). Multi-repo teleport is missing (claude-code #23627). The Codex iOS remote drops the secondary folders (codex #54508).

**Feasibility constraint:** Third parties can use these today:
- Local multi-repo workspaces and orchestrators around the agent CLI (extra directories, coordinated branches, one subagent per repository).
- Multi-repo cloud sessions where the vendor already offers them.
- Forge APIs or CI checks to link PRs and enforce merge order.

These require the vendor to change the product:
- Multi-repo cloud environments where they are missing (Codex cloud).
- Multi-repo teleport and `--cloud`.
- Diff and review views that cover every repository.
- Per-repository permissions inside the app.
- Mobile clients that keep the secondary folders.

## P8

**Unattended work stops at usage limits**

- **R1 (core).** When a delegated task hits a usage limit with a known reset time, it continues by itself after the reset and carries on to completion with no engineer action, even when the reset falls overnight. Partly: resumes only in some situations, or the engineer must still confirm or re-issue the prompt.
- **R2. Every run mode.** Covers interactive sessions, headless (-p) and background runs, goal or long-running modes, and sessions with remote control connected. SC: auto-continue is not offered for background or -p runs (interactive-mode docs; wmedia write-up). It never arms when Remote Control is connected (claude-code #100650). The Codex CLI has no auto-resume, and Goals stay in usageLimited until a new user message (codex #21073, #28931).
- **R3. Every limit type, and any number of resets.** Handles weekly resets more than 24 h away and model-specific limits, and re-arms as many times as the task needs. SC: auto-continue does not start for resets more than 24 h away and re-arms at most twice (wmedia write-up). A model-specific weekly limit stalls the session instead of continuing (claude-code #104623).
- **R4. Survives the machine's state and the starting state.** Works after laptop sleep, with the terminal closed, and when started while already over the limit. SC: auto-continue needs Enter after more than 30 min of sleep and ends if the terminal closes (interactive-mode docs; wmedia write-up). claude-auto-resume fails if already over a session limit (claude-auto-resume #27).
- **R5. No stalls after resuming.** The resumed task does not stop on consent or permission prompts that the engineer's configuration already answers. SC: the continued task still stops on permission prompts (interactive-mode docs). The session stalls on a consent prompt at a model-specific weekly limit (claude-code #104623).
- **R6. Robust reset detection, and visible failure.** Learns the reset time in a way that survives changes in the agent's output wording, and reports a failure to resume instead of leaving the task silently stopped. SC: claude-auto-resume broke when the limit message format changed (claude-auto-resume #24). The built-in auto-continue does not trigger (claude-code #103591).

**Feasibility constraint:** Third parties can use these today:
- Wrappers, OS schedulers and session-resume commands (and desktop automation for the apps) that wait out the reset and restart or resume the session.
- Settings that pre-approve permissions.

These require the vendor to change the product:
- Auto-continue for headless, background and Remote Control sessions.
- Auto-continue for weekly resets.
- A machine-readable reset time.
- Removing the consent prompt at model-specific limits.
- Native auto-resume in Codex.

## P9

**No way to line up the next tasks**

- **R1 (core).** While the agent works, the engineer can line up several next tasks. Each starts only after the previous one has finished, in the order given, without interrupting the running task and without the engineer being present between tasks. Partly: only one item can be queued, queued items still change the running task, or it works on only some surfaces.
- **R2. Waits for the end of the task.** Queued items are held until the current turn or task has fully ended, instead of being passed in once the current tool calls finish. Steering the running task remains a separate, explicit choice. SC: queued messages are passed in mid-turn and steer the running task (interactive-mode docs; claude-code #63190). There is no setting to hold them until the turn completes (claude-code #87656). Codex queued prompts behave like steer prompts (codex #17285).
- **R3. One item, one task, in order.** Each queued item runs as its own turn, first in first out, and is never merged with others or sent at the same time. SC: queued messages are merged into one combined turn (claude-code #73661). Codex sends several queued prompts at once (codex #17285, #45019).
- **R4. Every surface.** Works in the CLI, the IDE extension (VS Code) and the desktop app. A message sent on any of them while the agent works waits its turn instead of interrupting. SC: in the VS Code extension a new message interrupts, and the request is still open (claude-code #30677). The desktop Code tab cannot hold a message until the turn ends, and Ctrl+Enter interrupts (claude-code #92988).
- **R5. No silent loss.** Queued items are kept and visible until delivered and survive client errors, and a failed delivery is reported. SC: queued messages are never delivered in Claude Code desktop (claude-code #104517). Codex prompts disappear before entering the queue (codex #25928), and Codex reports "queued follow-up no longer exists" errors (codex #45019).
- **R6. Portable and maintained.** Not tied to one OS or terminal multiplexer, and has a maintenance story or regression checks. SC: the cmux workaround needs macOS and cmux, and earlier queue requests were auto-closed (claude-code #33323). The most-starred third-party queue tool has had no push since 2025-08 (Claude-Autopilot). Public criticism cites a cycle of partial fixes and regressions (digg).

**Feasibility constraint:** Third parties can use these today:
- Stop, SessionStart and UserPromptSubmit hooks that feed one queued prompt per turn.
- Wrappers or background queues that run successive headless invocations.
- A side pane, web UI or chat bot to manage the queue.

These require the vendor to change the product:
- How the built-in input box treats a message sent mid-task (folding it into the turn in the CLI, interrupting in VS Code and desktop).
- Fixing message loss in desktop.
