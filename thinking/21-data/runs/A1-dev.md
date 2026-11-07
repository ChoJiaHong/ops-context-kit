## cc-projects
### Analysis
The developer is doing the jobs of scheduler, tracker, QA and merge bot by hand. Each of those jobs becomes mechanical once the goal is written down as structured data. So the fix is a project layer above the sessions that owns the plan, the state and the integration, and brings the human in only at decision points.

Where parallel agent work actually breaks:
1. Decomposition hides coupling, so sessions edit the same files or invent incompatible interfaces.
2. "Done" is self-reported, so the human re-checks every PR.
3. Integration happens at the end, when conflicts are largest.
4. Progress is invisible unless you open each session.
5. Usage limits are hit mid-wave, leaving work half-finished.

Matching mechanisms:
- A plan file in the repo (a task DAG). Each task has a scope (the paths it may touch), dependencies, interface contracts and acceptance commands. A planner session drafts it and the human approves it once. Coupling is cut by landing shared interfaces and stubs first, as task zero.
- A dispatcher that launches one cloud session per ready task. Each session gets a generated brief and a branch cut from the integration branch. The dispatcher tracks a state machine (ready, running, PR open, verifying, verified, merged, failed, escalated) from session status and PR events.
- Verification that does not trust the worker. A separate verifier session or CI job runs the acceptance commands on the PR head, checks that the diff stays in scope, and reviews against the task spec. Failures go back to the worker with the concrete output, up to N retries, then escalate.
- Continuous integration of verified tasks through a merge queue into the integration branch. Dependent tasks start only after their prerequisites merge, so they build on real code instead of guesses.
- Budget-aware scheduling: cap concurrency, put the critical path first, record usage per task, and stop launching new tasks before the limit so in-flight ones can finish.

The human's touchpoints shrink to approving the plan, answering escalations and reviewing the final integration PR. That PR comes with a generated summary mapping tasks to commits and evidence.

Main risk: the planner splits the goal badly. Mitigation: a worker can report "blocked/needs-split", which returns the task to the planner instead of letting the worker improvise outside its scope.

### Proposals
P1: Plan-DAG orchestrator — A planner session writes `.project/plan.yaml`: tasks with id, brief, owned paths, depends_on, interface contracts and acceptance commands. After one human approval, a dispatcher launches a cloud session per ready task on a branch from an integration branch. It tracks each task through ready/running/PR/verifying/merged/escalated using session status and PR events, and shows everything on one dashboard. A worker can return "needs-split" to trigger replanning instead of improvising outside its scope.
P2: Independent verify-and-merge queue — A fresh verifier session or CI job checks each PR: it runs the task's acceptance commands on the PR head, rejects diffs that touch paths outside the task's scope, and reviews against the spec. Failures go back to the worker with the exact output (at most N retries, then escalate). Verified PRs merge into the integration branch in dependency order, and dependent tasks launch only after that. The final PR carries a generated task→commit→evidence table.
P3: Contract-first, budget-aware scheduling — Task zero lands shared types, interfaces and stubs, so parallel tasks code against fixed contracts. The scheduler caps concurrency, orders tasks by critical-path length and logs usage per task from session metadata. It stops launching new work once projected usage would exceed the remaining subscription allowance, lets in-flight tasks finish and resumes after the reset. A task that uses more than twice its estimate is paused for replanning.

## honest-arch-diagrams
### Analysis
The model hallucinates because it is asked for a picture and fills gaps from priors: most services it has seen "have" a Redis and an auth gateway. The fix is to separate extraction from rendering. A deterministic CLI builds a typed graph in which every node and edge carries evidence (a file plus a JSON pointer or line number). The agent may only render, label or summarize that graph. Anything without evidence is either left out or drawn as an explicit gap.

