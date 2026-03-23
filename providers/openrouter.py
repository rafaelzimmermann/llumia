"""OpenRouter credit usage via /api/v1/credits."""

import json
import os
import time
import urllib.request
import urllib.error
from providers import ProviderResult

NAME = "OpenRouter"
SHORT = "OR"

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 300  # 5 minutes


def fetch() -> ProviderResult | None:
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {api_key}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception:
        return None

    try:
        total = data["data"]["total_credits"]
        used = data["data"]["usage"]
        pct = min(100, round(used / total * 100)) if total > 0 else 0
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        pct = 0

    result = ProviderResult(name=NAME, pct=pct, reset_secs=0)
    _cache["data"] = result
    _cache["ts"] = now
    return result
