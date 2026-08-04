"""
Brixy — central configuration.

Sob 'knobs' ekhane. .env file theke load hoy (python-dotenv), so kono secret
(Picovoice access key, LLM API key) code e hardcode thake na — .env e thake,
ar .env, git-ignored + exe er pashe thake plaintext (parer step e encrypt
kora jete pare user-specific machine key diye, but MVP e eta thik ache).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# .env file ta project root e (dev mode) othoba exe er pashe (packaged mode) khoja hoy
_ENV_CANDIDATES = [
    Path(__file__).resolve().parent.parent.parent / ".env",  # dev: repo root
    Path(os.environ.get("APPDATA", ".")) / "Brixy" / ".env",  # packaged: %APPDATA%\Brixy\.env
]
for _candidate in _ENV_CANDIDATES:
    if _candidate.exists():
        load_dotenv(_candidate)
        break
else:
    load_dotenv()  # fallback: cwd er .env, or shudhu already-set env vars


def _app_data_dir() -> Path:
    """Windows e %APPDATA%\\Brixy, onno OS e ~/.brixy (dev/testing er jonno)."""
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) / "Brixy" if appdata else Path.home() / ".brixy"
    base.mkdir(parents=True, exist_ok=True)
    return base


@dataclass
class BrixyConfig:
    # --- Picovoice / wake word ---
    picovoice_access_key: str = field(
        default_factory=lambda: os.environ.get("PICOVOICE_ACCESS_KEY", "")
    )
    # Default: built-in keyword "jarvis" (test korar jonno). Custom "brixy" wake
    # word banate hole Picovoice Console theke .ppn file train kore niye eikhane
    # path bosao — README.md e full instruction ache.
    wake_word_builtin: str = field(
        default_factory=lambda: os.environ.get("BRIXY_WAKE_WORD_BUILTIN", "jarvis")
    )
    wake_word_ppn_path: str = field(
        default_factory=lambda: os.environ.get("BRIXY_WAKE_WORD_PPN", "")
    )
    wake_word_sensitivity: float = field(
        default_factory=lambda: float(os.environ.get("BRIXY_WAKE_SENSITIVITY", "0.6"))
    )

    # --- Mic ---
    input_device_index: int | None = field(
        default_factory=lambda: (
            int(os.environ["BRIXY_INPUT_DEVICE"])
            if os.environ.get("BRIXY_INPUT_DEVICE")
            else None
        )
    )

    # --- Pipeline behaviour ---
    # Wake word detect howar por eto second listen korbe command er jonno
    command_listen_seconds: float = field(
        default_factory=lambda: float(os.environ.get("BRIXY_COMMAND_SECONDS", "6.0"))
    )
    # Eto second no activity thakle heavy models (STT/LLM session) unload kore dibe
    idle_unload_seconds: float = field(
        default_factory=lambda: float(os.environ.get("BRIXY_IDLE_UNLOAD_SECONDS", "60.0"))
    )

    # --- Paths ---
    app_data_dir: Path = field(default_factory=_app_data_dir)
    log_file: Path = field(default_factory=lambda: _app_data_dir() / "brixy.log")

    def validate(self) -> list[str]:
        """Startup e call kore — je gulo missing shegulo list kore dey (crash na kore)."""
        problems = []
        if not self.picovoice_access_key:
            problems.append(
                "PICOVOICE_ACCESS_KEY missing — .env e set koro "
                "(console.picovoice.ai theke free key nao)"
            )
        if self.wake_word_ppn_path and not Path(self.wake_word_ppn_path).exists():
            problems.append(f"Custom wake word file paoa jayni: {self.wake_word_ppn_path}")
        return problems


config = BrixyConfig()
