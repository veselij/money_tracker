from itertools import islice

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from categories import Categories


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
