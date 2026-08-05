from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from brixy.config import config
_LOG = logging.getLogger("brixy")


def get_logger() -> logging.Logger:
    if _LOG.handlers:
        return _LOG

    _LOG.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        config.log_file, maxBytes=2_000_000, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    _LOG.addHandler(file_handler)

    # Dev mode e (console theke run korle) console e o log dekhabe.
    # Packaged --noconsole build e eta silently ignore hoy.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    _LOG.addHandler(stream_handler)

    return _LOG