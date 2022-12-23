import logging
import os
import pathlib
from dataclasses import dataclass
from logging.handlers import TimedRotatingFileHandler

MONTH_START_DAY = 10

log_dir = pathlib.Path(__name__).parent / "logs"
log_dir.mkdir(exist_ok=True)


@dataclass
class Config:
    bot_token: str
    allowed_tg_ids: list[int]


def get_config() -> Config:
    token = os.environ.get("bot_token")
    if not token:
        raise ValueError("Token is not set in os environ")
    ids = os.environ.get("tg_ids")
    parsed_ids = [int(id) for id in ids.split(",")] if ids else []
    return Config(token, parsed_ids)


config = get_config()


def create_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    flh = TimedRotatingFileHandler(
        log_dir / "info.log",
        when="W0",
        interval=1,
        backupCount=52,
    )
    flh.setLevel(level)
    flh.setFormatter(
        logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    )
    logger.addHandler(flh)
    logger.setLevel(level)
    return logger
