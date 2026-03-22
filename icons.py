"""Paths to logo icons for Claude and Z.ai."""

import os

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".icons")


def claude_icon() -> str | None:
    p = os.path.join(_DIR, "claude@2x.png")
    return p if os.path.exists(p) else None


def zai_icon() -> str | None:
    p = os.path.join(_DIR, "zai@2x.png")
    return p if os.path.exists(p) else None
