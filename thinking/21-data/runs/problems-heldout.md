# Problems (heldout)

## blastradius

Problem: I maintain many repositories that share infrastructure artifacts: Docker base images, Terraform modules, GitHub Actions, Helm charts, npm/Python packages. When I ask an agent in one repo to 'bump react to 19' or change a module version, it has no idea which other repos consume the same artifact or how tightly they pin it; a single session cannot see across repository boundaries. Vulnerabilities in pinned versions spread across repos also go unnoticed between sessions.

Context: Claude Code hooks (PreToolUse, Stop), MCP server, skills, headless claude -p, OSV.dev advisories. Constraints: everything local (one SQLite file), no account/server/API key; hooks run under a ~5 s timeout; injected context costs tokens every time.

## claude-bouncer

Problem: Claude Code's permission rules judge a shell command by its name, and a name is a bad ID: Bash(grep:*) can't tell an in-repo grep from one reading ~/.aws/credentials, Bash(git push:*) can't tell claude/fix-42 from main, Bash(kubectl:*) can't tell a local kind cluster from the one customers are on. So I either trust every command or answer a prompt every time. Separately, the agent writes commands whose failure reads as success (a test run piped into tail, a gate backgrounded behind an echo) and then reports green.

Context: Claude Code PreToolUse hooks distributed as plugins; kubeconfig, git remotes/branches, terraform/gcloud/aws/helm CLIs, environment. Constraints: no network, no model call, answer from the command string plus local config; must also behave sanely in bypassPermissions mode where nobody answers prompts.

## elephant-goldfish

Problem: When I design a feature spec together with an agent over a long conversation, the resulting document reads perfectly to both of us, yet it is full of assumptions we never wrote down, unclear requirements and risks; implementers (human or agent) trip over them later. I want design documents that hold up once implementation starts.

Context: Coding agents with skills and the ability to spawn subagents (Claude Code, Codex, Antigravity); the project's source code; human approves the final spec.

## evolveguard

Problem: Claude Agent Skills (SKILL.md, with bundled hook scripts) and Claude Code MEMORY.md files change over time, increasingly edited by the agent itself. An edit can quietly expand what the agent will do when the skill or memory is loaded, and nobody reviews every such edit. I want to catch these regressions before the edit is merged.

Context: SKILL.md files with YAML frontmatter (declared tools, network, filesystem, scope, hooks) plus body text and hook scripts; MEMORY.md (no frontmatter); git pre-commit and CI. Constraints: no LLM calls, no live agent run, no hosted infrastructure, no SDK integration, must not execute the skill's scripts; runs offline.

## k8s-skills

Problem: I want AI agents to help troubleshoot Kubernetes (crashloops, DNS, cert-manager, Flux/Argo, Istio, storage...) on real clusters. Out of the box they guess from memory - docs and training data don't match the error strings the cluster actually prints - investigate in no particular order, and may 'fix' things (delete pods, apply manifests) in the middle of an investigation. Handing an agent cluster credentials feels risky and I can't tell whether its diagnosis is right.

Context: Agent Skills (SKILL.md) for Claude Code/Codex/Gemini/Copilot; kubectl, az; Kubernetes RBAC; Claude Code PreToolUse hooks; CI. Constraints: Secrets must never be read; the human applies anything destructive.

## openqodex

Problem: My coding agent writes a change and then tells me it is fine. The LLM reviews I have tried report problems that turn out not to exist, silently skip parts of the change, and bury me in scanner noise from code I never touched. I want a review I can trust before the agent pushes.

Context: Claude Code/Codex on the user's login, Cursor/Cline, git hooks/pre-push, static scanners (gitleaks, semgrep, osv-scanner, kubeconform, checkov...). Constraints: runs locally, no account/API key of its own, no telemetry.

## stalebrain

Problem: Agents keep 'ignoring the rules' in CLAUDE.md, AGENTS.md, .cursorrules and friends, but half the time the rules are unfollowable: they name paths that moved, scripts that were renamed, a package manager swapped months ago, an owner who left. Fed contradictory memory, the agent is confidently wrong every session, at a token cost paid every session. Across many agents' memory files nobody knows which lines are still true.

Context: A git repo with history; memory files for ~13 agents in 18+ locations; Claude Code skills (also a portable pasteable protocol). Constraints: no embeddings, server, database or network; never execute scripts; every edit approved by the human.

## stop-that-shit

Problem: I ask the agent to export a file and it also writes a SHA-256 nobody reads 'just in case'. I ask for a review and it starts editing; I ask for one fix and it refactors the neighbouring module; it re-runs checks that already answered the question and spawns another agent 'to double-check'. Every time I get annoyed I add another 'don't' to AGENTS.md, and AGENTS.md itself turns into a mess while I still have to babysit the agent.

Context: Claude Code, Codex, OpenCode, Pi, Hermes plugins with pre-tool-call hooks and skills; Node 18+. Constraint: necessary work (callers, migrations, tests) must still be done completely; the guard must not decide by keywords that caches/retries/migrations are unnecessary.
