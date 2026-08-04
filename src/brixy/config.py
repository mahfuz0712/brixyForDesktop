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
    # --- Wake word (openWakeWord — fully offline, no account/API key needed) ---
    # Bundled pretrained model name (test korar jonno, package er shathei ashe):
    # alexa_v0.1 | hey_jarvis_v0.1 | hey_mycroft_v0.1 | hey_marvin_v0.1 | timer_v0.1 | weather_v0.1
    wake_word_builtin: str = field(
        default_factory=lambda: os.environ.get("BRIXY_WAKE_WORD_BUILTIN", "hey_jarvis_v0.1")
    )
    # Custom trained "Brixy" model (.onnx / .tflite) — Colab notebook diye train
    # kore niye path dile eta builtin ke override kore dibe. README.md e steps ache.
    wake_word_model_path: str = field(
        default_factory=lambda: os.environ.get("BRIXY_WAKE_WORD_MODEL", "")
    )
    # Detection score threshold (0.0-1.0). Beshi hole kom false-positive kintu
    # kono somoy real wake word miss korte pare, kom hole ulto.
    wake_word_threshold: float = field(
        default_factory=lambda: float(os.environ.get("BRIXY_WAKE_THRESHOLD", "0.5"))
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
        if self.wake_word_model_path and not Path(self.wake_word_model_path).exists():
            problems.append(f"Custom wake word model file paoa jayni: {self.wake_word_model_path}")
        return problems


config = BrixyConfig()