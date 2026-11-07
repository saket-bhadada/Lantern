"""Lantern – Preflight verification script (Phase 5).

Checks:
1. Ollama reachable and local model cached
2. Switch core reachable
3. Mattermost reachable
4. Git repository status
5. Optional cloud API keys
6. Database initialization
"""

from __future__ import annotations

import os
import subprocess
import sys
import httpx

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lantern.config import load_settings
from lantern.db import Database


def check_ollama(settings) -> bool:
    print("Checking Ollama server...", end=" ", flush=True)
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{settings.ollama_url}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                target = settings.local_model
                has_model = any(target in m for m in models)
                if has_model:
                    print(f"[OK] ({target} available)")
                    return True
                else:
                    print(f"[WARN] Ollama is up, but {target} is NOT cached. Available: {models}")
                    print(f"   Run: ollama pull {target}")
                    return False
    except Exception as exc:
        print(f"[FAIL] ({exc})")
        print(f"   Ensure Ollama is running at {settings.ollama_url}")
        return False
    return False


def check_switch(settings) -> bool:
    print("Checking Switch Core...", end=" ", flush=True)
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{settings.switch_core_url}/health")
            if resp.status_code == 200:
                print(f"[OK] (status: {resp.status_code})")
                return True
            else:
                print(f"[WARN] Switch returned status {resp.status_code}")
                return False
    except Exception:
        print(f"[WARN] Switch Core not reachable at {settings.switch_core_url} (Phase 1 container pending)")
        return False


def check_mattermost() -> bool:
    print("Checking Mattermost...", end=" ", flush=True)
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get("http://localhost:8065/api/v4/system/ping")
            if resp.status_code == 200:
                print("[OK]")
                return True
            else:
                print(f"[WARN] Mattermost returned status {resp.status_code}")
                return False
    except Exception:
        print("[WARN] Mattermost not reachable at http://localhost:8065 (Phase 1 container pending)")
        return False


def check_git() -> bool:
    print("Checking Git status...", end=" ", flush=True)
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if res.returncode == 0:
            print("[OK]")
            return True
        else:
            print("[WARN] Git command returned error")
            return False
    except Exception as exc:
        print(f"[FAIL] Git check failed: {exc}")
        return False


def check_cloud_keys(settings) -> None:
    print("Checking optional cloud keys:")
    for p in settings.cloud_providers:
        status = "configured [OK]" if p.api_key else "missing (offline fallback active) [INFO]"
        print(f"  - {p.name}: {status}")


def check_db(settings) -> bool:
    print("Checking SQLite database...", end=" ", flush=True)
    try:
        db = Database(settings.db_path)
        q_len = db.queue_length()
        print(f"[OK] (queue length: {q_len})")
        return True
    except Exception as exc:
        print(f"[FAIL] ({exc})")
        return False


def main() -> None:
    print("=" * 60)
    print("Lantern AI Teammate - Preflight Checks")
    print("=" * 60)
    settings = load_settings()

    ok_ollama = check_ollama(settings)
    ok_switch = check_switch(settings)
    ok_mm = check_mattermost()
    ok_git = check_git()
    ok_db = check_db(settings)
    check_cloud_keys(settings)

    print("=" * 60)
    if ok_ollama and ok_db:
        print("[READY] Ready for offline operations! (Ollama + local state OK)")
    else:
        print("[WARN] Prerequisites need attention before offline demo.")
    print("=" * 60)


if __name__ == "__main__":
    main()
