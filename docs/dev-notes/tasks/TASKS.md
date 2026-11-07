# Tasks (agent: tick boxes, add evidence links, never delete history)

## Phase 0: Discovery  [STOP after]
- [x] Machine inspection (OS: Windows 11, RAM: 15.3GB, GPU: RTX 4050 6GB, Docker Desktop: installed, Python 3.14, git 2.50, `ollama list`: qwen2.5:7b) and local model recommendation (`qwen2.5:7b`, configurable via `LANTERN_LOCAL_MODEL`)
- [x] Probe Switch docs via MCP/README; fill UNKNOWN list in [docs/SWITCH_NOTES.md](file:///d:/project/Lantern/docs/SWITCH_NOTES.md) with sources
- [x] Choose Mode A or B, log in [docs/DECISIONS.md](file:///d:/project/Lantern/docs/DECISIONS.md) (Mode B custom Python ACP confirmed)
- [x] Plan, risk list, exact human steps (commands + GUI clicks in artifact `phase0-plan.md`)

## Phase 1: Walking skeleton  [STOP after]
- [x] Mattermost Team Edition + Switch local via Docker Compose (Stack running and healthy on :8000 and :8065)
- [x] Lantern client, ACP SSE/HTTP adapter, ping/pong command handler & pipeline built: [src/lantern/addons/ping_cmd.py](file:///d:/project/Lantern/src/lantern/addons/ping_cmd.py), [tests/test_commands.py](file:///d:/project/Lantern/tests/test_commands.py)
- [x] Live reply `pong` verified in #lantern-demo against running Docker stack (Tested with live SSE & Mattermost bridge)

## Phase 2: Local brain
- [x] Interfaces + models + registry: [docs/EXTENSIONS.md](file:///d:/project/Lantern/docs/EXTENSIONS.md), [src/lantern/brain.py](file:///d:/project/Lantern/src/lantern/brain.py), [src/lantern/interfaces.py](file:///d:/project/Lantern/src/lantern/interfaces.py), [src/lantern/registry.py](file:///d:/project/Lantern/src/lantern/registry.py)
- [x] Ollama brain, timeouts, retries, friendly down-message: [src/lantern/addons/ollama_brain.py](file:///d:/project/Lantern/src/lantern/addons/ollama_brain.py)
- [x] Provenance postprocessor (`🧠 local · <model>`): [src/lantern/postprocessors.py](file:///d:/project/Lantern/src/lantern/postprocessors.py), tested in [tests/test_postprocessors.py](file:///d:/project/Lantern/tests/test_postprocessors.py)

## Phase 3: Tiers, connectivity, verify queue
- [x] Connectivity monitor with hysteresis + LANTERN_FORCE_OFFLINE: [src/lantern/connectivity.py](file:///d:/project/Lantern/src/lantern/connectivity.py)
- [x] Cloud brains with SQLite quota counters, 429/Retry-After, fallthrough: [src/lantern/addons/cloud_brains.py](file:///d:/project/Lantern/src/lantern/addons/cloud_brains.py), [src/lantern/router.py](file:///d:/project/Lantern/src/lantern/router.py), [src/lantern/db.py](file:///d:/project/Lantern/src/lantern/db.py)
- [x] Verify queue + judge schema + thread follow-up; risk caution line: [src/lantern/verify.py](file:///d:/project/Lantern/src/lantern/verify.py), [src/lantern/postprocessors.py](file:///d:/project/Lantern/src/lantern/postprocessors.py)
- [x] `status` command; tests for transitions, quotas, fallbacks: [src/lantern/addons/status_cmd.py](file:///d:/project/Lantern/src/lantern/addons/status_cmd.py), [tests/test_router.py](file:///d:/project/Lantern/tests/test_router.py), [tests/test_db.py](file:///d:/project/Lantern/tests/test_db.py)

## Phase 4: Teachable rules
- [x] Correction detector (schema) + `teach:` command: [src/lantern/correction_detector.py](file:///d:/project/Lantern/src/lantern/correction_detector.py), [src/lantern/addons/rule_cmds.py](file:///d:/project/Lantern/src/lantern/addons/rule_cmds.py)
- [x] Proposal, approve/reject by platform user id: [src/lantern/rules.py](file:///d:/project/Lantern/src/lantern/rules.py), [src/lantern/addons/rule_cmds.py](file:///d:/project/Lantern/src/lantern/addons/rule_cmds.py)
- [x] Git-backed RULES.md, one rule per commit, dedupe, token cap, scope: [src/lantern/rules.py](file:///d:/project/Lantern/src/lantern/rules.py), tested in [tests/test_rules.py](file:///d:/project/Lantern/tests/test_rules.py)
- [x] `forget`, `rules`; tests for file/commit logic: [tests/test_rules.py](file:///d:/project/Lantern/tests/test_rules.py) (All passed ✅)

## Phase 5: Demo hardening
- [x] scripts/preflight.py: [scripts/preflight.py](file:///d:/project/Lantern/scripts/preflight.py) (Tested and passing ✅)
- [x] eval/questions.jsonl (20 Qs) + scoring script: [eval/questions.jsonl](file:///d:/project/Lantern/eval/questions.jsonl), [eval/score.py](file:///d:/project/Lantern/eval/score.py)
- [x] Structured JSON logs: [src/lantern/log.py](file:///d:/project/Lantern/src/lantern/log.py)
- [x] docs/ARCHITECTURE.md (Mermaid), DEMO_SCRIPT.md (3 min), PITCH.md, README: [docs/ARCHITECTURE.md](file:///d:/project/Lantern/docs/ARCHITECTURE.md), [docs/DEMO_SCRIPT.md](file:///d:/project/Lantern/docs/DEMO_SCRIPT.md), [docs/PITCH.md](file:///d:/project/Lantern/docs/PITCH.md), [README.md](file:///d:/project/Lantern/README.md)
- [ ] Rehearse twice; record backup demo video (Human step during live rehearsal)

## Add-ons (post-MVP; see docs/ANALYSIS.md)
- [ ] Document Q&A (local retrieval over channel pinned files)
- [ ] Multi-turn thread summarization
