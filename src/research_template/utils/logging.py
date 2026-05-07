"""Logging utilities."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger with a StreamHandler, avoiding duplicate handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
