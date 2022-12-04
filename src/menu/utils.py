import logging
from itertools import islice

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from categories import Categories

logger = logging.getLogger(__name__)


def make_category_inline_menu(categories: Categories) -> InlineKeyboardMarkup:
    step = 3
    keyboard = []
    for i in range(0, len(categories), step):
        sub_keys = []
        for cat in islice(categories, i, i + step):
            sub_keys.append(InlineKeyboardButton(cat.name, callback_data=str(cat.id)))
        keyboard.append(sub_keys)

    replay_markup = InlineKeyboardMarkup(keyboard)
    return replay_markup


async def delete_old_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    old_msg_id = context.user_data.get("msg", None)
    if old_msg_id:
        try:
            await context.bot.delete_message(update.effective_user.id, old_msg_id)
        except BadRequest as e:
            logger.exception(e)
