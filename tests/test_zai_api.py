import os
import pytest
import zai_api


def _expanduser_factory(tmp_path):
    """Return a fake expanduser that maps ~ to tmp_path."""
    def fake_expanduser(p):
        if p.startswith("~"):
            return str(tmp_path / p[2:])  # strip "~/"
        return p
    return fake_expanduser


# ---------------------------------------------------------------------------
# Continue.dev YAML fallback
# ---------------------------------------------------------------------------

def test_continue_yaml_returns_key(tmp_path, monkeypatch):
    """Finds apiKey from ~/.continue/config.yaml when env and opencode absent."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: yaml-key\n"
    )

    assert zai_api._get_api_key() == "yaml-key"


def test_continue_yaml_skips_wrong_provider(tmp_path, monkeypatch):
    """Ignores models with a different provider."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: anthropic\n    apiKey: wrong-key\n"
    )

    assert zai_api._get_api_key() is None


def test_continue_yaml_skips_empty_key(tmp_path, monkeypatch):
    """Treats empty apiKey as absent."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: \"\"\n"
    )

    assert zai_api._get_api_key() is None


def test_continue_yaml_first_matching_provider_wins(tmp_path, monkeypatch):
    """Returns the first model entry whose provider is zAI."""
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

    assert zai_api._get_api_key() == "correct-key"


def test_continue_yaml_missing_file_falls_through(tmp_path, monkeypatch):
    """Missing config.yaml does not raise; returns None."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    assert zai_api._get_api_key() is None


# ---------------------------------------------------------------------------
# Continue.dev JSON fallback
# ---------------------------------------------------------------------------

def test_continue_json_returns_key(tmp_path, monkeypatch):
    """Finds apiKey from ~/.continue/config.json when yaml absent."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        '{"models": [{"provider": "zAI", "apiKey": "json-key"}]}'
    )

    assert zai_api._get_api_key() == "json-key"


def test_continue_json_skips_wrong_provider(tmp_path, monkeypatch):
    """Ignores models with a different provider in config.json."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        '{"models": [{"provider": "openai", "apiKey": "wrong"}]}'
    )

    assert zai_api._get_api_key() is None


def test_continue_json_skips_empty_key(tmp_path, monkeypatch):
    """Treats empty apiKey as absent in config.json."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        '{"models": [{"provider": "zAI", "apiKey": ""}]}'
    )

    assert zai_api._get_api_key() is None


def test_continue_json_missing_file_falls_through(tmp_path, monkeypatch):
    """Missing config.json does not raise; returns None."""
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    assert zai_api._get_api_key() is None


def test_yaml_takes_priority_over_json(tmp_path, monkeypatch):
    """config.yaml is checked before config.json."""
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

    assert zai_api._get_api_key() == "yaml-wins"


# ---------------------------------------------------------------------------
# Priority order: env var > opencode > yaml > json
# ---------------------------------------------------------------------------

def test_env_var_takes_priority(tmp_path, monkeypatch):
    """ZAI_API_KEY env var wins over all file-based sources."""
    monkeypatch.setenv("ZAI_API_KEY", "env-key")
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: yaml-key\n"
    )

    assert zai_api._get_api_key() == "env-key"


def test_opencode_takes_priority_over_continue(tmp_path, monkeypatch):
    """opencode.json wins over Continue.dev files."""
    import json as _json
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(os.path, "expanduser", _expanduser_factory(tmp_path))

    opencode_dir = tmp_path / ".config" / "opencode"
    opencode_dir.mkdir(parents=True)
    (opencode_dir / "opencode.json").write_text(_json.dumps({
        "provider": {
            "zai-coding-plan": {
                "options": {"apiKey": "opencode-key"}
            }
        }
    }))

    cfg_dir = tmp_path / ".continue"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "models:\n  - provider: zAI\n    apiKey: yaml-key\n"
    )

    assert zai_api._get_api_key() == "opencode-key"
