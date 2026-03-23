#!/usr/bin/env python3
"""macOS menu bar widget showing AI quota usage."""

import rumps
from providers import PROVIDERS
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
        provider_items = [rumps.MenuItem(p.NAME) for p in PROVIDERS]
        self.menu = provider_items + [
            None,
            rumps.MenuItem("Refresh", callback=self.refresh),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        for p in PROVIDERS:
            icon = icons.load_icon(p.NAME)
            if icon:
                self.menu[p.NAME].set_icon(icon, dimensions=(16, 16), template=False)
        self._timer = rumps.Timer(self.refresh, 60)
        self._timer.start()
        self.refresh(None)

    def refresh(self, _):
        results = {p.NAME: p.fetch() for p in PROVIDERS}
        active = [r for r in results.values() if r is not None]

        parts = [f"{p.SHORT} {results[p.NAME].pct}%" for p in PROVIDERS if results[p.NAME]]
        self.title = "🤖 " + "  ".join(parts) if parts else "🤖"

        if not active:
            # rumps cannot hide items; blank all but first to avoid clutter
            self.menu[PROVIDERS[0].NAME].title = "No AI tool found"
            for p in PROVIDERS[1:]:
                self.menu[p.NAME].title = ""
            return

        for p in PROVIDERS:
            result = results[p.NAME]
            if result:
                reset_str = fmt_reset(result.reset_secs)
                bar = pct_bar(result.pct)
                self.menu[p.NAME].title = (
                    f"{p.NAME}  {bar}  {result.pct}%  (resets {reset_str})"
                )
            else:
                self.menu[p.NAME].title = f"{p.NAME}  unavailable"


if __name__ == "__main__":
    AIUsageWidget().run()
