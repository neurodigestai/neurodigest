import logging
import os

from config_loader import Config
from constants import LOG_FILE_PATH


def setup_logger(name: str = "neuroai") -> logging.Logger:
    """Create and configure the application logger.

    Outputs to both the console and ``logs/app.log`` using the format:
        [YYYY-MM-DD HH:MM:SS] [LEVEL] module_name: message

    Parameters
    ----------
    name : str
        The logger name (defaults to ``"neuroai"``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    # Custom formatter matching the required output format
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler ───────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ── File handler ──────────────────────────────────────────────────
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
