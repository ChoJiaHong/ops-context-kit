## cc-projects
### Analysis
The developer is doing four jobs by hand: splitting the work, sending it out, tracking it, and joining it back up. The fix is to move each job into durable artifacts and automation, so the human approves only twice: the plan and the final merge.

Diverge:
1. An orchestrator session writes a task graph file (DAG) and launches cloud sessions for the tasks that are ready.
2. Plan as GitHub issues with acceptance criteria. Sessions take issues, and PRs link back to them.
3. Contract-first: land interfaces, stubs and failing acceptance tests first. Workers then fill in against fixed contracts.
4. Read status from PR and CI state, not from chat.
5. An integration branch plus a merge queue that rebases automatically.
6. A separate verifier session with fresh context reviews each PR against its acceptance criteria.
7. A budget-aware scheduler that caps concurrency to fit the usage limits.
8. A file-ownership map so parallel tasks don't touch the same files.
9. A retrospective loop that improves the decomposition templates.

Converge: Issues alone (2) still leave tracking to the human. Retrospectives (9) are slow to pay off. The strongest combination is a machine-readable plan with dependencies, owned paths and acceptance commands (1, 8), status read from git, PR and CI (4), and independent verification against contracts that land first (3, 6). Budget control (7) matters because of the limits, but it comes second.

### Proposals
P1: Plan-file orchestrator — An orchestrator session writes plan.yaml: one entry per task, with id, dependencies, owned paths, acceptance commands and branch name. The human approves it once. A dispatcher starts a cloud session for each ready task with a generated prompt telling it to open a PR to the integration branch, labelled with its task id. A poller uses gh to read PR/CI state into a status table. When dependencies merge, it starts the next tasks.
P2: Contract-first plus verifier sessions — Phase one lands interfaces, stubs and failing acceptance tests on the integration branch. Workers implement against them. Each PR starts a fresh verifier session. It runs that task's acceptance commands, checks that the diff stays inside the task's owned paths, and posts an approve or reject review. Only approved PRs go into the merge queue, so the human doesn't check each result by hand.
P3: Budget-aware scheduling — The dispatcher records the usage of each session it runs and sets a cap on concurrent sessions. It ranks ready tasks by critical-path length. As the subscription limit gets close, it holds new low-priority tasks back and posts a short digest of what is done, running, blocked and deferred.

## honest-arch-diagrams
### Analysis
The failure is a model inventing components. Trust has to come from construction: every node and edge must trace to a piece of evidence, and gaps must be drawn as gaps. The LLM should choose scope and describe the diagram, not author it. Constraints: a zero-dependency Node CLI, and no secret values in any output.

Diverge:
1. Deterministic extractors build a graph IR with provenance, and the diagram is rendered only from that IR.
2. The LLM drafts a diagram and a validator removes anything without evidence.
3. Evidence tiers: observed (traces), declared (manifests), inferred (naming conventions), each with its own line style.
4. Explicit "unknown" nodes for references that don't resolve.
5. Trace-first paths, with config filling the gaps.
6. Field allowlists so secret values never leave the parsers.
7. A drift view of declared versus observed edges.
8. Skill rules that forbid drawing without CLI output and require element ids.
9. Golden-fixture tests for the parsers.
10. Asking the user about gaps.

Converge: Validating a draft (2) is weaker than generating from evidence, but it is still useful when agents edit a diagram. Asking the user (10) and drift (7) are extras. The core is 1, 3, 4, 6 and 8.

### Proposals
P1: Evidence graph IR with provenance — The CLI parses each source. Kubernetes: Ingress to Service to selector to Deployment. Helm and compose: links. Terraform JSON: load balancer, listener, target. OpenAPI: routes. OTel: span parent and peer.service. It emits nodes and edges, each carrying the source file, a JSON pointer and its evidence tier. Mermaid is rendered only from this IR. Line style shows the tier, and references that don't resolve become "?" nodes.
P2: Diagram claim verifier — The skill tells agents to generate diagrams through the CLI. If an agent edits one, `verify` parses the Mermaid and matches every node and edge to an IR element id. It fails with a list of unsupported elements, for example a cache with no evidence. The agent must remove each one, or mark it "assumed" with the user's confirmation, which shows as dashed and labelled.
P3: Allowlist extraction with a fail-closed scan — Parsers copy only structural fields: kind, name, namespace, ports, hostnames, selectors and env var names. Secret data, env values and credentials in URLs are replaced by the variable name and "redacted". Before anything is written, the output is scanned for credential patterns and high-entropy strings. Any hit aborts the write.

## squadra
### Analysis
Coordination state lives in chat memory, so it disappears on reset and can't be checked. It needs to become an append-only local ledger. Every claim (received, tested, reviewed, shipped) should be tied to a git object hash. Constraints: Python stdlib only; Codex can't wake Claude; Cursor is never launched; nothing is published.

