import json
import os
import subprocess
import pytest
from providers import ProviderResult
from providers import claude


def _expanduser_factory(tmp_path):
    def fake_expanduser(p):
        if p.startswith("~"):
            return str(tmp_path / p[2:])
        return p
    return fake_expanduser


def test_claude_has_required_constants():
    assert claude.NAME == "Claude"
    assert claude.SHORT == "C"


def test_get_token_returns_none_without_credentials(tmp_path, monkeypatch):
    """_get_token() returns None when Keychain and credentials file are absent."""
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **kw: type("R", (), {"returncode": 1, "stdout": ""})()
    )
    assert claude._get_token() is None


def test_get_token_reads_credentials_file(tmp_path, monkeypatch):
    """_get_token() falls back to ~/.claude/.credentials.json."""
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **kw: type("R", (), {"returncode": 1, "stdout": ""})()
    )
    creds_dir = tmp_path / ".claude"
    creds_dir.mkdir()
    (creds_dir / ".credentials.json").write_text(
        json.dumps({"claudeAiOauth": {"accessToken": "test-token"}})
    )
    assert claude._get_token() == "test-token"


def test_fetch_returns_none_without_token(tmp_path, monkeypatch):
    """fetch() returns None when _get_token() returns None."""
    monkeypatch.setattr(claude, "_get_token", lambda: None)
    claude._cache["data"] = None
    claude._cache["ts"] = 0
    assert claude.fetch() is None


def test_fetch_returns_provider_result_type(monkeypatch):
    """fetch() returns a ProviderResult instance (not a dict) on success."""
    # Inject a cached result to avoid a real network call
    claude._cache["data"] = ProviderResult(name="Claude", pct=50, reset_secs=3600)
    claude._cache["ts"] = 9_999_999_999  # far future — cache hit guaranteed
    result = claude.fetch()
    assert isinstance(result, ProviderResult)
    assert result.name == "Claude"
    assert result.pct == 50


def test_fetch_cache_ttl_respected(monkeypatch):
    """A second fetch() within TTL returns cached data without updating ts."""
    sentinel = ProviderResult(name="Claude", pct=77, reset_secs=100)
    claude._cache["data"] = sentinel
    claude._cache["ts"] = 9_999_999_999
    ts_before = claude._cache["ts"]
    result = claude.fetch()
    assert result is sentinel  # exact same object, cache not refreshed
    assert claude._cache["ts"] == ts_before  # timestamp must not update on cache hit
