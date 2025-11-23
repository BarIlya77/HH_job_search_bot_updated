import logging
import sys
from typing import Optional
from src.core.config import settings


class CustomFormatter(logging.Formatter):
    """Кастомный форматтер для цветного вывода"""

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"

    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Создает и настраивает логгер"""
    logger = logging.getLogger(name or "hh_bot")

    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

        # Создаем обработчик для stdout
        handler = logging.StreamHandler(sys.stdout)

        if settings.COLORED_LOGS:
            handler.setFormatter(CustomFormatter())
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger