## cc-projects
### Analysis
Two directions: downward (goal → acceptance criteria → tasks → session prompts) and upward (session results → task checks → integrated branch → goal criteria). The end of going down (a session running a task) is where going up starts (its PR). The end of going up (goal criteria still failing) is where the next downward pass starts.

Pass 1, down: the developer's coordination cost splits into split, assign, track, check, stitch. A naive split ("you do auth, you do UI") gives tasks with no shared definition of done.

Pass 1, up: so the human has to read every PR to judge it (check cost) and resolve conflicts and mismatched interfaces (stitch cost). These upward costs come from what the downward pass left out: an executable acceptance check per task, separate file ownership for each task, and fixed interfaces.

Pass 2, down: so every task must carry (a) the paths it owns, (b) an acceptance command, (c) the interfaces it consumes and provides, (d) its dependencies. Interfaces are committed before fan-out so parallel work cannot drift apart.

Pass 2, up: now checking is mechanical (run acceptance, confirm the diff stays inside owned paths, CI green), and stitching is a merge in dependency order. What is left for the human: tasks that failed their check twice, scope violations, and goal-level failures. Each of those becomes a new task, which means going down again.

Tracking comes for free: state lives in the PRs and the plan file, not in the human's head.

Usage limits: every session costs usage, and a failed session costs it twice. Upward data (tokens per task, retries) feeds the next downward pass, which sizes tasks and caps concurrency to the budget.

Switching rule: go down until every leaf task has an executable check and a scope that does not overlap other tasks. Go up whenever a session finishes. Stop when goal acceptance passes. Progress is the number of goal criteria passing, not the number of PRs merged.

### Proposals
P1: Plan ledger with reconciler — A planner session writes plan.json in the repo: goal acceptance tests, and per task its owned paths, acceptance command, dependencies and interface files. A dispatcher starts one cloud session per ready task on branch task/<id>. A reconciler polls PRs: it runs acceptance, rejects diffs outside owned paths, merges green PRs into an integration branch in dependency order, runs the goal tests, and turns each failure into a new task. The human sees only exceptions.
P2: Contract-first skeleton PR — Before fan-out, one session commits interfaces, types, stub functions and one failing test per task, and this PR merges first. Each parallel session's only job is to turn its own tests green without editing the shared interface files; a CI path check enforces that. Mismatches between pieces then show up as compile or test failures in CI, not during manual stitching.
P3: Budget-aware scheduler and exception board — Record tokens and retries for each finished task from session usage, and estimate pending tasks' cost by size class. Launch sessions in critical-path order only while projected usage stays inside the subscription window. One status page built from plan.json plus PR and CI states shows each task as ready, running, blocked or needs-human. The developer reviews only the needs-human items.

## honest-arch-diagrams
### Analysis
Two directions: evidence → diagram (extract nodes and edges from sources) and diagram → evidence (trace every drawn element back to the source line that justifies it). Extraction produces a diagram, and tracing starts from that diagram. Whatever tracing cannot justify starts the next extraction: either find a source for it or drop it.

Forward pass: an LLM reading manifests fills gaps with priors ("services like this usually have Redis"). So extraction must be deterministic code, not generation. It parses Ingress → Service (selector) → Pods/Deployment → container ports; env vars and ConfigMaps that name hosts; Terraform resources (LB listeners, RDS, ElastiCache, security groups); compose links; OpenAPI routes; and OTel spans (service.name, server.address, db.system).

Backward pass: for each element, ask "which file, which JSON pointer?". Many edges have weak grounding. An env var REDIS_URL proves configuration, not traffic; a trace proves traffic, not intent. So every element needs an evidence class: observed (traces), declared (manifest wiring) or inferred (naming/heuristic). A TLS hop is drawn only if an Ingress tls block, a mesh mTLS policy or a listener protocol says so. An auth gateway is drawn only if an annotation, policy or route names it.

Forward again: the diagram must show uncertainty visually, with a line style per class, and must show gaps as explicit "unknown" nodes instead of plausible fillers. Joining declared and observed sources gives the most useful findings: declared-but-not-observed (dead config?) and observed-but-not-declared (a missing source).

