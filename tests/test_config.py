"""Tests for config loading — env vars, TOML file, error cases."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bookstack_cli.config import (
    CONFIG_DIR,
    CONFIG_FILE,
    BookStackConfig,
    get_config,
    save_config,
)
from bookstack_cli.exceptions import BookStackConfigError


def _write_toml(path: Path, url: str, token_id: str, token_secret: str) -> None:
    """Helper to write a valid TOML config file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '[connection]\n'
        f'url = "{url}"\n'
        f'token_id = "{token_id}"\n'
        f'token_secret = "{token_secret}"\n'
    )


class TestLoadEnv:
    """Environment variable loading."""

    def test_returns_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("BOOKSTACK_URL", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_ID", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_SECRET", raising=False)
        from bookstack_cli.config import _load_env

        assert _load_env() is None

    def test_returns_none_when_partial(self, monkeypatch):
        monkeypatch.setenv("BOOKSTACK_URL", "http://test.local")
        monkeypatch.delenv("BOOKSTACK_TOKEN_ID", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_SECRET", raising=False)
        from bookstack_cli.config import _load_env

        assert _load_env() is None

    def test_returns_config_when_all_set(self, monkeypatch):
        monkeypatch.setenv("BOOKSTACK_URL", "http://test.local/")
        monkeypatch.setenv("BOOKSTACK_TOKEN_ID", "tid123")
        monkeypatch.setenv("BOOKSTACK_TOKEN_SECRET", "ts456")
        from bookstack_cli.config import _load_env

        cfg = _load_env()
        assert cfg is not None
        assert cfg.url == "http://test.local"  # trailing slash stripped
        assert cfg.token_id == "tid123"
        assert cfg.token_secret == "ts456"


class TestLoadToml:
    """TOML config file loading."""

    def test_returns_none_when_file_missing(self, monkeypatch):
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", Path("/nonexistent/bookstack/config.toml"))
        from bookstack_cli.config import _load_toml

        assert _load_toml() is None

    def test_returns_config_when_file_valid(self, monkeypatch, tmp_path):
        cfg_file = tmp_path / "config.toml"
        _write_toml(cfg_file, "http://toml.local/", "tid_toml", "ts_toml")
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)
        from bookstack_cli.config import _load_toml

        cfg = _load_toml()
        assert cfg is not None
        assert cfg.url == "http://toml.local"
        assert cfg.token_id == "tid_toml"
        assert cfg.token_secret == "ts_toml"

    def test_returns_none_when_missing_keys(self, monkeypatch, tmp_path):
        """Partial TOML returns None."""
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text('[connection]\nurl = "http://x.local"\n')
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)
        from bookstack_cli.config import _load_toml

        assert _load_toml() is None


class TestGetConfig:
    """Config cascade logic."""

    def test_env_overrides_toml(self, monkeypatch, tmp_path):
        """get_config returns env config even when TOML exists."""
        monkeypatch.setenv("BOOKSTACK_URL", "http://env.local")
        monkeypatch.setenv("BOOKSTACK_TOKEN_ID", "tid_env")
        monkeypatch.setenv("BOOKSTACK_TOKEN_SECRET", "ts_env")

        cfg_file = tmp_path / "config.toml"
        _write_toml(cfg_file, "http://toml.local", "tid_toml", "ts_toml")
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)

        cfg = get_config()
        assert cfg.url == "http://env.local"
        assert cfg.token_id == "tid_env"

    def test_falls_back_to_toml_when_env_missing(self, monkeypatch, tmp_path):
        """When env vars absent, TOML file is used."""
        monkeypatch.delenv("BOOKSTACK_URL", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_ID", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_SECRET", raising=False)

        cfg_file = tmp_path / "config.toml"
        _write_toml(cfg_file, "http://toml.local", "tid_toml", "ts_toml")
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)

        cfg = get_config()
        assert cfg.url == "http://toml.local"
        assert cfg.token_id == "tid_toml"

    def test_raises_when_nothing_set(self, monkeypatch):
        monkeypatch.delenv("BOOKSTACK_URL", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_ID", raising=False)
        monkeypatch.delenv("BOOKSTACK_TOKEN_SECRET", raising=False)
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", Path("/nonexistent/other/config.toml"))

        with pytest.raises(BookStackConfigError, match="not found"):
            get_config()


class TestSaveConfig:
    """Writing config to TOML."""

    def test_saves_to_file(self, monkeypatch, tmp_path):
        cfg_file = tmp_path / "config.toml"
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)
        monkeypatch.setattr("bookstack_cli.config.CONFIG_DIR", cfg_file.parent)

        result = save_config("http://saved.local/", "tid_save", "ts_save")

        assert result == cfg_file
        assert cfg_file.exists()
        import tomllib

        raw = tomllib.loads(cfg_file.read_text())
        assert raw["connection"]["url"] == "http://saved.local"
        assert raw["connection"]["token_id"] == "tid_save"
        assert raw["connection"]["token_secret"] == "ts_save"

    def test_trailing_slash_stripped(self, monkeypatch, tmp_path):
        cfg_file = tmp_path / "config.toml"
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)
        monkeypatch.setattr("bookstack_cli.config.CONFIG_DIR", cfg_file.parent)

        save_config("http://saved.local///", "t", "s")
        import tomllib

        raw = tomllib.loads(cfg_file.read_text())
        assert raw["connection"]["url"] == "http://saved.local"

    def test_creates_parent_directory(self, monkeypatch, tmp_path):
        """Parent dir is created if it doesn't exist."""
        cfg_file = tmp_path / "sub" / "config.toml"
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)
        monkeypatch.setattr("bookstack_cli.config.CONFIG_DIR", cfg_file.parent)

        save_config("http://saved.local", "t", "s")
        assert cfg_file.exists()

    def test_escape_special_chars(self, monkeypatch, tmp_path):
        """TOML special chars in values are escaped."""
        cfg_file = tmp_path / "config.toml"
        monkeypatch.setattr("bookstack_cli.config.CONFIG_FILE", cfg_file)
        monkeypatch.setattr("bookstack_cli.config.CONFIG_DIR", cfg_file.parent)

        secret = 'abc"def\\ghi\njkl\tmno'
        save_config("http://local", "tid", secret)
        raw = cfg_file.read_text()
        # Verify backslash, quote, newline, tab are escaped in output
        assert '\\\\' in raw or "\\n" in raw or '\\"' in raw
        # Verify it reads back correctly
        import tomllib

        data = tomllib.loads(raw)
        assert data["connection"]["token_secret"] == secret
