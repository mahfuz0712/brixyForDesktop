"""
Always-on wake word listener — Brixy er 'idle state' engine.

Eta hocche shei part jeta 24/7 background e chalte thakbe. Porcupine
(Picovoice) khub lightweight — tiny on-device model, ~1-3% CPU ekta core e,
kono network call nai, kono heavy STT/LLM load hoy na. Battery drain
practically negligible.

Design:
    - WakeWordListener ekta background thread e run kore
    - Keyword detect hole ekta callback fire hoy (main thread e handle kora hoy)
    - stop() call korle cleanly thread ar Porcupine resource dutoi free hoy
"""

from __future__ import annotations

import threading
from collections.abc import Callable

import pvporcupine

from brixy.audio_utils import MicStream
from brixy.config import config
from brixy.logging_utils import get_logger

log = get_logger()

OnWakeWordCallback = Callable[[], None]


class WakeWordListener:
    def __init__(self, on_wake_word: OnWakeWordCallback):
        self._on_wake_word = on_wake_word
        self._porcupine: pvporcupine.Porcupine | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _build_porcupine(self) -> pvporcupine.Porcupine:
        kwargs: dict = {
            "access_key": config.picovoice_access_key,
            "sensitivities": [config.wake_word_sensitivity],
        }
        if config.wake_word_ppn_path:
            # Custom trained wake word (e.g. "Brixy") — Picovoice Console theke .ppn banano
            kwargs["keyword_paths"] = [config.wake_word_ppn_path]
            log.info("Loading custom wake word: %s", config.wake_word_ppn_path)
        else:
            # Built-in keyword diye test kora (jemon "jarvis", "computer", "picovoice")
            kwargs["keywords"] = [config.wake_word_builtin]
            log.info("Loading built-in wake word: %s", config.wake_word_builtin)
        return pvporcupine.create(**kwargs)

    def _run(self) -> None:
        try:
            self._porcupine = self._build_porcupine()
        except pvporcupine.PorcupineError:
            log.exception("Porcupine init failed — wake word listener start hote parlo na")
            return

        try:
            with MicStream(
                sample_rate=self._porcupine.sample_rate,
                frame_length=self._porcupine.frame_length,
            ) as mic:
                log.info("Wake word listener active — idle listening shuru")
                for frame in mic.frames():
                    if self._stop_event.is_set():
                        break
                    result = self._porcupine.process(frame)
                    if result >= 0:
                        log.info("Wake word detected!")
                        try:
                            self._on_wake_word()
                        except Exception:  # noqa: BLE001 - callback crash e listener mora uchit na
                            log.exception("on_wake_word callback e error")
        finally:
            if self._porcupine is not None:
                self._porcupine.delete()
                self._porcupine = None
            log.info("Wake word listener stopped")

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            log.warning("Listener already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="brixy-wakeword")
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None
