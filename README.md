# 🏮 Lantern

An offline-first AI teammate for team chat via the open-source **Switch** infrastructure ([sandbox-quantum/switch](https://github.com/sandbox-quantum/switch)).

> **Project Brief & Handoff History:**  
> - **Phase 0 Discovery & Foundation:** Completed machine inspection, Switch protocol probing, and core architectural skeleton.  
> - **Opus 4.6 Handoff Point:** Claude Opus 4.6 implemented the initial foundation up through the postprocessor pipeline (`postprocessors.py`), database (`db.py`), brain router (`router.py`), verify worker (`verify.py`), rule store (`rules.py`), and Switch client (`switch_client.py`).  
> - **Continued & Completed Implementation:** Gemini 3.8 Flash resumed directly from `postprocessors.py`, implementing:
>   - Protocol interfaces & pipeline context (`interfaces.py`)
>   - Pluggable extension registry (`registry.py`)
>   - Ping, Status, and Rule command handlers (`addons/ping_cmd.py`, `addons/status_cmd.py`, `addons/rule_cmds.py`)
>   - LLM structured-output Correction Detector (`correction_detector.py`)
>   - System persona & delimited learned-rules prompt assembler (`prompts.py`)
>   - Central message processing pipeline (`engine.py`) and CLI entrypoint (`main.py`)
>   - Preflight diagnostic utility (`scripts/preflight.py`)
>   - 20-question evaluation benchmark and automated scorer (`eval/questions.jsonl`, `eval/score.py`)
>   - Comprehensive unit test suite (`tests/`) and full architecture, pitch, and demo documentation.

---

## 🚀 Key Features

1. **Joins Mattermost via Switch:** Speaks the Switch Agent Client Protocol (HTTP POST upstream, SSE downstream) and replies to mentions, DMs, and active threads.
2. **Transparent Brain Tiers:**
   - 🧠 **Local Tier:** Runs on local Ollama (`qwen2.5:7b`), zero cost, works with network disconnected.
   - ☁️ **Cloud Tier:** Utilizes free OpenAI-compatible cloud models (Gemini, Groq, OpenRouter) with daily quota counters in SQLite and automatic fallback.
   - Every reply is explicitly tagged: `_🧠 local · qwen2.5:7b_` or `_☁️ gemini_`.
3. **Double-Check Verify Queue:**
   - Risky offline advice (commands, numbers, instructions) is flagged with an upfront warning banner and queued in SQLite.
   - When connectivity is restored, an asynchronous judge evaluates the answer and posts a follow-up in the thread (`✅ Verified online` or `⚠️ Correction: ...`).
4. **Teachable Rules with Git Governance:**
   - Corrections or explicit `teach: <rule>` commands create proposed rules.
   - Authorized approvers (matched by platform user ID) approve or reject.
   - Approved rules are committed atomically to `lessons/RULES.md` in Git.
   - `forget <id>` executes a clean `git revert`.
5. **Commands:**
   - `@lantern ping`: Responds `pong`.
   - `status`: Displays network state, active tier, active model, pending verify queue count, cloud usage, and active rule count.
   - `rules`: Lists active and pending learned rules.
   - `teach: <rule>`: Proposes a new guideline.
   - `approve <id>` / `reject <id>` / `forget <id>`: Manages learned rules.

---

## 📦 Directory Structure

```text
d:\project\Lantern
├── .env.example              # Environment variables template
├── pyproject.toml            # Package configuration
├── lantern.db                # SQLite store (queue, quotas)
├── lessons/                  # Git-backed learned rules
│   └── RULES.md
├── src/lantern/
│   ├── config.py             # Settings loader (.env + config.yaml)
│   ├── models.py             # Pydantic data schemas
│   ├── log.py                # Structured JSON logging
│   ├── switch_client.py      # Switch ACP HTTP/SSE client
│   ├── brain.py              # Brain protocol definition
│   ├── router.py             # Tier manager & fallback routing
│   ├── connectivity.py       # Connectivity monitor with hysteresis
│   ├── db.py                 # SQLite database helper
│   ├── verify.py             # Async background verifier
│   ├── rules.py              # Git-backed rule store
│   ├── postprocessors.py     # Provenance, Risk caution, Queueing
│   ├── interfaces.py         # Extension protocols & Ctx
│   ├── registry.py           # Add-on registry
│   ├── correction_detector.py# Structured correction analyzer
│   ├── prompts.py            # System prompt assembler
│   ├── engine.py             # Main processing pipeline
│   ├── main.py               # Application entrypoint
│   └── addons/
│       ├── ollama_brain.py   # Ollama integration
│       ├── cloud_brains.py   # OpenAI-compatible cloud integration
│       ├── ping_cmd.py       # Ping command
│       ├── status_cmd.py     # Status command
│       └── rule_cmds.py      # Rule management commands
├── scripts/
│   └── preflight.py          # Preflight diagnostic checks
├── eval/
│   ├── questions.jsonl       # 20 evaluation benchmark questions
│   └── score.py              # Benchmark execution script
├── tests/                    # Pytest test suite
└── docs/
    ├── ARCHITECTURE.md       # Architecture & Mermaid diagram
    ├── DEMO_SCRIPT.md        # 3-minute live demonstration flow
    ├── PITCH.md              # Project pitch & honest limits
    ├── SWITCH_NOTES.md       # Switch integration facts & protocol reference
    ├── DECISIONS.md          # Architectural decisions log
    └── EXTENSIONS.md         # Add-on extension contract
```

---

## 🛠️ Quick Start

### 1. Python Environment Setup
```powershell
# Create venv and install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in:
```env
SWITCH_CORE_URL=http://localhost:8000
SWITCH_AGENT_API_KEY=<your-agent-key-from-switch-console>
LANTERN_AGENT_NAME=lantern
OLLAMA_URL=http://localhost:11434
LANTERN_LOCAL_MODEL=qwen2.5:7b
LANTERN_APPROVER_IDS=admin_user_id
```

### 3. Run Preflight Checks
```powershell
python scripts/preflight.py
```

### 4. Run Test Suite
```powershell
pytest tests -v
```

### 5. Launch Lantern
```powershell
python -m lantern.main
```

---

## 🔌 Running with Switch & Mattermost
1. Start Docker Desktop.
2. In the `switch` repository:
   ```bash
   just init-env
   just standalone-up
   ```
3. Open Switch Console (`http://localhost:8000`), register agent `lantern`, and copy the API key into `.env`.
4. Open Mattermost (`http://localhost:8065`), create `#lantern-demo`, and mention `@lantern ping`.
