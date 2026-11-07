# Lantern: Pitch & Honest Limits

## The Problem
Most AI teammates in enterprise chat are cloud-bound black boxes. When the office internet flickers, remote connectivity drops, or cloud rate limits bite, the team's AI collaborator goes silent. Worse, users cannot tell whether an answer came from a 400B frontier model or a hallucinating quick-inference endpoint, and when an AI teammate makes a mistake, correcting it in chat rarely sticks.

## The Solution: Lantern
**Lantern is an offline-first AI teammate built on the open-source Switch infrastructure (SandboxAQ) that stays beside your team when the internet goes dark.**

### Why Switch?
SandboxAQ's open-source **Switch** turns chat platforms (like Mattermost) into open collaborative rooms where humans and AI agents interact seamlessly over standard protocols (HTTP and SSE) without vendor lock-in.

### Key Pillars
1. **$0 Stack, True Offline:** Runs 100% locally on standard consumer developer hardware (RTX 4050 / 16GB RAM) using Ollama (`qwen2.5:7b`), Mattermost Team Edition, and Switch Core.
2. **Transparent Brain Tiers:** Every message is tagged with its provenance (`🧠 local · qwen2.5:7b` vs `☁️ gemini`).
3. **Double-Check Verify Queue:** Risky offline advice (commands, numbers, configurations) is served with an upfront warning, queued locally in SQLite, and asynchronously verified when connectivity returns with a thread follow-up.
4. **Auditable, Teachable Rules:** Corrections become drafted rules that require explicit human approval by authorized teammates. Approved rules become atomic Git commits in `lessons/RULES.md` and can be reverted at any time via `forget`.

## Honest Limits
- **Local Model Capacity:** Local 7B models can struggle with complex multi-step reasoning compared to frontier cloud models.
- **Async Verification Window:** If internet connectivity remains down for hours, verification cannot occur until reconnection.
- **Hardware Footprint:** Running Mattermost, Switch, and Ollama together requires ~8-12 GB RAM on the host machine.
