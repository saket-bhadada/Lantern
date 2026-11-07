# Lantern — Windows Runbook

Verified on Windows 11, Python 3.14, Docker Desktop 29.2.1, Ollama with `qwen2.5:7b`, 6 GB VRAM GPU.

---

## Prerequisites

| Tool | Version tested | Check |
|------|---------------|-------|
| Python | 3.14+ | `python --version` |
| Git | 2.50+ | `git --version` |
| Docker Desktop | 29.2.1 | `docker info` (must show Server section) |
| Ollama | running | `curl http://localhost:11434/api/tags` → lists `qwen2.5:7b` |
| just | 1.40.0 | `$env:LOCALAPPDATA\just\just.exe` |

### `just` Location & Windows PATH Setup

`just.exe` is downloaded directly into:
```
$env:LOCALAPPDATA\just\just.exe
(e.g., C:\Users\<Username>\AppData\Local\just\just.exe)
```

Because `justfile` recipes contain shebangs like `#!/usr/bin/env bash`, you must expose Git Bash utilities (`bash`, `sed`, `grep`, `openssl`) and `just` in your PowerShell session:

```powershell
$env:PATH = "C:\Program Files\Git\bin;C:\Program Files\Git\usr\bin;$env:LOCALAPPDATA\just;$env:PATH"
```

If `just` is not yet present on the machine:

```powershell
# Option A: winget (if available)
winget install Casey.Just

# Option B: direct download without admin (Verified working)
$justDir = "$env:LOCALAPPDATA\just"
New-Item -ItemType Directory -Path $justDir -Force | Out-Null
$zipUrl = "https://github.com/casey/just/releases/download/1.40.0/just-1.40.0-x86_64-pc-windows-msvc.zip"
Invoke-WebRequest -Uri $zipUrl -OutFile "$justDir\just.zip" -UseBasicParsing
Expand-Archive -Path "$justDir\just.zip" -DestinationPath $justDir -Force
Remove-Item "$justDir\just.zip"
```

---

## Step 1: Clone Lantern & set up Python

```powershell
cd d:\Projects\Lantern

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (all 14 should pass)
pytest tests -v
```

## Step 2: Create `.env`

```powershell
Copy-Item .env.example .env
```

Edit `.env` — fill in at minimum:
```
OLLAMA_URL=http://localhost:11434
LANTERN_LOCAL_MODEL=qwen2.5:7b
```

Leave `SWITCH_AGENT_API_KEY`, `LANTERN_APPROVER_IDS`, and cloud API keys blank until Step 5.

## Step 3: Verify Ollama

```powershell
# Check Ollama is running and model is cached
curl http://localhost:11434/api/tags

# If qwen2.5:7b not listed:
ollama pull qwen2.5:7b
```

## Step 4: Run Preflight

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/preflight.py
```

Expected output: Ollama ✅, Switch ⚠️ (not started yet), Mattermost ⚠️ (not started yet), Git ✅, DB ✅, Cloud keys ℹ️ (optional).

## Step 5: Clone & Start Switch + Mattermost

> **Important:** Every `just` command in the Switch repo needs Git Bash on PATH.
> Run this at the start of your PowerShell session:
> ```powershell
> $env:PATH = "C:\Program Files\Git\bin;C:\Program Files\Git\usr\bin;$env:LOCALAPPDATA\just;$env:PATH"
> ```

```powershell
# Clone Switch (one-time, into sibling folder)
git clone https://github.com/sandbox-quantum/switch d:\Projects\switch

# Ensure LF line endings (CRLF breaks Switch's skill frontmatter parser):
cd d:\Projects\switch
git config core.autocrlf false
git config core.eol lf
git checkout .

# Generate .env with random secrets
just init-env
# Records the gateway admin email/password — note it down!

# Start the full stack (Postgres + Mattermost + Switch Core + Gateway)
# First run pulls/builds images (~5-10 min)
just standalone-up
```

Wait for all containers to be healthy:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected services: `postgres`, `init-db` (completed), `mattermost`, `switch`, `gateway`, `setup`.

Verify endpoints:
```powershell
# Switch Core
curl http://localhost:8000/health

# Mattermost
curl http://localhost:8065/api/v4/system/ping
```

## Step 6: Register Lantern Agent (GUI — one-time)

1. Download **Switch Console** from [GitHub Releases](https://github.com/sandbox-quantum/switch/releases/latest/download/switch-console-x64.exe) and install.
2. Open Switch Console → Settings → point at local server `http://localhost:8000`.
3. Log in with the gateway admin credentials from `just init-env` output.
4. Go to **Your Agents** → **Create Agent**.
5. Name: `lantern` (lowercase). Description: "Offline-first AI teammate".
6. Copy the generated **API Key**.
7. Paste it into `d:\Projects\Lantern\.env` as `SWITCH_AGENT_API_KEY=<key>`.

