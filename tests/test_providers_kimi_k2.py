import io
import json
import os
import urllib.request
import pytest
from providers import ProviderResult
from providers import kimi_k2


def _fake_urlopen(data: dict):
    class Ctx:
        def __enter__(self):
            return io.BytesIO(json.dumps(data).encode())
        def __exit__(self, *a):
            pass
    return lambda *a, **kw: Ctx()


def _usage_response(used=25000, limit=50000, reset_time="2099-12-31T00:00:00Z"):
    return {
        "usages": [{
            "scope": "FEATURE_CODING",
            "detail": {
                "limits": [{"detail": limit}],
                "used": used,
                "resetTime": reset_time,
            }
        }]
    }


def test_kimi_k2_has_required_constants():
    assert kimi_k2.NAME == "Kimi K2"
    assert isinstance(kimi_k2.SHORT, str) and kimi_k2.SHORT


def test_fetch_returns_none_without_token(monkeypatch):
    """fetch() returns None when KIMI_AUTH_TOKEN is not set."""
    monkeypatch.delenv("KIMI_AUTH_TOKEN", raising=False)
    kimi_k2._cache["data"] = None
    kimi_k2._cache["ts"] = 0
    assert kimi_k2.fetch() is None


def test_fetch_calculates_pct_correctly(monkeypatch):
    """pct = round(used / limit * 100); reset_secs derived from resetTime."""
    monkeypatch.setenv("KIMI_AUTH_TOKEN", "test-jwt")
    kimi_k2._cache["data"] = None
    kimi_k2._cache["ts"] = 0
    monkeypatch.setattr(urllib.request, "urlopen",
                        _fake_urlopen(_usage_response(used=25000, limit=50000)))
    result = kimi_k2.fetch()
    assert result is not None
    assert result.pct == 50
    assert result.reset_secs > 0  # reset_time is far in the future


def test_fetch_returns_zero_on_parse_failure(monkeypatch):
    """Malformed response does not crash; pct=0."""
    monkeypatch.setenv("KIMI_AUTH_TOKEN", "test-jwt")
    kimi_k2._cache["data"] = None
    kimi_k2._cache["ts"] = 0
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen({"bad": "data"}))
    result = kimi_k2.fetch()
    assert result is not None
    assert result.pct == 0


def test_fetch_handles_missing_reset_time(monkeypatch):
    """Missing resetTime → reset_secs=0; pct still computed correctly."""
    monkeypatch.setenv("KIMI_AUTH_TOKEN", "test-jwt")
    kimi_k2._cache["data"] = None
    kimi_k2._cache["ts"] = 0
    data = {
        "usages": [{
            "scope": "FEATURE_CODING",
            "detail": {
                "limits": [{"detail": 50000}],
                "used": 10000,
                # no resetTime
            }
        }]
    }
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(data))
    result = kimi_k2.fetch()
    assert result is not None
    assert result.pct == 20
    assert result.reset_secs == 0


def test_fetch_returns_provider_result_type():
    """Cache hit returns a ProviderResult instance."""
    kimi_k2._cache["data"] = ProviderResult(name="Kimi K2", pct=40, reset_secs=3600)
    kimi_k2._cache["ts"] = 9_999_999_999
    result = kimi_k2.fetch()
    assert isinstance(result, ProviderResult)


def test_fetch_cache_ttl_respected():
    """Second fetch() within TTL returns same object; ts unchanged."""
    sentinel = ProviderResult(name="Kimi K2", pct=60, reset_secs=100)
    kimi_k2._cache["data"] = sentinel
    kimi_k2._cache["ts"] = 9_999_999_999
    ts_before = kimi_k2._cache["ts"]
    result = kimi_k2.fetch()
    assert result is sentinel
    assert kimi_k2._cache["ts"] == ts_before
