## cc-projects
### Analysis
The developer is acting as a human scheduler, message bus and QA department. Coordination has four parts: decomposition, dispatch, tracking, and verification/integration. Most of it can be mechanical if the plan is an explicit artifact rather than something in the developer's head. The expensive failures in parallel agent work are: (a) tasks that overlap in files and produce merge conflicts, (b) tasks that silently assume different interfaces, (c) sessions reporting "done" without meeting the goal, and (d) spending the subscription limit on low-priority or blocked work.

So the system should produce a task graph with explicit dependencies, file-ownership scope and executable acceptance criteria, and have the human approve it once. It should then dispatch ready tasks to cloud sessions on separate branches and check results without relying on the session's own claim: run the acceptance commands in CI, and have a separate session review the diff against the spec. It merges in dependency order into an integration branch and shows the human only exceptions (blocked, failing, questions). The orchestrator loop itself should be deterministic code, not an LLM, so its state survives restarts and can be inspected. LLMs do the planning, implementation and review.

Interface drift is best prevented up front. If a scaffold step lands interfaces, stubs and failing tests before fan-out, "stitching" becomes "making the tests green", and acceptance can be checked mechanically.

Usage limits mean parallelism should be treated as a budget. Concurrency should be capped by the remaining quota and critical-path tasks should run first. Tasks should be checkpointed so that a fresh session can resume a paused one without rediscovering context.

Human attention belongs at two points: approving the plan and approving the final integration PR. Questions from sessions should be answered in batches rather than as constant interruptions.

### Proposals
P1: Task-graph orchestrator with independent verification — A planner session writes `.plan/graph.yaml`: tasks with goal, owned paths, dependencies and acceptance commands. After human approval, a deterministic loop launches a cloud session per ready task on its own branch and polls status files the sessions must update. On each PR it runs the acceptance commands in CI plus a fresh reviewer session that compares the diff to the spec. Passing PRs merge into an integration branch in dependency order. Failures are re-dispatched with the failure log, and only exceptions reach the human.
P2: Contract-first scaffold before fan-out — Before parallel work starts, one session lands a scaffold PR: shared interfaces, type signatures, stub modules, fixtures, failing tests for each task's acceptance criteria, and a path-ownership map that assigns each path to one task. Parallel sessions implement against these frozen interfaces and may only touch their own paths; a CI check rejects out-of-scope diffs. Interface changes need a separate small PR, which the orchestrator rebases dependent tasks onto. Integration becomes "all tests green" instead of manual stitching.
P3: Quota-aware scheduler with resumable checkpoints — The orchestrator estimates each task's cost from history (usage per task size for similar past tasks) and tracks usage consumed against the subscription window, from session usage reports and limit warnings. It caps concurrency so the critical path finishes within the window and runs low-priority tasks only with spare quota. Sessions must commit a `progress.md` checkpoint (done, next, open questions) at each milestone, so a session stopped by a limit can be resumed from its branch by a fresh one.

## honest-arch-diagrams
### Analysis
The failure comes from the model treating "diagram this" as a generation task and filling gaps from its priors: in its experience every web service "has" Redis and an auth gateway. Trust requires the reverse. The diagram should be a rendering of an evidence graph built deterministically from artifacts, and the model's role is limited to choosing scope, naming and explaining. It never adds nodes or edges.

Every node and edge needs provenance: the source file or object plus a JSON pointer (`Service/payments#/spec/selector`, `aws_db_instance.main`, trace span IDs). Edges also differ in evidence strength:
- observed: OTel client/server span pairs;
- declared: Ingress backend to Service, Service selector matching Deployment labels, or an env var/ConfigMap value whose host resolves to a known Service DNS name or Terraform endpoint;
- inferred: name heuristics only.

The tiers must render differently. Anything that cannot be resolved, such as an env var pointing at an unknown host, appears as an explicit "unresolved" node instead of being guessed or dropped. TLS, auth and caches appear only with evidence: mesh injection annotations or PeerAuthentication, Ingress `tls` blocks, auth middleware CRDs or annotations, or a cache resource that something actually references.

