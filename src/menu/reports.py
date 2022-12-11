import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from menu import callbacks as cb
from menu.states import AUTH, REPORTS
from menu.utils import delete_old_message
from report_manager import func_map

logger = logging.getLogger(__name__)


async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_old_message(update, context)
    keyboard = [
        [InlineKeyboardButton("Список", callback_data=cb.report_list)],
        [InlineKeyboardButton("Тотал", callback_data=cb.report_total)],
        [InlineKeyboardButton("Тренд", callback_data=cb.report_trend)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(
        "Выберете отчет расходов", reply_markup=mark_up
    )
    context.user_data["msg"] = int(msg.id)
    return REPORTS


async def select_report_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["func"] = query.data

    keyboard = [
        [InlineKeyboardButton("Мои", callback_data=cb.report_my)],
        [InlineKeyboardButton("Общие", callback_data=cb.report_all)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    msg = await query.edit_message_text("Выберете чьи расходы", reply_markup=mark_up)
    context.user_data["msg"] = int(msg.id)
    return REPORTS


async def select_ordering(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    group = True if query.data == cb.report_all else False
    context.user_data["group"] = group

    if context.user_data["func"] in [cb.report_total, cb.report_trend]:
        update.callback_query.data = "1"
        return await send_report(update, context)

    keyboard = [
        [InlineKeyboardButton("По дате", callback_data=cb.report_by_date)],
        [InlineKeyboardButton("По расходу", callback_data=cb.report_by_amount)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    msg = await query.edit_message_text("Выберете сортировку", reply_markup=mark_up)
    context.user_data["msg"] = int(msg.id)
    return REPORTS


async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    func = func_map[context.user_data["func"]]
    group = context.user_data["group"]
    msg = await func(query, int(update.effective_user.id), group, query.data)
    context.user_data["msg"] = int(msg.id)
    return AUTH
