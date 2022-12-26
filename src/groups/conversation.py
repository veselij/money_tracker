from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import constants.callbacks as cb
from backend.db import db_client
from config import create_logger
from constants.states import AUTH, GROUPS_CREATE, GROUPS_MANAGE
from constants.userdata import UserData
from decorators import delete_old_message, log

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
@delete_old_message(logger)
async def send_menu_manage_groups(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    keyboard = [
        [InlineKeyboardButton("Создать", callback_data=cb.groups_create)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    context.user_data[UserData.msg_id] = await context.bot.send_message(
        update.effective_user.id, "Что сделать с группами", reply_markup=mark_up
    )
    return GROUPS_MANAGE


@log(logger)
async def request_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Введите название категории"
    )
    return GROUPS_CREATE


@log(logger)
@delete_old_message(logger)
async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group = update.message.text
    db_client.create_group(update.effective_user.id, group)
    context.user_data[UserData.msg_id] = await update.message.reply_text(
        f"Группа {group} созадана"
    )
    return END


groups_conversation = ConversationHandler(
    name="groups",
    persistent=True,
    entry_points=[CallbackQueryHandler(request_group_name, pattern=cb.groups_create)],
    states={
        GROUPS_MANAGE: [
            CallbackQueryHandler(request_group_name, pattern=cb.groups_create),
        ],
        GROUPS_CREATE: [
            MessageHandler(~filters.COMMAND, create_group),
        ],
    },
    map_to_parent={END: AUTH},
    fallbacks=[],
)
