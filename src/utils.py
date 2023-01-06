from itertools import islice

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram._utils.types import ReplyMarkup
from telegram.ext import ContextTypes

from backend.db import Group
from categories.categories import Categories
from config import create_logger
from constants.userdata import UserData
from decorators import delete_old_message

logger = create_logger(__name__)


def make_inline_menu(
    callback_items: Categories | list[Group],
) -> InlineKeyboardMarkup:
    step = 3
    keyboard = []
    for i in range(0, len(callback_items), step):
        sub_keys = []
        for callback_item in islice(callback_items, i, i + step):
            sub_keys.append(
                InlineKeyboardButton(
                    callback_item.name,
                    callback_data=f"{callback_item.__class__.__name__.lower()} {callback_item.id}",
                )
            )
        keyboard.append(sub_keys)

    replay_markup = InlineKeyboardMarkup(keyboard)
    return replay_markup


@delete_old_message(logger)
async def send_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: str,
    reply_markup: ReplyMarkup | None = None,
) -> None:

    context.user_data[UserData.msg_id] = await context.bot.send_message(
        update.effective_user.id, message, reply_markup=reply_markup
    )


def validate_message_expense_ids(message: str, id_map: dict) -> list[int] | None:
    ids = message.split(",")
    expenses = []
    if not ids:
        return None
    for id in ids:
        try:
            expense_id = int(id)
        except ValueError:
            return None
        if expense_id not in id_map:
            continue
        expenses.append(expense_id)
    return expenses
