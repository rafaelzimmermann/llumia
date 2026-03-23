"""Z.ai quota usage via monitor API."""

import json
import os
import time
import urllib.request
import urllib.error
import yaml

NAME = "Z.ai"
SHORT = "Z"

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 60  # 1 minute


def _get_api_key() -> str | None:
    return None  # stub — full implementation in Task 3


def fetch():
    return None  # stub — full implementation in Task 3
