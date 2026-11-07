## cc-projects
### Analysis
Two opposite directions: downward (goal -> tasks -> dispatched sessions) and upward (session results -> verified pieces -> integrated goal). The end of the downward pass (tasks running in sessions) is where the upward pass starts, and the end of the upward pass (an integrated result checked against the goal) shows the gaps that start the next downward pass.

Downward pass: the human's coordination costs are splitting, assigning and briefing. A machine can do these if the split produces tasks with disjoint file scopes, explicit dependencies and acceptance commands. Without acceptance commands the upward pass cannot be automated, so the downward pass must produce them.

Upward pass: tracking, checking and stitching. Cloud sessions already open PRs and run tests, so tracking can come from PR and CI state, not from asking sessions. Checking = running the task's acceptance commands on the PR head. Stitching = merging into an integration branch and running the full suite; failures there become new tasks for the next downward pass.

Second loop: the plan itself improves. Tasks that keep failing upward are split smaller or given clearer interfaces downward.

Usage limits: concurrency should be budgeted. Critical-path tasks first; idle sessions cost nothing, retries do.

Stop when the integration branch passes the goal-level acceptance suite and no open tasks remain; the human reviews one final PR plus the plan.

### Proposals
P1: Plan-as-contract orchestrator — A coordinator session writes plan.yaml: tasks with id, owned file globs, dependencies, acceptance commands and a brief. A dispatcher starts one cloud session per ready task on branch task/<id> off an integration branch. A watcher polls PR and CI status, runs acceptance commands on each PR head, merges passing PRs into integration, runs the full suite, and turns failures or unmet goal criteria into new tasks. The human approves the plan and the final PR.
P2: Interface-first wave — Wave 0 is a single session that lands shared types, interface stubs and failing contract tests on the integration branch. Wave 1 sessions implement against those compiled contracts in disjoint scopes, so merges rarely conflict and each piece can be checked alone by its contract tests before stitching.
P3: Budget-aware status board — A script reads each session's PR, CI result and usage, renders one markdown table (task, owner session, state, last check, blocking deps), caps concurrent sessions to a configured budget, and queues lower-priority tasks when usage nears the limit, always serving critical-path tasks first.

## honest-arch-diagrams
### Analysis
Two opposite directions: evidence -> diagram (extract components and edges from sources) and diagram -> evidence (trace every drawn element back to a source line). The output of extraction is a draft diagram; the input of tracing is that draft; tracing removes or downgrades unsupported elements, and the gaps it finds tell extraction where to look next (another source, a trace).

Extraction: deterministic parsers, not the LLM, produce candidate nodes and edges. Ingress host/path rules -> Service -> selector -> Pods -> container env/config naming hostnames -> other Services or terraform resources (RDS, ElastiCache, queues). OpenAPI gives routes; OTel spans give observed calls. Each element gets an evidence reference (file + JSON pointer) and a tier: observed (trace), declared (manifest/terraform), inferred (name or convention), unresolved.

Tracing: a verifier rejects any element without an evidence reference. The LLM may label, group and choose layout, but may only reference element ids the extractor produced. A hostname that resolves to nothing is drawn as an explicit "unresolved: host" stub rather than a guessed Redis.

Secrets: parsers read Secret and env objects only for key names and references; values are dropped at parse time, never kept in memory structures that render.

Stop when every element is traced and no unresolved stub can be resolved by available sources. Honesty is shown in the rendering: tiers styled differently with a legend.

### Proposals
P1: Evidence-graph CLI with provenance gate — Zero-dependency Node CLI parses kubectl JSON, rendered Helm/GitOps manifests, compose, terraform show -json, OpenAPI and OTel exports into a typed graph where every node and edge carries evidence refs and a tier. It emits Mermaid/D2 (solid=observed, normal=declared, dashed=inferred, red stub=unresolved) plus a legend. A verify command fails if any diagram element lacks an evidence ref. The agent skill must call the CLI rather than draw freehand.
P2: Entry-point request-path walker — Starting from each Ingress, LoadBalancer Service or gateway route, walk hop by hop (rule -> Service -> selector -> workload -> referenced hosts/ports -> target), recording each hop's evidence. Stop at the first unresolvable hop and draw it as an explicit gap with the reference text, so request paths are never completed by guessing.
P3: Declared-vs-observed diff with redaction — When OTel traces exist, compare declared edges with observed span edges; mark declared-but-unseen and seen-but-undeclared. All output passes a redaction step: Secret data, env values matching secret key patterns and connection-string credentials are replaced by key names before rendering.

## squadra
### Analysis
Two opposite directions: intent -> execution (decide, assign, deliver) and execution -> intent (receive, test, review, ship, record back). The end of assignment (a window holding a task) starts the evidence pass; the end of the evidence pass (a recorded, verified state) is what the next decision starts from.

