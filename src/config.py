import logging
import os
import pathlib
from dataclasses import dataclass
from functools import wraps
from logging.handlers import TimedRotatingFileHandler

from telegram import Update
from telegram.ext import ContextTypes

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


def log(logger: logging.Logger):
    def inner(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text if update.message else ""
            data = update.callback_query.data if update.callback_query else ""
            userdata = ";".join([f"{k}:{v}" for k, v in context.user_data.items()])
            text = f"text = {text} and callback data = {data}"
            logger.info(
                "calling function %s with args %s and user_data %s",
                func.__name__,
                text,
                userdata,
            )
            return await func(update, context)

        return wrapper

    return inner
