import io
import json
import os
import urllib.request
import pytest
from providers import ProviderResult
from providers import openrouter


def _fake_urlopen(data: dict):
    """Return a fake urlopen that yields the given dict as JSON."""
    class Ctx:
        def __enter__(self):
            return io.BytesIO(json.dumps(data).encode())
        def __exit__(self, *a):
            pass
    return lambda *a, **kw: Ctx()


def test_openrouter_has_required_constants():
    assert openrouter.NAME == "OpenRouter"
    assert isinstance(openrouter.SHORT, str) and openrouter.SHORT


def test_fetch_returns_none_without_api_key(monkeypatch):
    """fetch() returns None when OPENROUTER_API_KEY is not set."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    openrouter._cache["data"] = None
    openrouter._cache["ts"] = 0
    assert openrouter.fetch() is None


def test_fetch_calculates_pct_correctly(monkeypatch):
    """pct = round(usage / total_credits * 100); result.name == NAME."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    openrouter._cache["data"] = None
    openrouter._cache["ts"] = 0
    fake = {"data": {"total_credits": 100.0, "usage": 45.0}}
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
    result = openrouter.fetch()
    assert result is not None
    assert result.pct == 45
    assert result.name == "OpenRouter"


def test_fetch_caps_pct_at_100(monkeypatch):
    """Usage exceeding credits is capped at 100%."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    openrouter._cache["data"] = None
    openrouter._cache["ts"] = 0
    fake = {"data": {"total_credits": 10.0, "usage": 15.0}}
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
    result = openrouter.fetch()
    assert result.pct == 100


def test_fetch_returns_zero_pct_when_no_credits(monkeypatch):
    """total_credits=0 returns pct=0 without crashing."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    openrouter._cache["data"] = None
    openrouter._cache["ts"] = 0
    fake = {"data": {"total_credits": 0.0, "usage": 0.0}}
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
    result = openrouter.fetch()
    assert result.pct == 0


def test_reset_secs_is_zero(monkeypatch):
    """reset_secs is always 0 for OpenRouter (prepaid credits, no reset window)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    openrouter._cache["data"] = None
    openrouter._cache["ts"] = 0
    fake = {"data": {"total_credits": 100.0, "usage": 50.0}}
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
    result = openrouter.fetch()
    assert result.reset_secs == 0


def test_fetch_returns_provider_result_type():
    """Cache hit returns a ProviderResult instance."""
    openrouter._cache["data"] = ProviderResult(name="OpenRouter", pct=50, reset_secs=0)
    openrouter._cache["ts"] = 9_999_999_999
    result = openrouter.fetch()
    assert isinstance(result, ProviderResult)
    assert result.pct == 50


def test_fetch_cache_ttl_respected():
    """Second fetch() within TTL returns same object; _cache['ts'] unchanged."""
    sentinel = ProviderResult(name="OpenRouter", pct=30, reset_secs=0)
    openrouter._cache["data"] = sentinel
    openrouter._cache["ts"] = 9_999_999_999
    ts_before = openrouter._cache["ts"]
    result = openrouter.fetch()
    assert result is sentinel
    assert openrouter._cache["ts"] == ts_before


def test_fetch_populates_cache_on_success(monkeypatch):
    """After a successful fetch, _cache['data'] is set."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    openrouter._cache["data"] = None
    openrouter._cache["ts"] = 0
    fake = {"data": {"total_credits": 100.0, "usage": 20.0}}
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
    openrouter.fetch()
    assert openrouter._cache["data"] is not None
