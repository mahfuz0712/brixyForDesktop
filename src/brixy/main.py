from __future__ import annotations
import signal
import sys
from brixy import pipeline
from brixy.config import config
from brixy.logging_utils import get_logger
from brixy.tray import TrayApp
from brixy.wake_word import WakeWordListener
log = get_logger()

def run() -> None:
    problems = config.validate()
    for p in problems:
        log.error("Config problem: %s", p)
        sys.exit(1)

    listener = WakeWordListener(on_wake_word=pipeline.handle_wake_word)
    listener.start()

    tray = TrayApp(on_exit=lambda: listener.stop())
    tray.run_in_thread()
    def _handle_sigterm(signum, frame):  # noqa: ANN001, ARG001
        log.info("Signal %s received, shutting down", signum)
        listener.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)

    log.info("Brixy started. Wake word: %s", config.wake_word_model_path or config.wake_word_builtin)
    tray.run_blocking()  # blocks main thread until "Exit" clicked


if __name__ == "__main__":
    run()