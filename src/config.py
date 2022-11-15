import os
from dataclasses import dataclass

MONTH_START_DAY = 10


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
