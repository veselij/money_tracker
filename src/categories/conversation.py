from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from backend.db import db_client
from categories.categories import Categories
from config import create_logger
from constants import callbacks as cb
from constants.states import AUTH, CAT, CAT_ADD, CAT_DEL
from constants.userdata import UserData
from decorators import delete_old_message, log
from groups.groups import send_groups
from utils import make_inline_menu

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
@delete_old_message(logger)
async def send_groups_for_manage_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await send_groups(update, context)
    return CAT


@log(logger)
async def send_menu_manage_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    keyboard = [
        [InlineKeyboardButton("Добавить", callback_data=cb.category_add)],
        [InlineKeyboardButton("Удалить", callback_data=cb.category_delete)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.group_id] = int(query.data.split()[1])
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Категории:", reply_markup=mark_up
    )

    return CAT


@log(logger)
async def request_category_name_to_add(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Введите название категории"
    )

    return CAT_ADD


@delete_old_message(logger)
@log(logger)
async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text
    categories = Categories(db_client, context.user_data.get(UserData.group_id))
    categories.append(category)
    context.user_data[UserData.msg_id] = await update.message.reply_text(
        f"Категория {category} добавлена"
    )
    return END


@log(logger)
async def chouse_category_name_to_delete(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    categories = Categories(db_client, context.user_data.get(UserData.group_id))
    replay_markup = make_inline_menu(categories)
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Выберет категорию", reply_markup=replay_markup
    )

    return CAT_DEL


@log(logger)
async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    id = int(query.data.split()[1])
    categories = Categories(db_client, context.user_data.get(UserData.group_id))
    del categories[id]
    await query.edit_message_text("Категория удалена")
    return END


categories_conversation = ConversationHandler(
    name="categories",
    persistent=True,
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(send_menu_manage_categories, pattern=cb.groups_id),
    ],
    states={
        CAT: [
            CallbackQueryHandler(send_menu_manage_categories, pattern=cb.groups_id),
            CallbackQueryHandler(request_category_name_to_add, pattern=cb.category_add),
            CallbackQueryHandler(
                chouse_category_name_to_delete, pattern=cb.category_delete
            ),
        ],
        CAT_ADD: [
            MessageHandler(~filters.COMMAND, add_category),
        ],
        CAT_DEL: [
            CallbackQueryHandler(delete_category),
        ],
    },
    map_to_parent={END: AUTH},
    fallbacks=[],
)
