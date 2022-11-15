import re

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
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
            BotCommand("total", "Посмотреть расходы"),
            BotCommand("total_all", "Посмотреть расходы всех"),
            BotCommand("last", "Посмотреть последние 10 расходов"),
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
        message = prepare_expense_message_last(
            expenses, expense_manger.get_categories()
        )
        await context.bot.send_message(
            update.effective_user.id, message, parse_mode=ParseMode.MARKDOWN_V2
        )
    return AUTH


async def del_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id = int(update.message.text.replace("/del", ""))
    expense_manger.del_expense(id)
    await update.message.reply_markdown_v2(f"Расход номер {id} удален")
    return AUTH


async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text.replace("/catadd", "").strip()
    expense_manger.insert_category(category)
    await update.message.reply_markdown_v2(f"Категория {category} добавлена")
    expense_manger._load_categories()
    return AUTH


async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text.replace("/catdel", "").strip()
    expense_manger.delete_category(category)
    await update.message.reply_markdown_v2(f"Категория {category} удалена")
    expense_manger._load_categories()
    return AUTH


async def insert_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = re.match(r"(\d+)(.*)", update.message.text)
    if not text or not text.group(0) or not text.group(1):
        await update.message.reply_markdown_v2("неправильный формат")
        return AUTH
    if not update.effective_user:
        return AUTH
    if not context.user_data:
        await update.message.reply_markdown_v2("сначала выберете категорию")
        return AUTH
    category = context.user_data["category"]
    id = expense_manger.save_expense(
        int(text.group(1)), category, text.group(2), update.effective_user.id
    )
    await update.message.reply_markdown_v2(
        "расход *{0}* руб добавлен в категорию *{1}* удалить /del{2}".format(
            text.group(1), expense_manger._categories[category], id
        )
    )
    context.user_data.clear()
    return AUTH


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    id = int(query.data)
    await query.answer()
    context.user_data["category"] = id
    await query.message.reply_markdown_v2(
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
        MessageHandler(filters.Regex("^/del.*"), del_expense),
        MessageHandler(filters.Regex("^/catadd .*"), add_category),
        MessageHandler(filters.Regex("^/catdel .*"), delete_category),
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
    main()
