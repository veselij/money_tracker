from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler

from config import create_logger
from constants import callbacks as cb
from constants.states import AUTH, REPORTS
from constants.userdata import UserData
from decorators import delete_old_message, log
from groups.groups import send_groups
from reports.reports import func_map

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
@delete_old_message(logger)
async def send_group_for_report_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await send_groups(update, context)
    return REPORTS


@log(logger)
async def send_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.group_id] = int(query.data)
    keyboard = [
        [InlineKeyboardButton("Список", callback_data=cb.report_list)],
        [InlineKeyboardButton("Тотал", callback_data=cb.report_total)],
        [InlineKeyboardButton("Тренд", callback_data=cb.report_trend)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Выберете отчет расходов", reply_markup=mark_up
    )

    return REPORTS


@log(logger)
async def select_report_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.func] = query.data

    keyboard = [
        [InlineKeyboardButton("Мои", callback_data=cb.report_my)],
        [InlineKeyboardButton("Общие", callback_data=cb.report_all)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Выберете чьи расходы", reply_markup=mark_up
    )

    return REPORTS


@log(logger)
async def select_ordering(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.all] = True if query.data == cb.report_all else False

    if context.user_data.get(UserData.func) in [cb.report_total, cb.report_trend]:
        update.callback_query.data = "1"
        return await send_report(update, context)

    keyboard = [
        [InlineKeyboardButton("По дате", callback_data=cb.report_by_date)],
        [InlineKeyboardButton("По расходу", callback_data=cb.report_by_amount)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    context.user_data["msg"] = await query.edit_message_text(
        "Выберете сортировку", reply_markup=mark_up
    )

    return REPORTS


@log(logger)
@delete_old_message(logger)
async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    func = func_map[context.user_data[UserData.func]]
    all = context.user_data[UserData.all]
    group_id = context.user_data[UserData.group_id]
    context.user_data[UserData.msg_id] = await func(
        query, int(update.effective_user.id), group_id, all, query.data
    )

    return END


reports_conversation = ConversationHandler(
    name="reports",
    persistent=True,
    entry_points=[
        CallbackQueryHandler(send_report_menu, pattern=cb.nums),
    ],
    states={
        REPORTS: [
            CallbackQueryHandler(send_report_menu, pattern=cb.nums),
            CallbackQueryHandler(select_report_type, pattern=cb.report_list),
            CallbackQueryHandler(select_report_type, pattern=cb.report_total),
            CallbackQueryHandler(select_report_type, pattern=cb.report_trend),
            CallbackQueryHandler(select_ordering, pattern=cb.report_my),
            CallbackQueryHandler(select_ordering, pattern=cb.report_all),
            CallbackQueryHandler(send_report, pattern=cb.report_by_date),
            CallbackQueryHandler(send_report, pattern=cb.report_by_amount),
        ]
    },
    map_to_parent={END: AUTH},
    fallbacks=[],
)