Diverge:
1. An append-only JSONL ledger in the git common dir, shared by all worktrees.
2. Assignment inboxes with an explicit acknowledgement that records the session id.
3. A test wrapper that records the tree hash, the command and the exit code.
4. Reviews tied to a tree hash, and a ship check that compares the shipped tree to the reviewed one.
5. A rule that rejects self-review.
6. Transcript reconciliation to check agents' claims.
7. A decision log plus a resume briefing for new windows.
8. Path locks for ownership.
9. Polling at session or prompt hooks, because agents can't wake each other.
10. A status CLI for the human.

Converge: Transcript reconciliation (6) is useful but harness-specific. Path locks (8) are folded into assignments. The best three are hash-bound evidence (1, 3, 4, 5), the acknowledgement handshake (2, 9) and the resume briefing (7).

### Proposals
P1: Hash-bound evidence ledger — A stdlib CLI appends JSONL under `git rev-parse --git-common-dir`/squadra. `squadra test -- cmd` records the tree hash (plus a digest of any uncommitted changes), the exit code and a log digest. `squadra review` records the reviewer's session and the reviewed hash, and rejects authors reviewing their own work. `squadra ship-check` fails unless the exact tree being shipped has a passing test and an independent review.
P2: Acknowledged assignments — `squadra assign` records owner, scope paths and acceptance criteria. Session hooks (Claude SessionStart/UserPromptSubmit; an instruction in Codex and Cursor to run `squadra inbox`) show pending work. `squadra ack` records the session id and transcript path. If an assignment isn't acknowledged within N minutes, `squadra status` shows it as "not received", so the human relays it by hand, for example to Cursor.
P3: Decision log and resume briefing — `squadra decide` records a timestamped decision with its author and rationale. `squadra brief --for <window>` rebuilds from the ledger that window's owned tasks, latest test and review evidence, open items and recent decisions. It runs at session start, so a reset or new window starts from recorded facts instead of from what the chat remembers.

## termaxa
### Analysis
The risk comes from ordinary chores done with the most destructive variant of a command, run unattended. A useful guard has to be deterministic and local. Its policy has to be reviewable. It shouldn't stall the agent: instead of a bare refusal, it should give a safer route the agent can take on its own. Because hooks only advise, it also helps to make damage recoverable.

Diverge:
1. Parse commands into argv per segment and match per-tool rules (git, rm, psql, terraform, kubectl, docker).
2. Deny with a reason that names a safer equivalent.
3. Context checks: uncommitted changes, whether the branch is shared upstream, whether the database target is production, whether paths are inside the workspace.
4. Automatic recovery points before operations that discard work.
5. Require a terraform plan or a kubectl dry run before applying.
6. A policy file in the repo with example cases that are tested in CI.
7. An audit log of each decision.
8. A conservative default for commands it can't parse.
9. Checks on write tools for protected paths.

Converge: Dry-run-first (5) and protected paths (9) fit into the rule engine. The best three are context-aware rules with safer redirects (1, 2, 3, 8), recovery points (4), and a tested repo policy with audit (6, 7).

### Proposals
P1: Context-aware rules with safer redirects — One binary is called from each agent's pre-execution hook. It splits compound commands, matches per-tool rules, and checks live state: uncommitted files, upstream tracking, and database host versus a production list. It returns allow, or deny with a concrete safer alternative: force-with-lease, a soft reset or revert, moving files to a trash directory, plan before apply. The agent can retry without a human. Commands it can't parse get the conservative default.
P2: Automatic recovery points — Before allowing a git operation that would discard working-tree changes or move refs, the hook saves `git stash create` output and HEAD under refs/termaxa/<timestamp>. Before deletions inside the repo, it copies the affected files into .git/termaxa-trash. `termaxa undo` lists recovery points and restores one. Destructive SQL or cluster deletes are allowed only if a recent recorded export of that target exists.
P3: Tested in-repo policy and audit — Policy lives in a committed .termaxa.toml. Each rule has an id, a matcher, conditions, a verdict, a message, and example commands with their expected verdicts. `termaxa test` checks the examples in CI, so policy changes are reviewed like code. Every decision is appended to a local log with its rule id, for review after unattended runs and for tuning false positives.

## tokeneconomizer
### Analysis
Cost comes from the prefix re-sent every turn (instructions, tool definitions, history), from cache misses, and from cold-start exploration in every session. The only levers are settings, instruction files, hooks and plugins. Every change must be reversible and measured with cache-aware pricing, including the tool's own model calls. It must never end a turn.

Diverge:
1. Disable MCP servers and tools a repo never uses, based on usage in transcripts.
2. Keep the prefix byte-stable so cache reads hit: no timestamps or volatile state in instruction files.
3. Compact the instruction files.
4. A repo warm-start digest that cuts exploration turns.
5. Shrink large tool outputs where the harness allows it.
6. Suggest fresh sessions when context gets large.
7. Run A/B experiments on settings patches, judging them by cost per successful task.
8. Warn about idle gaps longer than the cache TTL.
9. Precomputed answers to frequent first questions.

Converge: Shrinking output (5) depends on the harness. Session suggestions (6) and TTL warnings (8) are small wins, and precomputed answers (9) overlap with the digest. Measurement (7) has to be the base or the savings can't be shown. Then pruning plus prefix stability (1, 2, 3), then the warm-start digest (4).

