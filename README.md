# llumia

macOS menu bar widget showing Claude and Z.ai quota usage.

> *Llumia* — Catalan for "light", hiding both **LLM** and **IA** (Intel·ligència Artificial).

## Requirements

- macOS
- Python 3.9+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`
- `~/.claude/.credentials.json` (written by Claude Code automatically)
- `~/.config/opencode/opencode.json` with Z.ai API key, or `ZAI_API_KEY` env var

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/rafaelzimmermann/llumia/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/rafaelzimmermann/llumia.git
cd llumia
./install.sh
```

## How it works

- **Claude**: Sends a minimal POST to `api.anthropic.com/v1/messages` using your OAuth token (from `~/.claude/.credentials.json`) with the undocumented `anthropic-beta: oauth-2025-04-20` header. Usage data comes back in response headers (`anthropic-ratelimit-unified-*`). Results cached 5 minutes.
- **Z.ai**: GETs `https://api.z.ai/api/monitor/usage/quota/limit` using the API key from your opencode config. Results cached 1 minute.

## Display

| Color | Meaning |
|-------|---------|
| ○ | < 70% used |
| ◕ | 70–89% used |
| ● | ≥ 90% used or rejected |

Refreshes every 60 seconds. Click **Refresh** in the menu to force an update.

## Auto-launch on login

The install script sets this up automatically. To do it manually:

```bash
./install.sh --launchagent
```

## Uninstall

```bash
./install.sh --uninstall
```

Stops the app, removes the launch agent, log file, and the entire repo directory.
