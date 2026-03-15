from loguru import logger
import sys
from app.core.config import get_settings

settings = get_settings()


def setup_logger():
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG" if settings.DEBUG else "INFO"
    )
    logger.add(
        f"{settings.LOG_DIR}/app.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )
    return logger