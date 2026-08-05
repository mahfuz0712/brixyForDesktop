from __future__ import annotations
import threading
from brixy.logging_utils import get_logger

log = get_logger()

# Ekbar e ekta pipeline run e overlapping wake-word trigger ignore korar jonno
_pipeline_lock = threading.Lock()


def handle_wake_word() -> None:
    """Wake word detect howar por call hoy. Ekhon shudhu log/beep — porer
    step e ekhane STT capture -> LLM function-calling -> dispatcher call
    -> TTS response boshbe."""
    if not _pipeline_lock.acquire(blocking=False):
        log.info("Pipeline already running, ignoring new trigger")
        return

    def _run():
        try:
            log.info("Pipeline triggered — STT/LLM stage porer ধাপে add hobe")
            # TODO (next stage):
            #   1. mic.read_seconds(config.command_listen_seconds) diye command capture
            #   2. STT (faster-whisper) diye text-e convert
            #   3. LLM API call (function calling / tool_use)
            #   4. dispatcher.execute(tool_name, tool_args) diye actual system action
            #   5. TTS diye result speaker e bola, othoba shudhu text hole speaker e read
        finally:
            _pipeline_lock.release()

    threading.Thread(target=_run, daemon=True, name="brixy-pipeline").start()