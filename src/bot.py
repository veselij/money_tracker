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
    filters,
)

from config import config
from db import SqliteClient
from expenses import ExpenseManager

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
        message = expense_manger.get_expenses_total(int(update.effective_user.id))
        await context.bot.send_message(
            update.effective_user.id, message, parse_mode=ParseMode.MARKDOWN_V2
        )
    return AUTH


async def get_last_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user:
        message = expense_manger.get_expenses_last(update.effective_user.id)
        await context.bot.send_message(
            update.effective_user.id, message, parse_mode=ParseMode.MARKDOWN_V2
        )
    return AUTH


async def del_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id = int(update.message.text.replace("/del", ""))
    expense_manger.del_expense(id)
    await update.message.reply_markdown_v2(f"Расход номер {id} удален")
    return AUTH


def create_callback_func_choosing_category(category: int):
    async def callback_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        await query.message.reply_markdown_v2(
            "Напишите сумму расхода и комментарий для категории *{0}*".format(
                expense_manger._categories[category]
            )
        )
        return category

    return callback_func


def create_callback_func_inserting_expence(category: int):
    async def callback_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = re.match(r"(\d+)(.*)", update.message.text)
        if not text or not text.group(0) or not text.group(1):
            await update.message.reply_markdown_v2("неправильный формат")
            return category
        if update.effective_user:
            id = expense_manger.save_expense(
                int(text.group(1)), category, text.group(2), update.effective_user.id
            )
            await update.message.reply_markdown_v2(
                "расход *{0}* руб добавлен в категорию *{1}* удалить /del{2}".format(
                    text.group(1), expense_manger._categories[category], id
                )
            )
        return AUTH

    return callback_func


def create_conversation_states(categories: dict) -> dict:
    handlers = [
        CallbackQueryHandler(
            create_callback_func_choosing_category(c), pattern=re.compile(f"^{c}$")
        )
        for c in categories.keys()
    ]
    handlers.append(CommandHandler("add", add_expense))
    handlers.append(CommandHandler("total", get_expenses_total))
    handlers.append(CommandHandler("last", get_last_expenses))
    handlers.append(MessageHandler(filters.Regex("^/del.*"), del_expense))
    states = {AUTH: handlers}

    for c in categories:
        states[c] = handlers.copy()
        states[c].append(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                create_callback_func_inserting_expence(c),
            )
        )
    return states


def main() -> None:
    bot = ApplicationBuilder().token(config.bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=create_conversation_states(expense_manger._categories),
        fallbacks=[],
    )
    bot.add_handler(conv_handler)

    bot.run_polling()


if __name__ == "__main__":
    main()
