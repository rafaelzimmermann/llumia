# llumia

macOS menu bar widget showing Claude and Z.ai quota usage.

<img width="870" height="344" alt="image" src="https://github.com/user-attachments/assets/04f299b4-539b-431f-b914-61c365090fc1" />


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

## Usage

The menu bar shows current usage at a glance:

```
🤖 C 42%  Z 67%
```

Click the icon to expand the menu and see details for each provider — usage bar, percentage, quota window, and time until reset.

Refreshes every 60 seconds. Click **Refresh** to force an update.

## Display

| Indicator | Meaning |
|-----------|---------|
| ○ | < 70% used |
| ◕ | 70–89% used |
| ● | ≥ 90% used or rejected |

## How it works

- **Claude**: reads your OAuth token from Keychain (or `~/.claude/.credentials.json`) and makes a minimal API call to read usage from response headers. Cached for 5 minutes.
- **Z.ai**: reads your API key from `~/.config/opencode/opencode.json` (or `ZAI_API_KEY` env var) and polls the quota endpoint. Cached for 1 minute.

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
