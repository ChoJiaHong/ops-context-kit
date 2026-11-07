# Judge packet (dev)

## cc-projects

Problem: A developer runs several Claude Code sessions in parallel on one larger goal. They have to split the goal into tasks by hand, decide which session gets what, keep track of each session's progress, check each result, and stitch the pieces back together. Most of their time goes into coordination rather than the work.

Core mechanism of the real tool:
- M1: A coordinator agent (one conversation) decomposes the goal and dispatches tasks to separate full sessions running in parallel, instead of the human assigning them.
- M2: Each parallel thread gets its own branch / copy of the repository, and the coordinator checks the threads' results and integrates them back.

Score 2 (full match): Proposal contains M1 and M2: an agent coordinator that splits work across independent parallel sessions with isolated branches/workspaces, then verifies and merges results.

Score 1 (partial match): Coordinator that dispatches tasks but no per-thread isolation or result checking; or isolated worktrees per session with human still assigning tasks.

Score 0 (not a match), including: A dashboard listing sessions; better task templates for the human; running subagents within a single session context

### S1

P1: Plan-file orchestrator — An orchestrator session writes plan.yaml: one entry per task, with id, dependencies, owned paths, acceptance commands and branch name. The human approves it once. A dispatcher starts a cloud session for each ready task with a generated prompt telling it to open a PR to the integration branch, labelled with its task id. A poller uses gh to read PR/CI state into a status table. When dependencies merge, it starts the next tasks.
P2: Contract-first plus verifier sessions — Phase one lands interfaces, stubs and failing acceptance tests on the integration branch. Workers implement against them. Each PR starts a fresh verifier session. It runs that task's acceptance commands, checks that the diff stays inside the task's owned paths, and posts an approve or reject review. Only approved PRs go into the merge queue, so the human doesn't check each result by hand.
P3: Budget-aware scheduling — The dispatcher records the usage of each session it runs and sets a cap on concurrent sessions. It ranks ready tasks by critical-path length. As the subscription limit gets close, it holds new low-priority tasks back and posts a short digest of what is done, running, blocked and deferred.

### S2

P1: Plan-DAG orchestrator — A planner session writes `.project/plan.yaml`: tasks with id, brief, owned paths, depends_on, interface contracts and acceptance commands. After one human approval, a dispatcher launches a cloud session per ready task on a branch from an integration branch. It tracks each task through ready/running/PR/verifying/merged/escalated using session status and PR events, and shows everything on one dashboard. A worker can return "needs-split" to trigger replanning instead of improvising outside its scope.
P2: Independent verify-and-merge queue — A fresh verifier session or CI job checks each PR: it runs the task's acceptance commands on the PR head, rejects diffs that touch paths outside the task's scope, and reviews against the spec. Failures go back to the worker with the exact output (at most N retries, then escalate). Verified PRs merge into the integration branch in dependency order, and dependent tasks launch only after that. The final PR carries a generated task→commit→evidence table.
P3: Contract-first, budget-aware scheduling — Task zero lands shared types, interfaces and stubs, so parallel tasks code against fixed contracts. The scheduler caps concurrency, orders tasks by critical-path length and logs usage per task from session metadata. It stops launching new work once projected usage would exceed the remaining subscription allowance, lets in-flight tasks finish and resumes after the reset. A task that uses more than twice its estimate is paused for replanning.

### S3

P1: Plan-as-code dispatcher — A planner session turns the goal into plan.yaml. Each task has an id, owned paths, dependencies, an acceptance command, and interface stubs committed first. The human approves the plan once. A small dispatcher starts one cloud session per ready task from a template (spec, owned paths, acceptance command, branch name task/<id>). Each session must open a PR tagged with the task id. Progress is read from branches, PRs and CI, never from chat.
P2: Independent verifier plus merge train — For each PR, a fresh session that did not write it checks four things: only owned paths changed, the acceptance command passes, no tests were deleted or weakened, and the diff matches the spec. Passing PRs merge in dependency order into an integration branch, with the full test suite run after each merge. If a merge fails the suite, it is reverted automatically and the task is requeued with the failure log added.
P3: Budget-aware status board — A script polls GitHub for task/<id> branches, PRs and check results. It renders a table with each task's state (queued, running, PR open, verified, merged, failed), its blocker and its last activity. The dispatcher starts a task only when its dependencies have merged, and caps concurrent sessions at a limit set in plan.yaml from the subscription quota.

### S4

P1: Plan ledger with reconciler — A planner session writes plan.json in the repo: goal acceptance tests, and per task its owned paths, acceptance command, dependencies and interface files. A dispatcher starts one cloud session per ready task on branch task/<id>. A reconciler polls PRs: it runs acceptance, rejects diffs outside owned paths, merges green PRs into an integration branch in dependency order, runs the goal tests, and turns each failure into a new task. The human sees only exceptions.
P2: Contract-first skeleton PR — Before fan-out, one session commits interfaces, types, stub functions and one failing test per task, and this PR merges first. Each parallel session's only job is to turn its own tests green without editing the shared interface files; a CI path check enforces that. Mismatches between pieces then show up as compile or test failures in CI, not during manual stitching.
P3: Budget-aware scheduler and exception board — Record tokens and retries for each finished task from session usage, and estimate pending tasks' cost by size class. Launch sessions in critical-path order only while projected usage stays inside the subscription window. One status page built from plan.json plus PR and CI states shows each task as ready, running, blocked or needs-human. The developer reviews only the needs-human items.

### S5

P1: Plan-as-contract orchestrator — A coordinator session writes plan.yaml: tasks with id, owned file globs, dependencies, acceptance commands and a brief. A dispatcher starts one cloud session per ready task on branch task/<id> off an integration branch. A watcher polls PR and CI status, runs acceptance commands on each PR head, merges passing PRs into integration, runs the full suite, and turns failures or unmet goal criteria into new tasks. The human approves the plan and the final PR.
P2: Interface-first wave — Wave 0 is a single session that lands shared types, interface stubs and failing contract tests on the integration branch. Wave 1 sessions implement against those compiled contracts in disjoint scopes, so merges rarely conflict and each piece can be checked alone by its contract tests before stitching.
P3: Budget-aware status board — A script reads each session's PR, CI result and usage, renders one markdown table (task, owner session, state, last check, blocking deps), caps concurrent sessions to a configured budget, and queues lower-priority tasks when usage nears the limit, always serving critical-path tasks first.