Agents still embellish when they redraw or write prose, so the CLI needs a verify mode that checks any agent-produced diagram against the evidence graph, and the skill must require running it.

Traces make a strong honesty check possible: declared edges never observed (dead config) and observed edges never declared (drift, unmanaged egress).

Zero dependencies: the JSON inputs are trivial to parse. YAML (Helm output, compose) needs a vendored parser for a minimal subset that fails loudly on unsupported anchors or tags; Helm charts are rendered with `helm template` first.

Secrets: never read `Secret.data` values, only key names. Env values go through a classifier that keeps only the scheme, host and port of URLs and drops userinfo, query strings, credential-pattern matches and high-entropy strings. Terraform `sensitive_values` are honoured. The final output is scanned again, and the tool fails closed if anything suspicious remains.

Output is Mermaid, which renders in GitHub and IDEs, plus a JSON evidence index with stable IDs that the diagram footnotes reference.

### Proposals
P1: Evidence-graph extractor with provenance-tagged rendering — `archmap build` parses kubectl JSON, rendered manifests, compose, `terraform show -json`, OpenAPI and OTel traces into nodes and edges. Each carries evidence IDs (file plus JSON pointer, or span ID) and a tier: observed, declared or inferred. `archmap render --from <entrypoint>` walks the request path and emits Mermaid with solid, dashed or dotted lines per tier, evidence footnotes and explicit "unresolved: host X" nodes. Nothing without evidence is emitted, and secret values and URL credentials are never read.
P2: Diagram verify gate in the skill — The skill tells agents to produce diagrams only through the CLI. If they edit or hand-write one, they must run `archmap verify diagram.mmd`. Verify parses the Mermaid, maps each node and edge to the evidence graph by ID or name, and fails with a list of every element that has no evidence or an overstated tier (for example a dashed edge drawn solid). The skill forbids presenting a diagram that has not passed verify and requires quoting its summary line.
P3: Observed-vs-declared reconciliation — When OTel traces are supplied, `archmap diff` joins client/server spans (peer.service, server.address, k8s.* resource attributes) to declared edges. It reports three sets: confirmed, declared but never observed in the trace window, and observed but undeclared (for example egress to an external host missing from the manifests). Edges are coloured accordingly. The report states the trace window and sample size, so a lack of traffic is not presented as proof that an edge does not exist.

## squadra
### Analysis
Task ownership, assignment delivery, test provenance, whether reviewed code is the shipped code, and decisions all live in conversational memory. That memory is lossy, not shared between vendors, and erased by a reset. This state needs a durable append-only record outside any agent, with claims bound to content hashes so they can be checked rather than believed.

The setup constrains the design. The Codex sandbox can usually write only inside its workspace and cannot signal other windows; Cursor is driven by the human; nothing publishes automatically. So communication has to be pull-based. Each agent appends events only to an outbox in its own checkout (`.squadra/events.jsonl`, git-ignored). A Python-stdlib `squadra` CLI merges the logs of all registered checkouts, which are readable from any of them, into one project view. Incoming messages are files read at session start or on each prompt:
- Claude Code: SessionStart and UserPromptSubmit hooks inject pending items.
- Codex: an AGENTS.md instruction to run `squadra inbox`.
- Cursor: a generated prompt the human pastes.

Whether a window received its assignment can be answered from the transcripts on disk. Each assignment carries a nonce; squadra looks for the nonce in that agent's transcript and then for an ack event. The states are written, delivered, acknowledged, done.

Which code was tested, reviewed and shipped is answered with tree hashes. `squadra run -- pytest` records the command, the exit code and a tree ID of the exact working state (temporary index, `git add -A`, `git write-tree`), so uncommitted changes count. Reviews record the tree ID they examined. A ship check compares the tree about to be pushed with the latest passing test receipt and review receipt, and shows the diff between them. Transcripts allow a cross-check as well: "tests pass" with no matching command and exit code is flagged.

