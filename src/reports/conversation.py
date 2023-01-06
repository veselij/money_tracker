from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler

from backend.db import ReportRequest, User
from config import create_logger
from constants import callbacks as cb
from constants.states import AUTH, REPORTS
from constants.userdata import UserData
from decorators import delete_old_message, log
from groups.groups import save_group, send_groups
from reports.reports import func_map
from utils import send_message

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
async def send_group_for_report_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    return await send_groups(update, context, send_report_menu, REPORTS)


@log(logger)
async def send_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await save_group(update, context)
    keyboard = [
        [InlineKeyboardButton("Список", callback_data=cb.report_list)],
        [InlineKeyboardButton("Тотал", callback_data=cb.report_total)],
        [InlineKeyboardButton("Тренд", callback_data=cb.report_trend)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "Выберете отчет расходов", mark_up)
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
    await send_message(update, context, "Выберете чьи расходы", mark_up)
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
    await send_message(update, context, "Выберете сортировку", mark_up)

    return REPORTS


@log(logger)
@delete_old_message(logger)
async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    func = func_map[context.user_data[UserData.func]]
    all = context.user_data[UserData.all]
    group = context.user_data[UserData.group]
    report = ReportRequest(
        user=User(int(update.effective_user.id)),
        group=group,
        ordering=query.data,
        all=all,
    )
    context.user_data[UserData.msg_id] = await func(query, report)

    return END


reports_conversation = ConversationHandler(
    name="reports",
    persistent=True,
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(send_report_menu, pattern=cb.groups_id),
        CallbackQueryHandler(select_report_type, pattern=cb.report_list),
        CallbackQueryHandler(select_report_type, pattern=cb.report_total),
        CallbackQueryHandler(select_report_type, pattern=cb.report_trend),
        CallbackQueryHandler(select_ordering, pattern=cb.report_my),
        CallbackQueryHandler(select_ordering, pattern=cb.report_all),
        CallbackQueryHandler(send_report, pattern=cb.report_by_date),
        CallbackQueryHandler(send_report, pattern=cb.report_by_amount),
    ],
    states={
        REPORTS: [
            CallbackQueryHandler(send_report_menu, pattern=cb.groups_id),
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
