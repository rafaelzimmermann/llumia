"""Claude plan quota usage via OAuth API."""

import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from providers import ProviderResult

NAME = "Claude"
SHORT = "C"

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 300  # 5 minutes


def _get_token() -> str | None:
    # macOS: credentials stored in Keychain
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout.strip())
            return data["claudeAiOauth"]["accessToken"]
    except Exception:
        pass

    # Fallback: credentials file (Linux / older Claude Code versions)
    try:
        creds_path = os.path.expanduser("~/.claude/.credentials.json")
        with open(creds_path) as f:
            return json.load(f)["claudeAiOauth"]["accessToken"]
    except Exception:
        pass

    return None


def fetch() -> ProviderResult | None:
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    token = _get_token()
    if not token:
        return None

    body = json.dumps({
        "model": "claude-haiku-4-5",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "Hi"}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "oauth-2025-04-20",
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            headers = resp.headers
    except urllib.error.HTTPError as e:
        headers = e.headers
    except Exception:
        return None

    def h(name):
        return headers.get(f"anthropic-ratelimit-unified-{name}", "")

    claim = h("representative-claim")
    prefix = "5h" if claim == "five_hour" else "7d"

    try:
        utilization = float(h(f"{prefix}-utilization"))
        pct = round(utilization * 100)
    except ValueError:
        pct = 0

    try:
        reset_ts = int(h(f"{prefix}-reset"))
        reset_secs = max(0, reset_ts - int(now))
    except ValueError:
        reset_secs = 0

    result = ProviderResult(name=NAME, pct=pct, reset_secs=reset_secs)
    _cache["data"] = result
    _cache["ts"] = now
    return result
