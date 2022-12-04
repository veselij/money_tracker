import logging
import re

from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

import menu.callbacks as cb
from config import config
from menu.cats import (
    add_category,
    chouse_category_name_to_delete,
    delete_category,
    request_category_name_to_add,
    send_menu_manage_categories,
)
from menu.expense import (
    insert_expense,
    manual_insert_expense,
    request_expense_anount_for_category,
    send_categories,
)
from menu.manage_expense import (
    delete_expense,
    delete_expense_request,
    manage_expenses,
    move_expense,
    move_expense_request_categories,
    select_new_category,
)
from menu.reports import report_menu, select_ordering, select_report_type, send_report
from menu.states import AUTH, CAT, DELETE_EXPENSE, MANAGE_EXPENSE, MOVE_EXPENSE, REPORTS

logger = logging.getLogger(__name__)

nums = re.compile(r"\d+")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id: int = update.effective_user.id if update.effective_user else 0
    if id not in config.allowed_tg_ids:
        await update.message.reply_text("Вы не авторизованы {0}".format(id))
        return ConversationHandler.END
    await context.bot.set_my_commands(
        [
            BotCommand("add", "Записать расход"),
            BotCommand("reports", "Отчеты расходов"),
            BotCommand("cats", "Управление категориями"),
            BotCommand("manage", "Управление расходами"),
        ]
    )
    await update.message.reply_text("Добро пожаловать в Money Tracker {0}".format(id))
    return AUTH


def create_conversation_states() -> dict:
    menu = [
        CommandHandler("add", send_categories),
        CommandHandler("cats", send_menu_manage_categories),
        CommandHandler("reports", report_menu),
        CommandHandler("manage", manage_expenses),
    ]
    handlers = {
        AUTH: [
            CallbackQueryHandler(request_expense_anount_for_category, pattern=nums),
            MessageHandler(filters.TEXT & ~filters.COMMAND, insert_expense),
            MessageHandler(
                filters.Regex("^/offadd,.*") & filters.COMMAND, manual_insert_expense
            ),
            *menu,
        ],
        CAT: [
            CallbackQueryHandler(request_category_name_to_add, pattern=cb.add_category),
            MessageHandler(~filters.COMMAND, add_category),
            CallbackQueryHandler(
                chouse_category_name_to_delete, pattern=cb.delete_category
            ),
            CallbackQueryHandler(delete_category),
            *menu,
        ],
        REPORTS: [
            CallbackQueryHandler(select_report_type, pattern=cb.report_list),
            CallbackQueryHandler(select_report_type, pattern=cb.report_total),
            CallbackQueryHandler(select_ordering, pattern=cb.report_my),
            CallbackQueryHandler(select_ordering, pattern=cb.report_all),
            CallbackQueryHandler(send_report, pattern=cb.report_by_date),
            CallbackQueryHandler(send_report, pattern=cb.report_by_amount),
            *menu,
        ],
        MANAGE_EXPENSE: [
            CallbackQueryHandler(
                move_expense_request_categories, pattern=cb.manage_move_expense
            ),
            CallbackQueryHandler(
                delete_expense_request, pattern=cb.manage_delete_expense
            ),
            *menu,
        ],
        DELETE_EXPENSE: [
            MessageHandler(~filters.COMMAND, delete_expense),
            *menu,
        ],
        MOVE_EXPENSE: [
            CallbackQueryHandler(select_new_category, pattern=nums),
            MessageHandler(~filters.COMMAND, move_expense),
            *menu,
        ],
    }
    return handlers


def main() -> None:
    bot_persistence = PicklePersistence(filepath="persistance_states")

    bot = (
        ApplicationBuilder()
        .token(config.bot_token)
        .persistence(persistence=bot_persistence)
        .build()
    )

    conv_handler = ConversationHandler(
        name="menu",
        persistent=True,
        entry_points=[CommandHandler("start", start)],
        states=create_conversation_states(),
        fallbacks=[],
    )
    bot.add_handler(conv_handler)
    bot.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
