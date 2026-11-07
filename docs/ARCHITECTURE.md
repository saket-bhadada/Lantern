# Lantern Architecture

Lantern is an offline-first AI teammate connecting to team chat via the open-source Switch infrastructure (SandboxAQ).

## System Flow & Components

```mermaid
flowchart TD
    subgraph Chat ["Team Chat Platform"]
        MM["Mattermost Server (:8065)"]
        User["Human Teammate"]
        User <-->|WebSocket / Web UI| MM
    end

    subgraph SwitchInfra ["Switch Control Plane"]
        SC["Switch Core (:8000)"]
        MM <-->|Bridge WebSocket| SC
    end

    subgraph LanternNode ["Lantern Process (Python 3.11+)"]
        Client["SwitchClient\n(SSE downstream, HTTP upstream)"]
        SC -->|SSE /events| Client
        Client -->|HTTP POST /rooms/...| SC

        subgraph CorePipeline ["Event Pipeline"]
            Guard["Guard Filter\n(bot check, allow-list, dedup)"]
            Router["Brain Router & Tier Manager"]
            Commands["Command Handlers\n(ping, status, rules, teach)"]
            Correction["Correction Detector\n(structured schema)"]
            Post["Postprocessors\n(Risk caution, Provenance, Queue)"]
        end

        Client --> Guard
        Guard --> Commands
        Commands -.->|Unhandled| Correction
        Correction -.->|Normal Q&A| Router
        Router --> Post
        Post --> Client

        DB[("SQLite (lantern.db)\n(verify queue & quota counters)")]
        GitStore[("Git Lessons Store\n(lessons/RULES.md)")]

        Router <--> DB
        Commands <--> GitStore
        Post --> DB
    end

    subgraph Models ["Intelligence Backends"]
        Ollama["Local Ollama (:11434)\n(e.g. qwen2.5:7b)"]
        Cloud["Free Cloud Providers\n(Gemini, Groq, OpenRouter)"]
    end

    Router -->|HTTP /api/chat| Ollama
    Router -.->|HTTPS (when online)| Cloud

    subgraph BackgroundWorker ["Verify Worker"]
        VW["VerifyWorker (async)"]
        VW <--> DB
        VW -.->|HTTPS Judge (when online)| Cloud
        VW -->|Thread follow-up| Client
    end
```

## Security & Reliability Design

1. **Untrusted Chat Boundary:** Chat text is untrusted. Lantern contains zero execution shell/tooling triggers.
2. **Deterministic Provenance:** Every response identifies its source: `🧠 local · <model>` or `☁️ <provider>`.
3. **Upfront Caution & Asynchronous Verification:** Local answers containing risky instructions or assertions are flagged with an upfront caution header and queued in SQLite. When internet connectivity returns, the verify worker obtains a second opinion and posts a follow-up in the thread.
4. **Git-Backed Learned Rules:** Learned rules are strictly data, isolated in a delimited prompt section `<LEARNED_RULES>`. Every rule is committed individually to Git with its commit hash, allowing safe, atomic `git revert` via `forget <id>`.
