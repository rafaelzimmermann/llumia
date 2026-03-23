"""Claude plan quota usage via OAuth API."""

import json
import os
import subprocess
import time
import urllib.request
import urllib.error

NAME = "Claude"
SHORT = "C"

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 300  # 5 minutes


def _get_token() -> str | None:
    return None  # stub — full implementation in Task 2


def fetch():
    return None  # stub — full implementation in Task 2