What each source can prove:
- kubectl JSON and rendered manifests: Ingress or HTTPRoute → Service, Service → workload by selector match, ports, hostnames in env vars and ConfigMaps, NetworkPolicy, mesh mTLS resources.
- Helm: only `helm template` output counts. Raw templates are refused, not guessed at.
- compose: services, networks, hostnames in env vars.
- terraform show -json: managed endpoints (databases, caches, load balancer listeners and certificates) that can be matched against hostnames.
- OpenAPI: entry routes.
- OTel traces: calls that were actually observed (client spans with server.address, peer.service, db.system). This is the strongest evidence.

Each edge gets a tier, drawn differently: observed, declared, or inferred from a hostname match. Attributes are claims too. TLS appears only if there is an Ingress tls block, a listener certificate or a STRICT mTLS policy; otherwise the label says "TLS: unknown". Edges that are declared but never observed, and edges observed but never declared, are reported as drift.

Secrets: the parser never reads Secret `data` or `stringData`. A secretKeyRef becomes a name/key reference only, terraform `sensitive_values` paths are dropped, and credential-shaped strings in URLs are cut down to scheme, host and port. Redaction happens at parse time, so secrets never reach the graph or the agent's context.

Zero dependencies: JSON is built in. YAML needs a small built-in parser for the block subset that manifests use, and it should fail loudly on anything it does not support.

The skill tells the agent to run the CLI, present its output, never add elements, and run a verifier on any diagram it edits. The verifier fails on any element that has no evidence behind it.

### Proposals
P1: Evidence graph CLI — `archgraph extract` reads kubectl JSON, rendered Helm, compose, terraform show -json, OpenAPI and OTLP JSON traces. It writes graph.json, where each node and edge has an evidence list [{file, jsonPointer/line}] and a tier (observed, declared or inferred). It joins Ingress→Service via backend refs, Service→workload via selector, and workload→dependency via env/ConfigMap hostnames matched to Services or terraform endpoints. Secret data, sensitive_values and credential substrings are dropped while parsing. `render` outputs Mermaid, an evidence table and an explicit gaps list.
P2: Grounding checker for agent-drawn diagrams — `archgraph verify diagram.mmd --graph graph.json` parses Mermaid or D2 and requires every node and edge to carry an id that exists in graph.json. It fails with a list of ungrounded elements and of attribute claims (TLS, auth, cache) that have no evidence. The skill makes agents run verify before presenting any diagram and draw unknowns as dashed "unverified" boxes. CI runs it on committed docs, so diagrams fail visibly when manifests change.
P3: Declared-vs-observed reconciliation — Merges edges from traces with edges from config and draws each tier differently: solid if observed in traces within the window, dashed if declared but never observed, red if observed but undeclared. Attributes like TLS appear only with proof (Ingress tls, a listener certificate, mesh PeerAuthentication STRICT); otherwise they are labeled "unknown". A drift report surfaces both stale config and undocumented dependencies, so the agent cannot quietly paper over either.

## squadra
### Analysis
Everything the user loses lives in chat memory. The fix is a durable, local, append-only ledger that every window reads and writes through a small CLI, plus rules that tie every claim to a hash instead of a sentence.

Location: separate clones and worktrees need one shared place. The default is `~/.squadra/<project-id>/`, with the project id taken from the root commit hash, and it can be overridden. Codex's sandbox either gets that directory added as a writable root, or writes to an `outbox/` inside its checkout that the human-side CLI imports. Writes are JSONL appends under `fcntl` locks. Each event is hash-chained to the previous one, so edits can be detected, and current state is rebuilt by replaying the log.