### S6

P1: Task-graph orchestrator with independent verification — A planner session writes `.plan/graph.yaml`: tasks with goal, owned paths, dependencies and acceptance commands. After human approval, a deterministic loop launches a cloud session per ready task on its own branch and polls status files the sessions must update. On each PR it runs the acceptance commands in CI plus a fresh reviewer session that compares the diff to the spec. Passing PRs merge into an integration branch in dependency order. Failures are re-dispatched with the failure log, and only exceptions reach the human.
P2: Contract-first scaffold before fan-out — Before parallel work starts, one session lands a scaffold PR: shared interfaces, type signatures, stub modules, fixtures, failing tests for each task's acceptance criteria, and a path-ownership map that assigns each path to one task. Parallel sessions implement against these frozen interfaces and may only touch their own paths; a CI check rejects out-of-scope diffs. Interface changes need a separate small PR, which the orchestrator rebases dependent tasks onto. Integration becomes "all tests green" instead of manual stitching.
P3: Quota-aware scheduler with resumable checkpoints — The orchestrator estimates each task's cost from history (usage per task size for similar past tasks) and tracks usage consumed against the subscription window, from session usage reports and limit warnings. It caps concurrency so the critical path finishes within the window and runs low-priority tasks only with spare quota. Sessions must commit a `progress.md` checkpoint (done, next, open questions) at each milestone, so a session stopped by a limit can be resumed from its branch by a fresh one.

## honest-arch-diagrams

Problem: Ask an LLM to 'diagram this service' and it draws a Redis, a TLS hop and an auth gateway it never saw. A confident wrong architecture diagram is worse than none. I want agents to produce request-path diagrams of services in our Kubernetes/GitOps/Terraform estate that I can actually trust.

Core mechanism of the real tool:
- M1: An intermediate renderer-agnostic model in which every hop must carry evidence (a concrete source object such as Ingress/Service/Endpoints), derived by deterministic adapters from real sources (traces > live k8s > declared manifests > OpenAPI, with evidence strength recorded) instead of the LLM's recall.
- M2: A linter gate before rendering that rejects any hop without evidence ('omitted means absent, not guessed'), with a separate visually distinct tier for inferred companions (dashed, evidence on the edge) that may never sit on the verified path.

Score 2 (full match): Proposal contains M1 and M2 (evidence-carrying model built from real infra sources AND a validation gate that refuses unevidenced hops).

Score 1 (partial match): Proposal generates diagrams deterministically from manifests/traces without an evidence-required gate, or asks the LLM to cite sources without mechanical rejection.

Score 0 (not a match), including: better prompting of the LLM; LLM self-check of its diagram; prettier rendering (D2/Mermaid); service-mesh auto-generated topology UI alone

### S1

P1: Provenance graph + verifier CLI — `archmap extract <sources>` (zero-dependency Node) builds graph.json, where each node and edge carries evidence entries {file, JSON pointer, class: observed|declared|inferred}. `archmap render` emits Mermaid with solid/dashed/dotted edges by class, explicit "unknown" hops and an evidence footnote table. `archmap verify diagram.mmd` fails on any element without an evidence ID. The skill tells agents to run these commands and never to add nodes by hand.
P2: Declared-vs-observed reconciliation — Join manifest edges with OTel trace edges, keyed by a normalized service identity (k8s Service DNS, service.name, server.address). Output three sets: confirmed (in both), declared-only and observed-only. Each set gets its own style in the diagram and is listed as questions for the human. An observed-only edge produces a request naming which source is missing, never an invented explanation.
P3: Fail-closed secret hygiene — An allowlist of fields per resource kind. Secret resources are read for metadata.name only. Env and ConfigMap values go through a URL parser that keeps scheme, host and port; userinfo, query strings, and any value matching key/token patterns or showing high entropy are replaced with a hash. A final scan over the output aborts the write if any secret-like string survives.

### S2

P1: Evidence graph IR with provenance — The CLI parses each source. Kubernetes: Ingress to Service to selector to Deployment. Helm and compose: links. Terraform JSON: load balancer, listener, target. OpenAPI: routes. OTel: span parent and peer.service. It emits nodes and edges, each carrying the source file, a JSON pointer and its evidence tier. Mermaid is rendered only from this IR. Line style shows the tier, and references that don't resolve become "?" nodes.
P2: Diagram claim verifier — The skill tells agents to generate diagrams through the CLI. If an agent edits one, `verify` parses the Mermaid and matches every node and edge to an IR element id. It fails with a list of unsupported elements, for example a cache with no evidence. The agent must remove each one, or mark it "assumed" with the user's confirmation, which shows as dashed and labelled.
P3: Allowlist extraction with a fail-closed scan — Parsers copy only structural fields: kind, name, namespace, ports, hostnames, selectors and env var names. Secret data, env values and credentials in URLs are replaced by the variable name and "redacted". Before anything is written, the output is scanned for credential patterns and high-entropy strings. Any hit aborts the write.

### S3

P1: Evidence-graph CLI with provenance gate — Zero-dependency Node CLI parses kubectl JSON, rendered Helm/GitOps manifests, compose, terraform show -json, OpenAPI and OTel exports into a typed graph where every node and edge carries evidence refs and a tier. It emits Mermaid/D2 (solid=observed, normal=declared, dashed=inferred, red stub=unresolved) plus a legend. A verify command fails if any diagram element lacks an evidence ref. The agent skill must call the CLI rather than draw freehand.
P2: Entry-point request-path walker — Starting from each Ingress, LoadBalancer Service or gateway route, walk hop by hop (rule -> Service -> selector -> workload -> referenced hosts/ports -> target), recording each hop's evidence. Stop at the first unresolvable hop and draw it as an explicit gap with the reference text, so request paths are never completed by guessing.
P3: Declared-vs-observed diff with redaction — When OTel traces exist, compare declared edges with observed span edges; mark declared-but-unseen and seen-but-undeclared. All output passes a redaction step: Secret data, env values matching secret key patterns and connection-string credentials are replaced by key names before rendering.

