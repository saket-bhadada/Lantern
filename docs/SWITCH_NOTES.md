# Switch notes (Phase 0 — probed 2026-11-07)

Status legend: CONFIRMED = seen in a primary source; UNVERIFIED = secondhand summary; UNKNOWN = must still probe.

## Confirmed facts

| # | Fact | Source |
|---|---|---|
| 1 | Repo: https://github.com/sandbox-quantum/switch. License Apache-2.0 + Commons Clause. | repo README |
| 2 | Agents speak the **Agent Client Protocol (ACP)**: HTTP POST up, SSE/WebSocket down. | repo README + GitHub source (bridges/) |
| 3 | Chat adapters: Slack, Teams, Discord, Telegram, Mattermost. Mattermost adapter uses WebSocket bridge internally. | repo README |
| 4 | Self-host images: `ghcr.io/sandbox-quantum/switch-core`, `ghcr.io/sandbox-quantum/setup`. Health endpoints `/health`, `/health/ready`. | Railway template, repo deploy/ |
| 5 | Dev-mode local setup: `just init-env` → `uv sync` → `just up` (Docker Compose: Postgres + Mattermost) → `just run` (switch-core on :8000). | repo README |
| 6 | Standalone all-Docker: `just standalone-up` uses `deploy/local/` compose file. | repo README |
| 7 | Switch Console desktop app available (Win/Mac/Linux) from GitHub Releases. Bundles `switch-buddy` assistant. Can point at a local server at `http://localhost:8000`. | GitHub Releases page, docs.switchagents.ai |
| 8 | Agents are registered in the Console under **Your Agents**: name (lowercase, hyphens, underscores), description, brief/instructions. Registration generates an **API key**. | docs.switchagents.ai |
| 9 | Agent auth header: `Authorization: ApiKey <key>`. | GitHub source |
| 10 | Downstream events via **SSE stream** (or WebSocket); upstream actions via **HTTP POST** to switch-core. | GitHub source, docs.switchagents.ai |
| 11 | Message envelopes use `BEGIN / END SWITCH MESSAGE` markers with per-message cryptographic nonce (prompt-injection defence). | GitHub source |
| 12 | Agent placement: `POST /agents/{agent_id}/connection/placements` to declare room presence. | GitHub source |
| 13 | Thread replies supported: events carry `thread_id` / `root_id` / `parent_id`; agent can reply in-thread by including them. | GitHub source, web search |
| 14 | switch-core does **not** phone home at startup. Telemetry is **off by default** (`TELEMETRY_ENABLED=false`). No licence-key server. | GitHub repo (env config), web search |
| 15 | Switch supplies no model inference. You bring the agent + model. | flintai.dev listing |
| 16 | Agent has lowercase `name` for routing and optional `display_name`. Mattermost shows display_name only if `TeamSettings.TeammateNameDisplay` ≠ `username`. | repo PR #347 |
| 17 | Docs MCP endpoint: `https://docs.switchagents.ai/mcp` (HTTP transport). | docs.switchagents.ai |

## Still UNKNOWN (will resolve in Phase 1 by running the stack)

| # | Question | Fallback if unanswerable |
|---|---|---|
| U1 | Exact SSE event JSON schema (fields beyond thread_id, root_id, parent_id, sender, text, channel). | Inspect live SSE stream once running. |
| U2 | Can agents **edit** their own messages? | If not: append corrections as new thread replies (acceptable for MVP). |
| U3 | Can agents **add reactions** (emoji)? | If not: use text-based approval ("approve R-007"). |
| U4 | Are there Switch **roles** we can read to identify approvers? | Fallback: allow-list of Mattermost user IDs in config.yaml. |
| U5 | Rate limits or message-size limits on agent sends. | Be conservative (≤4000 chars, ≤1 msg/s). Test in Phase 1. |
| U6 | Can a custom agent be registered purely via API, without the Console GUI? | Fallback: one-time GUI step documented for the user. |

## Source log

| Date | Source | Fact | Command/URL |
|---|---|---|---|
| 2026-11-07 | GitHub repo README | Facts 1-6 | https://github.com/sandbox-quantum/switch |
| 2026-11-07 | docs.switchagents.ai (web search) | Facts 7-8, 10 | site:docs.switchagents.ai search |
| 2026-11-07 | GitHub source / PRs | Facts 9, 11-13, 16 | web search targeting sandbox-quantum/switch |
| 2026-11-07 | GitHub repo env config | Fact 14 | web search for telemetry/offline |
| 2026-11-07 | Railway template / flintai listing | Facts 4, 15 | web search |
| 2026-11-07 | docs.switchagents.ai | Fact 17 | web search for MCP endpoint |