Mechanisms:
- Ownership: `claim task --paths` creates a lease tied to (harness, session id, checkout). Claims on overlapping paths are refused. A lease expires when the owner's transcript shows no activity for N minutes.
- Was the assignment received: assignments are pulled, not pushed, because Codex cannot wake Claude windows and Cursor is never launched. Each window checks its inbox at session start or on each prompt (via a hook in Claude Code; via AGENTS.md or Cursor rules telling it to run `squadra inbox` elsewhere). Receipt is an explicit `ack`, independently confirmed by finding the assignment's nonce in the transcripts on disk. If neither happens before a timeout, the assignment shows as "not delivered" with a ready-to-paste prompt for the human.
- Which code was tested: `squadra run -- <cmd>` records the exact tree hash (built with a temporary index that includes uncommitted files), the command, the exit code and a digest of the log.
- Was the reviewed code the shipped code: reviews record a verdict against a tree hash, and the reviewer must be a different identity from the author (a different session, ideally a different harness). `squadra gate <commit>` checks that the commit's tree matches both a passing test run and an approved review. It only reports and never pushes.
- Decisions: `decide` events with timestamp, author and a supersedes link.
- Context reset: `squadra brief --me` prints current claims, pending assignments, open reviews and recent decisions. Claude Code injects it on SessionStart; other tools run it by hand.

Self-review is blocked by structure, not by trusting the agent: approvals from the author identity never satisfy the gate.

