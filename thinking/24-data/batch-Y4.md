# Batch

## F26: Built-in sandbox blocks legitimate work

- **id:** F26
- **problem:** Engineers who turn on the agent's built-in sandbox to contain its actions find it blocks ordinary development work: connections to localhost are refused even when listed as allowed, so integration tests against local Docker services fail, and on macOS it breaks TLS verification for Go-based tools such as gh, terraform and kubectl. They must choose between containment and getting the task done, and the sandbox does not honour settings they configured.
- **issues:**
  - anthropics/claude-code#28018 (80)
  - anthropics/claude-code#23416 (70)
- **total_reactions:** 150
- **third_party_solvable:** Engineers can run agents inside their own containers, devcontainers or VMs with network and filesystem policies they control, instead of relying on the built-in sandbox.

## F22: No audit trail of what subagents were told and did

- **id:** F22
- **problem:** Engineers who delegate to multi-agent setups lost the readable record of what the orchestrator sent each subagent once those messages were encrypted. They can no longer audit or debug delegated tasks after the fact, which undermines accountability for multi-agent work.
- **issues:**
  - openai/codex#28058 (152)
- **total_reactions:** 152
- **third_party_solvable:** Hooks or a recording wrapper can log each subagent's task and result into an independent audit trail.

## F18: Cross-repository work in one session

- **id:** F18
- **problem:** Organizations with multi-repository architectures cannot use cloud or app agent sessions for cross-service changes, because a session assumes one repository, one branch and one pull request. Changes that span services, such as shared types or API contracts, must be split by hand into separate sessions and coordinated manually.
- **issues:**
  - anthropics/claude-code#23627 (100)
  - openai/codex#11956 (86)
- **total_reactions:** 186
- **third_party_solvable:** Wrappers can assemble multi-repo workspaces, and orchestrators can coordinate per-repo sessions and linked pull requests.

## F14: Long sessions lose working context at compaction

- **id:** F14
- **problem:** In long, code-heavy sessions, auto-compaction triggers at a fixed threshold without consent and replaces working context with a lossy summary, with no way to restore the detail later, and the pre-compaction conversation cannot be viewed in the UI even though the transcript is on disk. The agent loses details it needed mid-task, and the engineer cannot see what was dropped.
- **issues:**
  - openai/codex#4106 (138)
  - anthropics/claude-code#17428 (117)
  - anthropics/claude-code#27242 (91)
- **total_reactions:** 346
- **third_party_solvable:** Pre-compaction hooks can save state and references to files for later reload, and transcript viewers can browse the full history on disk.

## F10: No visibility or control over where tokens go

- **id:** F10
- **problem:** Engineers paying for heavy agent use cannot see or steer what consumes their tokens: remaining quota and context usage are not shown in the desktop app or exposed to the CLI and scripts, a usage stats panel was removed, background calls such as subagent spinner summaries take an invisible share (about 18% of weighted tokens in one measured session), spend cannot be labelled by team, and model and effort level must be switched by hand per task. They overspend on simple work and hit limits without warning.
- **issues:**
  - anthropics/claude-code#13585 (133)
  - anthropics/claude-code#86879 (121)
  - anthropics/claude-code#102264 (93)
  - anthropics/claude-code#43326 (82)
  - anthropics/claude-code#41456 (71)
  - google-gemini/gemini-cli#12819 (6)
- **total_reactions:** 506
- **third_party_solvable:** Usage trackers that parse local logs or OpenTelemetry data, status-line scripts, request-labelling proxies and model-routing wrappers can provide attribution, budgets and routing without the vendor.

## F06: Reviewing agent changes before they land

- **id:** F06
- **problem:** Engineers who delegate changes need to inspect and accept or reject what the agent wrote, but the IDE surfaces offer no inline per-change review flow and show diffs in different places depending on which internal tool made the edit, so engineers leave the agent panel to diff by hand; the built-in automated review reports only a handful of findings. Changes slip in unreviewed, or problems the review pass could have flagged go unreported.
- **issues:**
  - anthropics/claude-code#33932 (313)
  - openai/codex#2998 (244)
  - openai/codex#5547 (87)
  - anthropics/claude-code#29388 (73)
- **total_reactions:** 717
- **third_party_solvable:** Review tools built on git diffs and staging, and custom review skills or subagents with their own criteria and depth, work independently of the vendor's UI.

## F02: No way back to the state before an agent turn

- **id:** F02
- **problem:** When an agent deletes untracked files or makes unwanted edits, engineers cannot return to the workspace as it was before a given turn: rewinding the conversation does not revert the files, and editing an earlier message does not undo the edits that followed it. Work not yet committed to git can be lost outright, so engineers commit defensively or hesitate to let the agent run.
- **issues:**
  - openai/codex#9203 (547)
  - openai/codex#11626 (231)
  - openai/codex#2948 (85)
  - openai/codex#11086 (84)
- **total_reactions:** 947
- **third_party_solvable:** Hooks or wrappers can snapshot the working tree, untracked files included, before each turn or edit and restore a chosen snapshot together with its point in the conversation.
