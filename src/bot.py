from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    PicklePersistence,
)

from categories.conversation import (
    categories_conversation,
    send_groups_for_manage_categories,
)
from config import config, create_logger
from constants.states import (
    AUTH,
    CAT,
    EXPENSE_ADD,
    EXPENSE_MANAGE,
    GROUPS_MANAGE,
    REPORTS,
)
from expenses.conversation_add_expense import (
    add_expense_conversation,
    send_groups_for_add_expenses,
)
from expenses.conversation_manage_expense import (
    expense_manage_conversation,
    send_groups_for_manage_expenses,
)
from groups.conversation import groups_conversation, send_menu_manage_groups
from groups.groups import register_user
from reports.conversation import reports_conversation, send_group_for_report_menu

logger = create_logger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id: int = update.effective_user.id if update.effective_user else 0
    await context.bot.set_my_commands(
        [
            BotCommand("add", "Записать расход"),
            BotCommand("reports", "Отчеты расходов"),
            BotCommand("cats", "Управление категориями"),
            BotCommand("manage", "Управление расходами"),
            BotCommand("groups", "Управление группами"),
        ]
    )
    register_user(id, update.effective_user.username)

    await update.message.reply_text(
        "Добро пожаловать в Money Tracker, теперь создайте через меню группы для учета расходов"
    )
    return AUTH


def main() -> None:
    bot_persistence = PicklePersistence(filepath="persistance_states")

    bot = (
        ApplicationBuilder()
        .token(config.bot_token)
        .persistence(persistence=bot_persistence)
        .build()
    )

    menu = [
        CommandHandler("add", send_groups_for_add_expenses),
        CommandHandler("cats", send_groups_for_manage_categories),
        CommandHandler("reports", send_group_for_report_menu),
        CommandHandler("manage", send_groups_for_manage_expenses),
        CommandHandler("groups", send_menu_manage_groups),
    ]

    conv_handler = ConversationHandler(
        name="menu",
        persistent=True,
        entry_points=[CommandHandler("start", start)],
        states={
            AUTH: [*menu],
            CAT: [categories_conversation],
            EXPENSE_ADD: [add_expense_conversation],
            EXPENSE_MANAGE: [expense_manage_conversation],
            GROUPS_MANAGE: [groups_conversation],
            REPORTS: [reports_conversation],
        },
        fallbacks=[*menu],
    )
    bot.add_handler(conv_handler)
    bot.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
