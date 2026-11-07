# Problems (dev)

## cc-projects

Problem: A developer runs several Claude Code sessions in parallel on one larger goal. They have to split the goal into tasks by hand, decide which session gets what, keep track of each session's progress, check each result, and stitch the pieces back together. Most of their time goes into coordination rather than the work.

Context: Claude Code with cloud sessions; each session can work on a repository, run tests and open pull requests. Subscription usage limits apply.

## honest-arch-diagrams

Problem: Ask an LLM to 'diagram this service' and it draws a Redis, a TLS hop and an auth gateway it never saw. A confident wrong architecture diagram is worse than none. I want agents to produce request-path diagrams of services in our Kubernetes/GitOps/Terraform estate that I can actually trust.

Context: Agent skills (Claude Code, Cursor, Gemini CLI, Copilot); available sources: kubectl JSON dumps, GitOps/Helm manifests, docker-compose, terraform show -json, OpenAPI specs, OpenTelemetry traces. Constraint: zero-dependency Node CLI; never emit secret values.

## squadra

Problem: I run several agent windows (Claude Code, Codex, Cursor) on one project at once. Coordination lives in chat memory: who owns which task, whether a window actually received its assignment, which code was really tested, whether the code that got reviewed is the code that shipped, and what I decided and when. Agents reviewing their own work say it is fine, and a context reset or new window loses all of it.

Context: Multiple Claude Code/Codex/interactive Cursor sessions, each possibly in its own git checkout of the same project; transcripts on disk; Python stdlib only; local machine, no account. Constraints: Codex sandbox cannot discover/wake Claude windows; Cursor never launched automatically; nothing published automatically.

## termaxa

Problem: I let coding agents (Claude Code, Codex, Cursor, Copilot CLI) run shell commands with approvals off or barely watched. The damage is rarely an attack; it is an ordinary chore done with the most forceful spelling: rm -rf to clean up, git push --force, git reset --hard to 'undo my last commit' (19 of 36 models in one benchmark destroyed uncommitted work in a file nobody mentioned), DROP TABLE. Approving every command defeats the point of an agent; trusting it blindly works until uncommitted work, remote commits or table rows are gone.

Context: Agent hook paths (Claude Code PreToolUse on Bash and write tools; Codex/Cursor/Copilot hooks), git, psql, terraform, kubectl, docker. Constraints: single local binary, no model, no service, no account; must work unattended (agent approvals off); policy must be reviewable in the repo; hooks advise, they are not a sandbox.

## tokeneconomizer

Problem: Developers run the same coding agents on the same repositories again and again, and the bill is high. Every turn pays again for the agent's instructions, every loaded tool definition and the conversation so far, and each session behaves as if it had never seen the repository before. We want sessions to get cheaper without hurting task success.

Context: Claude Code, Codex, Copilot CLI, Pi plugins (session/prompt/tool hooks, agent settings files, transcripts with usage); the agent's own login for any model calls. Constraints: black box - cannot change the agent's model, weights or code; no API key of its own; every action reversible; must never stop a turn itself; cost counted with cache pricing including its own calls.

## transcripto

Problem: An engineer hands tasks to coding agents (Claude Code, Codex, Cursor) and comes back to a closing message saying the work is done. Sometimes edits silently failed, a command errored, or a result was never produced, but the summary still sounds confident. Reading the whole raw session to find out what really happened takes longer than the task itself.

Context: Agents already write local session transcripts (e.g. ~/.claude/projects JSONL, Codex and Cursor session files). Must run locally, no accounts, no extra runtime dependencies, should work across several agent harnesses.

## unlazy

Problem: On substantial multi-part work (a refactor with many migration paths, work fanned out to subagents), the agent truncates, partially complies, and then reports 'done' with confidence. Subagents hand back work that the parent accepts on their word. I find out later that several required outcomes were never met.

Context: Claude Code skills and hooks, Codex skills, parallel subagents/fresh contexts, shell. Constraints: Node 16+ with no runtime dependencies; hooks installed only with user consent; checks run with ambient access (no sandbox).