Problem: both directions live in chat memory, so nothing is checkable. Fix: an append-only ledger on disk, outside any one window, that both directions write to.

Intent -> execution: decision and assignment events in the ledger; delivery via per-window mailbox files. Receipt must be proven, not assumed: the assignment carries a token, and the tool checks the window's transcript on disk for that token (a Claude hook can also write an ack on prompt submit). Codex cannot wake Claude windows, so it only writes to mailboxes; delivery happens on the recipient's next prompt via hook, and the ledger shows "delivered, not yet acked".

Execution -> intent: tests, reviews and ship events record commit SHA and tree hash. A gate checks reviewed tree == tested tree == shipped tree. Self-review is not counted: reviewer session id must differ from author session id and preferably be a different harness.

Context reset: a brief command rebuilds the current state (owners, open tasks, unacked assignments, last decisions) from the ledger for a new window.

Nothing auto-published; Cursor never launched; stdlib Python only.

### Proposals
P1: Append-only ledger with hash-bound gates — Python stdlib CLI writes JSONL events (decision, assign, ack, test, review, ship) under the repo's git common dir so all checkouts share it. Test/review/ship events store commit SHA and tree hash; a check command fails unless shipped tree equals reviewed and tested tree and reviewer identity differs from author. A brief command prints current state for a fresh window.
P2: Mailbox with transcript-verified receipt — Each window has a mailbox file. Assignments include a unique token. A Claude SessionStart/UserPromptSubmit hook injects pending messages and logs an ack; for Codex and Cursor, the tool scans their transcript files for the token and marks the assignment received only when found.
P3: Cross-agent review requests — A review command packages a diff by tree hash and writes it to another harness's mailbox with a checklist; the verdict is accepted only if it references the same tree hash, so stale or self-reviews cannot satisfy the gate.

## termaxa
### Analysis
Two opposite directions: command -> consequence (what would this command actually remove, given current state) and consequence -> command (starting from the assets at risk, what is the gentlest command that does the same chore). The output of the first is a loss estimate; that estimate is the input to the second, which produces a safer suggestion; the agent's retried command then re-enters the first direction.

Command -> consequence must use real state, not just pattern matching, otherwise it either blocks everything (defeating the agent) or nothing. Examples: reset --hard on a clean tree loses nothing; on a dirty tree it loses edits. A force push loses remote commits only if the remote tip is not an ancestor of the local branch. Deleting a gitignored build directory is cheap; deleting a directory containing modified tracked or untracked non-ignored files is not. Dropping a table with rows is a loss; for psql/terraform/kubectl, state queries may be costly, so policy can fall back to "require snapshot".

Consequence -> command: suggest the safer spelling the agent can run unattended: stash before reset, --force-with-lease, revert instead of reset for pushed commits, move to a trash directory, plan before apply, dump before drop.

Unattended operation means a deny must return a reason and a concrete alternative so the agent can continue. Hooks advise and are not a sandbox, so add recovery: snapshots before allowed risky actions.

Policy lives in the repo as a readable file with tests.

### Proposals
P1: State-aware loss check with suggested alternative — Single binary used as PreToolUse/hook handler tokenizes the shell command, matches rules, then queries state (git status, merge-base of remote tip vs local, ignored/untracked status of rm targets, row counts if configured). If real loss is predicted, it denies with the reason and a safer equivalent command; if nothing would be lost, it allows silently, keeping approvals rare.
P2: Snapshot-before-allow — For risky commands the policy allows, first create a recovery point: git stash create stored under refs/termaxa/<time>, a backup ref of the remote tip before a lease-protected force push, files moved to a trash directory instead of deleted, a configured dump before DROP. Each snapshot is logged with its restore command.
P3: Repo policy file and decision log — A .termaxa policy file lists rules (match, state condition, action: allow/deny/snapshot, suggestion) with inline test cases run by a test subcommand in CI. Every decision is appended to a JSONL log, and an explain subcommand shows which rule fired and why.

## tokeneconomizer
### Analysis
Two opposite directions: cost -> cause (attribute spend in transcripts to its sources) and cause -> cost (apply a reversible change to a source and measure the cost and success effect). Attribution produces a ranked list of causes; that list selects the next intervention; the measured result returns to attribution as new transcripts.

Cost -> cause: transcripts include usage with cache read/write/input/output tokens. Split per turn into stable prefix (instructions, tool definitions), history, tool outputs, and cache misses (prefix changed, TTL expired between turns). Also per-repo patterns: repeated exploratory reads of the same files across sessions.

Cause -> cost: interventions must be reversible and must never stop a turn. Candidates: remove tool definitions for MCP servers never used in this repo; shorten instruction files; keep the prefix stable to protect cache; a compact repo digest injected at session start so sessions do not rediscover structure; truncate huge tool outputs via hooks with a pointer to the full file; suggest a fresh session or compaction when history dominates. Model cannot be changed.

