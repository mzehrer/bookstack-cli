"""Configuration loader for BookStack connection settings.

Config file: ~/.config/bookstack-cli/config.toml

```toml
[connection]
url = "http://10.0.0.1:8080"              # API endpoint (internal)
resolve_url = "https://wiki.example.com"  # Public web URL (optional, falls back to url)
token_id = "<your-token-id>"
token_secret = "<your-token-secret>"
```

Env vars override file values:
- BOOKSTACK_URL
- BOOKSTACK_RESOLVE_URL
- BOOKSTACK_TOKEN_ID
- BOOKSTACK_TOKEN_SECRET
"""

import os
import tomllib
from pathlib import Path
from typing import NamedTuple

from bookstack_cli.exceptions import BookStackConfigError


class BookStackConfig(NamedTuple):
    """Connection configuration for a BookStack instance."""

    url: str
    token_id: str
    token_secret: str
    resolve_url: str | None = None


CONFIG_DIR = Path.home() / ".config" / "bookstack-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def _load_env() -> BookStackConfig | None:
    """Load config from environment variables."""
    url = os.environ.get("BOOKSTACK_URL")
    token_id = os.environ.get("BOOKSTACK_TOKEN_ID")
    token_secret = os.environ.get("BOOKSTACK_TOKEN_SECRET")
    if url and token_id and token_secret:
        resolve_url = os.environ.get("BOOKSTACK_RESOLVE_URL") or url
        return BookStackConfig(
            url=url.rstrip("/"),
            token_id=token_id,
            token_secret=token_secret,
            resolve_url=resolve_url.rstrip("/"),
        )
    return None


def _load_toml() -> BookStackConfig | None:
    """Load config from ~/.config/bookstack-cli/config.toml."""
    if not CONFIG_FILE.exists():
        return None
    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)
    conn = data.get("connection", {})
    url = conn.get("url")
    token_id = conn.get("token_id")
    token_secret = conn.get("token_secret")
    if url and token_id and token_secret:
        resolve_url = conn.get("resolve_url") or url
        return BookStackConfig(
            url=url.rstrip("/"),
            token_id=token_id,
            token_secret=token_secret,
            resolve_url=resolve_url.rstrip("/"),
        )
    return None


def get_config() -> BookStackConfig:
    """Load config from env vars (priority) or TOML file.

    Precedence:
    1. BOOKSTACK_URL, BOOKSTACK_RESOLVE_URL, BOOKSTACK_TOKEN_ID,
       BOOKSTACK_TOKEN_SECRET env vars
    2. ~/.config/bookstack-cli/config.toml

    Raises BookStackConfigError if neither source has complete config.
    """
    env_cfg = _load_env()
    if env_cfg:
        return env_cfg

    toml_cfg = _load_toml()
    if toml_cfg:
        return toml_cfg

    raise BookStackConfigError(
        "BookStack config not found. "
        "Run `bookstack auth` or set BOOKSTACK_URL, BOOKSTACK_TOKEN_ID, "
        "BOOKSTACK_TOKEN_SECRET env vars."
    )


def save_config(url: str, token_id: str, token_secret: str, resolve_url: str | None = None) -> Path:
    """Save connection to ~/.config/bookstack-cli/config.toml.

    Creates parent directories if needed.
    Returns the path to the written file.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        '[connection]',
        f'url = "{_escape_toml(url.rstrip("/"))}"',
    ]
    if resolve_url:
        lines.append(f'resolve_url = "{_escape_toml(resolve_url.rstrip("/"))}"')
    lines.extend([
        f'token_id = "{_escape_toml(token_id)}"',
        f'token_secret = "{_escape_toml(token_secret)}"',
    ])
    CONFIG_FILE.write_text("\n".join(lines) + "\n")
    return CONFIG_FILE


def _escape_toml(value: str) -> str:
    """Escape special chars for TOML basic string."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
