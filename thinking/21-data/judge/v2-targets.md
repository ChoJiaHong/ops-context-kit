# Targets (real tools released after June 2026)

## blastradius  (heldout)

Problem: I maintain many repositories that share infrastructure artifacts: Docker base images, Terraform modules, GitHub Actions, Helm charts, npm/Python packages. When I ask an agent in one repo to 'bump react to 19' or change a module version, it has no idea which other repos consume the same artifact or how tightly they pin it; a single session cannot see across repository boundaries. Vulnerabilities in pinned versions spread across repos also go unnoticed between sessions.

Core mechanism:
- M1: A persistent cross-repo index of infra/package artifacts (images, TF modules, Actions, Helm charts, packages) with exact version specs and file:line, accumulated from every repo the agent opens, answering 'if I bump this, who breaks?'.
- M2: Push, not pull: a PreToolUse hook on Read/Edit/Bash that touches a manifest injects a terse, ranked (open advisory > breadth > version drift), capped and session-deduplicated list of other-repo consumers and their pins into the agent's context, without the agent calling a tool.
- M3: Extraction is delegated to the model: a Stop hook flags manifests not yet indexed and the agent records dependencies via an MCP tool (no parsers shipped, except lockfiles); a background watcher matches OSV advisories against what each pin can actually resolve to.

Full match: Proposal contains M1 and M2 (cross-repo artifact index AND automatic hook-driven injection when the agent touches a manifest).

Partial match: Proposal contains M1 with only an on-demand query tool, or hook injection of single-repo dependency info.

## cc-projects  (dev)

Problem: A developer runs several Claude Code sessions in parallel on one larger goal. They have to split the goal into tasks by hand, decide which session gets what, keep track of each session's progress, check each result, and stitch the pieces back together. Most of their time goes into coordination rather than the work.

Core mechanism:
- M1: A coordinator agent (one conversation) decomposes the goal and dispatches tasks to separate full sessions running in parallel, instead of the human assigning them.
- M2: Each parallel thread gets its own branch / copy of the repository, and the coordinator checks the threads' results and integrates them back.

Full match: Proposal contains M1 and M2: an agent coordinator that splits work across independent parallel sessions with isolated branches/workspaces, then verifies and merges results.

Partial match: Coordinator that dispatches tasks but no per-thread isolation or result checking; or isolated worktrees per session with human still assigning tasks.

## claude-bouncer  (heldout)

Problem: Claude Code's permission rules judge a shell command by its name, and a name is a bad ID: Bash(grep:*) can't tell an in-repo grep from one reading ~/.aws/credentials, Bash(git push:*) can't tell claude/fix-42 from main, Bash(kubectl:*) can't tell a local kind cluster from the one customers are on. So I either trust every command or answer a prompt every time. Separately, the agent writes commands whose failure reads as success (a test run piped into tail, a gate backgrounded behind an echo) and then reports green.

Core mechanism:
- M1: Fully parse the shell command (shared lexer handling heredocs, command substitution, operators, wrappers like sudo/env/timeout) and judge the arguments against live local context: resolved paths vs workspace root, target branch vs protected branches, kube context/cluster or cloud project vs production (including commands relying on ambient context that could change), exit-status masking via pipes/;/background.
- M2: Three-way routing: stay silent (defer to normal permissions) / 'ask' the human only when intent is genuinely unknowable from the string / 'deny' with the exact rewrite in the reason returned to the model (e.g. add --context prod-us, capture $? and re-raise), so the agent self-corrects without interrupting the human.
- M3: Override 'pass' only as a real inline env-var assignment carrying a reason, which lifts only the verdict it names (e.g. prod deny -> ask), never everything.

Full match: Proposal contains M1 and M2 (argument/context-aware command judging AND deny-with-corrective-rewrite fed back to the agent, reserving human prompts for unknowable intent).

Partial match: Proposal contains M1 only (argument-aware allow/ask/deny), or deny-with-fix messaging on simple prefix matching.

## elephant-goldfish  (heldout)

Problem: When I design a feature spec together with an agent over a long conversation, the resulting document reads perfectly to both of us, yet it is full of assumptions we never wrote down, unclear requirements and risks; implementers (human or agent) trip over them later. I want design documents that hold up once implementation starts.

