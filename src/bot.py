import logging
import re

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
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

from config import config
from db import SqliteClient
from expenses import ExpenseManager
from formater import (
    generate_chart,
    prepare_expense_message,
    prepare_expense_message_last,
)

logger = logging.getLogger(__name__)
AUTH = 0

db_client = SqliteClient()
expense_manger = ExpenseManager(db_client)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id: int = update.effective_user.id if update.effective_user else 0
    if id not in config.allowed_tg_ids:
        await update.message.reply_text("Вы не авторизованы {0}".format(id))
        return ConversationHandler.END
    await context.bot.set_my_commands(
        [
            BotCommand("add", "Записать расход"),
            BotCommand("total", "Свои расходы"),
            BotCommand("total_all", "Общие расходы"),
            BotCommand("last", "Свои расходы список"),
            BotCommand("last_all", "Общие расходы список"),
        ]
    )
    await update.message.reply_text("Добро пожаловать в Money Tracker {0}".format(id))
    return AUTH


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    categories = list(expense_manger._categories.items())
    step = 3
    keyboard = []
    for i in range(0, len(categories), step):
        sub_keys = []
        for cat in categories[i : i + step]:
            sub_keys.append(InlineKeyboardButton(cat[1], callback_data=str(cat[0])))
        keyboard.append(sub_keys)

    replay_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберет категорию", reply_markup=replay_markup)
    return AUTH


async def get_expenses_total(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user:
        expenses = expense_manger.get_expenses_total(int(update.effective_user.id))
        message, chart_data = prepare_expense_message(
            expenses, int(update.effective_user.id)
        )
        chart = generate_chart(chart_data)
        await context.bot.send_photo(update.effective_user.id, chart, message)
    return AUTH


async def get_expenses_total_all(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if update.effective_user:
        expenses = expense_manger.get_expenses_total()
        message, chart_data = prepare_expense_message(expenses)
        chart = generate_chart(chart_data)
        await context.bot.send_photo(update.effective_user.id, chart, message)
    return AUTH


async def get_last_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user:
        expenses = expense_manger.get_expenses_last(update.effective_user.id)
        message = prepare_expense_message_last(expenses, update.effective_user.id)
        await context.bot.send_message(update.effective_user.id, message)
    return AUTH


async def get_last_expenses_all(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if update.effective_user:
        expenses = expense_manger.get_expenses_last()
        message = prepare_expense_message_last(expenses)
        await context.bot.send_message(update.effective_user.id, message)
    return AUTH


async def del_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id = int(update.message.text.replace("/del", ""))
    expense_manger.del_expense(id)
    await update.message.reply_text(f"Расход номер {id} удален")
    return AUTH


async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text.replace("/catadd", "").strip()
    expense_manger.insert_category(category)
    await update.message.reply_text(f"Категория {category} добавлена")
    expense_manger._load_categories()
    return AUTH


async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text.replace("/catdel", "").strip()
    expense_manger.delete_category(category)
    await update.message.reply_text(f"Категория {category} удалена")
    expense_manger._load_categories()
    return AUTH


async def insert_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = re.match(r"(\d+)(.*)", update.message.text)
    if not text or not text.group(0) or not text.group(1):
        await update.message.reply_text("неправильный формат")
        return AUTH
    if not update.effective_user:
        return AUTH
    if not context.user_data:
        await update.message.reply_text("сначала выберете категорию")
        return AUTH
    category = context.user_data["category"]
    id = expense_manger.save_expense(
        int(text.group(1)), category, text.group(2), update.effective_user.id
    )
    await update.message.reply_text(
        "расход *{0}* руб добавлен в категорию *{1}* удалить /del{2}".format(
            text.group(1), expense_manger._categories[category], id
        )
    )
    context.user_data.clear()
    return AUTH


async def manual_insert_expense(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = update.message.text.split(",")
    amount, category, comment = "", "", ""
    if len(text) == 3:
        _, amount, category = text
    elif len(text) == 4:
        _, amount, category, comment = text
    else:
        await update.message.reply_text("неправильный формат")
        return AUTH
    categories_reversed = {v: k for k, v in expense_manger.get_categories().items()}
    if not update.effective_user:
        return AUTH
    id = expense_manger.save_expense(
        int(amount),
        categories_reversed[category.strip()],
        comment.strip(),
        update.effective_user.id,
    )
    await update.message.reply_text(
        "расход *{0}* руб добавлен в категорию *{1}* удалить /del{2}".format(
            amount, category, id
        )
    )
    context.user_data.clear()  # type: ignore
    return AUTH


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    id = int(query.data)
    await query.answer()
    context.user_data["category"] = id  # type: ignore
    await query.message.reply_text(
        "Напишите сумму расхода и комментарий для категории *{0}*".format(
            expense_manger._categories[id]
        )
    )
    return AUTH


def create_conversation_states() -> dict:
    handlers = [
        CallbackQueryHandler(category_callback),
        CommandHandler("add", add_expense),
        CommandHandler("total", get_expenses_total),
        CommandHandler("total_all", get_expenses_total_all),
        CommandHandler("last", get_last_expenses),
        CommandHandler("last_all", get_last_expenses_all),
        MessageHandler(filters.Regex("^/del.*") & filters.COMMAND, del_expense),
        MessageHandler(filters.Regex("^/catadd .*") & filters.COMMAND, add_category),
        MessageHandler(filters.Regex("^/catdel .*") & filters.COMMAND, delete_category),
        MessageHandler(
            filters.Regex("^/offadd,.*") & filters.COMMAND, manual_insert_expense
        ),
        MessageHandler(filters.TEXT & ~filters.COMMAND, insert_expense),
    ]
    return {AUTH: handlers}


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
