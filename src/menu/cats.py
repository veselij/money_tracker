from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from categories import categories
from config import create_logger, log
from menu import callbacks as cb
from menu.states import AUTH, CAT
from menu.utils import delete_old_message, make_category_inline_menu

logger = create_logger(__name__)


async def send_menu_manage_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await delete_old_message(update, context)
    keyboard = [
        [InlineKeyboardButton("Добавить", callback_data=cb.add_category)],
        [InlineKeyboardButton("Удалить", callback_data=cb.delete_category)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text("Категории:", reply_markup=mark_up)
    context.user_data["msg"] = int(msg.id)
    return CAT


async def request_category_name_to_add(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите название категории")
    return CAT


@log(logger)
async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text
    categories.append(category)
    await update.message.reply_text(f"Категория {category} добавлена")
    return AUTH


async def chouse_category_name_to_delete(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    replay_markup = make_category_inline_menu(categories)
    await query.edit_message_text("Выберет категорию", reply_markup=replay_markup)
    return CAT


@log(logger)
async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    id = int(query.data)
    del categories[id]
    await query.edit_message_text("Категория удалена")
    return AUTH
