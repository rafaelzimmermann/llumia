#!/usr/bin/env python3
"""macOS menu bar widget showing Claude and Z.ai usage."""

import rumps
import claude_api
import zai_api
import icons


def fmt_reset(secs: int) -> str:
    if secs <= 0:
        return "now"
    h, m = divmod(secs // 60, 60)
    if h:
        return f"{h}h{m:02d}m"
    return f"{m}m"


def pct_bar(pct: int, width: int = 8) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)



class AIUsageWidget(rumps.App):
    def __init__(self):
        super().__init__("…", quit_button=None)
        self.menu = [
            rumps.MenuItem("Claude"),
            rumps.MenuItem("Z.ai"),
            None,
            rumps.MenuItem("Refresh", callback=self.refresh),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

        # Set icons on menu items
        c_icon = icons.claude_icon()
        z_icon = icons.zai_icon()
        if c_icon:
            self.menu["Claude"].set_icon(c_icon, dimensions=(16, 16), template=False)
        if z_icon:
            self.menu["Z.ai"].set_icon(z_icon, dimensions=(16, 16), template=False)

        self._timer = rumps.Timer(self.refresh, 60)
        self._timer.start()
        self.refresh(None)

    def refresh(self, _):
        claude = claude_api.fetch()
        zai = zai_api.fetch()

        parts = []
        if claude:
            parts.append(f"C {claude['pct']}%")
        if zai:
            parts.append(f"Z {zai['pct']}%")

        self.title = "🤖 " + "  ".join(parts) if parts else "🤖"

        if not claude and not zai:
            self.menu["Claude"].title = "No AI tool found"
            self.menu["Z.ai"].title = ""
            return

        if claude:
            reset_str = fmt_reset(claude["reset_secs"])
            bar = pct_bar(claude["pct"])
            self.menu["Claude"].title = (
                f"Claude  {bar}  {claude['pct']}%  ({claude['window']} · resets {reset_str})"
            )
        else:
            self.menu["Claude"].title = "Claude  unavailable"

        if zai:
            reset_str = fmt_reset(zai["reset_secs"])
            bar = pct_bar(zai["pct"])
            rem = f"  ·  {zai['remaining_m']}M left" if zai.get("remaining_m") is not None else ""
            self.menu["Z.ai"].title = (
                f"Z.ai  {bar}  {zai['pct']}%{rem}  (resets {reset_str})"
            )
        else:
            self.menu["Z.ai"].title = "Z.ai  unavailable"


if __name__ == "__main__":
    AIUsageWidget().run()
