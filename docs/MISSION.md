# Mission: Lantern

Hackathon problem: use the open-source Switch infrastructure to connect an AI agent into team chat so it joins channels like any teammate.

**Pitch:** Lantern is the AI teammate that keeps working when the internet goes dark, shows which brain answered, double-checks itself when the network returns, and learns from corrections only with human approval.

Hard constraints: software cost $0; core features work with no internet.

## Features (MVP)
1. **Joins Mattermost via Switch** under its own name. Replies when @mentioned, DM'd, or in a thread it already took part in.
2. **Brain tiers.** Local Ollama always available; free OpenAI-compatible cloud models only when online. Every reply ends with a provenance tag: `🧠 local · <model>` or `☁️ <provider>`.
3. **Verify-later queue.** A 🧠 answer containing factual claims, numbers, or instructions is queued. When online, a cloud model re-checks it and Lantern replies in the thread: `✅ Verified online` or `⚠️ Correction: ...`.
4. **Teachable.** A human correction (thread reply or `teach: <rule>`) becomes a drafted one-line rule. An approver replies `approve R-007` / `reject R-007`. Approved rules are committed to `lessons/RULES.md` in git and injected into every prompt. `forget R-007` reverts that rule's commit.
5. **`status`** command: tier, online/offline, model, queue length, cloud usage today, active rules.

## Improvements over the original draft (see docs/ANALYSIS.md)
- Risky-answer warning shown up front, not only after verification (a wrong `git reset --hard` tip has already been used by then).
- Verify queue prioritises answers with commands, numbers, or destructive actions; trivial chat is not queued.
- Offline means the whole stack is local: Mattermost, Switch, Ollama on one laptop. Images and models are pre-pulled.
- Rules are scoped (channel/team), size-capped, de-duplicated, and stored with the commit hash so `forget` is a precise revert.
- A small evaluation set (`eval/questions.jsonl`) measures local vs cloud answer quality so claims are backed by numbers.
- A recorded backup demo video in case the live demo fails.

## Acceptance criteria per phase
- P1: `@lantern ping` in #lantern-demo returns `pong`. Evidence: screenshot or REST API output.
- P2: with internet off, a question returns a 🧠-tagged answer. Ollama down gives a friendly message.
- P3: force offline, answer is queued; go online, follow-up appears within 60 s. Tests cover state transitions, quotas, fallbacks.
- P4: correction, proposal, approval, git log entry, next answer follows the rule, forget undoes it.
- P5: preflight passes; 3-minute demo script rehearsed twice; docs complete.

## Cloud providers (ordered in config; free tiers change, so verify at build time)
Gemini `https://generativelanguage.googleapis.com/v1beta/openai/`, Groq `https://api.groq.com/openai/v1`, OpenRouter `:free` models `https://openrouter.ai/api/v1`. Conservative daily counters in SQLite, honour 429/Retry-After, fall through, then local-only.
