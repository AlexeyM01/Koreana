"""
app/core/logger.py
"""
import logging
import os
import sys


def configure_logging():
    """Настраивает логирование для приложения из файла logging.conf."""
    log_file_path = "logging.conf"
    if os.path.exists(log_file_path):
        logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
        print(f"Логирование сконфигурировано из файла: {log_file_path}")
    else:
        print(f"Файл конфигурации логирования не найден: {log_file_path}")
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
