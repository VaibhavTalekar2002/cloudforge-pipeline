import logging
import os
from datetime import datetime
import colorlog


def setup_logger(log_level="INFO", log_dir="logs"):
    """
    Creates and configures application logger.
    """

    os.makedirs(log_dir, exist_ok=True)

    log_filename = datetime.now().strftime("pipeline_%Y%m%d.log")
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger("CloudForgePipeline")

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper()))

    # Console Formatter
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    # File Formatter
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # File Handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger