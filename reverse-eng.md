# Reverse Engineering Claude Code's `/usage` Command

How we discovered the undocumented OAuth authentication mechanism for `api.anthropic.com` and replicated the `/usage` command in a Waybar status bar widget.

---

## Goal

Show Claude plan quota usage (like the `/usage` slash command) in a Waybar status bar widget — without an Admin API key, which is unavailable for individual accounts.

---

## Step 1: Confirm the Admin API is a dead end

The [Anthropic Usage & Cost API](https://docs.anthropic.com/en/build-with-claude/usage-cost-api) and the [Claude Code Analytics API](https://docs.anthropic.com/en/build-with-claude/claude-code-analytics-api) both require an Admin API key (`sk-ant-admin...`). The docs explicitly state:

> **The Admin API is unavailable for individual accounts.**

Regular API keys (`sk-ant-api...`) return `authentication_error: invalid x-api-key` on those endpoints.

---

## Step 2: Understand what `/usage` actually shows

Claude Code's `/usage` command description, extracted by running `strings` on the binary:

```
"usage", description: "Show plan usage limits"
```

Not session cost — **plan quota limits**. These come from response headers, not a separate API call.

---

## Step 3: Find all API endpoints in the binary

The Claude Code binary at `~/.local/share/claude/versions/2.1.81` is a 227MB compiled Bun executable with embedded JavaScript source. `strings` extracts readable content:

```bash
strings ~/.local/share/claude/versions/2.1.81 | grep 'api/claude_code/'
```

Output:
```
api/claude_code/metrics
api/claude_code/organizations/metrics_enabled
api/claude_code/policy_limits
api/claude_code/settings
api/claude_code/team_memory
```

And the key one:
```bash
strings ... | grep 'api/oauth/'
# → api/oauth/account/settings
# → api/oauth/claude_cli/client_data
```

---

## Step 4: Find the rate limit headers

Searching for how the binary parses response headers:

```bash
strings ~/.local/share/claude/versions/2.1.81 | grep -oE '"anthropic-ratelimit-unified-reset"[^}]{0,200}'
```

This revealed a full set of undocumented response headers:

```
anthropic-ratelimit-unified-status
anthropic-ratelimit-unified-5h-status
anthropic-ratelimit-unified-5h-reset
anthropic-ratelimit-unified-5h-utilization
anthropic-ratelimit-unified-7d-status
anthropic-ratelimit-unified-7d-reset
anthropic-ratelimit-unified-7d-utilization
anthropic-ratelimit-unified-representative-claim
anthropic-ratelimit-unified-reset
anthropic-ratelimit-unified-overage-status
```

And the data model:
```
rateLimitType: enum ["five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "overage"]
overageStatus: enum ["allowed", "allowed_warning", "rejected"]
```

---

## Step 5: Try the OAuth token directly — fails

The credentials file at `~/.claude/.credentials.json` contains the OAuth Bearer token:

```bash
python3 -c "import json; d=json.load(open('~/.claude/.credentials.json')); print(list(d['claudeAiOauth'].keys()))"
# ['accessToken', 'refreshToken', 'expiresAt', 'scopes', 'subscriptionType', 'rateLimitTier']
```

Trying it against the API:

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "anthropic-version: 2023-06-01" \
     "https://api.anthropic.com/v1/messages" ...
# → HTTP 401: "OAuth authentication is currently not supported."
```

---

## Step 6: Intercept traffic with mitmproxy

Since `SSLKEYLOGFILE` and `NODE_OPTIONS --tls-keylog` don't work on Bun binaries, we used `mitmproxy`:

```bash
mitmdump -p 8088 --save-stream-file /tmp/claude-traffic.mitm &

HTTPS_PROXY=http://localhost:8088 \
SSL_CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem \
claude --print "say hi"
```

No certificate pinning — it worked.

Reading the captured traffic:

```bash
mitmdump --mode regular@8082 -r /tmp/claude-traffic.mitm
```

Revealed all endpoints Claude Code calls on startup:
```
GET  /api/eval/sdk-...
GET  /v1/mcp_servers
GET  /api/claude_code_penguin_mode
GET  /api/oauth/claude_cli/client_data
GET  /api/claude_code_grove
GET  /api/oauth/account/settings        ← 200 OK (was 401 with our token!)
POST /v1/messages?beta=true             ← inference
POST /api/event_logging/v2/batch
```

---

## Step 7: Find the missing header

Parsing the captured request headers for the `v1/messages` call:

```python
import mitmproxy.io
from mitmproxy import http

with open('/tmp/claude-traffic.mitm', 'rb') as f:
    reader = mitmproxy.io.FlowReader(f)
    for flow in reader.stream():
        if 'v1/messages' in flow.request.pretty_url:
            for k, v in flow.request.headers.items():
                print(f"{k}: {v}")
```

The key difference from our earlier attempts:

```
Authorization: Bearer sk-ant-oat01-...
anthropic-beta: claude-code-20250219,oauth-2025-04-20,...
                                      ^^^^^^^^^^^^^^^^
```

The undocumented beta flag **`oauth-2025-04-20`** enables OAuth Bearer token authentication on `api.anthropic.com`.

---

## Step 8: Confirm it works

```bash
ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('~/.claude/.credentials.json'))['claudeAiOauth']['accessToken'])")

curl -si \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: oauth-2025-04-20" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5","max_tokens":1,"messages":[{"role":"user","content":"Hi"}]}' \
  "https://api.anthropic.com/v1/messages" | grep unified
```

Response headers:
```
anthropic-ratelimit-unified-status: allowed
anthropic-ratelimit-unified-5h-status: allowed
anthropic-ratelimit-unified-5h-reset: 1774220400
anthropic-ratelimit-unified-5h-utilization: 0.2
anthropic-ratelimit-unified-7d-status: allowed
anthropic-ratelimit-unified-7d-reset: 1774641600
anthropic-ratelimit-unified-7d-utilization: 0.35
anthropic-ratelimit-unified-representative-claim: five_hour
anthropic-ratelimit-unified-overage-status: rejected
```

---

## Result: Waybar script

```bash
#!/usr/bin/env bash
CREDENTIALS="$HOME/.claude/.credentials.json"
ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('$CREDENTIALS'))['claudeAiOauth']['accessToken'])")

headers=$(curl -si -m 15 \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: oauth-2025-04-20" \
    -H "content-type: application/json" \
    -d '{"model":"claude-haiku-4-5","max_tokens":1,"messages":[{"role":"user","content":"Hi"}]}' \
    "https://api.anthropic.com/v1/messages" 2>/dev/null | grep -i 'ratelimit-unified')

# Parse utilization and reset time, display as "󰭻 21% (resets in 3h02m)"
```

Output: `󰭻 21%` with tooltip `Claude: 21% of 5h quota used, resets in 3h02m`

---

## Key findings

| Finding | Detail |
|---|---|
| Binary format | Compiled Bun executable with embedded JS source |
| No cert pinning | mitmproxy works transparently |
| Auth mechanism | OAuth Bearer token, not API key |
| Magic header | `anthropic-beta: oauth-2025-04-20` |
| Usage data source | `anthropic-ratelimit-unified-*` response headers |
| Token location | `~/.claude/.credentials.json` → `claudeAiOauth.accessToken` |