Backward again: agents will still edit the diagram. So the check must work on any diagram text: parse Mermaid/D2 and reject any node or edge without an evidence ID.

Secrets: extraction reads only allowlisted fields. Secret objects contribute only their names, and URLs are cut down to scheme, host and port.

Stop when every element has evidence or is marked unknown. Progress is the fraction of elements backed by observed or declared evidence.

### Proposals
P1: Provenance graph + verifier CLI — `archmap extract <sources>` (zero-dependency Node) builds graph.json, where each node and edge carries evidence entries {file, JSON pointer, class: observed|declared|inferred}. `archmap render` emits Mermaid with solid/dashed/dotted edges by class, explicit "unknown" hops and an evidence footnote table. `archmap verify diagram.mmd` fails on any element without an evidence ID. The skill tells agents to run these commands and never to add nodes by hand.
P2: Declared-vs-observed reconciliation — Join manifest edges with OTel trace edges, keyed by a normalized service identity (k8s Service DNS, service.name, server.address). Output three sets: confirmed (in both), declared-only and observed-only. Each set gets its own style in the diagram and is listed as questions for the human. An observed-only edge produces a request naming which source is missing, never an invented explanation.
P3: Fail-closed secret hygiene — An allowlist of fields per resource kind. Secret resources are read for metadata.name only. Env and ConfigMap values go through a URL parser that keeps scheme, host and port; userinfo, query strings, and any value matching key/token patterns or showing high entropy are replaced with a hash. A final scan over the output aborts the write if any secret-like string survives.

## squadra
### Analysis
Two directions: outward (intent → assignment → work in a window) and inward (artifact or receipt in a window → ledger → decision). Outward ends with a window doing something; inward starts from the evidence it leaves. Inward ends with an updated ledger, and the next outward pass starts from it.

Outward first: the human assigns work in chat, and nothing records that the window received it. Codex cannot wake Claude windows and Cursor is never launched automatically, so push delivery is impossible. Delivery has to be pull: each window reads its inbox at session start or when a prompt is submitted. Receipt means an explicit ack command that records the window id, session id, checkout path and HEAD.

Inward: claims come back as prose. "Tested" and "reviewed" must be bound to content, not words. A test record holds the command, the exit code and the checkout's tree hash at that moment. A review record holds the reviewed tree hash and the reviewer's identity. Shipping compares the hashes. Self-review can be detected: the reviewer's session or harness equals the author's.

Outward again: assignments should therefore name the evidence expected (test command, reviewer harness), so the window knows what to produce.

Inward again: an agent can still claim it ran a test without using the wrapper. The transcripts on disk let the ledger cross-check: did a matching command run after the last edit and exit 0?

Context resets: state lives in the ledger. A SessionStart hook, or a first-line instruction in AGENTS.md or Cursor rules, replays a short brief for that window.

Storage: separate checkouts do not share .git. So the ledger lives in a user-level directory keyed by the repo's root commit, as append-only JSONL with file locking (stdlib fcntl). Decisions are timestamped events too.

Stop when every task's shipped tree hash has a passing test and an independent review on that same hash. Nothing is published: ship-check only prints the chain, and the human pushes.