Success guard: compare task outcomes before and after (tests pass at end, no immediate user correction, no re-run of same task). Count the tool's own calls (digest generation via the agent's login) with cache pricing. Roll back an intervention automatically if cost per successful task does not drop.

### Proposals
P1: Attribution ledger with reversible experiments — Parse transcripts into per-turn cost by component using cache pricing. Rank causes per repo. Apply one intervention at a time as a settings patch with stored backup; tag sessions as before/after; compare cost per successful task (tests green, no correction prompt), including the tool's own calls. Keep the patch only if cost drops and success holds; otherwise restore the backup automatically.
P2: Repo digest at session start — Generate a compact digest (layout, build/test commands, key modules, conventions) from the repo, regenerated only when relevant files change, and inject it via SessionStart hook. Measure drop in exploratory read/search calls per session; drop the digest if it does not pay for its own tokens.
P3: Tool-surface pruning with auto-restore — From transcripts, count per-repo usage of each MCP server and tool. Disable unused ones in project settings with a backup. A hook watching for missing-tool errors or explicit requests re-enables them and logs the event, so pruning never blocks work.

## transcripto
### Analysis
Two opposite directions: claims -> evidence (take each statement in the closing message and look for tool results that support it) and evidence -> claims (take every failure in the session and check whether the closing message admits it). The first ends with a list of supported and unsupported claims; the second starts from the raw events those claims did not cover and ends with failures that need new claims or caveats.

Normalize transcripts from each harness into one event model: tool call, arguments, result, error flag, exit code, file path, timestamp. Adapters per harness; plain stdlib or a single binary.

Claims -> evidence: extract claims from the closing message with simple patterns (file names, "tests pass", "created", "updated"). Match to events: a successful write/edit to that file, a test command whose last run after the last edit exited zero.

Evidence -> claims: list failed edits (string-not-found), non-zero exits, errors never followed by a successful retry, tests not re-run after later edits, and files mentioned but never written. Flag those not mentioned in the summary.

Ground truth check: compare with git diff of the working tree so claimed edits that do not exist on disk show up.

Output: a short report readable in under a minute, each item linked to the transcript line.

### Proposals
P1: Claim-evidence reconciler — Local CLI with per-harness adapters normalizes transcripts into events. It extracts claims from the final message, marks each supported, contradicted or unverified by matching events, then lists failures the summary never mentions (errored edits, non-zero exits without successful retry, tests not re-run after the last edit), each with a transcript line reference.
P2: Final-state verifier — For every file touched, compute final status (last edit succeeded or failed) and compare with git diff; for every test/build command, report the result of its last run after the last edit. Produces a one-screen table showing what is actually on disk and actually passing.
P3: End-of-session hook — Register the reconciler as a Stop/session-end hook where the harness supports it, so the report is written next to the transcript and printed under the agent's closing message; for other harnesses, a watch command processes new transcript files as they finish.

## unlazy
### Analysis
Two opposite directions: requirements -> work (enumerate outcomes, fan out to agents) and work -> requirements (verify each outcome independently of anyone's report). The output of fan-out is work claimed done; that is the input of verification, whose unmet items become the next fan-out.

Root cause: "done" is self-reported, and the parent accepts subagent reports on their word. So the requirements must exist as checkable predicates before work starts, and verification must run those predicates, not read summaries.

Requirements -> work: at task start, write a contract file of outcomes, each with a shell check (grep that old API has zero call sites, a file exists, a test target passes, a count matches an inventory). For migrations, generate an inventory of all sites up front so partial completion is visible as a number.

Work -> requirements: a Stop hook runs the contract; if any check fails, it blocks the stop and returns the unmet list, so the agent continues instead of reporting done. For subagents, the parent runs the subset of checks for that subagent's assignment before accepting.

Ambient access: checks run unsandboxed, so the user approves the contract once; the hook runs only checks whose hash matches the approved contract. Hooks installed only after consent. Node 16 without dependencies.

Stop when all checks pass, or when the agent explicitly reports specific items as blocked with reasons, which the user sees.

### Proposals
P1: Outcome contract with stop gate — A skill makes the agent write .unlazy/contract.json listing required outcomes, each with a shell check. The user approves it; its hash is stored. A consented Stop hook (Node 16, no deps) runs the approved checks and, if any fail, blocks completion and returns the failing items, so the agent cannot report done until checks pass or items are explicitly marked blocked with a reason.
P2: Parent-side subagent acceptance — Each subagent receives its slice of contract ids. When it returns, the parent runs only those checks and accepts the slice only if they pass; failing ids are re-dispatched to a fresh-context subagent with the failure output. Subagent prose is never used as evidence.
P3: Inventory counters for fan-out work — At start, generate an explicit inventory (every call site, migration path or file to change) by search and store it. Progress is computed by re-running the search, shown as remaining/total, and the stop gate requires remaining to reach zero or each leftover to be listed with a reason.