Core mechanism:
- M1: Split roles by context: the drafter keeps the full project/conversation context, while reviewers are freshly spawned subagents given only the document and its referenced source material, deliberately without the earlier conversation, so unstated assumptions become visible; review is refused if fresh contexts cannot be created.
- M2: Multiple focused fresh reviewers in stages (design soundness, clarity, fit with the code, implementation plan), with the human resolving trade-offs and choosing which findings to address.

Full match: Proposal contains M1 (reviewer deliberately denied the drafting conversation, given only the doc plus referenced sources).

Partial match: Proposal uses a separate reviewer agent or panel but gives it full context, or does not make context removal the point.

## evolveguard  (heldout)

Problem: Claude Agent Skills (SKILL.md, with bundled hook scripts) and Claude Code MEMORY.md files change over time, increasingly edited by the agent itself. An edit can quietly expand what the agent will do when the skill or memory is loaded, and nobody reviews every such edit. I want to catch these regressions before the edit is merged.

Core mechanism:
- M1: Statically derive a 'capability surface' from the skill/memory artifact: declared frontmatter permissions and scopes combined with evidence scanned from the body text and bundled hook scripts (network calls, filesystem writes, write scopes), and record it as a baseline (optionally filtered per labeled fixture prompt).
- M2: On every edit, re-derive the surface with the same logic and diff it against the baseline (per fixture and whole-surface), failing CI on any new or widened capability (e.g. new fs.write, scope ./workspace/** -> ./**, hook gains a network call).

Full match: Proposal contains M1 and M2 (static capability inventory of the skill incl. scripts, baselined and diffed on edit).

Partial match: Proposal diffs only declared frontmatter/permissions, or keyword-scans the edited text for risky patterns without a baseline diff.

## honest-arch-diagrams  (dev)

Problem: Ask an LLM to 'diagram this service' and it draws a Redis, a TLS hop and an auth gateway it never saw. A confident wrong architecture diagram is worse than none. I want agents to produce request-path diagrams of services in our Kubernetes/GitOps/Terraform estate that I can actually trust.

Core mechanism:
- M1: An intermediate renderer-agnostic model in which every hop must carry evidence (a concrete source object such as Ingress/Service/Endpoints), derived by deterministic adapters from real sources (traces > live k8s > declared manifests > OpenAPI, with evidence strength recorded) instead of the LLM's recall.
- M2: A linter gate before rendering that rejects any hop without evidence ('omitted means absent, not guessed'), with a separate visually distinct tier for inferred companions (dashed, evidence on the edge) that may never sit on the verified path.

Full match: Proposal contains M1 and M2 (evidence-carrying model built from real infra sources AND a validation gate that refuses unevidenced hops).

Partial match: Proposal generates diagrams deterministically from manifests/traces without an evidence-required gate, or asks the LLM to cite sources without mechanical rejection.

## k8s-skills  (heldout)

Problem: I want AI agents to help troubleshoot Kubernetes (crashloops, DNS, cert-manager, Flux/Argo, Istio, storage...) on real clusters. Out of the box they guess from memory - docs and training data don't match the error strings the cluster actually prints - investigate in no particular order, and may 'fix' things (delete pods, apply manifests) in the middle of an investigation. Handing an agent cluster credentials feels risky and I can't tell whether its diagnosis is right.

Core mechanism:
- M1: Every command in the skill text is assigned a tier - run freely (read-only verbs), ask first (reversible changes, shown with what changes and an '# Undo:' line), never run (destructive; proposed for the human) - and CI lints the skill text against per-tier allow-lists, requires an undo line for every change and rejects any Secret-reading command.
- M2: Each skill is verified by scenarios that break a throwaway kind cluster on purpose; a fresh agent with only the skill and a view-only kubeconfig must name the cause, cite the evidence and propose an acceptable fix without changing anything; every quoted error string is reproduced on a pinned version.
- M3: The real guarantee is a read-only RBAC identity; a secret-guard hook is a best-effort second layer.

Full match: Proposal contains M1 and M2 (tiered command policy embedded in and CI-checked against the skill content AND break-it scenario tests run by a fresh agent with read-only credentials).

Partial match: Proposal contains only one of M1/M2, or runbook skills plus read-only kubeconfig without tiering or scenario verification.

## openqodex  (heldout)

Problem: My coding agent writes a change and then tells me it is fine. The LLM reviews I have tried report problems that turn out not to exist, silently skip parts of the change, and bury me in scanner noise from code I never touched. I want a review I can trust before the agent pushes.

Core mechanism:
- M1: Reviewer is a separate agent process from the author; finder sessions propose candidate findings each with a quoted code line as evidence, and a script mechanically checks every quote against the actual code (unverifiable candidates dropped).
- M2: Verifier sessions must confirm or refute every candidate and every scanner finding with a reason; scripts check coverage (every changed line assigned to a reviewer, every scanner finding answered) and mark the review 'incomplete' otherwise.
- M3: Scanner findings filtered to changed lines; a push-gate hook requires a passing review of the current work.

Full match: Proposal contains M1 and M2 (independent reviewer with mechanically verified evidence quotes AND verify-every-finding plus coverage accounting).

Partial match: Proposal uses a separate reviewer agent plus scanners and a push gate, but without mechanical evidence checking or coverage accounting.

## squadra  (dev)

Problem: I run several agent windows (Claude Code, Codex, Cursor) on one project at once. Coordination lives in chat memory: who owns which task, whether a window actually received its assignment, which code was really tested, whether the code that got reviewed is the code that shipped, and what I decided and when. Agents reviewing their own work say it is fine, and a context reset or new window loses all of it.

Core mechanism:
- M1: One shared local registry (SQLite, hash-chained append-only events) that every window reads/writes through a CLI: tasks with owner and reviewer, messages requiring explicit ACK before work starts, recorded owner decisions with verbatim words, checkpoints for context handover.
- M2: Proof and review bound to the exact code: the builder runs the agreed check (exact argv) on a frozen candidate whose source fingerprint is recorded; any change after proof invalidates proof and review; review must be by a non-author window, by default of the other model (Claude writes/Codex reads), before the coordinator can close.
- M3: For defect-fix tasks, closure requires showing the same test bytes fail on the base and pass on the candidate.

Full match: Proposal contains M1 and M2 (shared durable registry across sessions AND fingerprint-bound proof with mandatory non-author, preferably cross-model, review).

Partial match: Proposal has a shared task board/registry across sessions without binding proof to exact code, or cross-agent review without a shared durable record.

## stalebrain  (heldout)

Problem: Agents keep 'ignoring the rules' in CLAUDE.md, AGENTS.md, .cursorrules and friends, but half the time the rules are unfollowable: they name paths that moved, scripts that were renamed, a package manager swapped months ago, an owner who left. Fed contradictory memory, the agent is confidently wrong every session, at a token cost paid every session. Across many agents' memory files nobody knows which lines are still true.

Core mechanism:
- M1: Extract memory prose into typed claims (PATH, SCRIPT, SYMBOL, DEP, FACT, OWNER, CONVENTION; opinions skipped), each verified by a type-specific mechanical recipe against the live repo (lockfiles, scripts blocks, CODEOWNERS + git shortlog for owners), with git archaeology to cite the commit that contradicted it and propose the corrected line.
- M2: Provenance stamps (inline invisible 'verified <date>' comments) plus per-claim-type half-life confidence decay: past its half-life a claim is re-verified or downgraded to 'as of <date>'; stamps make re-audits incremental.

Full match: Proposal contains M1 and M2 (typed claim verification against repo/git AND per-claim verification stamps with type-dependent expiry/decay).

Partial match: Proposal contains only M1 (check memory references against the repo) or only M2 (date/expiry metadata on memory entries).

## stop-that-shit  (heldout)

Problem: I ask the agent to export a file and it also writes a SHA-256 nobody reads 'just in case'. I ask for a review and it starts editing; I ask for one fix and it refactors the neighbouring module; it re-runs checks that already answered the question and spawns another agent 'to double-check'. Every time I get annoyed I add another 'don't' to AGENTS.md, and AGENTS.md itself turns into a mess while I still have to babysit the agent.

Core mechanism:
- M1: The user declares a per-task contract on the first line of the prompt: a mode (review/answer/monitor = read-only; change) plus explicit bounds (files=..., deps=allow, hash=allow, agents=N), parsed into session state.
- M2: A pre-tool-call guard enforces only those explicit bounds mechanically: blocks file writes in read-only modes and writes outside the declared file list, blocks subagent launches beyond the budget, blocks recognizable hash/checksum operations unless allowed, asks on dependency additions.
- M3: A skill with an ordered judgement procedure (what is the deliverable -> does existing capability suffice -> what concrete gap remains -> what does each defensive layer actually detect -> is verification done, then stop).

Full match: Proposal contains M1 and M2 (per-task user-declared mode/budget contract enforced by a tool-call hook).

Partial match: Proposal has a hook enforcing a static read-only/write policy not tied to a per-task declaration, or only the instruction/procedure (M3).

## tokeneconomizer  (dev)

Problem: Developers run the same coding agents on the same repositories again and again, and the bill is high. Every turn pays again for the agent's instructions, every loaded tool definition and the conversation so far, and each session behaves as if it had never seen the repository before. We want sessions to get cheaper without hurting task success.

Core mechanism:
- M1: Micro-skills: learn repo facts across sessions from failures that repeat across sessions (and a periodic model review of recent sessions), inject a fact at session start only after it is confirmed in 3 sessions, and drop it when later sessions contradict it.
- M2: Tool pruning: tools unused over p prompts spanning >= m sessions are removed via the agent's own settings deny list, written only after the repo has been idle (cache already expired), with one-command restore.
- M3: Loop guard: learn a per-repo envelope of normal turn length from turns that ended well; when a turn repeats failures, a judge model decides if it is stuck and injects at most one redirect note, then only tells the human how to stop.

Full match: Proposal contains at least two of M1-M3, each driven by evidence accumulated across prior sessions in the same repo.

Partial match: Proposal contains one of M1-M3, or all three as static rules without cross-session learning.

## transcripto  (dev)

Problem: An engineer hands tasks to coding agents (Claude Code, Codex, Cursor) and comes back to a closing message saying the work is done. Sometimes edits silently failed, a command errored, or a result was never produced, but the summary still sounds confident. Reading the whole raw session to find out what really happened takes longer than the task itself.

Core mechanism:
- M1: Reconstruct the session from the transcripts the agents already write (no new instrumentation): request, each tool call, and its recorded result, in order.
- M2: Classify every tool call's outcome (attempt / success / failure / unknown) from the recorded tool results themselves, independently of and without relying on the agent's closing message.

Full match: Proposal contains M1 and M2: reads existing transcripts and labels each action's real outcome from tool results, explicitly not trusting the agent's own summary.

Partial match: Proposal reads existing transcripts to show what happened but does not classify outcomes independent of the agent's claim; or verifies claims by re-running checks rather than from recorded results.

## unlazy  (dev)

Problem: On substantial multi-part work (a refactor with many migration paths, work fanned out to subagents), the agent truncates, partially complies, and then reports 'done' with confidence. Subagents hand back work that the parent accepts on their word. I find out later that several required outcomes were never met.

Core mechanism:
- M1: Write an acceptance ledger before work: each outcome is a gate with a runnable CHECK command and an EXPECT output matcher; a gate passes only on exit 0 AND matched output; recorded evidence is bound to a digest of the gate definition (editing the gate makes evidence stale); the parent re-runs all gates (--reverify) on returned subagent work instead of trusting it.
- M2: A Stop hook that blocks the agent from ending its turn/session while any gate is unmet or a dispatched wave is incomplete, with a progress guard that releases after N blocks without real progress; abandonment is an explicit non-success handoff.
- M3: Parallel leaves must declare disjoint owned paths and claim leases before running; check commands need an approval record keyed to the exact command/cwd/shell/PATH.

Full match: Proposal contains M1 and M2 (machine-checkable acceptance gates written up front AND a stop/exit hook that refuses completion until they pass).

Partial match: Proposal contains M1 without a stop-blocking hook, or a Stop hook keyed to a plain checklist/TODO without executable checks.
