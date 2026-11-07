# 🏮 Lantern — 3-Minute Live Demonstration Script

**Test Environment:** Windows / macOS / Linux with Switch local stack on `:8000`, Mattermost on `:8065`, and local Ollama (`qwen2.5:7b`) on `:11434`.

> **Note on Accounts:** Log in to Mattermost (`http://localhost:8065`) as user `user` (password from `switch/.env`: `MATTERMOST_USER_PASSWORD`). Switch's Mattermost bridge intentionally ignores messages from `admin` to avoid recursion loops.

---

## 🎬 Act 1: The AI Teammate in the Channel (0:00 – 0:45)

**Context:** The team uses Mattermost bridged via Switch. Lantern is listening in `#lantern-demo`.

1. **User sends in `#lantern-demo`:**
   ```text
   @lantern ping
   ```
   *Expected reply:*
   ```text
   pong
   ```

2. **User checks system status:**
   ```text
   @lantern status
   ```
   *Expected reply:*
   ```text
   **Lantern Status**
   - **Network:** online
   - **Active Tier:** cloud
   - **Active Model:** `gemini-3.5-flash`
   - **Verify Queue Length:** 0 pending
   - **Cloud Usage Today:** gemini: 1
   - **Active Rules:** 0
   ```

3. **User asks a normal question:**
   ```text
   @lantern What are the advantages of an offline-first architecture?
   ```
   *Expected reply:* Fast, structured answer ending with provenance tag:
   ```text
   ...
   _☁️ gemini-3.5-flash_
   ```

---

## 🔌 Act 2: Cutting the Wire (0:45 – 1:30)

**Context:** Simulating an internet outage or deep offline development. Turn off Wi-Fi or set `LANTERN_FORCE_OFFLINE=1` in `.env`.

1. **User asks a technical/risky question offline:**
   ```text
   @lantern How do I discard all untracked files in git?
   ```
   *Expected reply:* Lantern detects destructive git commands (`git clean -fd`), prepends an immediate safety banner, answers via local Ollama, and silently queues the answer in SQLite for later cloud verification:
   ```text
   ⚠️ _This answer is from my local brain and hasn't been verified online yet. Double-check before acting on it._

   To discard all untracked files in git, run:
   ```bash
   git clean -fd
   ```
   _🧠 local · qwen2.5:7b_
   ```

2. **User checks queue status:**
   ```text
   @lantern status
   ```
   *Expected reply:*
   ```text
   **Lantern Status**
   - **Network:** offline
   - **Active Tier:** local
   - **Active Model:** `qwen2.5:7b`
   - **Verify Queue Length:** 1 pending
   - ...
   ```

---

## 🌐 Act 3: Returning Online & Automatic Verification (1:30 – 2:15)

**Context:** Network connection is restored (turn Wi-Fi back on or set `LANTERN_FORCE_OFFLINE=0`).

1. **Wait for background `VerifyWorker` (~15-30s):**
   The worker detects online connectivity, dequeues the pending item, runs the fact-checking judge prompt through `gemini-3.5-flash`, and posts an automatic in-thread follow-up.

2. **Expected in-thread follow-up from Lantern:**
   ```text
   ✅ Verified online — git clean -fd accurately removes untracked files and directories.

   _☁️ gemini-3.5-flash_
   ```

---

## 🛡️ Act 4: Teachable Rules & Git Governance (2:15 – 3:00)

**Context:** The team establishes a new operating rule directly in chat, governed by human approver permissions and backed by an atomic Git commit audit trail.

1. **User proposes a team rule:**
   ```text
   @lantern teach: Never deploy code to production on Friday after 4 PM
   ```
   *Expected reply:*
   ```text
   📝 Proposed rule **R-001**:
   > Never deploy code to production on Friday after 4 PM

   Approvers can reply `approve R-001` or `reject R-001`.
   ```

2. **User (authorized approver) approves the rule:**
   ```text
   @lantern approve R-001
   ```
   *Expected reply:*
   ```text
   ✅ Approved and committed rule **R-001** to `lessons/RULES.md`:
   > Never deploy code to production on Friday after 4 PM
   ```

3. **Switch to terminal to show the proof (for judges):**
   ```powershell
   git log -1 --stat
   ```
   *Shows atomic commit:*
   ```text
   commit a856cf4...
   Author: AG <...>
   Date:   Sat Nov 7 2026
       rule: approve R-001 – Never deploy code to production on Friday after 4 PM
   lessons/RULES.md | 1 +
   ```

4. **Verify team memory:**
   ```text
   @lantern rules
   ```
   *Expected reply:*
   ```text
   **Active Learned Rules:**
   - **[R-001]** Never deploy code to production on Friday after 4 PM
   ```

5. **Clean rollback (Forget rule):**
   ```text
   @lantern forget R-001
   ```
   *Expected reply:*
   ```text
   🧹 Reverted git commit for rule R-001.
   ```
   *(Running `git log -1` in terminal shows the clean `git revert` commit)*
