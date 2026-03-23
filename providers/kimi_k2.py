"""Kimi K2 credit usage via billing API."""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime
from providers import ProviderResult

NAME = "Kimi K2"
SHORT = "K2"

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 60  # 1 minute


def fetch() -> ProviderResult | None:
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    token = os.environ.get("KIMI_AUTH_TOKEN")
    if not token:
        return None

    body = json.dumps({"scope": ["FEATURE_CODING"]}).encode()
    req = urllib.request.Request(
        "https://www.kimi.com/apiv2/kimi.gateway.billing.v1.BillingService/GetUsages",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception:
        return None

    try:
        detail = data["usages"][0]["detail"]
        limit = detail["limits"][0]["detail"]
        used = detail["used"]
        pct = min(100, round(used / limit * 100)) if limit > 0 else 0
    except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
        pct = 0

    try:
        reset_time = data["usages"][0]["detail"]["resetTime"]
        reset_dt = datetime.fromisoformat(reset_time.replace("Z", "+00:00"))
        reset_secs = max(0, int(reset_dt.timestamp()) - int(now))
    except (KeyError, IndexError, ValueError, TypeError):
        reset_secs = 0

    result = ProviderResult(name=NAME, pct=pct, reset_secs=reset_secs)
    _cache["data"] = result
    _cache["ts"] = now
    return result
