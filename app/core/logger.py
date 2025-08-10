"""
app/core/logger.py
"""
import logging
import sys

import uvicorn


def configure_logging():
    """Настраивает логирование для приложения."""
    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    file_handler = logging.FileHandler('app_errors.log')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