Self-review shares the author's blind spots. The reviewer must therefore be a different agent from the author, ideally from another vendor, and reviews a generated packet (spec plus diff at a tree ID).

Decisions: `squadra decide` appends timestamped entries with supersedes links. Scanning the human's messages in transcripts for a `DECISION:` prefix captures decisions without extra typing.

Recovery: `squadra brief <agent>` regenerates the agent's role, owned tasks, open messages, receipts and decisions as a prompt for a new window.

### Proposals
P1: Hash-bound receipt ledger — Each checkout keeps an append-only `.squadra/events.jsonl`, and `squadra` merges them by timestamp into tasks, owners and decisions. `squadra run -- <test cmd>` records the exit code and a tree ID of the exact working state (temporary index plus `git write-tree`). Reviews record the tree ID they examined. `squadra ship-check` fails, printing the problem and never pushing, when the tree to be shipped differs from the last passing test and approved review, and shows the diff between them.
P2: Nonce handshake verified from transcripts — Assignments go into the target agent's inbox with a nonce. Claude Code hooks inject inbox items at session start and on each prompt; Codex is told in AGENTS.md to run `squadra inbox`; Cursor gets a paste-ready prompt. squadra scans each agent's transcript files for the nonce to mark the assignment "delivered". It marks it "accepted" only after an ack event containing the nonce and the agent's current HEAD. Unacknowledged assignments surface in `squadra status` after a timeout.
P3: Cross-agent review packets and reset briefs — `squadra review-request` builds a packet (task spec, diff at a tree ID, test receipts) that can be assigned only to an agent other than the author, preferably from another vendor. The verdict must cite file:line and is bound to that tree ID, so self-approval is rejected. `squadra brief <agent>` regenerates a context-restoration prompt from the ledger: role, owned tasks, open messages, timestamped decisions and latest receipts. A SessionStart hook injects it, or the human pastes it after a reset.

## termaxa
### Analysis
The risk is an ordinary chore done with maximum force, not malice. So the hook should not ban whole command categories. It should ask "would this destroy something unrecoverable that was not the target?" and, if so, steer the agent to the gentlest command that still does the chore. With approvals off there is nobody to ask, so the useful outcomes are: allow; deny with an exact alternative, which agents reliably follow; and snapshot, then allow.

Requirements:
1. Real parsing, not regex. Handle quotes, `&&`, `;`, pipes, subshells, recursive `bash -c`, `xargs`, `find -delete` / `-exec rm`, env prefixes, `git -C`, combined flags (`-rf`, `-fr`, `--force`), `+refspec` pushes and heredocs into psql. Dynamically built commands (`eval`, `base64 -d | sh`) count as high risk by default.
2. Predicates that check live state:
   - git: `reset --hard` on a clean tree is harmless, but on a dirty one it destroys work. `push --force` is harmless when the remote-tracking ref is an ancestor of the local branch and the branch is not protected.
   - files: `rm -rf dist/` on ignored build output is fine; on tracked-modified or untracked non-ignored files it is not.
   - SQL: classify DROP, TRUNCATE and DELETE/UPDATE without WHERE, and match the connection target against policy.
   - Terraform: `destroy`, or `apply -auto-approve` without a saved plan; with a saved plan, inspect `terraform show -json` for delete/replace actions on protected types.
   - kubectl: current context, `--all`, `-A`, namespace deletes.
   - docker: volume removal, `prune --volumes`, `compose down -v`.
3. Reversibility where it is cheap. Before allowing a command, local git and file state can be snapshotted into a hidden ref: temporary index including untracked files, `write-tree`, `commit-tree`, `update-ref refs/termaxa/...`. Remote, database and cluster state cannot be snapshotted cheaply, so those commands are denied.
4. Write tools: overwriting a file that has uncommitted changes the session did not make triggers the same snapshot.
5. Reviewable policy in the repo, a local JSONL decision log, and policy tests.

