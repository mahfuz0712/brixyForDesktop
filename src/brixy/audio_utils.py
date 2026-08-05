

from __future__ import annotations

import queue
from collections.abc import Iterator
from contextlib import contextmanager

import numpy as np
import sounddevice as sd

from brixy.config import config
from brixy.logging_utils import get_logger

log = get_logger()


class MicStream:
    """Context-managed mic stream jeta fixed-size int16 frame gulo yield kore.

    Usage:
        with MicStream(sample_rate=16000, frame_length=512) as stream:
            for frame in stream.frames():
                ...
    """

    def __init__(self, sample_rate: int, frame_length: int, device: int | None = None):
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.device = device if device is not None else config.input_device_index
        self._q: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None

    def _callback(self, indata, frames, time_info, status):  # noqa: ANN001 - sd callback sig
        if status:
            log.warning("Mic stream status: %s", status)
        # int16 mono frame, copy kore queue e push kora (callback thread block kora jabe na)
        self._q.put(indata[:, 0].copy())

    def __enter__(self) -> "MicStream":
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.frame_length,
            channels=1,
            dtype="int16",
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()
        log.info(
            "Mic stream started (rate=%d, frame=%d, device=%s)",
            self.sample_rate,
            self.frame_length,
            self.device,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            log.info("Mic stream stopped")

    def frames(self) -> Iterator[np.ndarray]:
        """Blocking generator — protiti call e ekta frame_length shaped int16 array dey."""
        while True:
            yield self._q.get()

    def read_seconds(self, seconds: float) -> np.ndarray:
        """Command capture korar jonno — nirdisto shomoy dhore audio jomiye
        ekta single flat int16 array hishebe ferot dey (STT ke deyar jonno)."""
        n_frames_needed = int((seconds * self.sample_rate) / self.frame_length) + 1
        chunks = []
        for _ in range(n_frames_needed):
            chunks.append(self._q.get())
        return np.concatenate(chunks)


@contextmanager
def list_input_devices():
    """Debug helper — kon mic index ki, terminal e dekhar jonno."""
    devices = sd.query_devices()
    yield [d for d in devices if d["max_input_channels"] > 0]