### Proposals
P1: Measured, reversible optimization loop — Adapters parse each harness's transcripts. They compute session cost from input, cache-write, cache-read and output tokens at cache pricing, including the tool's own calls. Each optimization is a versioned patch to settings or instruction files, backed up before it applies. Patches are switched on for alternate sessions. Cost per successful task (tests pass, commit kept, no user redo) is compared, and patches that raise cost or lower success are reverted automatically.
P2: Usage-based pruning with a stable prefix — From transcripts, count which MCP tools, skills and instruction sections each repo actually uses. Write per-repo settings that disable servers never used. Propose a compacted instruction file. Move dynamic content (date, git status) out of always-loaded instructions into hook context added later, so the cached prefix stays byte-identical across turns and sessions.
P3: Warm-start repo digest — Mine the read and search calls that repeat across sessions for stable facts: build and test commands, module map, entry points, known pitfalls. Write them into a small digest loaded by a SessionStart hook. Store the hashes of the source files behind it and regenerate when they change. Measure whether exploratory turns and tokens actually drop, and remove the digest if they don't.

## transcripto
### Analysis
The truth is already in the transcripts, but finding it takes too much reading. A local, dependency-free tool should turn them into a common event stream, find failures that were never resolved, and check the closing claims against the evidence.

Diverge:
1. Per-harness adapters into one event schema.
2. A failure detector: error flags, nonzero exits, failed edits, denials, interruptions.
3. Work out which errors were never followed by a successful retry.
4. Extract claims from the final message and check each against events.
5. Use git diff since session start as ground truth for files.
6. Check that expected artifacts exist.
7. A Stop hook that prints a receipt right away.
8. Timeline reports with transcript line references.
9. An optional LLM judge (it conflicts with the no-dependency rule).
10. A watch mode for live sessions.

Converge: Drop the LLM judge (9). Watch mode (10) is secondary. The best three are the normalizer with unresolved-failure detection (1, 2, 3, 8), the claim cross-check (4, 5, 6), and the receipt delivered at the right moment (7).

### Proposals
P1: Normalized events and unresolved failures — Adapters for Claude JSONL, Codex session files and Cursor storage map entries to {time, tool, args, result, exit code, error flag, paths}. The detector flags failures with no later successful equivalent: errored edits, commands whose last run failed, denied permissions, interrupted calls, expected outputs never written. It prints a one-screen report with a line reference into the transcript for each item.
P2: Claim-versus-evidence check — Pattern rules pull claims from the closing message ("tests pass", "created X", "updated Y", "ran Z"). For each claim, it looks for support: the exit code of the last matching test command, a successful write plus the file existing now, and the path appearing in git diff. Each claim is marked supported, contradicted or unsupported, with the evidence line.
P3: Stop-hook receipt — A snapshot of git state is taken at session start. At session end, a hook runs the analyzer and stores a receipt next to the transcript, showing files actually changed, failed commands still unresolved and unsupported claims. The receipt appears before the agent's summary, so the engineer reads verified facts first.

## unlazy
### Analysis
The agent quietly drops required outcomes, and parents accept subagents' word for their work. Completion has to be defined by checks the user approved, run by hooks, and not by the agent's own report. Checks run with ambient access, so the user must approve them and they must be locked against quiet edits.

Diverge:
1. A requirements manifest with a deterministic check for each outcome.
2. A Stop hook that refuses to finish while checks fail.
3. Work lists generated from the codebase (remaining call sites), with zero remaining as the goal.
4. Structured subagent receipts that the parent verifies independently.
5. A fresh-context auditor that compares requirements with the diff.
6. Scan diffs for elision placeholders and new TODOs.
7. Smaller batches to reduce truncation.
8. A hash-pinned manifest that needs re-approval when changed.
9. A progress ledger.

Converge: The auditor (5) is still the model judging itself. Batching (7) helps but doesn't verify anything. The best three are the pinned manifest with a stop gate (1, 2, 8), generated work queues (3), and receipt verification with placeholder scanning (4, 6).

### Proposals
P1: Pinned outcome manifest with a Stop gate — A skill turns the request into .unlazy/manifest.json: numbered outcomes, each with a check command and an expected exit code or output pattern. The user approves it once, and its hash is recorded, so changed checks need re-approval. A dependency-free Node Stop hook runs every check and blocks finishing, listing the failures as feedback. The Codex skill runs the same verifier as its last step.
P2: Generated work queue — For fan-out work, a user-approved generator command lists the items, for example remaining old-API call sites. Subagents get slices of the list. The check reruns the generator and expects zero items left, so the parent judges completion from the codebase, not from what subagents report.
P3: Verified subagent receipts — A SubagentStop hook requires a JSON receipt listing the items claimed and the files touched. A verifier on the parent's side checks those files really changed in git and runs the per-item checks. It also scans the diffs for elision placeholders, newly added TODOs and newly skipped tests. Mismatches go back to the parent as rejected work, not accepted output.
