import sys

from loguru import logger


def setup_logging():
    logger.remove()

    logger.add(
        sink=sys.stderr,
        level="INFO",
        colorize=True,
        format="<green>{time:DD-MM-YYYY HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    logger.add(
        sink="/bot_app/logs/bot_history.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )
