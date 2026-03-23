"""Kiro credit usage via kiro-cli subprocess."""

import re
import subprocess
import time
from datetime import date, datetime
from providers import ProviderResult

NAME = "Kiro"
SHORT = "Ki"

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 60  # 1 minute

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
_PCT_RE = re.compile(r'(\d+)%')
_RESET_RE = re.compile(r'[Rr]eset[s]?\s+(?:on\s+)?(\d{1,2})/(\d{1,2})')


def fetch() -> ProviderResult | None:
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    try:
        proc = subprocess.run(
            ["kiro-cli", "chat", "--no-interactive", "/usage"],
            capture_output=True, text=True, timeout=20,
        )
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None

    if proc.returncode != 0:
        return None

    output = _ANSI_RE.sub('', proc.stdout)

    pct_match = _PCT_RE.search(output)
    pct = min(100, int(pct_match.group(1))) if pct_match else 0

    reset_secs = 0
    reset_match = _RESET_RE.search(output)
    if reset_match:
        month, day = int(reset_match.group(1)), int(reset_match.group(2))
        today = date.today()
        reset_date = date(today.year, month, day)
        if reset_date <= today:
            reset_date = date(today.year + 1, month, day)
        reset_dt = datetime(reset_date.year, reset_date.month, reset_date.day, 0, 0, 0)
        reset_secs = max(0, int(reset_dt.timestamp()) - int(now))

    result = ProviderResult(name=NAME, pct=pct, reset_secs=reset_secs)
    _cache["data"] = result
    _cache["ts"] = now
    return result
