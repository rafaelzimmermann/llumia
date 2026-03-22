#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.llumia.plist"

# ── dependencies ────────────────────────────────────────────────────────────
if command -v uv &>/dev/null; then
    echo "Installing dependencies with uv..."
    uv pip install -r "$REPO_DIR/requirements.txt" --quiet
else
    echo "Installing dependencies with pip..."
    pip install -r "$REPO_DIR/requirements.txt" --quiet
fi

# ── launch agent ────────────────────────────────────────────────────────────
install_launch_agent() {
    # Detect python
    if command -v uv &>/dev/null; then
        RUNNER="$(command -v uv)"
        PROG_ARGS="<string>$RUNNER</string>
        <string>run</string>
        <string>$REPO_DIR/widget.py</string>"
    else
        RUNNER="$(command -v python3)"
        PROG_ARGS="<string>$RUNNER</string>
        <string>$REPO_DIR/widget.py</string>"
    fi

    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$LAUNCH_AGENT" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.llumia</string>
    <key>ProgramArguments</key>
    <array>
        $PROG_ARGS
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$REPO_DIR</string>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/llumia.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/llumia.log</string>
</dict>
</plist>
EOF

    # Unload if already loaded
    launchctl unload "$LAUNCH_AGENT" 2>/dev/null || true
    launchctl load "$LAUNCH_AGENT"
    echo "Launch agent installed — llumia will start at login."
}

uninstall() {
    echo "Stopping and removing llumia..."

    # Stop and remove launch agent
    if [[ -f "$LAUNCH_AGENT" ]]; then
        launchctl unload "$LAUNCH_AGENT" 2>/dev/null || true
        rm -f "$LAUNCH_AGENT"
        echo "  Removed launch agent."
    fi

    # Remove log file
    rm -f "$HOME/Library/Logs/llumia.log"

    # Remove repo directory
    echo "  Removing $REPO_DIR..."
    rm -rf "$REPO_DIR"

    echo "llumia uninstalled."
}

if [[ "$1" == "--launchagent" ]]; then
    install_launch_agent
    exit 0
fi

if [[ "$1" == "--uninstall" ]]; then
    uninstall
    exit 0
fi

echo ""
echo "llumia installed."
echo ""
echo "Run now:           ./start.sh"
echo "Auto-start login:  ./install.sh --launchagent"
echo "Uninstall:         ./install.sh --uninstall"
