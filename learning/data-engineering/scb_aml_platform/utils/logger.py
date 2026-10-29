"""Centralised loguru logger setup."""

import sys
from pathlib import Path
from loguru import logger

from scb_aml_platform.config.settings import LOG_LEVEL, LOG_DIR


def setup_logger(name: str = "aml_platform"):
    logger.remove()
    logger.add(sys.stderr, level=LOG_LEVEL,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    log_file = Path(LOG_DIR) / f"{name}.log"
    logger.add(str(log_file), level="DEBUG", rotation="50 MB", retention="30 days",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}")
    return logger
