"""JetBrains AI quota from local IDE config file (no network calls)."""

import glob
import html
import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from providers import ProviderResult

NAME = "JetBrains AI"
SHORT = "JB"

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 300  # 5 minutes


def _find_xml() -> str | None:
    """Return path to the newest AIAssistantQuotaManager2.xml, or None."""
    pattern = os.path.expanduser(
        "~/Library/Application Support/JetBrains/*/options/AIAssistantQuotaManager2.xml"
    )
    matches = glob.glob(pattern)
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)


def fetch() -> ProviderResult | None:
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    xml_path = _find_xml()
    if not xml_path:
        return None

    try:
        tree = ET.parse(xml_path)
        for elem in tree.getroot().iter("option"):
            if elem.get("name") == "quotaInfo":
                raw = html.unescape(elem.get("value", ""))
                info = json.loads(raw)
                used = int(info["usedTokens"])
                maximum = int(info["maximumTokens"])
                pct = min(100, round(used / maximum * 100)) if maximum > 0 else 0

                try:
                    expiry_date = date.fromisoformat(info["expiration"])
                    expiry_dt = datetime(
                        expiry_date.year, expiry_date.month, expiry_date.day, 0, 0, 0
                    )
                    reset_secs = max(0, int(expiry_dt.timestamp()) - int(now))
                except (KeyError, ValueError, TypeError):
                    reset_secs = 0

                result = ProviderResult(name=NAME, pct=pct, reset_secs=reset_secs)
                _cache["data"] = result
                _cache["ts"] = now
                return result
    except Exception:
        return None

    return None  # quotaInfo element not found
