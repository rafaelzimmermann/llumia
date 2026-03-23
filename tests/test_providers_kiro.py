import subprocess
import pytest
from providers import ProviderResult
from providers import kiro

_SAMPLE_OUTPUT = (
    "Plan: Q Developer Pro\n"
    "\x1b[32m████████░░\x1b[0m 85%\n"
    "(8.50 of 10.00 covered in plan)\n"
    "Bonus credits: 2.25/5.00 credits used, expires in 15 days\n"
    "Plan resets on 04/30\n"
)


def _fake_run(stdout="", returncode=0):
    class R:
        pass
    r = R()
    r.stdout = stdout
    r.returncode = returncode
    return r


def test_kiro_has_required_constants():
    assert kiro.NAME == "Kiro"
    assert isinstance(kiro.SHORT, str) and kiro.SHORT


def test_fetch_returns_none_when_kiro_cli_missing(monkeypatch):
    """FileNotFoundError → None (kiro-cli not installed)."""
    def raise_fnf(*a, **kw):
        raise FileNotFoundError()
    monkeypatch.setattr(subprocess, "run", raise_fnf)
    kiro._cache["data"] = None
    kiro._cache["ts"] = 0
    assert kiro.fetch() is None


def test_fetch_returns_none_on_timeout(monkeypatch):
    """subprocess.TimeoutExpired → None."""
    def raise_timeout(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="kiro-cli", timeout=20)
    monkeypatch.setattr(subprocess, "run", raise_timeout)
    kiro._cache["data"] = None
    kiro._cache["ts"] = 0
    assert kiro.fetch() is None


def test_fetch_returns_none_on_nonzero_exit(monkeypatch):
    """Non-zero returncode (e.g. auth expired) → None."""
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _fake_run("Error: not authenticated", returncode=1))
    kiro._cache["data"] = None
    kiro._cache["ts"] = 0
    assert kiro.fetch() is None


def test_fetch_parses_pct_from_output(monkeypatch):
    """Parses 85% from sample CLI output."""
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _fake_run(_SAMPLE_OUTPUT))
    kiro._cache["data"] = None
    kiro._cache["ts"] = 0
    result = kiro.fetch()
    assert result is not None
    assert result.pct == 85
    assert result.name == "Kiro"


def test_fetch_strips_ansi_codes(monkeypatch):
    """ANSI escape sequences do not prevent % parsing."""
    output_with_ansi = "\x1b[1m\x1b[32m90%\x1b[0m some text\n"
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _fake_run(output_with_ansi))
    kiro._cache["data"] = None
    kiro._cache["ts"] = 0
    result = kiro.fetch()
    assert result.pct == 90


def test_fetch_returns_zero_pct_on_empty_stdout(monkeypatch):
    """Empty stdout → ProviderResult with pct=0 and reset_secs=0 (not None)."""
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _fake_run(""))
    kiro._cache["data"] = None
    kiro._cache["ts"] = 0
    result = kiro.fetch()
    assert result is not None
    assert result.pct == 0
    assert result.reset_secs == 0


def test_fetch_parses_reset_secs_from_output(monkeypatch):
    """Output with 'resets on MM/DD' → positive reset_secs."""
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _fake_run(_SAMPLE_OUTPUT))
    kiro._cache["data"] = None
    kiro._cache["ts"] = 0
    result = kiro.fetch()
    assert result.reset_secs > 0


def test_fetch_returns_provider_result_type():
    kiro._cache["data"] = ProviderResult(name="Kiro", pct=70, reset_secs=0)
    kiro._cache["ts"] = 9_999_999_999
    result = kiro.fetch()
    assert isinstance(result, ProviderResult)


def test_fetch_cache_ttl_respected():
    sentinel = ProviderResult(name="Kiro", pct=42, reset_secs=0)
    kiro._cache["data"] = sentinel
    kiro._cache["ts"] = 9_999_999_999
    ts_before = kiro._cache["ts"]
    result = kiro.fetch()
    assert result is sentinel
    assert kiro._cache["ts"] == ts_before
