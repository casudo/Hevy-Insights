import logging

from app.core.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
    )

    if settings.demo_mode:
        logging.warning("=" * 80)
        logging.warning("DEMO MODE ENABLED - Using sample data instead of real API calls")
        logging.warning("=" * 80)
