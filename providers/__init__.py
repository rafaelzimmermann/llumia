from dataclasses import dataclass

# ProviderResult MUST be defined before submodule imports to avoid circular import:
# providers/claude.py and providers/zai.py each do `from providers import ProviderResult`
# at module load time. If we import them first, ProviderResult doesn't exist yet.
@dataclass
class ProviderResult:
    name: str
    pct: int
    reset_secs: int

from providers import claude, zai  # noqa: E402 — must come after ProviderResult

PROVIDERS = [claude, zai]
