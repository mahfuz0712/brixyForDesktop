from __future__ import annotations
import os
import threading
import time
from collections.abc import Callable
from typing import cast
import numpy as np
import openwakeword
from openwakeword.model import Model
from brixy.audio_utils import MicStream
from brixy.config import config
from brixy.logging_utils import get_logger
log = get_logger()
OnWakeWordCallback = Callable[[], None]
# openWakeWord er expected input: 16kHz mono, 80ms (1280 samples) chunk
SAMPLE_RATE = 16000
FRAME_LENGTH = 1280

# Ekbar detect howar por eto second cooldown (double-trigger thekano jonno,
# karon audio buffer e keyword'er "tail" kichukhon thake)
_DETECTION_COOLDOWN_SECONDS = 2.0


class WakeWordListener:
    def __init__(self, on_wake_word: OnWakeWordCallback):
        self._on_wake_word = on_wake_word
        self._model: Model | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _resolve_model_path(self) -> str:
        if config.wake_word_model_path:
            # Custom trained "Brixy" model
            return config.wake_word_model_path
        # Bundled pretrained model (package er shathei ashe, download lage na)
        base = os.path.join(os.path.dirname(openwakeword.__file__), "resources", "models")
        return os.path.join(base, f"{config.wake_word_builtin}.onnx")

    def _build_model(self) -> Model:
        model_path = self._resolve_model_path()
        log.info("Loading wake word model: %s", model_path)
        return Model(wakeword_model_paths=[model_path])

    def _run(self) -> None:
        try:
            self._model = self._build_model()
        except Exception:  # noqa: BLE001 - model load fail hole listener crash na hoye clean exit
            log.exception("Wake word model load failed — listener start hote parlo na")
            return

        model_name = next(iter(self._model.models.keys()))
        last_detection_time = 0.0

        try:
            with MicStream(sample_rate=SAMPLE_RATE, frame_length=FRAME_LENGTH) as mic:
                log.info("Wake word listener active — idle listening shuru")
                for frame in mic.frames():
                    if self._stop_event.is_set():
                        break

                    # openwakeword er predict() a untyped/loose stubs ache (timing branch
                    # er karone Pylance union type infer kore). Runtime e always
                    # dict[str, float] — model name -> score. cast() shudhu type checker
                    # er jonno; runtime effect zero.
                    scores: dict[str, float] = cast(
                        "dict[str, float]", self._model.predict(frame)
                    )
                    score = scores.get(model_name, 0.0)

                    now = time.monotonic()
                    if (
                        score >= config.wake_word_threshold
                        and (now - last_detection_time) >= _DETECTION_COOLDOWN_SECONDS
                    ):
                        last_detection_time = now
                        log.info("Wake word detected! (score=%.3f)", score)
                        self._model.reset()  # internal buffer clear, double-trigger avoid
                        try:
                            self._on_wake_word()
                        except Exception:  # noqa: BLE001 - callback crash e listener mora uchit na
                            log.exception("on_wake_word callback e error")
        finally:
            self._model = None
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