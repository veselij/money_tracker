from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import constants.callbacks as cb
from backend.db import Group, User, db_client
from config import create_logger
from constants.states import (
    AUTH,
    GROUPS_ADD_USER,
    GROUPS_CREATE,
    GROUPS_MANAGE,
    GROUPS_REMOVE_USER,
)
from constants.userdata import UserData
from decorators import log
from groups.groups import add_user_to_group, delete_group, delete_user_from_group
from utils import make_inline_menu, send_message

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
async def send_menu_manage_groups(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    keyboard = [
        [InlineKeyboardButton("Создать", callback_data=cb.groups_create)],
        [InlineKeyboardButton("Удалить", callback_data=cb.groups_delete)],
        [InlineKeyboardButton("Добавить в группу", callback_data=cb.groups_add_user)],
        [
            InlineKeyboardButton(
                "Удалить из группы", callback_data=cb.groups_remove_user
            )
        ],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "Что сделать с группами", mark_up)
    return GROUPS_MANAGE


@log(logger)
async def chouse_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    groups = db_client.get_user_groups(update.effective_user.id)
    replay_markup = make_inline_menu(groups)
    context.user_data[UserData.group_action] = query.data
    await send_message(update, context, "Выберете группу", replay_markup)
    return GROUPS_MANAGE


@log(logger)
async def perform_group_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    action = context.user_data.get(UserData.group_action)
    group = Group(int(query.data.split()[1]))
    context.user_data[UserData.group] = group

    message = ""
    status = END
    if action == cb.groups_add_user:
        message = "Введите user id"
        status = GROUPS_ADD_USER
    elif action == cb.groups_remove_user:
        message = "Введите user id"
        status = GROUPS_REMOVE_USER
    elif action == cb.groups_delete:
        delete_group(group)
        message = "Группа удалена"
    await send_message(update, context, message)
    return status


@log(logger)
async def request_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await send_message(update, context, "Введите название категории")
    return GROUPS_CREATE


@log(logger)
async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_name = update.message.text
    db_client.create_group(update.effective_user.id, group_name)
    await send_message(update, context, f"Группа {group_name} созадана")
    return END


@log(logger)
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = int(update.message.text)
    except TypeError as e:
        logger.exception(e)
        await send_message(update, context, "Некорректный user id")
        return END
    if not add_user_to_group(context.user_data.get(UserData.group), User(user_id)):
        message = "Пользователь не зарегистрирован в боте."
    else:
        message = "Готово"
    await send_message(update, context, message)
    return END


@log(logger)
async def remove_user_from_group(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    try:
        user_id = int(update.message.text)
    except TypeError as e:
        logger.exception(e)
        await send_message(update, context, "Некорректный user id")
        return END
    delete_user_from_group(context.user_data.get(UserData.group), User(user_id))
    await send_message(update, context, "готово")
    return END


groups_conversation = ConversationHandler(
    name="groups",
    persistent=True,
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(request_group_name, pattern=cb.groups_create),
        CallbackQueryHandler(chouse_group, pattern=cb.groups_delete),
        CallbackQueryHandler(chouse_group, pattern=cb.groups_add_user),
        CallbackQueryHandler(chouse_group, pattern=cb.groups_remove_user),
    ],
    states={
        GROUPS_MANAGE: [
            CallbackQueryHandler(perform_group_action, pattern=cb.groups_id),
            CallbackQueryHandler(request_group_name, pattern=cb.groups_create),
            CallbackQueryHandler(chouse_group, pattern=cb.groups_delete),
            CallbackQueryHandler(chouse_group, pattern=cb.groups_add_user),
            CallbackQueryHandler(chouse_group, pattern=cb.groups_remove_user),
        ],
        GROUPS_CREATE: [
            MessageHandler(~filters.COMMAND, create_group),
        ],
        GROUPS_ADD_USER: [
            MessageHandler(~filters.COMMAND, add_user),
        ],
        GROUPS_REMOVE_USER: [
            MessageHandler(~filters.COMMAND, remove_user_from_group),
        ],
    },
    map_to_parent={END: AUTH},
    fallbacks=[],
)
