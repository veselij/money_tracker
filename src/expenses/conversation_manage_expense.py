from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import constants.callbacks as cb
from backend.db import Category, ReportRequest, User, db_client
from categories.categories import Categories
from config import create_logger
from constants.states import AUTH, EXPENSE_DELETE, EXPENSE_MANAGE, EXPENSE_MOVE
from constants.userdata import UserData
from decorators import log
from expenses.expenses import ExpenseManager
from groups.groups import save_group, send_groups
from reports.reports import get_expenses_list_with_ids
from utils import make_inline_menu, send_message, validate_message_expense_ids

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
async def send_groups_for_manage_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    return await send_groups(update, context, send_menu_manage_expenses, EXPENSE_MANAGE)


@log(logger)
async def send_menu_manage_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await save_group(update, context)

    keyboard = [
        [InlineKeyboardButton("Перенести", callback_data=cb.manage_move_expense)],
        [InlineKeyboardButton("Удалить", callback_data=cb.manage_delete_expense)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "Что сделать с расходами", mark_up)
    return EXPENSE_MANAGE


@log(logger)
async def move_expense_request_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:

    message, replay_markup = await _build_id_map(update, context)

    await send_message(
        update, context, f"{message}\n\nВыберете новую категорию", replay_markup
    )
    return EXPENSE_MOVE


@log(logger)
async def select_new_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.category] = Category(int(query.data.split()[1]))

    await send_message(
        update,
        context,
        query.message.text
        + "\n\nВведите номер или номера расходов для удаления через запятую",
    )
    return EXPENSE_MOVE


@log(logger)
async def move_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id_map = context.user_data.get(UserData.id_map)
    new_category = context.user_data.get(UserData.category)
    ids = validate_message_expense_ids(update.message.text, id_map)
    if not ids:
        await send_message(update, context, "неверный формат, попробуйте снова")
        return END

    expense_manger = ExpenseManager(
        db_client,
        User(update.effective_user.id),
        context.user_data.get(UserData.group),
    )
    for id in ids:
        expense_manger.move_expense(id, new_category.id)
    await send_message(update, context, "готово")
    return END


@log(logger)
async def delete_expense_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    message, _ = await _build_id_map(update, context)
    await send_message(
        update,
        context,
        f"{message}\n\nВведите номер или номера расходов для удаления через запятую",
    )
    return EXPENSE_DELETE


@log(logger)
async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id_map = context.user_data.get(UserData.id_map)
    ids = validate_message_expense_ids(update.message.text, id_map)
    if not ids:
        await send_message(update, context, "неверный формат, попробуйте снова")
        return END
    expense_manger = ExpenseManager(
        db_client,
        User(update.effective_user.id),
        context.user_data.get(UserData.group),
    )
    for id in ids:
        expense_manger.del_expense(id)
    await send_message(update, context, "готово")
    return END


async def _build_id_map(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> tuple[str, InlineKeyboardMarkup]:
    query = update.callback_query
    await query.answer()
    group = context.user_data.get(UserData.group)
    expenses, id_map = get_expenses_list_with_ids(
        ReportRequest(User(update.effective_user.id), group, cb.report_by_date)
    )
    context.user_data[UserData.id_map] = id_map
    categories = Categories(db_client, group)
    replay_markup = make_inline_menu(categories)
    return expenses, replay_markup


expense_manage_conversation = ConversationHandler(
    name="manage_expense",
    persistent=True,
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(send_menu_manage_expenses, pattern=cb.groups_id),
        CallbackQueryHandler(
            move_expense_request_categories, pattern=cb.manage_move_expense
        ),
        CallbackQueryHandler(delete_expense_request, pattern=cb.manage_delete_expense),
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
