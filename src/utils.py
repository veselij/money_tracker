from itertools import islice

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from backend.db import Group
from categories.categories import Categories


def make_inline_menu(
    categories: Categories | list[Group],
) -> InlineKeyboardMarkup:
    step = 3
    keyboard = []
    for i in range(0, len(categories), step):
        sub_keys = []
        for cat in islice(categories, i, i + step):
            sub_keys.append(
                InlineKeyboardButton(
                    cat.name, callback_data=f"{cat.__class__.__name__.lower()} {cat.id}"
                )
            )
        keyboard.append(sub_keys)

    replay_markup = InlineKeyboardMarkup(keyboard)
    return replay_markup
