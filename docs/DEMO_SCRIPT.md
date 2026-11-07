# Lantern 3-Minute Live Demo Script

**Environment:** Single laptop running Windows/macOS/Linux. Everything on `localhost` (Mattermost on :8065, Switch on :8000, Ollama on :11434, Lantern in background).
**Preparation:**
- Two browser windows or profiles: **Alice** (teammate/approver) and **Bob** (teammate).
- Channel: `#lantern-demo`.

---

## Act 1: The AI Teammate in the Channel (0:00 - 0:45)
1. **Alice:** `@lantern ping`
   - *Lantern immediately replies:* `pong`
2. **Bob:** `@lantern What is our deployment policy?`
   - *Lantern replies with local brain:*
   - Reply ends with `🧠 local · qwen2.5:7b` (or active cloud if online).

---

## Act 2: Cutting the Wire (0:45 - 1:30)
1. **Presenter:** "Now, let's turn off Wi-Fi (or set `LANTERN_FORCE_OFFLINE=1`)."
2. **Alice:** `@lantern How do I clean all untracked files in git?`
   - *Lantern responds immediately (zero network lag):*
   - Shows caution header:
     `⚠️ This answer is from my local brain and hasn't been verified online yet...`
     `git clean -fd`
     `_🧠 local · qwen2.5:7b_`
   - Notice the answer is flagged as risky and silently queued in `lantern.db`.

---

## Act 3: Returning Online & Self-Verification (1:30 - 2:15)
1. **Presenter:** "We restore the network connection."
2. Within 60 seconds, the background `VerifyWorker` detects internet restoration and contacts a free cloud model to double-check the local advice.
3. *Lantern posts an in-thread reply:*
   - `✅ Verified online — git clean -fd accurately removes untracked files and directories.`
   - Tagged: `_☁️ gemini-2.0-flash_`

---

## Act 4: Teachable Rules with Human Approval (2:15 - 3:00)
1. **Bob:** `Actually Lantern, on our team we never deploy on Fridays after 4 PM.`
2. *Lantern detects the correction via structured schema and posts a proposal:*
   - `💡 I noted your correction and drafted rule R-001:`
   - `> Never deploy code to production on Fridays after 4 PM.`
   - `Approvers can reply approve R-001 or reject R-001.`
3. **Bob:** `approve R-001`
   - *Lantern checks Bob's user ID against approvers:* `⛔ Permission denied: User is not in approver allow-list.`
4. **Alice (Approver):** `approve R-001`
   - *Lantern accepts:* `✅ Approved and committed rule R-001 to lessons/RULES.md`
5. **Presenter opens terminal:**
   - `git log -1` shows the clean atomic commit: `rule: approve R-001 – Never deploy code to production...`
6. **Alice:** `@lantern Can we deploy the fix right now at 4:30 PM on Friday?`
   - *Lantern references the learned rule and advises against it!*
7. **Alice:** `forget R-001`
   - *Lantern runs `git revert` cleanly:* `🧹 Reverted git commit for rule R-001.`