### S4

P1: Evidence-cited fact graph — The Node CLI has one parser per source. Each parser emits nodes and edges carrying evidence {file, JSON pointer, source kind}. Edges come only from resolvable links: Ingress to Service, selector to Deployment, env value to Service DNS name, terraform reference, compose link, cross-service trace span. The renderer emits Mermaid with numbered evidence footnotes. With no evidence, nothing is drawn. The skill tells the agent to run the CLI and only add prose.
P2: Confidence tiers and explicit gaps — Every edge gets a tier: observed (trace spans), declared (manifests or terraform), or inferred (naming heuristics). Tiers render as solid, dashed and dotted lines with a legend. Hosts that resolve to nothing become "unresolved: <host>" boxes rather than guessed Redis or gateway nodes. A section under the diagram lists edges seen in traces but not declared, and edges declared but never observed.
P3: Verify gate with secret hygiene — `verify diagram.mmd` parses any diagram an agent wrote and checks each node and edge against the fact graph. It exits non-zero and lists unsupported elements, and the skill requires a pass before the diagram is shown. Secret objects are read only for names and keys. URLs lose their userinfo, and values are dropped unless they parse as host:port. A final pass masks high-entropy strings.

### S5

P1: Evidence-graph extractor with provenance-tagged rendering — `archmap build` parses kubectl JSON, rendered manifests, compose, `terraform show -json`, OpenAPI and OTel traces into nodes and edges. Each carries evidence IDs (file plus JSON pointer, or span ID) and a tier: observed, declared or inferred. `archmap render --from <entrypoint>` walks the request path and emits Mermaid with solid, dashed or dotted lines per tier, evidence footnotes and explicit "unresolved: host X" nodes. Nothing without evidence is emitted, and secret values and URL credentials are never read.
P2: Diagram verify gate in the skill — The skill tells agents to produce diagrams only through the CLI. If they edit or hand-write one, they must run `archmap verify diagram.mmd`. Verify parses the Mermaid, maps each node and edge to the evidence graph by ID or name, and fails with a list of every element that has no evidence or an overstated tier (for example a dashed edge drawn solid). The skill forbids presenting a diagram that has not passed verify and requires quoting its summary line.
P3: Observed-vs-declared reconciliation — When OTel traces are supplied, `archmap diff` joins client/server spans (peer.service, server.address, k8s.* resource attributes) to declared edges. It reports three sets: confirmed, declared but never observed in the trace window, and observed but undeclared (for example egress to an external host missing from the manifests). Edges are coloured accordingly. The report states the trace window and sample size, so a lack of traffic is not presented as proof that an edge does not exist.

### S6

P1: Evidence graph CLI — `archgraph extract` reads kubectl JSON, rendered Helm, compose, terraform show -json, OpenAPI and OTLP JSON traces. It writes graph.json, where each node and edge has an evidence list [{file, jsonPointer/line}] and a tier (observed, declared or inferred). It joins Ingress→Service via backend refs, Service→workload via selector, and workload→dependency via env/ConfigMap hostnames matched to Services or terraform endpoints. Secret data, sensitive_values and credential substrings are dropped while parsing. `render` outputs Mermaid, an evidence table and an explicit gaps list.
P2: Grounding checker for agent-drawn diagrams — `archgraph verify diagram.mmd --graph graph.json` parses Mermaid or D2 and requires every node and edge to carry an id that exists in graph.json. It fails with a list of ungrounded elements and of attribute claims (TLS, auth, cache) that have no evidence. The skill makes agents run verify before presenting any diagram and draw unknowns as dashed "unverified" boxes. CI runs it on committed docs, so diagrams fail visibly when manifests change.
P3: Declared-vs-observed reconciliation — Merges edges from traces with edges from config and draws each tier differently: solid if observed in traces within the window, dashed if declared but never observed, red if observed but undeclared. Attributes like TLS appear only with proof (Ingress tls, a listener certificate, mesh PeerAuthentication STRICT); otherwise they are labeled "unknown". A drift report surfaces both stale config and undocumented dependencies, so the agent cannot quietly paper over either.

## squadra

Problem: I run several agent windows (Claude Code, Codex, Cursor) on one project at once. Coordination lives in chat memory: who owns which task, whether a window actually received its assignment, which code was really tested, whether the code that got reviewed is the code that shipped, and what I decided and when. Agents reviewing their own work say it is fine, and a context reset or new window loses all of it.

Core mechanism of the real tool:
- M1: One shared local registry (SQLite, hash-chained append-only events) that every window reads/writes through a CLI: tasks with owner and reviewer, messages requiring explicit ACK before work starts, recorded owner decisions with verbatim words, checkpoints for context handover.
- M2: Proof and review bound to the exact code: the builder runs the agreed check (exact argv) on a frozen candidate whose source fingerprint is recorded; any change after proof invalidates proof and review; review must be by a non-author window, by default of the other model (Claude writes/Codex reads), before the coordinator can close.
- M3: For defect-fix tasks, closure requires showing the same test bytes fail on the base and pass on the candidate.

Score 2 (full match): Proposal contains M1 and M2 (shared durable registry across sessions AND fingerprint-bound proof with mandatory non-author, preferably cross-model, review).

Score 1 (partial match): Proposal has a shared task board/registry across sessions without binding proof to exact code, or cross-agent review without a shared durable record.

Score 0 (not a match), including: one orchestrator agent spawning subagents in a single session; Jira/kanban board; chat-based handoff notes; agent self-review

### S1

