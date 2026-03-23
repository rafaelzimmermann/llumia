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
        self._timer = rumps.Timer(self.refresh, 60)
        self._timer.start()
        self.refresh(None)

    def refresh(self, _):
        results = {p.NAME: p.fetch() for p in PROVIDERS}
        active = [(p, results[p.NAME]) for p in PROVIDERS if results[p.NAME] is not None]

        parts = [f"{p.SHORT} {r.pct}%" for p, r in active]
        self.title = "🤖 " + "  ".join(parts) if parts else "🤖"

        if not active:
            provider_items = [rumps.MenuItem("No AI tool found")]
        else:
            provider_items = []
            for p, result in active:
                reset_str = fmt_reset(result.reset_secs)
                bar = pct_bar(result.pct)
                item = rumps.MenuItem(p.NAME)
                item.title = f"{p.NAME}  {bar}  {result.pct}%  (resets {reset_str})"
                icon = icons.load_icon(p.NAME)
                if icon:
                    item.set_icon(icon, dimensions=(16, 16), template=False)
                provider_items.append(item)

        self.menu.clear()
        self.menu = provider_items + [
            None,
            rumps.MenuItem("Refresh", callback=self.refresh),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]


if __name__ == "__main__":
    AIUsageWidget().run()
