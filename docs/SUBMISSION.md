# 🏮 Lantern — Hackathon Submission Details

**Event:** WeMakeDevs x DevTools Academy x Switch — "Flip the Switch" Hackathon  
**Submission Date:** November 7, 2026  
**Repository:** [github.com/anirudh-garg/Lantern](https://github.com/anirudh-garg/Lantern)

---

## 📝 150-Word Project Description

Lantern is an offline-first, local-reasoning AI teammate designed to bring reliable, zero-cost intelligence into engineering team chat via Switch. While existing AI assistants fail immediately during internet drops or cloud API outages, Lantern seamlessly transitions between local Ollama (`qwen2.5:7b`) and cloud models, tagging every reply with explicit provenance. When offline, potentially risky advice (destructive commands, configuration parameters) is flagged with an upfront safety caution and queued in SQLite. Once internet connectivity is restored, a background worker automatically verifies the advice with cloud intelligence and posts thread follow-ups. Teammates can teach Lantern project guidelines through natural chat or explicit proposals, which human approvers authorize via platform user IDs to create atomic, auditable Git commits (`lessons/RULES.md`). Through Switch's Agent Client Protocol, Lantern joins existing channels, respects room boundaries, and provides dependable team assistance with no monthly subscription or cloud lock-in.

---

## ⚡ How Switch is Used

Switch is the central nervous system connecting Lantern to human chat environments:
1. **Agent Client Protocol (ACP) Transport:** Lantern operates as an external ACP agent communicating over local HTTP POST (for message delivery and placement) and Server-Sent Events (SSE) on `http://localhost:8000/agents/lantern/events`.
2. **Channel & Room Abstraction:** Switch bridges Mattermost team channels into rooms (`/ops/list_rooms`). Lantern dynamically discovers and claims these rooms upon establishing its SSE connection.
3. **Cryptographic Identity & Security:** Switch ensures messages originate from verified room members. Platform user IDs (`@switch-...-username`) provide the non-spoofable identity tokens Lantern relies upon to enforce approver authorization for learned rules.
4. **Resilient Connection Management:** Lantern maintains an active connection heartbeat (`POST /agents/{name}/connection/beat`) every 8 seconds, ensuring uninterrupted two-way event streaming.

---

## 💻 Tech Stack

- **Switch Core & Gateway:** [sandbox-quantum/switch](https://github.com/sandbox-quantum/switch) (Dockerized on `:8000` and `:3000`)
- **Chat Platform:** Mattermost Team Edition (bundled in Switch Docker compose)
- **Local Brain:** [Ollama](https://ollama.com/) running `qwen2.5:7b` (optimized for 6 GB VRAM GPUs with `num_ctx=4096` and `keep_alive=30m`)
- **Cloud Brain (Free-tier):** Google Gemini `gemini-3.5-flash` via OpenAI-compatible endpoint
- **Application Engine:** Python 3.11+ (`httpx`, `pydantic`, `pytest`, `respx`)
- **Local Storage & Audit:** Python stdlib `sqlite3` (`lantern.db`) + Git CLI (`lessons/RULES.md`)

---

## 🆓 What is 100% Free

- **$0 Compute:** Runs completely on existing consumer hardware (tested on Windows 11 with an NVIDIA RTX 4050 6GB GPU).
- **$0 Inference:** Local reasoning powered by open-weight `qwen2.5:7b` on Ollama.
- **$0 Cloud Keys:** Optional verification and cloud tier utilize free-tier Gemini API keys with zero paid subscriptions.
- **$0 Chat Infrastructure:** Open-source Switch stack and Mattermost Team Edition.

---

## 🔨 What Was Built During the Hackathon

1. **Custom Switch ACP Client (`switch_client.py`):** Full SSE listener, UUID connection management, room discovery, and keep-alive heartbeats.
2. **Tiered Brain Router (`router.py` & `addons/`):** Dynamic failover between local Ollama and cloud endpoints with SQLite daily quota counters.
3. **Connectivity Monitor (`connectivity.py`):** Background DNS probe with hysteresis and `LANTERN_FORCE_OFFLINE` toggle.
4. **Verify Queue & Judge Worker (`verify.py`):** Asynchronous fact-checker that queues risky offline advice and posts in-thread verifications upon reconnect.
5. **Teachable Rule Store (`rules.py` & `addons/rule_cmds.py`):** Natural correction detection, platform approver validation, atomic Git commits, and `git revert` rollback.
6. **Preflight & Benchmark Suite (`scripts/preflight.py`, `eval/`):** Diagnostic verification tool and 20-question technical evaluation harness.

---

## 🚀 Next Steps

1. **Local Channel Document Retrieval:** Augment Ollama with local embeddings over pinned channel documents and READMEs.
2. **Multi-Turn Thread Summarization:** Provide one-click summaries of lengthy offline discussions when disconnected teammates catch up.
3. **Cross-Platform Switch Adapters:** Leverage Switch's multi-bridge architecture to expand Lantern into Slack, Discord, and Telegram without modifying agent core logic.