## Step 7: Set Up Mattermost (GUI — one-time)

1. Open browser to `http://localhost:8065`.
2. Log in with the Mattermost admin credentials from `d:\Projects\switch\.env`:
   - Username: value of `MATTERMOST_ADMIN_USER` (default: `admin`)
   - Password: value of `MATTERMOST_ADMIN_PASSWORD`
3. Create channel `#lantern-demo` (Public Channel).
4. Find your Mattermost user ID:
   - Click your avatar → **Profile** → note the URL, it contains the user ID.
   - Or use the API: `curl http://localhost:8065/api/v4/users/me -H "Authorization: Bearer <token>"`
5. Paste user ID into `d:\Projects\Lantern\.env` as `LANTERN_APPROVER_IDS=<user_id>`.

## Step 8: Launch Lantern

```powershell
cd d:\Projects\Lantern
.\.venv\Scripts\Activate.ps1
python -m lantern.main
```

## Step 9: Test in Mattermost

> **Crucial Switch Architecture Detail:**
> Switch's Mattermost bridge runs under the `admin` account and contains a loop-prevention filter (`mattermost/adapter.py:2815`):
> `if user_id in self._bridge_bot_ids or user_id == self._admin_user_id: return`
> Because of this, Switch **completely ignores** messages sent by the `admin` user!
> To chat with `@lantern`, you must log in as a regular team member, NOT `admin`.

1. Open an Incognito / Private browser window (or log out of `admin`) at `http://localhost:8065`.
2. Log in as the regular user:
   - **Username:** `user`
   - **Password:** value of `MATTERMOST_USER_PASSWORD` in `d:\Projects\switch\.env` (or see below)
3. Join `#lantern-demo`.
4. In `#lantern-demo`, type: `@lantern ping`
   - Expected: Lantern replies `pong`
5. Ask a real question: `@lantern What are the guidelines for deploying to staging vs production?`
   - Expected: Answer tagged `_🧠 local · qwen2.5:7b_` (or cloud model if configured)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `@lantern` does not reply in Mattermost | Check who you are logged in as! Switch's Mattermost bridge intentionally ignores posts by `admin` (`user_id == self._admin_user_id`) to avoid bot feedback loops. Open an Incognito window and log in as `user` (password in `d:\Projects\switch\.env`). |
| `CatalogError: Connection airtable SKILL.md needs frontmatter` | Windows Git converted files to CRLF. Run `git config core.autocrlf false; git config core.eol lf; git checkout .` in `d:\Projects\switch` and rebuild image. |
| `just` shebang error "cannot find file" | Add Git Bash to PATH: `$env:PATH = "C:\Program Files\Git\bin;C:\Program Files\Git\usr\bin;$env:PATH"` |
| `just init-env` says ".env already exists" | Delete `d:\Projects\switch\.env` first, then rerun |
| `just standalone-up` fails with `SWITCH_VERSION required` | Ensure `SWITCH_VERSION=latest` is in `d:\Projects\switch\.env` |
| Docker build OOM / slow | Close other apps. Building from source needs ~4 GB RAM for Docker. |
| Mattermost image fails to pull | It's `linux/amd64` only — Docker Desktop emulates on ARM. May be slow. |
| Ollama "model not found" | Run `ollama pull qwen2.5:7b` |
| Ollama slow first response (~16s) | Model cold-loading. `keep_alive=30m` keeps it hot for 30 min after first query. |
| Preflight says Switch not reachable | Ensure `just standalone-up` completed and `docker ps` shows `switch` healthy. |
| `pip install` exit code 1 but says "Successfully installed" | Harmless — stderr from pip update notice triggers non-zero exit in PowerShell. |
| Tests show DeprecationWarnings about `asyncio.get_event_loop_policy` | Python 3.14 deprecation in pytest-asyncio — safe to ignore, all tests pass. |
| Gateway admin password lost | Check `d:\Projects\switch\.env` for `GATEWAY_ADMIN_PASSWORD` |
| Mattermost admin password lost | Check `d:\Projects\switch\.env` for `MATTERMOST_ADMIN_PASSWORD` |
| `num_ctx` / VRAM issues | Lantern sets `num_ctx=4096` (safe for 6 GB VRAM). Don't increase without more VRAM. |
| Port conflict on 8000/8065/5432 | Edit the `*_HOST_PORT` vars in `d:\Projects\switch\.env` |

