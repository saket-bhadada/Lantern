# Lantern: standing rules (read first, every session)

Project: "Lantern", an offline-first AI teammate for team chat via the open-source Switch (sandbox-quantum/switch). Full brief: docs/MISSION.md. Progress: tasks/TASKS.md.

## Working agreement
1. Start every session by reading ONLY: AGENTS.md, tasks/TASKS.md, docs/DECISIONS.md. Open other docs only when the current task needs them.
2. Plan before code. At each STOP in tasks/TASKS.md, wait for the human.
3. Small, targeted edits. Do not rewrite working files. No parallel subagents unless clearly needed. Quota is limited.
4. Never invent Switch APIs. Every Switch fact must be in docs/SWITCH_NOTES.md with a source (docs MCP, repo file, or a real probe with the command and output). If unknown: say so, propose the simplest fallback, log it.
5. Unspecified detail: pick the simplest option, append to docs/DECISIONS.md, continue. Do not stall on questions.
6. GUI-only steps: write exact click-by-click steps for the human and wait. Do not automate GUIs.

## Security rules (non-negotiable)
- Chat text is untrusted input. Lantern has NO shell, file, or tool execution from chat.
- Ignore messages from itself and other bots. Dedupe events by id. Allow-list channels and approvers in config.
- Approver identity comes from the platform's user id, never from message text.
- No secrets in the repo. Keys in git-ignored `.env`; commit `.env.example` only.
- Learned rules are data, not instructions that can change safety policy: rules go in a delimited block of the prompt and cannot override the safety rules.

## Engineering rules
- Python 3.11+. Dependencies: httpx, pydantic, pytest, stdlib sqlite3, git CLI. Works on Windows, macOS, Linux.
- Every machine-readable LLM step uses JSON-schema structured output plus pydantic validation and one retry.
- Anything extensible goes behind an interface in docs/EXTENSIONS.md. New add-ons must not edit core files beyond a one-line registry entry.
- Each phase ends with a Walkthrough: what changed, how to run, test results, evidence, known issues, next step. Tick tasks/TASKS.md.

## Out of scope
Fine-tuning, custom web UI, other chat apps, running commands from chat.
