# API Credential Fallbacks Design

**Date:** 2026-03-22
**Status:** Approved

## Overview

Extend `zai_api.py`'s credential lookup to check additional popular AI tool config files, so the widget works out-of-the-box for users of Continue.dev without requiring manual env var setup. `claude_api.py` requires no changes as its OAuth token is Claude Code-specific and already has two robust fallbacks.

## Scope

- **In scope:** `zai_api.py` — add two more file-based fallbacks for the Z.ai API key
- **Out of scope:** `claude_api.py`, VS Code SecretStorage / OS keychain probing for third-party extensions, Zed (stores keys in OS secure storage, not files), alternative API auth methods

## Design

### `zai_api.py` — updated `_get_api_key()` fallback chain

Check sources in order, returning the first non-empty value found:

1. `ZAI_API_KEY` env var *(existing)*
2. `~/.config/opencode/opencode.json` → `provider["zai-coding-plan"]["options"]["apiKey"]` *(existing)*
3. `~/.continue/config.yaml` → the `apiKey` of the first `models` entry where `provider == "zAI"` (case-sensitive, exact match)
4. `~/.continue/config.json` → same structure, JSON format (deprecated but still in use); same case-sensitive match

### Error handling

Each fallback is wrapped in its own `try/except Exception`. A missing file, malformed format, missing key, or wrong type silently falls through to the next source. An empty-string `apiKey` (`""`) is treated as absent and also falls through. No errors are surfaced to the caller; `None` is returned if all sources fail.

For the YAML fallback, use `yaml.safe_load()` (single-document load). Continue.dev's config is a single-document file; using `safe_load_all()` would yield a generator instead of a dict.

### Dependencies

The YAML fallback requires `pyyaml`, which is not currently in the venv. Add it to both `requirements.txt` and the `dependencies` list in `pyproject.toml` to keep them in sync.

### `claude_api.py`

No changes. The Claude Code OAuth token has two existing fallbacks (macOS Keychain → `~/.claude/.credentials.json`) that cover all known file-based sources.

## Continue.dev config structure

**YAML** (`~/.continue/config.yaml`, current format):
```yaml
models:
  - name: GLM-5
    provider: zAI
    model: glm-5
    apiKey: <key>
```

**JSON** (`~/.continue/config.json`, deprecated):
```json
{
  "models": [
    {
      "provider": "zAI",
      "apiKey": "<key>"
    }
  ]
}
```

The lookup iterates `models` and returns the `apiKey` of the first entry whose `provider` equals `"zAI"` (case-sensitive). An empty `apiKey` is treated as absent.

## Files changed

- `zai_api.py` — extend `_get_api_key()`
- `requirements.txt` — add `pyyaml`
- `pyproject.toml` — add `pyyaml` to `dependencies`
