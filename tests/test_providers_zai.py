import json
import os
import pytest
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
