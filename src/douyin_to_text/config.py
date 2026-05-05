"""Lightweight local config: persist DASHSCOPE_API_KEY across sessions.

Stored at ~/.douyin-to-text/config.json (Windows: %USERPROFILE%\\.douyin-to-text\\).
Plain JSON — same posture as gh / git / npm tokens. We chmod 0600 on POSIX.
"""

from __future__ import annotations

import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".douyin-to-text"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def get_saved_api_key() -> str:
    return load_config().get("dashscope_api_key", "")


def save_api_key(key: str) -> Path:
    """Persist the key, returns the file path so callers can show it."""
    key = (key or "").strip()
    cfg = load_config()
    if key:
        cfg["dashscope_api_key"] = key
    else:
        cfg.pop("dashscope_api_key", None)
    save_config(cfg)
    return CONFIG_FILE