### Proposals
P1: Hash-bound event ledger — A stdlib Python CLI that writes append-only JSONL under ~/.squadra/<root-commit>/ with fcntl locks. Commands: assign; ack; test -- <cmd> (runs the command, records exit code and the tree hash from `git stash create` or HEAD); review (records the reviewed hash and reviewer session, rejected if the reviewer is the author); decide; ship-check (verifies the shipped commit's tree matches a tested and independently reviewed tree, otherwise lists the gap).
P2: Pull inbox with acks — Each window has an identity file in its checkout. Claude Code SessionStart/UserPromptSubmit hooks run `squadra inbox`, and AGENTS.md or Cursor-rule instructions tell the other agents to run it. It prints pending assignments and the window's current brief. An assignment stays "sent" until acked. `squadra status` flags unacked assignments after a timeout and prints a ready-to-paste prompt for manual delivery to Cursor or Codex.
P3: Transcript cross-check — Parsers for Claude JSONL, Codex rollouts and Cursor logs extract executed commands, exit codes and file edits with timestamps. For every "tested" or "done" event, verify that a matching command ran and succeeded after the last edit in that checkout. Mismatches are recorded in the ledger as disputed events and shown in status.

## termaxa
### Analysis
Two directions: command → consequence (what state would this destroy?) and consequence → command (what spelling achieves the intent while keeping that state?). The first ends at an at-risk state, which is where the second starts. The second ends at a rewritten command, which goes back into the first so its own consequences get checked.

Command → consequence: matching on spelling alone ("rm -rf is bad") either blocks too much or misses things. Damage depends on state. `rm -rf build/` with nothing tracked or modified inside is harmless; `reset --hard` on a clean tree loses nothing; `push --force` loses nothing when the remote holds no commits missing locally. So the hook must inspect state: git status --porcelain, untracked files under the target path, remote-only commits (remote ref vs local), row counts for DROP or for DELETE without WHERE, delete actions in the terraform plan JSON, and kubectl dry-run object lists.

Consequence → command: when state is at risk, unattended operation means the hook cannot ask anyone. It has two options. (a) Make the change reversible first, then allow it: snapshot with git stash create + update-ref, copy untracked files to a trash directory, pg_dump the table. (b) Deny, giving an equivalent safer spelling the agent can rerun (--force-with-lease, reset --keep, restoring named files, an explicit terraform target list).

Back to consequence: the safer spelling has its own effects. --force-with-lease still overwrites if a background fetch refreshed the remote ref, so --force-if-includes must be added too. Snapshots must not fill the disk, so they need size caps and retention.

Parsing: agents wrap commands (cd x && …, sh -c, xargs, env prefixes). Any command the parser cannot handle that contains a destructive verb gets deny-with-explanation.

Reviewable policy: the rules live in a repo file next to a corpus of sample commands and their decisions, so a policy change is reviewed together with its effects. Hooks only advise, so every message tells the agent why and what to run instead.

Stop when every destructive verb class in the corpus maps to allow, snapshot-then-allow or deny-with-alternative.

### Proposals
P1: State-aware preflight with snapshot-then-allow — The hook binary parses the command and, for destructive verbs, measures what would be lost: dirty or untracked files under an rm target, uncommitted changes before reset/checkout/clean, remote-only commits before a force push. Nothing at risk: allow. Recoverable risk: snapshot (stash create + update-ref refs/termaxa/<ts>, untracked files copied to .git/termaxa-trash), then allow and print the restore command. Unrecoverable risk: deny with a safer alternative.
P2: Safer-spelling rewrite rules in repo — .termaxa.toml maps forceful forms to intent-preserving ones: push --force → --force-with-lease --force-if-includes; reset --hard HEAD~1 → reset --soft or --keep; rm -rf → move to trash; DROP/TRUNCATE → pg_dump of the table required first; terraform apply → only a saved plan with no deletes outside an allowlist. If the harness supports input rewriting (e.g. updated tool input), rewrite the command; otherwise deny and give the exact replacement command.
P3: Shell-aware parser plus decision corpus — Split compound commands (&&, ;, pipes, subshells, sh -c, env prefixes, xargs, find -delete) into simple commands before matching. A command with a destructive verb that cannot be parsed is denied with an explanation. `termaxa test` runs a corpus of commands with fixture repo/database states, checked into the repo, against the policy and diffs the decisions against expected ones, so policy changes are reviewed as decision changes.

## tokeneconomizer
### Analysis
Two directions: cost → cause (attribute the spend recorded in transcripts to its sources) and cause → cost (change one source reversibly, then measure the new spend). Attribution ends with a ranked cause, which starts an intervention. The intervention ends with new transcripts that carry usage, which start the next attribution.

Cost → cause: each turn records input, cache-write, cache-read and output tokens. At cache prices, re-sending the fixed prefix is usually cheap (cache reads) unless the cache breaks. So attribution must separate four things: prefix size (instructions + tool definitions), cache misses (changed prefix, TTL expiry between turns), history growth (large tool results kept forever) and exploration (reads and greps that rediscover the repo).

Cause → cost: what can be changed without touching the agent: disable unused MCP servers and tools in settings; trim instruction files or split them into files loaded on demand; make hook-injected content stable (no timestamps or git status early in context); provide a compact repo brief so exploration shrinks; steer wide searches into subagents so only summaries enter history. Each change is a reversible patch recorded in a journal.

Back to cause: every intervention has its own cost. A repo brief is paid for on every turn and pays off only if exploration tokens fall by more. Generating it through the agent's login also costs tokens, and those must be counted. Removing a tool can cause failures. So measurement must include task success.

Cause → cost again: compare arms across sessions on the same repo by alternating configurations per session. Measure cost per successful session. Success proxy: tests green at the end, no user correction or revert in the next turn, session not abandoned. Keep a change only if cost falls and success does not drop past a threshold; otherwise revert it automatically.

Never stopping a turn: every action happens between sessions or adds context through hooks; nothing blocks.

Stop when no candidate intervention beats the current configuration by more than noise. Progress is cache-priced cost per successful session, including the tool's own calls.

### Proposals
P1: Attribution ledger plus reversible A/B — Parse per-turn usage from transcripts, price it at cache rates, and attribute it to prefix, cache misses, history and tool results by tool. Generate candidate changes (disable MCP servers unused in N sessions, move unreferenced instruction sections into on-demand files) as journaled patches to settings files. Alternate patched and unpatched configs across sessions. Keep a patch only if cost per successful session drops and success holds; otherwise revert it automatically.
P2: Cache-break detector — Across consecutive turns, flag cache-write spikes that new history does not explain. Compare prefix hashes where available, and correlate spikes with hooks or instruction files that inject volatile text (dates, git status, random IDs) and with idle gaps longer than the cache TTL. Report the source and apply a stable rewrite as a reversible patch, e.g. move volatile text into the user turn, sort lists deterministically.
P3: Commit-keyed repo brief — A SessionStart hook injects a short, byte-stable brief (layout, build/test commands, entry points, conventions). The agent's own CLI generates it once per significant commit range, and that cost is booked. Exploration tokens (Read/Grep/Glob results in early turns) are measured with and without the brief. Where the brief does not pay for its per-turn cost, the hook disables itself.

## transcripto
### Analysis
Two directions: claims → evidence (start from the closing summary and look for support in the transcript) and evidence → claims (start from the transcript's events, especially failures, and check whether the summary reflects them). Each direction ends where the other starts: an unsupported claim sends you into the event stream, and an unmentioned failure sends you back to the summary.

Claims → evidence: summaries say "updated X", "tests pass", "created report.md". Each maps to an event type: a successful edit or write to X; a test command that exited 0 after the last edit; a file that exists now. Claims can be extracted deterministically from file paths, command names, verbs such as pass/fixed/created/added, and counts.

Evidence → claims: the dangerous cases never appear in the summary. Examples: an Edit that failed with "string not found" and was never retried; a command that timed out; a background job that was killed. So scan every tool result for error markers (is_error, nonzero exit, known error strings per tool), then check whether a later event resolved each one (the same file edited successfully afterwards, the same command later succeeding). The headline finding is unresolved failures the summary does not mention.

Back to claims: many claims have no event-level evidence at all ("handles edge cases"). Those are marked unverified, not false. Keeping contradicted and unverified apart is what keeps the report trustworthy.

Back to evidence: the transcript can be right while the files have changed since, so the present state needs checking too: files exist, and git diff contains the claimed changes.

Across harnesses: adapters convert Claude JSONL, Codex rollout JSONL and Cursor's local store into one event schema (call, args, result, error flag, exit code, paths, time). No extra dependencies: a single-file Python stdlib tool (json, sqlite3) or Node built-ins.

The report must be faster to read than the session: one screen, contradicted claims first, then unresolved failures, then unverified claims, each with a transcript line reference.

Stop when every claim is classified and every failure is either resolved or reported.

### Proposals
P1: Two-way reconciliation report — Adapters turn Claude, Codex and Cursor transcripts into one event list. Backward pass: extract claims from the final message (paths, commands, test/build verbs, counts) and look for supporting events after the last relevant edit. Forward pass: collect every failed event and check whether a later event resolved it and whether the summary mentions it. Output is one screen: contradicted claims, unresolved and unmentioned failures, unverified claims, each with transcript line numbers.
P2: Present-state check — Compare claims with the working tree. Claimed files must exist and appear in git diff against the session's start commit (from the cwd and HEAD at the first transcript event). Claimed outputs must have mtimes inside the session window, and files claimed deleted must be gone. An optional flag reruns the last claimed test command and records its exit code.
P3: End-of-turn notifier — Install as a Claude Code Stop hook, and as a watcher on the Codex and Cursor session directories, so the reconciliation runs as soon as a session ends. It shows a one-line verdict with counts and writes the full report next to the transcript, so the engineer sees discrepancies before reading the agent's summary.

## unlazy
### Analysis
Two directions: requirements → work (list the required outcomes and dispatch them) and work → requirements (check the produced work against each required outcome). Dispatch ends with produced work, which is where checking starts. Checking ends with a list of unmet outcomes, which is where the next dispatch starts.

Requirements → work: truncation starts here. If the agent lists migration paths from memory, the list is already short, and nothing later catches an item that was never listed. So the list must come from a command (grep for old API call sites, the list of failing tests, a file glob). It is recorded as a contract with one entry per outcome, each with an executable check: a command exits 0, a pattern is absent, a file exists, a test passes.

Work → requirements: "done" is only the model's word. The check must run outside the model: Stop and SubagentStop hooks run every check and block completion, listing the failing ids. Subagent reports do not count as evidence; the parent accepts a slice only when the checks for its ids pass in a fresh process.

Back to requirements: agents game checks by deleting tests, adding skip markers, weakening a regex or editing the contract. So the contract is hashed at approval, and any change needs user consent. The gate also looks for weakened tests (lower test count, new skip/only, deleted assertions) and for placeholder code in the diff ("... existing code", "not implemented", TODO stubs).

Back to work: failing items are redispatched, with their check output, to a fresh context. That works better than asking the same worn-out context to "finish". Rounds are capped; after N rounds the remaining items are reported explicitly, not as "done".

Constraints: checks run with ambient access, so they are shown to the user at consent time, and read-only checks are preferred. Only Node 16 built-ins are used (child_process, fs, crypto). Codex lacks the same hooks, so its skill tells the agent to run `unlazy verify` and paste the output verbatim as its final report.

Stop when all contract checks pass, or when the round cap is hit with the remaining items listed. Progress is passing checks out of total checks.

### Proposals
P1: Enumerated contract with Stop gate — The skill has the agent run a generator command (e.g. `rg -l oldApi`) that creates .unlazy/contract.json, with one item per outcome and an executable check for each. The user approves it and the contract hash is stored. Stop and SubagentStop hooks (Node 16, no dependencies) run all checks and block completion while any fail, listing the failing ids. The final report comes from checker output, not the model's prose.
P2: Slice receipts and fresh-context retries — The parent dispatches slices of item ids to subagents. A subagent's work is accepted only when `unlazy check --ids`, run by the parent in a fresh process, passes. Failed items, with their check output, go to a new subagent. After N rounds the remaining ids are reported as unmet. The parent's state lives in the contract file, so compaction cannot lose it.
P3: Anti-gaming diff scan — When the gate runs, compare against the baseline taken at approval: contract hash changed, test count dropped, new skip/only markers, deleted assertions, edited checks. Also scan added lines for placeholders ("... existing code", "not implemented", empty bodies, TODO stubs). Any hit blocks completion and shows the exact lines, unless the user has approved the change.
