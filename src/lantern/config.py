"""Lantern – configuration loader.

Reads .env (via python-dotenv) then overlays config.yaml if present.
All config is exposed as a single frozen Settings object.
"""

from __future__ import annotations

import os
import pathlib
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load_env() -> None:
    """Load .env from project root (if it exists)."""
    env_path = _PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def _load_yaml() -> dict[str, Any]:
    """Load config.yaml from project root (if it exists)."""
    cfg_path = _PROJECT_ROOT / "config.yaml"
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


class CloudProvider(BaseModel):
    name: str
    base_url: str
    api_key_env: str = ""
    model: str = ""
    daily_limit: int = 50

    @property
    def api_key(self) -> str:
        if self.api_key_env:
            return os.getenv(self.api_key_env, "")
        return ""


_DEFAULT_CLOUD_PROVIDERS = [
    CloudProvider(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key_env="GEMINI_API_KEY",
        model="gemini-2.0-flash",
        daily_limit=50,
    ),
    CloudProvider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        model="llama-3.3-70b-versatile",
        daily_limit=30,
    ),
    CloudProvider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        model="meta-llama/llama-3.3-70b-instruct:free",
        daily_limit=30,
    ),
]


class Settings(BaseModel):
    """Immutable app settings – built once at startup."""

    # Switch / Mattermost
    switch_core_url: str = "http://localhost:8000"
    switch_agent_api_key: str = ""
    agent_name: str = "lantern"

    # Ollama
    ollama_url: str = "http://localhost:11434"
    local_model: str = "qwen2.5:7b"

    # Cloud
    cloud_providers: list[CloudProvider] = Field(
        default_factory=lambda: list(_DEFAULT_CLOUD_PROVIDERS)
    )

    # Behaviour
    force_offline: bool = False
    allowed_channels: list[str] = Field(default_factory=list)
    approver_ids: list[str] = Field(default_factory=list)

    # Paths
    db_path: str = "lantern.db"
    lessons_dir: str = "lessons"

    # Tunables
    max_reply_len: int = 4000
    send_rate_limit: float = 1.0   # seconds between sends
    verify_rate_limit: float = 10.0  # seconds between verify checks
    rule_token_cap: int = 2000     # max total chars for injected rules


def load_settings() -> Settings:
    """Build settings from env + yaml, env taking precedence."""
    _load_env()
    yaml_cfg = _load_yaml()

    def _env(key: str, default: str = "") -> str:
        return os.getenv(key, default)

    def _env_bool(key: str, default: bool = False) -> bool:
        v = os.getenv(key, "")
        if v == "":
            return default
        return v.strip().lower() in ("1", "true", "yes")

    def _csv(key: str) -> list[str]:
        raw = os.getenv(key, "")
        return [x.strip() for x in raw.split(",") if x.strip()]

    # Build cloud providers from yaml if present
    cloud_providers = list(_DEFAULT_CLOUD_PROVIDERS)
    if "cloud_providers" in yaml_cfg:
        cloud_providers = [CloudProvider(**cp) for cp in yaml_cfg["cloud_providers"]]

    return Settings(
        switch_core_url=_env("SWITCH_CORE_URL", "http://localhost:8000"),
        switch_agent_api_key=_env("SWITCH_AGENT_API_KEY"),
        agent_name=_env("LANTERN_AGENT_NAME", "lantern"),
        ollama_url=_env("OLLAMA_URL", "http://localhost:11434"),
        local_model=_env("LANTERN_LOCAL_MODEL", "qwen2.5:7b"),
        cloud_providers=cloud_providers,
        force_offline=_env_bool("LANTERN_FORCE_OFFLINE"),
        allowed_channels=_csv("LANTERN_ALLOWED_CHANNELS"),
        approver_ids=_csv("LANTERN_APPROVER_IDS"),
        db_path=_env("LANTERN_DB_PATH", "lantern.db"),
        lessons_dir=_env("LANTERN_LESSONS_DIR", "lessons"),
    )
