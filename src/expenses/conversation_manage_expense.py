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
from categories.categories import Categories
from config import create_logger
from constants.states import AUTH, EXPENSE_DELETE, EXPENSE_MANAGE, EXPENSE_MOVE
from constants.userdata import UserData
from decorators import delete_old_message, log
from expenses.expenses import ExpenseManager
from groups.groups import send_groups
from reports.reports import get_expenses_list_with_ids
from utils import make_inline_menu

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
@delete_old_message(logger)
async def send_groups_for_manage_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await send_groups(update, context)
    return EXPENSE_MANAGE


@log(logger)
async def send_menu_manage_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.group_id] = int(query.data.split()[1])

    keyboard = [
        [InlineKeyboardButton("Перенести", callback_data=cb.manage_move_expense)],
        [InlineKeyboardButton("Удалить", callback_data=cb.manage_delete_expense)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Что сделать с расходами", reply_markup=mark_up
    )

    return EXPENSE_MANAGE


@log(logger)
async def move_expense_request_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    group_id = context.user_data.get(UserData.group_id)
    expenses, id_map = get_expenses_list_with_ids(
        update.effective_user.id,
        group_id,
        False,
        cb.report_by_date,
    )
    context.user_data[UserData.id_map] = id_map
    categories = Categories(db_client, group_id)
    replay_markup = make_inline_menu(categories)
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        f"{expenses}\n\nВыберете новую категорию", reply_markup=replay_markup
    )
    return EXPENSE_MOVE


@log(logger)
async def select_new_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.category_id] = int(query.data.split()[1])
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        query.message.text
        + "\n\nВведите номер или номера расходов для удаления через запятую",
    )
    return EXPENSE_MOVE


@log(logger)
@delete_old_message(logger)
async def move_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id_map = context.user_data.get(UserData.id_map)
    new_category = context.user_data.get(UserData.category_id)
    ids = update.message.text.split(",")
    for id in ids:
        try:
            expense_id = id_map.get(int(id))
        except ValueError as e:
            logger.critical(e)
            continue
        if not expense_id:
            continue
        expense_manger = ExpenseManager(
            db_client,
            update.effective_user.id,
            context.user_data.get(UserData.group_id),
        )
        expense_manger.move_expense(expense_id, new_category)
    await update.message.reply_text("готово")
    return END


@log(logger)
async def delete_expense_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    expenses, id_map = get_expenses_list_with_ids(
        update.effective_user.id,
        context.user_data.get(UserData.group_id),
        False,
        cb.report_by_date,
    )
    context.user_data[UserData.id_map] = id_map
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        f"{expenses}\n\nВведите номер или номера расходов для удаления через запятую",
    )
    return EXPENSE_DELETE


@log(logger)
@delete_old_message(logger)
async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id_map = context.user_data.get(UserData.id_map)
    ids = update.message.text.split(",")
    for id in ids:
        expense_manger = ExpenseManager(
            db_client,
            update.effective_user.id,
            context.user_data.get(UserData.group_id),
        )
        try:
            expense_manger.del_expense(id_map.get(int(id)))
        except ValueError as e:
            logger.critical(e)
            continue
    context.user_data[UserData.msg_id] = await update.message.reply_text("готово")
    return END


expense_manage_conversation = ConversationHandler(
    name="manage_expense",
    persistent=True,
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(send_menu_manage_expenses, pattern=cb.groups_id),
    ],
    states={
        EXPENSE_MANAGE: [
            CallbackQueryHandler(send_menu_manage_expenses, pattern=cb.groups_id),
            CallbackQueryHandler(
                move_expense_request_categories, pattern=cb.manage_move_expense
            ),
            CallbackQueryHandler(
                delete_expense_request, pattern=cb.manage_delete_expense
            ),
        ],
        EXPENSE_MOVE: [
            CallbackQueryHandler(select_new_category, pattern=cb.category_id),
            MessageHandler(~filters.COMMAND, move_expense),
        ],
        EXPENSE_DELETE: [
            MessageHandler(~filters.COMMAND, delete_expense),
        ],
    },
    map_to_parent={END: AUTH},
    fallbacks=[],
)
