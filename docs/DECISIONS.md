# Decisions log (append only: date, decision, reason, alternative)

| Date | Decision | Reason | Alternative |
|---|---|---|---|
| seed | Integration Mode B (custom Python Agent Protocol service) preferred, Mode A fallback | Full control of tiers and tags | Console agent with OpenCode against Ollama |
| seed | Demo on local Mattermost Team Edition only | True offline needs a local chat server | Slack/Discord need internet |
| seed | Risky answers get an up-front caution line | Verification arrives after the user may act | Verify only |
| seed | One rule per git commit; commit hash stored with rule | Clean `git revert` | Single batched commit |
| seed | Rules live in a delimited prompt block below safety rules | Limits rule-based injection | Raw concatenation |
| seed | Config via `.env` + `config.yaml` | Simple, cross-platform | Env only |
| P0 | **Mode B confirmed** (custom Python service speaking ACP) | ACP is HTTP+SSE, well-documented; Console GUI needed only once for agent registration. Full control of tiers, tags, verify queue. | Mode A (Console agent + proxy) would require OpenCode dependency and give less control |
| P0 | Local model: `qwen2.5:7b` (already pulled, 4.7 GB, fits 6 GB VRAM) | Already present on machine; 7B class appropriate for 15 GB RAM + 6 GB RTX 4050 | phi3:3.8b (smaller but not pre-pulled) |
| P0 | Switch setup via **Switch Console** local-server mode (GUI) | Console bundles Docker orchestration for switch-core + Mattermost; avoids manual compose wrangling | Manual docker-compose with separate switch-core image |
| P0 | Agent registration via Console GUI (one-time), then all runtime via ACP HTTP/SSE | No evidence of a pure-API registration endpoint; GUI step is acceptable | Reverse-engineer API (fragile) |
| P0 | Approvers via config allow-list of Mattermost user IDs | No confirmed Switch roles API; simplest option | Wait for U4 resolution |
| P0 | Corrections posted as new thread replies (not edits) | Agent edit capability is U2/UNKNOWN; thread replies are confirmed | Wait for U2 resolution |
| P1 | Ollama requests set `num_ctx=4096` and `keep_alive=30m` | 6 GB VRAM can't safely exceed 4096 context; 30m keep_alive avoids cold-loading latency during demo | Default context (32k) or short keep_alive |
| P5 | Default Gemini cloud model set to `gemini-3.5-flash` | `gemini-2.0-flash` deprecated by Google on OpenAI endpoint (404); 3.5-flash verified working | gemini-3.8-flash (experiencing 503 high demand) |
| P5 | Implementation handoff recorded | Initial architecture & skeleton by Claude Opus; completed pipeline, commands, verification, rules, and integration by Gemini | N/A |
