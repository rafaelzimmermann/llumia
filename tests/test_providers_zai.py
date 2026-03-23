import json
import os
import pytest
import yaml
from providers import ProviderResult
from providers import zai


def _expanduser_factory(tmp_path):
    """Return a fake expanduser that maps ~ to tmp_path."""
    def fake_expanduser(p):
        if p.startswith("~"):
            return str(tmp_path / p[2:])
        return p
    return fake_expanduser


def test_provider_result_is_dataclass():
    """ProviderResult can be instantiated with required fields."""
    r = ProviderResult(name="Test", pct=42, reset_secs=300)
    assert r.name == "Test"
    assert r.pct == 42
    assert r.reset_secs == 300


def test_zai_has_required_constants():
    """providers.zai exposes NAME and SHORT."""
    assert isinstance(zai.NAME, str) and zai.NAME
    assert isinstance(zai.SHORT, str) and zai.SHORT


def test_zai_fetch_returns_none_without_credentials(tmp_path, monkeypatch):
    """fetch() returns None when no credentials are configured."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    # Invalidate cache
    zai._cache["data"] = None
    zai._cache["ts"] = 0
    result = zai.fetch()
    assert result is None


# ---------------------------------------------------------------------------
# _get_api_key() — credential fallback chain (ported from test_zai_api.py)
# ---------------------------------------------------------------------------

def test_continue_yaml_returns_key(tmp_path, monkeypatch):
    """Finds apiKey from ~/.continue/config.yaml when env and opencode absent."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    zai._cache["data"] = None; zai._cache["ts"] = 0
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: yaml-key\n"
    )
    assert zai._get_api_key() == "yaml-key"


def test_continue_yaml_skips_wrong_provider(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: anthropic\n    apiKey: wrong-key\n"
    )
    assert zai._get_api_key() is None


def test_continue_yaml_skips_empty_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: \"\"\n"
    )
    assert zai._get_api_key() is None


def test_continue_yaml_first_matching_provider_wins(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n"
        "  - provider: anthropic\n    apiKey: wrong\n"
        "  - provider: zAI\n    apiKey: correct-key\n"
        "  - provider: zAI\n    apiKey: second-key\n"
    )
    assert zai._get_api_key() == "correct-key"


def test_continue_yaml_missing_file_falls_through(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    assert zai._get_api_key() is None


def test_continue_json_returns_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        '{"models": [{"provider": "zAI", "apiKey": "json-key"}]}'
    )
    assert zai._get_api_key() == "json-key"


def test_continue_json_skips_wrong_provider(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        '{"models": [{"provider": "openai", "apiKey": "wrong"}]}'
    )
    assert zai._get_api_key() is None


def test_continue_json_skips_empty_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        '{"models": [{"provider": "zAI", "apiKey": ""}]}'
    )
    assert zai._get_api_key() is None


def test_continue_json_missing_file_falls_through(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    assert zai._get_api_key() is None


def test_yaml_takes_priority_over_json(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: yaml-wins\n"
    )
    (cfg_dir / "config.json").write_text(
        '{"models": [{"provider": "zAI", "apiKey": "json-loses"}]}'
    )
    assert zai._get_api_key() == "yaml-wins"


def test_env_var_takes_priority(tmp_path, monkeypatch):
    monkeypatch.setenv("ZAI_API_KEY", "env-key")
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: yaml-key\n"
    )
    assert zai._get_api_key() == "env-key"


def test_opencode_takes_priority_over_continue(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    opencode_dir = tmp_path / ".config" / "opencode"
    opencode_dir.mkdir(parents=True)
    (opencode_dir / "opencode.json").write_text(json.dumps({
        "provider": {"zai-coding-plan": {"options": {"apiKey": "opencode-key"}}}
    }))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: yaml-key\n"
    )
    assert zai._get_api_key() == "opencode-key"


def test_continue_yaml_no_models_key_falls_through(tmp_path, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))
    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text("timeout: 30\n")
    assert zai._get_api_key() is None


# ---------------------------------------------------------------------------
# fetch() — ProviderResult type + caching
# ---------------------------------------------------------------------------

def test_fetch_returns_provider_result_type(monkeypatch):
    """fetch() returns a ProviderResult instance (not a dict) on success."""
    from providers import ProviderResult
    zai._cache["data"] = ProviderResult(name="Z.ai", pct=60, reset_secs=1800)
    zai._cache["ts"] = 9_999_999_999
    result = zai.fetch()
    assert isinstance(result, ProviderResult)
    assert result.name == "Z.ai"


def test_fetch_cache_ttl_respected():
    """A second fetch() within TTL returns the same cached object without updating ts."""
    from providers import ProviderResult
    sentinel = ProviderResult(name="Z.ai", pct=33, reset_secs=500)
    zai._cache["data"] = sentinel
    zai._cache["ts"] = 9_999_999_999
    ts_before = zai._cache["ts"]
    result = zai.fetch()
    assert result is sentinel
    assert zai._cache["ts"] == ts_before  # timestamp must not update on cache hit
