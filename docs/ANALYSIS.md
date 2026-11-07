# Analysis and suggestions

## Strengths
- Offline-first is a real differentiator; most entries will call a cloud API.
- Provenance tag + later verification is an honest, easy-to-demo story.
- Approval-gated, git-backed rules give auditability and reversal.

## Risks and fixes
| # | Risk | Fix |
|---|---|---|
| 1 | Slack/Discord need internet, so "offline" is false there | Demo on local Mattermost only; say so in the pitch |
| 2 | Switch is built around coding agents on an owner's machine; a non-coding custom agent may not fit cleanly | Phase 0 must check the Agent Protocol docs. Fallback is Mode A (Console agent running OpenCode against Ollama) |
| 3 | First Switch local-server start reportedly downloads a few GB (source: ai-tldr.dev summary, unverified) | Run it once online beforehand; preflight warns if images are not cached |
| 4 | "₹0" ignores hardware | Say "software cost $0"; name target RAM and model |
| 5 | Wrong 🧠 answer is acted on before verification | Up-front caution line on risky answers; queue risky ones first |
| 6 | Verifier model can be wrong and free tiers rate-limit | Judge returns a verdict plus reason; show it as "second opinion"; cap per provider |
| 7 | Prompt injection via rules or chat text | Rules in a delimited block; safety rules outrank them; approvers by platform user id; length cap; reject rules containing URLs or tool-like instructions |
| 8 | `git revert` can conflict when rules edit the same file | One rule per commit, store commit hash in the rule record, serialize writes with a lock |
| 9 | No quality evidence | `eval/questions.jsonl` with 20 questions; script scores local vs cloud |
| 10 | Live Wi-Fi cut can fail on stage | Use `LANTERN_FORCE_OFFLINE=1` as the fallback and keep a recorded video |

## Suggested add-ons (post-MVP, each fits docs/EXTENSIONS.md)
- Document Q&A: local retrieval over a channel's pinned files (stays offline).
- Notice/announcement templates with a rule-aware style guide.
- Multilingual replies (Hindi/English) using a local model.
- Confidence self-rating shown next to the tag.
- Weekly digest of corrections and approved rules posted to the channel.
- Streamed replies via message edits, if Phase 0 shows agents can edit.

## Scope advice
Build in this order: ping, local brain, rules, verify queue. If time is short, cut verification before cutting rules, since rules are the more visual demo.