Hooks only advise, so an agent can route around them by writing a script and running it. A partial mitigation: when the command executes a shell script, parse the script as well; for other interpreters, fall back to taking a git snapshot first.

Implementation: a single static binary (Go or Rust). An unparseable command is denied only if it contains destructive tokens. Latency stays around 20 ms, with git called only when a predicate needs it.

### Proposals
P1: State-aware deny with an exact safer equivalent — Parse the command into an AST and evaluate predicates against live state: git status, ignore rules, remote-tracking ancestry, DB target, kube context. When it would likely destroy state that nobody mentioned or that cannot be recovered, deny with a message saying what would be lost and giving the minimal command: `git reset --soft HEAD~1`, `git push --force-with-lease=main:<sha>`, `git clean -n` followed by specific paths, `rm -rf dist/` rather than `.`, `DELETE ... WHERE`, or `terraform plan -destroy` first.
P2: Snapshot-then-allow for local destruction — Before destructive local operations on a dirty tree (reset --hard, checkout -- ., clean -fd, stash drop, rm of tracked or untracked files, an overwriting Write), the hook captures everything into a hidden ref built from a temporary index that includes untracked files, or copies rm targets into `.termaxa/trash/<ts>/`. It logs the snapshot and allows the command. `termaxa undo` lists and restores snapshots; a size cap and expiry keep this cheap. Remote, database and cluster actions are never snapshot-allowed; they fall back to P1.
P3: Repo policy with replay tests — `.termaxa.toml` declares protected branches, DB URL patterns, kube contexts, Terraform resource types, cleanable globs and an action per rule. `termaxa explain '<cmd>'` prints the parse, the predicates and the decision. A corpus of (command, fixture state, expected decision), seeded from logged real agent commands, runs in CI via `termaxa test`. A policy PR shows which historical commands would change decision, so the policy is reviewed like code.

## tokeneconomizer
### Analysis
Cost per turn is roughly the fixed prefix (system prompt, tool definitions, instruction files) plus the conversation so far plus new output. These are priced differently: cache write (about 1.25x), cache read (about 0.1x) and uncached input. The levers are therefore: shrink the prefix, keep it cacheable, shorten conversations (fewer exploratory turns, smaller tool outputs), and stop re-learning the repo every session. Because the agent is a black box, every lever acts on inputs: settings files, instruction files, context injected by hooks, and command rewriting through PreToolUse.

"Without hurting task success" together with "every action reversible" means this has to be an experiment loop, not a list of tricks.

