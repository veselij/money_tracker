from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import menu.callbacks as cb
from categories import categories
from expense_manager import expense_manger
from menu.states import AUTH, DELETE_EXPENSE, MANAGE_EXPENSE, MOVE_EXPENSE
from menu.utils import delete_old_message, make_category_inline_menu
from report_manager import get_expenses_list_with_ids


async def manage_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_old_message(update, context)
    keyboard = [
        [InlineKeyboardButton("Перенести", callback_data=cb.manage_move_expense)],
        [InlineKeyboardButton("Удалить", callback_data=cb.manage_delete_expense)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(
        "Что сделать с расходами", reply_markup=mark_up
    )
    context.user_data["msg"] = int(msg.id)
    return MANAGE_EXPENSE


async def move_expense_request_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    expenses, id_map = get_expenses_list_with_ids(
        update.effective_user.id, False, cb.report_by_date
    )
    context.user_data["id_map"] = id_map
    replay_markup = make_category_inline_menu(categories)
    await query.edit_message_text(
        f"{expenses}\n\nВыберете новую категорию", reply_markup=replay_markup
    )
    return MOVE_EXPENSE


async def select_new_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["new_category"] = int(query.data)
    msg = await query.edit_message_text(
        query.message.text
        + "\n\nВведите номер или номера расходов для удаления через запятую",
    )
    context.user_data["msg"] = msg.id
    return MOVE_EXPENSE


async def move_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id_map = context.user_data["id_map"]
    new_category = context.user_data["new_category"]
    ids = update.message.text.split(",")
    for id in ids:
        expense_manger.move_expense(id_map.get(int(id)), new_category)
    await context.bot.delete_message(update.effective_user.id, context.user_data["msg"])
    await update.message.reply_text("готово")
    return AUTH


async def delete_expense_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    expenses, id_map = get_expenses_list_with_ids(
        update.effective_user.id, False, cb.report_by_date
    )
    context.user_data["id_map"] = id_map
    msg = await query.edit_message_text(
        f"{expenses}\n\nВведите номер или номера расходов для удаления через запятую",
    )
    context.user_data["msg"] = msg.id
    return DELETE_EXPENSE


async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id_map = context.user_data["id_map"]
    ids = update.message.text.split(",")
    for id in ids:
        expense_manger.del_expense(id_map.get(int(id)))
    await context.bot.delete_message(update.effective_user.id, context.user_data["msg"])
    await update.message.reply_text("готово")
    return AUTH
