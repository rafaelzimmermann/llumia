#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
uv run --with rumps widget.py