Measure first, from transcripts:
- price each turn's usage fields with cache pricing;
- attribute tokens to prefix components (each MCP server's tool schemas, each instruction file) and to tool results by tool and command;
- detect cache breaks: cache-creation spikes mid-session caused by dynamic hook content, tool-list changes, or idle gaps longer than the cache TTL.

Success needs a proxy: the session ended with tests passing or a commit/PR, with no user correction or revert afterwards and no repeat of the same task in the next session.

Each intervention is applied as a recorded diff with a backup and a one-command revert. It is evaluated by randomizing per session (on or off) and comparing cost per successful session. Interventions are kept only if they save significantly without lowering success, and reverted otherwise. The tool's own costs, such as model calls made through the agent's login, are charged to the intervention that caused them.

Candidate interventions:
- Tool diet: disable at project scope any MCP server or tool never invoked in this repo over N sessions. Tool schemas can cost thousands of tokens per turn, and changes to the tool list break the cache.
- Instruction slimming: move rarely relevant sections of CLAUDE.md/AGENTS.md into on-demand skills or docs, leaving a one-line pointer.
- Warm start: inject a learned repo brief at session start covering layout, build/test commands that actually worked, pitfalls, and the files typically read per task type. Keep it small and stable so it stays cached.
- Output offloading: rewrite known verbose commands so that full output goes to a file and the agent sees failures plus the tail.
- Cache hygiene: move dynamic hook output (timestamps, git status) out of the prefix and into per-turn context.

Never stopping a turn: hooks only add context or rewrite inputs, fail open on any error, and never return a block decision.

### Proposals
P1: Measured, reversible intervention loop — A transcript analyzer prices every turn at cache-write, cache-read and uncached rates. It attributes tokens to prefix components, tool outputs and cache breaks, and scores sessions with success proxies. Each intervention is a recorded settings or file diff with a backup and `undo`, and a per-session coin flip decides whether it applies. After enough sessions the tool compares cost per successful session, including its own calls. It keeps the winners and automatically reverts interventions that cost more or lower success.
P2: Prefix diet driven by usage — From transcripts, compute for each MCP server and tool the schema tokens paid per turn versus the times it was actually invoked in this repo, and disable unused servers at project scope. Split instruction files into sections, track which sections' topics actually come up in tasks, and move rarely relevant ones into on-demand skills or docs referenced by one-line pointers. Move dynamic hook output out of the cached prefix. Every change runs as a P1 intervention, so any drop in success reverts it.
P3: Warm-start repo brief and output offloading — After each session, deterministically extract from the transcript the commands that worked, the files read per task type and the failures hit. Distill them into a capped, stable `repo-brief.md` that is injected at session start, so the agent spends fewer turns exploring. A PreToolUse hook rewrites known verbose commands (test, build, install) to tee full output into a file. The agent sees the exit status, failure blocks, the tail and the file path.

## transcripto
### Analysis
The closing summary comes from what the model believes happened, which can differ from the tool results. Examples: an Edit that returned "old_string not found", a command that exited 1 and scrolled past, a file the agent later overwrote, tests run before the last edit. The transcript already holds the ground truth for all of these. A deterministic reader can produce a short reality report faster than a human, without trusting another model.

Design:
1. Per-harness adapters normalize everything into one event model: `call{id, tool, args, targets}`, `result{id, ok, exit_code, error_text}`, `message{role, text}`, plus timestamps.
   - Claude Code JSONL has tool_use/tool_result with is_error.
   - Codex rollout JSONL has function calls and outputs with exit codes.
   - Cursor stores conversations in SQLite, readable with Python's stdlib sqlite3.
   Python stdlib (or a single static binary) meets the no-extra-dependencies requirement. An unknown format fails loudly instead of reporting "no problems".
2. Failure resolution: a failure counts as resolved only if a later call of the same kind on the same target succeeds (the same file edited successfully, the same command exits 0). Unresolved failures are the core signal.
3. Freshness: did a passing test run happen after the last write to source files? "Tests pass" is a stale claim if edits followed the last green run.
4. Claim cross-check: extract claims from the final message with patterns (file paths, "tests pass", "created/updated/removed X", "all N") and attach supporting or contradicting evidence to each.
5. Workspace reconciliation: compare claimed or attempted changes against the git diff since the session's starting commit. A file the agent "updated" that shows no diff, or a "created" file that is missing, is a hard contradiction.
6. Presentation: one screen, ranked as contradictions, unresolved failures, stale verification, unverifiable claims, then counts. Each item gives transcript line numbers so the engineer can jump straight to it.

False positives matter: grep exiting 1 or diff exiting 1 is normal. Keep a list of benign exit codes per command and allow per-repo ignore rules.

Hook integration closes the loop. A Claude Code Stop hook can send contradictions back to the agent once, before the human ever sees the confident summary.

### Proposals
P1: Unresolved-failure ledger with claim cross-check — Adapters normalize Claude Code, Codex and Cursor transcripts into calls and results. Each failure is marked resolved only if a later call of the same kind on the same target succeeds. Failures include error results, non-zero exits outside the benign list, edits that were not applied, timeouts and interrupts. Claims in the final message are extracted by patterns and matched to evidence. `transcripto last` prints one screen of contradictions, unresolved failures, tests made stale by later edits and unverifiable claims, each with transcript line references.
P2: Stop-hook reality check — In Claude Code, a Stop hook runs transcripto on the live transcript. If it finds contradictions or unresolved failures, it returns a block decision once (guarded by stop_hook_active) listing them, so the agent either fixes them or states them in its summary. For Codex and Cursor, a notify or after-run hook writes the report next to the session and prints a one-line verdict. The engineer sees the verdict first, not the confident summary.
P3: Workspace reconciliation — Record git HEAD and hashes of dirty files at session start, via a SessionStart hook or from the first transcript event's cwd and timestamp. At review time, diff the workspace against that baseline and compare it with what the transcript claims. Flag claimed edits with no diff, claimed-created files that are missing, files changed that the transcript never touched, and commits or PRs mentioned but absent from git. These contradictions rank above all transcript-only findings.

## unlazy
### Analysis
The agent's "done" is a self-assessment made at the end of a long context, which is exactly when truncation and optimism are worst. Subagents make it worse because the parent receives a summary, not evidence. The fix is to move the definition of done out of the model's head into an artifact fixed before work starts, and to make completion something code checks rather than something the agent states.

Three parts:
1. Fix the denominator up front. Partial compliance goes unnoticed on a refactor with many migration paths when nobody counted the paths. A planning step generates the full item list mechanically where possible (`grep -l oldApi`, route lists, call sites) and stores it in `.unlazy/contract.json`. Each item gets a check: a command plus the expected result (exit code, zero matches, a named test passes, a file exists). Global checks cover the test suite, typecheck and build. Qualitative requirements get a "review" check type.
2. Freeze the contract with the user's consent. Checks run with ambient access, so the user reviews the contract once and unlazy stores a hash of each check command. Hooks run only approved checks; any edit by the agent invalidates the affected check and is shown as a diff. Weakening is detected too: removed items, edits to test files referenced by checks (via their hashes), and newly added skip markers.
3. Gate the hand-off points. A Claude Code Stop hook runs `unlazy verify` and, if checks fail, blocks with the unmet item IDs so the agent keeps working. A loop guard allows stopping after N blocks but appends an explicit report of the unmet items. SubagentStop runs only the shard of items assigned to that subagent, and the result is written as a receipt the parent reads instead of a claim. Codex has no equivalent hook, so its skill makes `unlazy verify --report` the mandatory last step and requires the receipt to be pasted verbatim. The receipt includes a tree hash that the user can re-check.

Non-mechanical items go to a fresh-context reviewer that sees only the requirement and the diff, not the implementer's narrative.

Node 16 with no dependencies: only fs, crypto and child_process. Hooks are written to settings only after an explicit `unlazy install-hooks` confirmation that shows the exact config being added.

### Proposals
P1: Frozen enumerated contract with Stop gate — Before work starts, `unlazy plan` builds `.unlazy/contract.json`: mechanically enumerated items (for example every file using the old API), each with a check command and expected result, plus global checks. The user approves it once; check hashes are stored and hooks run only approved checks. A Stop hook runs `unlazy verify` and blocks with the unmet item IDs until everything passes. After N attempts it allows stopping but appends an explicit report of the unmet items.
P2: Shard receipts for subagents — The contract is split into shards, each named in a subagent's prompt. A SubagentStop hook runs that shard's checks and blocks the subagent until they pass (with bounded retries), then writes `.unlazy/receipts/<shard>.json` with passed IDs, failed IDs and the tree hash. The parent's skill accepts subagent work only through receipts and re-dispatches failed IDs. After merging, the parent reruns the full verify, because shards can pass individually yet conflict together.
P3: Anti-gaming integrity checks — `unlazy verify` hashes the test files and fixtures referenced by checks and fails if they changed without approval. It scans the diff for added skip markers, deleted assertions or lowered expected counts, and rejects checks that pass vacuously (for example zero tests collected). Qualitative items go to a fresh-context reviewer subagent given only the requirement text and the diff. It must cite file:line evidence for each item, and items without evidence count as failed.