### Proposals
P1: Hash-bound ledger and ship gate — A Python-stdlib CLI appends hash-chained JSONL events (claim, assign, ack, test, review, decide) to `~/.squadra/<root-commit>/` under fcntl locks. `squadra run -- cmd` records the tree hash of the working state (via a temp index that includes untracked files), the command and the exit code. Reviews record a verdict against a tree hash, and the reviewer identity (harness+session) must differ from the author's. `squadra gate <commit>` passes only if that exact tree has a passing test and a non-author approval. It reports and never pushes.
P2: Pull inbox with verified delivery — Each assignment carries a nonce and waits in a per-window inbox. Claude Code hooks (SessionStart/UserPromptSubmit) inject pending items, and Codex/Cursor rules tell the agent to run `squadra inbox` at the start of each turn. Delivery is confirmed two ways: an explicit `ack`, and a scan of on-disk transcripts (Claude JSONL, Codex sessions, Cursor's SQLite store via stdlib sqlite3) for the nonce. Anything unconfirmed after a timeout is flagged "not delivered" with a ready-to-paste prompt for the human.
P3: Leases plus reset-proof briefs — `claim` takes a task and path globs and refuses any overlap with live leases. Liveness comes from the owner's transcript mtime, so abandoned work frees itself. `decide "text" --supersedes <id>` timestamps decisions. `squadra brief --me` rebuilds a compact state from the ledger: my leases, pending assignments, reviews I owe, and decisions since my last ack. Claude Code injects it on SessionStart and other windows print it manually, so a new window resumes from the ledger instead of from memory.

## termaxa
### Analysis
Blocklists fail in both directions. `rm -rf build/`, or `git reset --hard` on a clean tree, is harmless, while `git checkout -- .` or `git clean -fdx` can be the real disaster. The useful question is not "is this command scary" but "would this destroy something that cannot be recovered elsewhere?" That can be answered deterministically, from local state, before the command runs.

Approach: parse the command, compute the blast radius, decide, and if a lossy operation is allowed, make it recoverable first.

Parsing: a shell tokenizer that splits on `&&`, `;`, `|` and subshells, recurses into `bash -c`/`sh -c`/`eval` strings, strips env prefixes and `sudo`, and understands `xargs rm` and `find -delete`/`-exec rm`. Input it cannot parse that contains a destructive verb is treated as the worst case.

Blast radius by command family:
- Files: resolve the rm targets. Loss means modified files, untracked files that are not ignored, or anything outside the repo. Ignored build output costs nothing.
- git: for reset --hard, checkout --, restore, clean and stash drop/clear, use `git status --porcelain`, `git clean -n` and diffs to list exactly which files hold unsaved work. For push --force, loss means remote commits that are not in the local branch. For branch -D, it means unmerged commits.
- psql: DROP, TRUNCATE, or DELETE without WHERE, with the target host checked against the policy's list of local hosts.
- terraform destroy or apply -auto-approve in protected workspaces; kubectl delete in protected contexts; docker volume rm and prune --volumes.

Deciding with approvals off: no human is there to ask. The outcomes are allow; deny with a precise reason and a safer command ("a.ts and b.ts have uncommitted changes; run `git stash push -u` first"); or snapshot, then allow. Agents usually follow a specific denial and tend to work around a vague one.

Recoverability: snapshot the working tree, untracked files included, into a private git ref; record remote SHAs before force pushes; move deleted files into a trash directory; dump small tables before a DROP. `termaxa undo` restores any of these.

Policy lives in `.termaxa.toml` in the repo (deletable roots, protected branches, local DB hosts, protected contexts and workspaces, size limits), so changes get reviewed in PRs. A write-tool hook refuses agent edits to the policy and the hook config, on the understanding that hooks advise rather than enforce.

### Proposals
P1: Loss-aware evaluator — The hook binary parses the shell command (splits chains, recurses into `sh -c`, handles xargs and find -delete), then works out from local state what would be lost for good: `git status`/`git clean -n` for reset/checkout/restore/clean, remote-only commits for push --force, untracked non-ignored files for rm, non-local hosts for DROP/TRUNCATE, protected contexts or workspaces for kubectl/terraform. If nothing would be lost, it allows silently. Otherwise it denies, naming the exact files or commits and a concrete safer command.
P2: Snapshot-then-allow with undo — Before a lossy operation that the policy permits, make it recoverable. Commit the full working tree, untracked files included, via a temporary index and `git commit-tree` into `refs/termaxa/<timestamp>`. Record the remote SHA before a force push. Move rm targets under a size cap into `.termaxa/trash/<ts>/`, rewriting the command where the hook can modify input. `pg_dump` small tables before a DROP. `termaxa undo <id>` restores; snapshots are pruned after N days.
P3: Repo policy with safer-spelling rewrites — `.termaxa.toml`, committed in the repo, declares deletable roots, protected branches, local DB hosts, protected kube contexts and terraform workspaces, plus rewrite rules (`push --force` → `--force-with-lease`, `reset --hard` → `stash push -u && reset --hard`). Rewrites are applied where the hook can modify input; elsewhere they come back as the denial message. A write-tool hook refuses agent edits to the policy and the hook config, and every decision is logged as JSONL for review.

## tokeneconomizer
### Analysis
Per-turn cost has four parts. The fixed prefix (system prompt, instruction files, tool definitions), history and new input are billed mostly as cache reads. Cache writes are added whenever the prefix changes or the cache expires. Then there is output. Across sessions the waste comes from: tool definitions for MCP servers this repo never uses; bloated instruction files; cache rewrites caused by idle gaps or by hooks injecting text that changes every time; huge tool outputs that are re-sent with history on every later turn; and exploration that rediscovers the same repo facts each session.

We cannot change the agent or the model. The levers left are settings (enabled tools and servers, instruction files), context injected by hooks, and command rewriting in pre-tool hooks. Any lever can backfire: a digest adds prefix tokens to every turn, a pruned tool can cause a failure, and truncated output can hide an error. So the system has to measure rather than assume.

Measurement: transcripts record usage per turn (input, cache creation, cache read, output). Price each turn with the real cache multipliers and attribute cost to prefix, history and tool results. Define a success proxy per session: tests green at the end, a commit made, no user redo or correction, not abandoned. The tool's own model calls, made through the agent's CLI login, go into the same ledger.

Interventions: each one is a snapshotted patch to settings or hook config, and `revert` restores the files byte for byte. Sessions on a repo are randomly assigned on or off for each intervention. An intervention stays only if cost per successful session clearly drops and success does not; otherwise it is reverted automatically. Hooks only add context or rewrite inputs. They never block, and on any internal error they do nothing.

Highest-yield candidates:
- Prefix diet: disable MCP servers or tools unused in this repo over the last N sessions, or switch them to on-demand loading where the harness supports it; flag oversized instruction files.
- Cache stability: find mid-session cache-creation spikes and trace them to volatile hook text or toggled tools.
- Output spillover: full logs go to a file and only failures plus the path enter the context.
- Warm start: a digest of facts that sessions keep rediscovering, checked against file hashes.

### Proposals
P1: Measured reversible-intervention loop — Parses transcripts into a per-turn cost ledger priced with cache-write and cache-read multipliers, including the tool's own calls. Each candidate intervention (disable an unused MCP server, trim an instruction file, add a digest, filter output) is a snapshot-backed patch to settings or hooks. Sessions on a repo are randomly assigned on or off per intervention. An intervention stays only if cost per successful session (tests green, commit made, no user redo) drops with confidence and success holds; otherwise it is reverted byte for byte.
P2: Output spillover hook — A PreToolUse hook rewrites known verbose commands (test runners, builds, installs, large log reads) to tee full output into `.tokeneco/out/<id>.log`. The agent sees only the exit code (preserved), the failing sections, the last N lines and the log path. It can still open the full log, so no information is lost, but passing-test noise stops riding along in history on every later turn. If the wrapper itself errors, the original command runs unmodified.
P3: Prefix and cache hygiene plus warm-start digest — From usage history, list tools and MCP servers this repo never calls and propose disabling them. Find mid-session cache-creation spikes, trace them to volatile hook output or toggled tools, and move that text out of the prefix. Build a compact digest of facts that sessions keep rediscovering (build and test commands, module map), tie each line to file content hashes, and drop lines when they go stale. Inject it at session start only if the A/B test shows net savings.

## transcripto
### Analysis
The closing message is the agent's opinion. The transcript and the working tree are the evidence. The tool should read the evidence deterministically and show only the discrepancies, so the engineer reads one page instead of the whole session.

Step 1, normalize. One adapter per harness (Claude Code JSONL, Codex rollout files, Cursor's stored sessions) maps events into a single schema: user prompt; tool call (kind edit/write/shell/read/other, plus target path or command); tool result (ok or error, exit code, error text); assistant text. Unknown event types are counted and reported rather than silently dropped, so when a harness changes its format, the adapter's blind spots show up.

Step 2, derive facts:
- Failed operations: tool results flagged as errors, non-zero exit codes, and known failure strings (edit target not found, permission denied, command not found, failing tests in the output).
- Resolution: a failure counts as resolved only if a later operation of the same kind on the same target succeeds, such as the same file edited successfully or the same normalized command re-run with exit 0. Unresolved failures are the core signal.
- Staleness: compare the last successful test or build run with the edits made after it. "Tests passed" before the final edits says nothing about the final code.
- Missing outputs: paths named in the task prompt or claimed in the summary that do not exist on disk, or whose mtime is older than the session.
- Disk reconciliation: for each successful edit, check that the new text is still in the file; compare `git status` and the diff with the files claimed as changed.

Step 3, claims. Pull claims out of the final message with fixed patterns (tests pass, build succeeds, created/updated <path>, committed, fixed <thing>) and match each to the evidence as supported, contradicted or unverified.

Output: a short verdict (for example "3 claims unsupported, 2 unresolved failures, edits after last test run"), a table with transcript line references for drilling down, and an exit status for scripts. Optionally the same audit runs at session end through a stop hook, so the agent has to deal with contradictions before the human ever reads the summary.

No extra runtime: ship it as a single static binary, or as a stdlib-only script for a runtime already on the machine. Transcripts are only ever read.

### Proposals
P1: Claim-vs-evidence audit — Per-harness adapters normalize transcripts into tool-call and tool-result events. The auditor finds failed operations (error flags, non-zero exits, known failure strings), pairs each with any later successful retry on the same file or normalized command, and flags the ones never resolved. It pulls claims out of the final message by pattern (tests pass, created X, fixed Y) and labels each supported, contradicted or unverified, with transcript line references. Output is a one-screen verdict plus a drill-down table.
P2: Tested-code and disk reconciliation — Compares the session's history with the current workspace. Edits made after the last passing test or build are flagged "untested final changes". For each successful edit, it checks the inserted text is still in the file. For each path named in the prompt or summary, it checks the file exists and was modified after the session started. It compares `git status` with the files claimed as changed. This catches silently reverted edits, files that were never created and stale green test runs.
P3: Stop-hook self-audit — Where the harness supports stop hooks (Claude Code Stop/SubagentStop), the audit runs before the agent's turn ends. If it finds unresolved failures or contradicted claims, it blocks with a reason listing them, so the agent has to fix or disclose them. Blocking is capped at two (using stop_hook_active) to avoid loops, and the verdict is written next to the transcript for the human. Harnesses without stop hooks get the after-the-fact report from P1.

## unlazy
### Analysis
Two failures compound. The agent loses track of how many required outcomes there are (truncation), and completion is judged by the agent's own narrative (self-report). Subagents repeat both, and the parent accepts their narrative. The fix is to make outcomes explicit, countable and machine-checked, and to make "done" the result of a gate rather than a sentence the agent writes.

1. Outcome contract, written before the work. From the user's request the agent drafts `.unlazy/contract.json`. Each outcome has an id, a description and a check: a shell command with an expected exit code, a grep or AST query that must return zero matches, a file that must exist, or a test that must pass. The user approves it and its hash is recorded. Checks run with ambient access, so approval is also the security boundary: any check changed after approval does not run until it is re-approved.

2. Mechanical denominator. For multi-site work, such as migrating N call sites, the list of sites comes from a query (`rg` for the old API, or a small scanner), not from the agent's memory. Each site becomes an item. The gate re-runs the query, so the tool does the counting. When work fans out, each subagent gets a slice of the items.

3. Completion gate. Claude Code Stop and SubagentStop hooks run `unlazy gate`. If any check fails, the hook blocks with the ids of the failing outcomes and their output. A subagent's gate runs only its own slice's checks, and the parent re-runs them anyway, because "passed in the subagent's context" is still a claim. Where no stop hook exists (Codex skills), the skill requires the final message to include the gate's report, which carries a hash of the contract and results that can be checked later. Blocking is bounded: after K attempts the agent may stop, but the status is written as INCOMPLETE with the list of open outcomes.

4. Anti-gaming. Checks can be satisfied by weakening them. The gate treats these as failures unless the user approves them: added skip or only markers, deleted tests, new type-ignore or lint-disable comments, and edits to files the checks depend on.

Constraints: only Node 16+ built-ins (child_process, fs, crypto). Hooks are installed only through an explicit `unlazy install-hooks`, which shows the settings diff and asks first.

### Proposals
P1: Approved outcome contract with stop gate — Before any work, the agent drafts `.unlazy/contract.json` (outcome id, description, check command and expected result). The user approves it and its hash is stored; a check changed afterwards does not run until re-approved. Claude Code Stop and SubagentStop hooks, installed only with consent, run `unlazy gate`, and any failing outcome blocks stopping with the failing ids and output. After K blocks, stopping is allowed but recorded as INCOMPLETE. In Codex, the skill requires pasting the gate's hashed report.
P2: Query-computed work inventory — For multi-site changes, the contract defines an inventory query (an rg pattern or a small Node regex/AST scanner) that lists every site to migrate. `unlazy items` materializes the list, and `unlazy slice --n 4` splits it for subagents, each slice with its own check. The gate re-runs the query, so the remaining count comes from the code, not the agent's memory. The parent re-verifies every returned slice before merging it.
P3: Anti-gaming diff audit — At gate time, diff against the contract's base commit and fail on signs that checks were weakened: deleted or renamed tests, added `.skip`/`.only`/`xit`, new `@ts-ignore`/`eslint-disable`/`# noqa`, lowered coverage thresholds, and edits to files the checks read (test configs, the contract itself). Each finding needs explicit user approval. Optionally, spawn a fresh-context reviewer subagent that sees only the contract and the diff and must list unmet outcomes.
