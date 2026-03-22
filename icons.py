"""Paths to logo icons for Claude and Z.ai."""

import os

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".icons")


def _icon(name: str) -> str | None:
    p = os.path.join(_DIR, f"{name}@2x.png")
    return p if os.path.exists(p) else None


def claude_icon() -> str | None:
    return _icon("claude")


def zai_icon() -> str | None:
    return _icon("zai")