P1: Hash-bound ledger and ship gate — A Python-stdlib CLI appends hash-chained JSONL events (claim, assign, ack, test, review, decide) to `~/.squadra/<root-commit>/` under fcntl locks. `squadra run -- cmd` records the tree hash of the working state (via a temp index that includes untracked files), the command and the exit code. Reviews record a verdict against a tree hash, and the reviewer identity (harness+session) must differ from the author's. `squadra gate <commit>` passes only if that exact tree has a passing test and a non-author approval. It reports and never pushes.
P2: Pull inbox with verified delivery — Each assignment carries a nonce and waits in a per-window inbox. Claude Code hooks (SessionStart/UserPromptSubmit) inject pending items, and Codex/Cursor rules tell the agent to run `squadra inbox` at the start of each turn. Delivery is confirmed two ways: an explicit `ack`, and a scan of on-disk transcripts (Claude JSONL, Codex sessions, Cursor's SQLite store via stdlib sqlite3) for the nonce. Anything unconfirmed after a timeout is flagged "not delivered" with a ready-to-paste prompt for the human.
P3: Leases plus reset-proof briefs — `claim` takes a task and path globs and refuses any overlap with live leases. Liveness comes from the owner's transcript mtime, so abandoned work frees itself. `decide "text" --supersedes <id>` timestamps decisions. `squadra brief --me` rebuilds a compact state from the ledger: my leases, pending assignments, reviews I owe, and decisions since my last ack. Claude Code injects it on SessionStart and other windows print it manually, so a new window resumes from the ledger instead of from memory.

### S2

P1: Hash-bound receipt ledger — Each checkout keeps an append-only `.squadra/events.jsonl`, and `squadra` merges them by timestamp into tasks, owners and decisions. `squadra run -- <test cmd>` records the exit code and a tree ID of the exact working state (temporary index plus `git write-tree`). Reviews record the tree ID they examined. `squadra ship-check` fails, printing the problem and never pushing, when the tree to be shipped differs from the last passing test and approved review, and shows the diff between them.
P2: Nonce handshake verified from transcripts — Assignments go into the target agent's inbox with a nonce. Claude Code hooks inject inbox items at session start and on each prompt; Codex is told in AGENTS.md to run `squadra inbox`; Cursor gets a paste-ready prompt. squadra scans each agent's transcript files for the nonce to mark the assignment "delivered". It marks it "accepted" only after an ack event containing the nonce and the agent's current HEAD. Unacknowledged assignments surface in `squadra status` after a timeout.
P3: Cross-agent review packets and reset briefs — `squadra review-request` builds a packet (task spec, diff at a tree ID, test receipts) that can be assigned only to an agent other than the author, preferably from another vendor. The verdict must cite file:line and is bound to that tree ID, so self-approval is rejected. `squadra brief <agent>` regenerates a context-restoration prompt from the ledger: role, owned tasks, open messages, timestamped decisions and latest receipts. A SessionStart hook injects it, or the human pastes it after a reset.

### S3

P1: Hash-bound evidence ledger — A stdlib CLI appends JSONL under `git rev-parse --git-common-dir`/squadra. `squadra test -- cmd` records the tree hash (plus a digest of any uncommitted changes), the exit code and a log digest. `squadra review` records the reviewer's session and the reviewed hash, and rejects authors reviewing their own work. `squadra ship-check` fails unless the exact tree being shipped has a passing test and an independent review.
P2: Acknowledged assignments — `squadra assign` records owner, scope paths and acceptance criteria. Session hooks (Claude SessionStart/UserPromptSubmit; an instruction in Codex and Cursor to run `squadra inbox`) show pending work. `squadra ack` records the session id and transcript path. If an assignment isn't acknowledged within N minutes, `squadra status` shows it as "not received", so the human relays it by hand, for example to Cursor.
P3: Decision log and resume briefing — `squadra decide` records a timestamped decision with its author and rationale. `squadra brief --for <window>` rebuilds from the ledger that window's owned tasks, latest test and review evidence, open items and recent decisions. It runs at session start, so a reset or new window starts from recorded facts instead of from what the chat remembers.

### S4

P1: Hash-bound event ledger — A stdlib Python CLI that writes append-only JSONL under ~/.squadra/<root-commit>/ with fcntl locks. Commands: assign; ack; test -- <cmd> (runs the command, records exit code and the tree hash from `git stash create` or HEAD); review (records the reviewed hash and reviewer session, rejected if the reviewer is the author); decide; ship-check (verifies the shipped commit's tree matches a tested and independently reviewed tree, otherwise lists the gap).
P2: Pull inbox with acks — Each window has an identity file in its checkout. Claude Code SessionStart/UserPromptSubmit hooks run `squadra inbox`, and AGENTS.md or Cursor-rule instructions tell the other agents to run it. It prints pending assignments and the window's current brief. An assignment stays "sent" until acked. `squadra status` flags unacked assignments after a timeout and prints a ready-to-paste prompt for manual delivery to Cursor or Codex.
P3: Transcript cross-check — Parsers for Claude JSONL, Codex rollouts and Cursor logs extract executed commands, exit codes and file edits with timestamps. For every "tested" or "done" event, verify that a matching command ran and succeeded after the last edit in that checkout. Mismatches are recorded in the ledger as disputed events and shown in status.

### S5

P1: Append-only ledger with hash-bound gates — Python stdlib CLI writes JSONL events (decision, assign, ack, test, review, ship) under the repo's git common dir so all checkouts share it. Test/review/ship events store commit SHA and tree hash; a check command fails unless shipped tree equals reviewed and tested tree and reviewer identity differs from author. A brief command prints current state for a fresh window.
P2: Mailbox with transcript-verified receipt — Each window has a mailbox file. Assignments include a unique token. A Claude SessionStart/UserPromptSubmit hook injects pending messages and logs an ack; for Codex and Cursor, the tool scans their transcript files for the token and marks the assignment received only when found.
P3: Cross-agent review requests — A review command packages a diff by tree hash and writes it to another harness's mailbox with a checklist; the verdict is accepted only if it references the same tree hash, so stale or self-reviews cannot satisfy the gate.

### S6

P1: Content-bound event ledger — A Python stdlib CLI appends JSONL events to a ledger in the git common dir, shared by every checkout. Event types: task created, claimed (agent, checkout, lease), assigned, acked, tested (command, exit code, tree hash including uncommitted changes), reviewed (tree hash, reviewer), decided (text, time). `status` folds the events into current state. `brief <agent>` prints that agent's tasks and the recent decisions, so a new window recovers.
P2: Inbox with transcript-verified receipt — Each assignment goes to a per-agent inbox with a nonce. Instruction snippets tell agents to run `squadra inbox` at turn start and `squadra ack <nonce>`. For unacked items, the tool scans that harness's transcript files for the nonce and reports "not seen", "seen, not acked" or "acked". Status lists stale assignments so the human can prompt that window by hand. Nothing is launched or woken automatically.
P3: Ship gate on identical trees — `squadra check-ship <task>` passes only if three things hold: the latest passing test event's tree hash equals the branch HEAD tree, a review event exists for that same hash from a different harness or session than the author, and nothing changed after the review. Otherwise it lists exactly what is missing. It never pushes or publishes; it prints the command for the human.

## tokeneconomizer

Problem: Developers run the same coding agents on the same repositories again and again, and the bill is high. Every turn pays again for the agent's instructions, every loaded tool definition and the conversation so far, and each session behaves as if it had never seen the repository before. We want sessions to get cheaper without hurting task success.

Core mechanism of the real tool:
- M1: Micro-skills: learn repo facts across sessions from failures that repeat across sessions (and a periodic model review of recent sessions), inject a fact at session start only after it is confirmed in 3 sessions, and drop it when later sessions contradict it.
- M2: Tool pruning: tools unused over p prompts spanning >= m sessions are removed via the agent's own settings deny list, written only after the repo has been idle (cache already expired), with one-command restore.
- M3: Loop guard: learn a per-repo envelope of normal turn length from turns that ended well; when a turn repeats failures, a judge model decides if it is stuck and injects at most one redirect note, then only tells the human how to stop.

Score 2 (full match): Proposal contains at least two of M1-M3, each driven by evidence accumulated across prior sessions in the same repo.

Score 1 (partial match): Proposal contains one of M1-M3, or all three as static rules without cross-session learning.

Score 0 (not a match), including: context compaction/summarization; routing to a cheaper model; a hand-written CLAUDE.md; prompt caching tweaks only; hard token budgets that stop the agent

### S1

P1: Measured, reversible intervention loop — A transcript analyzer prices every turn at cache-write, cache-read and uncached rates. It attributes tokens to prefix components, tool outputs and cache breaks, and scores sessions with success proxies. Each intervention is a recorded settings or file diff with a backup and `undo`, and a per-session coin flip decides whether it applies. After enough sessions the tool compares cost per successful session, including its own calls. It keeps the winners and automatically reverts interventions that cost more or lower success.
P2: Prefix diet driven by usage — From transcripts, compute for each MCP server and tool the schema tokens paid per turn versus the times it was actually invoked in this repo, and disable unused servers at project scope. Split instruction files into sections, track which sections' topics actually come up in tasks, and move rarely relevant ones into on-demand skills or docs referenced by one-line pointers. Move dynamic hook output out of the cached prefix. Every change runs as a P1 intervention, so any drop in success reverts it.
P3: Warm-start repo brief and output offloading — After each session, deterministically extract from the transcript the commands that worked, the files read per task type and the failures hit. Distill them into a capped, stable `repo-brief.md` that is injected at session start, so the agent spends fewer turns exploring. A PreToolUse hook rewrites known verbose commands (test, build, install) to tee full output into a file. The agent sees the exit status, failure blocks, the tail and the file path.

### S2

P1: Attribution ledger plus reversible A/B — Parse per-turn usage from transcripts, price it at cache rates, and attribute it to prefix, cache misses, history and tool results by tool. Generate candidate changes (disable MCP servers unused in N sessions, move unreferenced instruction sections into on-demand files) as journaled patches to settings files. Alternate patched and unpatched configs across sessions. Keep a patch only if cost per successful session drops and success holds; otherwise revert it automatically.
P2: Cache-break detector — Across consecutive turns, flag cache-write spikes that new history does not explain. Compare prefix hashes where available, and correlate spikes with hooks or instruction files that inject volatile text (dates, git status, random IDs) and with idle gaps longer than the cache TTL. Report the source and apply a stable rewrite as a reversible patch, e.g. move volatile text into the user turn, sort lists deterministically.
P3: Commit-keyed repo brief — A SessionStart hook injects a short, byte-stable brief (layout, build/test commands, entry points, conventions). The agent's own CLI generates it once per significant commit range, and that cost is booked. Exploration tokens (Read/Grep/Glob results in early turns) are measured with and without the brief. Where the brief does not pay for its per-turn cost, the hook disables itself.

### S3

P1: Measured reversible-intervention loop — Parses transcripts into a per-turn cost ledger priced with cache-write and cache-read multipliers, including the tool's own calls. Each candidate intervention (disable an unused MCP server, trim an instruction file, add a digest, filter output) is a snapshot-backed patch to settings or hooks. Sessions on a repo are randomly assigned on or off per intervention. An intervention stays only if cost per successful session (tests green, commit made, no user redo) drops with confidence and success holds; otherwise it is reverted byte for byte.
P2: Output spillover hook — A PreToolUse hook rewrites known verbose commands (test runners, builds, installs, large log reads) to tee full output into `.tokeneco/out/<id>.log`. The agent sees only the exit code (preserved), the failing sections, the last N lines and the log path. It can still open the full log, so no information is lost, but passing-test noise stops riding along in history on every later turn. If the wrapper itself errors, the original command runs unmodified.
P3: Prefix and cache hygiene plus warm-start digest — From usage history, list tools and MCP servers this repo never calls and propose disabling them. Find mid-session cache-creation spikes, trace them to volatile hook output or toggled tools, and move that text out of the prefix. Build a compact digest of facts that sessions keep rediscovering (build and test commands, module map), tie each line to file content hashes, and drop lines when they go stale. Inject it at session start only if the A/B test shows net savings.

### S4

P1: Measured, reversible optimization loop — Adapters parse each harness's transcripts. They compute session cost from input, cache-write, cache-read and output tokens at cache pricing, including the tool's own calls. Each optimization is a versioned patch to settings or instruction files, backed up before it applies. Patches are switched on for alternate sessions. Cost per successful task (tests pass, commit kept, no user redo) is compared, and patches that raise cost or lower success are reverted automatically.
P2: Usage-based pruning with a stable prefix — From transcripts, count which MCP tools, skills and instruction sections each repo actually uses. Write per-repo settings that disable servers never used. Propose a compacted instruction file. Move dynamic content (date, git status) out of always-loaded instructions into hook context added later, so the cached prefix stays byte-identical across turns and sessions.
P3: Warm-start repo digest — Mine the read and search calls that repeat across sessions for stable facts: build and test commands, module map, entry points, known pitfalls. Write them into a small digest loaded by a SessionStart hook. Store the hashes of the source files behind it and regenerate when they change. Measure whether exploratory turns and tokens actually drop, and remove the digest if they don't.

### S5

P1: Attribution ledger with reversible experiments — Parse transcripts into per-turn cost by component using cache pricing. Rank causes per repo. Apply one intervention at a time as a settings patch with stored backup; tag sessions as before/after; compare cost per successful task (tests green, no correction prompt), including the tool's own calls. Keep the patch only if cost drops and success holds; otherwise restore the backup automatically.
P2: Repo digest at session start — Generate a compact digest (layout, build/test commands, key modules, conventions) from the repo, regenerated only when relevant files change, and inject it via SessionStart hook. Measure drop in exploratory read/search calls per session; drop the digest if it does not pay for its own tokens.
P3: Tool-surface pruning with auto-restore — From transcripts, count per-repo usage of each MCP server and tool. Disable unused ones in project settings with a backup. A hook watching for missing-tool errors or explicit requests re-enables them and logs the event, so pruning never blocks work.

### S6

P1: Measured, reversible settings experiments — Parse transcript usage (input, cache write, cache read, output), price each turn at cache rates, and split cost into fixed prefix (instructions plus tool definitions) and conversation. Propose changes: disable MCP servers or tools unused over N sessions, trim instruction files. Apply each change as a journaled diff, revertible with one command. Alternate sessions with and without the change, and keep it only if cost per successful task drops. Success means tests passed and work committed, with no user rework request.
P2: Stable repo brief at session start — Build a compact brief (layout, build and test commands, key modules, known pitfalls) from files and commands that earlier transcripts repeatedly explored. Generate it with the agent's own login in headless mode and count that cost. A SessionStart hook injects it byte-identical between sessions, so it stays cacheable. Regenerate only when the git tree changes materially. Keep the brief only if exploration calls and cost per task fall.
P3: Cache-bust detector — Flag mid-session spikes in cache creation tokens and attribute each to a cause: dynamic text in instruction files (dates, git status), tool list changes after MCP reconnects, edits to settings or instructions during a session. Recommend fixes, such as moving dynamic content out of the cached prefix. A PostToolUse hook only adds advice when outputs pass a size threshold, never blocking.

## transcripto

Problem: An engineer hands tasks to coding agents (Claude Code, Codex, Cursor) and comes back to a closing message saying the work is done. Sometimes edits silently failed, a command errored, or a result was never produced, but the summary still sounds confident. Reading the whole raw session to find out what really happened takes longer than the task itself.

Core mechanism of the real tool:
- M1: Reconstruct the session from the transcripts the agents already write (no new instrumentation): request, each tool call, and its recorded result, in order.
- M2: Classify every tool call's outcome (attempt / success / failure / unknown) from the recorded tool results themselves, independently of and without relying on the agent's closing message.

Score 2 (full match): Proposal contains M1 and M2: reads existing transcripts and labels each action's real outcome from tool results, explicitly not trusting the agent's own summary.

Score 1 (partial match): Proposal reads existing transcripts to show what happened but does not classify outcomes independent of the agent's claim; or verifies claims by re-running checks rather than from recorded results.

Score 0 (not a match), including: Asking the agent to self-report more carefully; adding a new logging proxy only; a generic session dashboard; requiring tests to pass before saying done

### S1

P1: Claim-vs-evidence audit — Per-harness adapters normalize transcripts into tool-call and tool-result events. The auditor finds failed operations (error flags, non-zero exits, known failure strings), pairs each with any later successful retry on the same file or normalized command, and flags the ones never resolved. It pulls claims out of the final message by pattern (tests pass, created X, fixed Y) and labels each supported, contradicted or unverified, with transcript line references. Output is a one-screen verdict plus a drill-down table.
P2: Tested-code and disk reconciliation — Compares the session's history with the current workspace. Edits made after the last passing test or build are flagged "untested final changes". For each successful edit, it checks the inserted text is still in the file. For each path named in the prompt or summary, it checks the file exists and was modified after the session started. It compares `git status` with the files claimed as changed. This catches silently reverted edits, files that were never created and stale green test runs.
P3: Stop-hook self-audit — Where the harness supports stop hooks (Claude Code Stop/SubagentStop), the audit runs before the agent's turn ends. If it finds unresolved failures or contradicted claims, it blocks with a reason listing them, so the agent has to fix or disclose them. Blocking is capped at two (using stop_hook_active) to avoid loops, and the verdict is written next to the transcript for the human. Harnesses without stop hooks get the after-the-fact report from P1.

### S2

P1: Unresolved-failure ledger with claim cross-check — Adapters normalize Claude Code, Codex and Cursor transcripts into calls and results. Each failure is marked resolved only if a later call of the same kind on the same target succeeds. Failures include error results, non-zero exits outside the benign list, edits that were not applied, timeouts and interrupts. Claims in the final message are extracted by patterns and matched to evidence. `transcripto last` prints one screen of contradictions, unresolved failures, tests made stale by later edits and unverifiable claims, each with transcript line references.
P2: Stop-hook reality check — In Claude Code, a Stop hook runs transcripto on the live transcript. If it finds contradictions or unresolved failures, it returns a block decision once (guarded by stop_hook_active) listing them, so the agent either fixes them or states them in its summary. For Codex and Cursor, a notify or after-run hook writes the report next to the session and prints a one-line verdict. The engineer sees the verdict first, not the confident summary.
P3: Workspace reconciliation — Record git HEAD and hashes of dirty files at session start, via a SessionStart hook or from the first transcript event's cwd and timestamp. At review time, diff the workspace against that baseline and compare it with what the transcript claims. Flag claimed edits with no diff, claimed-created files that are missing, files changed that the transcript never touched, and commits or PRs mentioned but absent from git. These contradictions rank above all transcript-only findings.

### S3

P1: Normalized events with failure detectors — One script with adapters for Claude Code JSONL, Codex and Cursor session files. Each event records tool, arguments, result, error flag, exit code, files touched and transcript line. Detectors flag errored tools, non-zero exits, failed edits, timeouts and interrupts, errors never followed by success, and tests whose last run after the final edit failed or never ran. The output is a short ranked report with transcript line references.
P2: Final-claim checker — Extract claims from the closing message with patterns ("tests pass", "created X", "updated Y", "fixed", "verified"). Match each to evidence: the last test run's exit code after the last edit, the named file existing with a matching edit event, the command actually executed. Each claim is labelled supported, contradicted or no evidence, citing transcript lines, so the engineer reads three flagged lines instead of the session.
P3: Transcript versus disk — Compare edits recorded in the transcript with the current `git status` and `git diff`. List edits the transcript claims that are absent on disk, disk changes the transcript does not explain, and claimed output files that do not exist. An optional Stop hook runs this together with P1 and P2 as the session ends and writes the report next to the transcript.

### S4

P1: Claim-evidence reconciler — Local CLI with per-harness adapters normalizes transcripts into events. It extracts claims from the final message, marks each supported, contradicted or unverified by matching events, then lists failures the summary never mentions (errored edits, non-zero exits without successful retry, tests not re-run after the last edit), each with a transcript line reference.
P2: Final-state verifier — For every file touched, compute final status (last edit succeeded or failed) and compare with git diff; for every test/build command, report the result of its last run after the last edit. Produces a one-screen table showing what is actually on disk and actually passing.
P3: End-of-session hook — Register the reconciler as a Stop/session-end hook where the harness supports it, so the report is written next to the transcript and printed under the agent's closing message; for other harnesses, a watch command processes new transcript files as they finish.

### S5

P1: Two-way reconciliation report — Adapters turn Claude, Codex and Cursor transcripts into one event list. Backward pass: extract claims from the final message (paths, commands, test/build verbs, counts) and look for supporting events after the last relevant edit. Forward pass: collect every failed event and check whether a later event resolved it and whether the summary mentions it. Output is one screen: contradicted claims, unresolved and unmentioned failures, unverified claims, each with transcript line numbers.
P2: Present-state check — Compare claims with the working tree. Claimed files must exist and appear in git diff against the session's start commit (from the cwd and HEAD at the first transcript event). Claimed outputs must have mtimes inside the session window, and files claimed deleted must be gone. An optional flag reruns the last claimed test command and records its exit code.
P3: End-of-turn notifier — Install as a Claude Code Stop hook, and as a watcher on the Codex and Cursor session directories, so the reconciliation runs as soon as a session ends. It shows a one-line verdict with counts and writes the full report next to the transcript, so the engineer sees discrepancies before reading the agent's summary.

### S6

P1: Normalized events and unresolved failures — Adapters for Claude JSONL, Codex session files and Cursor storage map entries to {time, tool, args, result, exit code, error flag, paths}. The detector flags failures with no later successful equivalent: errored edits, commands whose last run failed, denied permissions, interrupted calls, expected outputs never written. It prints a one-screen report with a line reference into the transcript for each item.
P2: Claim-versus-evidence check — Pattern rules pull claims from the closing message ("tests pass", "created X", "updated Y", "ran Z"). For each claim, it looks for support: the exit code of the last matching test command, a successful write plus the file existing now, and the path appearing in git diff. Each claim is marked supported, contradicted or unsupported, with the evidence line.
P3: Stop-hook receipt — A snapshot of git state is taken at session start. At session end, a hook runs the analyzer and stores a receipt next to the transcript, showing files actually changed, failed commands still unresolved and unsupported claims. The receipt appears before the agent's summary, so the engineer reads verified facts first.

## unlazy

Problem: On substantial multi-part work (a refactor with many migration paths, work fanned out to subagents), the agent truncates, partially complies, and then reports 'done' with confidence. Subagents hand back work that the parent accepts on their word. I find out later that several required outcomes were never met.

Core mechanism of the real tool:
- M1: Write an acceptance ledger before work: each outcome is a gate with a runnable CHECK command and an EXPECT output matcher; a gate passes only on exit 0 AND matched output; recorded evidence is bound to a digest of the gate definition (editing the gate makes evidence stale); the parent re-runs all gates (--reverify) on returned subagent work instead of trusting it.
- M2: A Stop hook that blocks the agent from ending its turn/session while any gate is unmet or a dispatched wave is incomplete, with a progress guard that releases after N blocks without real progress; abandonment is an explicit non-success handoff.
- M3: Parallel leaves must declare disjoint owned paths and claim leases before running; check commands need an approval record keyed to the exact command/cwd/shell/PATH.

Score 2 (full match): Proposal contains M1 and M2 (machine-checkable acceptance gates written up front AND a stop/exit hook that refuses completion until they pass).

Score 1 (partial match): Proposal contains M1 without a stop-blocking hook, or a Stop hook keyed to a plain checklist/TODO without executable checks.

Score 0 (not a match), including: prompting the agent to be thorough; TODO list the agent ticks itself; LLM self-review of completeness; just running the test suite at the end

### S1

P1: Approved outcome contract with stop gate — Before any work, the agent drafts `.unlazy/contract.json` (outcome id, description, check command and expected result). The user approves it and its hash is stored; a check changed afterwards does not run until re-approved. Claude Code Stop and SubagentStop hooks, installed only with consent, run `unlazy gate`, and any failing outcome blocks stopping with the failing ids and output. After K blocks, stopping is allowed but recorded as INCOMPLETE. In Codex, the skill requires pasting the gate's hashed report.
P2: Query-computed work inventory — For multi-site changes, the contract defines an inventory query (an rg pattern or a small Node regex/AST scanner) that lists every site to migrate. `unlazy items` materializes the list, and `unlazy slice --n 4` splits it for subagents, each slice with its own check. The gate re-runs the query, so the remaining count comes from the code, not the agent's memory. The parent re-verifies every returned slice before merging it.
P3: Anti-gaming diff audit — At gate time, diff against the contract's base commit and fail on signs that checks were weakened: deleted or renamed tests, added `.skip`/`.only`/`xit`, new `@ts-ignore`/`eslint-disable`/`# noqa`, lowered coverage thresholds, and edits to files the checks read (test configs, the contract itself). Each finding needs explicit user approval. Optionally, spawn a fresh-context reviewer subagent that sees only the contract and the diff and must list unmet outcomes.

### S2

P1: Enumerated contract with Stop gate — The skill has the agent run a generator command (e.g. `rg -l oldApi`) that creates .unlazy/contract.json, with one item per outcome and an executable check for each. The user approves it and the contract hash is stored. Stop and SubagentStop hooks (Node 16, no dependencies) run all checks and block completion while any fail, listing the failing ids. The final report comes from checker output, not the model's prose.
P2: Slice receipts and fresh-context retries — The parent dispatches slices of item ids to subagents. A subagent's work is accepted only when `unlazy check --ids`, run by the parent in a fresh process, passes. Failed items, with their check output, go to a new subagent. After N rounds the remaining ids are reported as unmet. The parent's state lives in the contract file, so compaction cannot lose it.
P3: Anti-gaming diff scan — When the gate runs, compare against the baseline taken at approval: contract hash changed, test count dropped, new skip/only markers, deleted assertions, edited checks. Also scan added lines for placeholders ("... existing code", "not implemented", empty bodies, TODO stubs). Any hit blocks completion and shows the exact lines, unless the user has approved the change.

### S3

P1: Pinned outcome manifest with a Stop gate — A skill turns the request into .unlazy/manifest.json: numbered outcomes, each with a check command and an expected exit code or output pattern. The user approves it once, and its hash is recorded, so changed checks need re-approval. A dependency-free Node Stop hook runs every check and blocks finishing, listing the failures as feedback. The Codex skill runs the same verifier as its last step.
P2: Generated work queue — For fan-out work, a user-approved generator command lists the items, for example remaining old-API call sites. Subagents get slices of the list. The check reruns the generator and expects zero items left, so the parent judges completion from the codebase, not from what subagents report.
P3: Verified subagent receipts — A SubagentStop hook requires a JSON receipt listing the items claimed and the files touched. A verifier on the parent's side checks those files really changed in git and runs the per-item checks. It also scans the diffs for elision placeholders, newly added TODOs and newly skipped tests. Mismatches go back to the parent as rejected work, not accepted output.

### S4

P1: Outcome contract with stop gate — A skill makes the agent write .unlazy/contract.json listing required outcomes, each with a shell check. The user approves it; its hash is stored. A consented Stop hook (Node 16, no deps) runs the approved checks and, if any fail, blocks completion and returns the failing items, so the agent cannot report done until checks pass or items are explicitly marked blocked with a reason.
P2: Parent-side subagent acceptance — Each subagent receives its slice of contract ids. When it returns, the parent runs only those checks and accepts the slice only if they pass; failing ids are re-dispatched to a fresh-context subagent with the failure output. Subagent prose is never used as evidence.
P3: Inventory counters for fan-out work — At start, generate an explicit inventory (every call site, migration path or file to change) by search and store it. Progress is computed by re-running the search, shown as remaining/total, and the stop gate requires remaining to reach zero or each leftover to be listed with a reason.

### S5

P1: Locked outcome manifest with Stop gate — The skill has the agent write unlazy.json before working. It lists each required outcome with a check: command plus expected exit code, a search pattern that must count zero, a required file, or a test that must pass. The user approves it, and the tool hashes and locks it. A consent-installed Stop hook runs every check and blocks completion with the list of failures, up to N retries, then reports them. A hash mismatch means unapproved edits.
P2: Evidence-checked subagent handoffs — On fan-out, each subagent gets manifest item ids and must return JSON listing, per item, its status, the files changed and the check to run. The parent never accepts the status itself: `unlazy verify` re-runs each item's locked check in the parent's own context. Failed or missing items go to a fresh subagent with the failure output attached, and the final report lists every item's check result.
P3: Truncation and test-weakening detector — Scans the session's diff for signs of partial work: placeholder comments ("rest unchanged", "...", "TODO implement"), not-implemented stubs, newly skipped or deleted tests, removed assertions, loosened expectations, and leftover matches of the migrated pattern. It runs inside the Stop gate and as a standalone command. Findings join the check-generated final report, which replaces the agent's own "done" summary.

### S6

P1: Frozen enumerated contract with Stop gate — Before work starts, `unlazy plan` builds `.unlazy/contract.json`: mechanically enumerated items (for example every file using the old API), each with a check command and expected result, plus global checks. The user approves it once; check hashes are stored and hooks run only approved checks. A Stop hook runs `unlazy verify` and blocks with the unmet item IDs until everything passes. After N attempts it allows stopping but appends an explicit report of the unmet items.
P2: Shard receipts for subagents — The contract is split into shards, each named in a subagent's prompt. A SubagentStop hook runs that shard's checks and blocks the subagent until they pass (with bounded retries), then writes `.unlazy/receipts/<shard>.json` with passed IDs, failed IDs and the tree hash. The parent's skill accepts subagent work only through receipts and re-dispatches failed IDs. After merging, the parent reruns the full verify, because shards can pass individually yet conflict together.
P3: Anti-gaming integrity checks — `unlazy verify` hashes the test files and fixtures referenced by checks and fails if they changed without approval. It scans the diff for added skip markers, deleted assertions or lowered expected counts, and rejects checks that pass vacuously (for example zero tests collected). Qualitative items go to a fresh-context reviewer subagent given only the requirement text and the diff. It must cite file:line evidence for each item, and items without evidence count as failed.
