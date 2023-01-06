import logging
from functools import wraps

from telegram import Message, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from config import create_logger
from constants.userdata import UserData

logger = create_logger(__name__)


def delete_old_message(logger: logging.Logger):
    def inner(func):
        @wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            if UserData.msg_id in context.user_data:
                old_msg_id = context.user_data.pop(UserData.msg_id)
                if old_msg_id and update.effective_user:
                    if isinstance(old_msg_id, Message):
                        old_msg_id = old_msg_id.id
                    try:
                        await context.bot.delete_message(
                            update.effective_user.id, old_msg_id
                        )
                    except BadRequest as e:
                        logger.exception(e)
                        pass
            return await func(update, context, *args, **kwargs)

        return wrapper

    return inner


def log(logger: logging.Logger):
    def inner(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text if update.message else ""
            data = (
                update.callback_query.data
                if update.callback_query
                else "no callback_query"
            )
            if context.user_data:
                userdata = ";".join([f"{k}:{v}" for k, v in context.user_data.items()])
            else:
                userdata = ""
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
