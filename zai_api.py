"""Z.ai quota usage via monitor API."""

import json
import os
import time
import urllib.request
import urllib.error

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 60  # 1 minute


def _get_api_key() -> str | None:
    key = os.environ.get("ZAI_API_KEY")
    if key:
        return key
    config_path = os.path.expanduser("~/.config/opencode/opencode.json")
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        return cfg["provider"]["zai-coding-plan"]["options"]["apiKey"]
    except Exception:
        return None


def fetch() -> dict | None:
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    api_key = _get_api_key()
    if not api_key:
        return None

    req = urllib.request.Request(
        "https://api.z.ai/api/monitor/usage/quota/limit",
        headers={
            "Authorization": api_key,
            "Accept-Language": "en-US,en",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception:
        return None

    try:
        pct = round(data["tokenUsagePercentage"] * 100)
    except (KeyError, TypeError, ValueError):
        pct = 0

    try:
        remaining = data["remainingQuota"]  # raw token count
        remaining_m = round(remaining / 1_000_000, 1)
    except (KeyError, TypeError, ValueError):
        remaining_m = None

    try:
        reset_ms = int(data["nextResetTime"])
        reset_secs = max(0, reset_ms // 1000 - int(now))
    except (KeyError, TypeError, ValueError):
        reset_secs = 0

    result = {"pct": pct, "remaining_m": remaining_m, "reset_secs": reset_secs}
    _cache["data"] = result
    _cache["ts"] = now
    return result
