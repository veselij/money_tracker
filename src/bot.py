import logging
import re
from functools import partial
from itertools import islice

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

import callbacks as cb
from categories import Categories
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
CAT = 1
REPORTS = 2

nums = re.compile("\d+")

db_client = SqliteClient()
expense_manger = ExpenseManager(db_client)
categories = Categories(db_client)


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
        ]
    )
    await update.message.reply_text("Добро пожаловать в Money Tracker {0}".format(id))
    return AUTH


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    step = 3
    keyboard = []
    for i in range(0, len(categories), step):
        sub_keys = []
        for cat in islice(categories, i, i + step):
            sub_keys.append(InlineKeyboardButton(cat.name, callback_data=str(cat.id)))
        keyboard.append(sub_keys)

    replay_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберет категорию", reply_markup=replay_markup)
    return AUTH


async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Свои расходы", callback_data=cb.report_personal)],
        [InlineKeyboardButton("Общие расходы", callback_data=cb.report_all)],
        [
            InlineKeyboardButton(
                "Свои список расходы", callback_data=cb.report_personal_list
            )
        ],
        [
            InlineKeyboardButton(
                "Общие список расходы", callback_data=cb.report_all_list
            )
        ],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберете отчет", reply_markup=mark_up)
    return REPORTS


async def get_expenses_total(
    update: Update, context: ContextTypes.DEFAULT_TYPE, all: bool = False
) -> int:
    query = update.callback_query
    await query.answer()
    if not update.effective_user:
        return AUTH
    user_id = int(update.effective_user.id) if not all else None
    expenses = expense_manger.get_expenses_total(user_id)
    message, chart_data = prepare_expense_message(expenses, user_id)
    chart = generate_chart(chart_data)
    await query.delete_message()
    await context.bot.send_photo(update.effective_user.id, chart, message)
    return AUTH


get_expenses_total_all = partial(get_expenses_total, all=True)


async def get_last_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE, all: bool = False
) -> int:
    query = update.callback_query
    await query.answer()
    if not update.effective_user:
        return AUTH

    user_id = int(update.effective_user.id) if not all else None
    expenses = expense_manger.get_expenses_last(user_id)
    message = prepare_expense_message_last(expenses, user_id)
    await query.edit_message_text(message)
    return AUTH


get_last_expenses_all = partial(get_last_expenses, all=True)


async def del_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    id = int(update.message.text.replace("/del", ""))
    expense_manger.del_expense(id)
    await update.message.reply_text(f"Расход номер {id} удален")
    return AUTH


async def manage_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Удалить категорию", callback_data=cb.delete_category)],
        [InlineKeyboardButton("Добавить категорию", callback_data=cb.add_category)],
    ]
    mark_up = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Управление категориями", reply_markup=mark_up)
    return CAT


async def catch_category_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите название категории")
    return CAT


async def chouse_category_to_delete(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    step = 3
    keyboard = []
    for i in range(0, len(categories), step):
        sub_keys = []
        for cat in islice(categories, i, i + step):
            sub_keys.append(InlineKeyboardButton(cat.name, callback_data=str(cat.id)))
        keyboard.append(sub_keys)

    replay_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберет категорию", reply_markup=replay_markup)
    return CAT


async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text
    categories.append(category)
    await update.message.reply_text(f"Категория {category} добавлена")
    return AUTH


async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    id = int(query.data)
    del categories[id]
    await query.edit_message_text(f"Категория удалена")
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
    cat = categories[category]
    await update.message.reply_text(
        "расход {0} руб добавлен в категорию {1} удалить /del{2}".format(
            text.group(1), cat.name, id
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
    if not update.effective_user:
        return AUTH
    try:
        id = expense_manger.save_expense(
            int(amount),
            categories.get_category_id(category.strip()),
            comment.strip(),
            update.effective_user.id,
        )
        await update.message.reply_text(
            "расход {0} руб добавлен в категорию {1} удалить /del{2}".format(
                amount, category, id
            )
        )
    except KeyError:
        await update.message.reply_text(
            "такой категории нет {0}".format(category.strip())
        )
    return AUTH


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    id = int(query.data)
    await query.answer()
    context.user_data["category"] = id  # type: ignore
    category = categories[id]
    await query.message.reply_text(
        "Напишите сумму расхода и комментарий для категории {0}".format(category.name)
    )
    return AUTH


def create_conversation_states() -> dict:
    handlers = {
        AUTH: [
            CallbackQueryHandler(category_callback, pattern=nums),
            CommandHandler("add", add_expense),
            CommandHandler("cats", manage_categories),
            CommandHandler("reports", report_menu),
            MessageHandler(filters.Regex("^/del.*") & filters.COMMAND, del_expense),
            MessageHandler(
                filters.Regex("^/offadd,.*") & filters.COMMAND, manual_insert_expense
            ),
            MessageHandler(filters.TEXT & ~filters.COMMAND, insert_expense),
        ],
        CAT: [
            CallbackQueryHandler(catch_category_name, pattern=cb.add_category),
            CallbackQueryHandler(chouse_category_to_delete, pattern=cb.delete_category),
            CallbackQueryHandler(delete_category),
            MessageHandler(~filters.COMMAND, add_category),
            CommandHandler("add", add_expense),
            CommandHandler("cats", manage_categories),
            CommandHandler("reports", report_menu),
        ],
        REPORTS: [
            CallbackQueryHandler(get_expenses_total, pattern=cb.report_personal),
            CallbackQueryHandler(get_expenses_total_all, pattern=cb.report_all),
            CallbackQueryHandler(get_last_expenses, pattern=cb.report_personal_list),
            CallbackQueryHandler(get_last_expenses_all, pattern=cb.report_all_list),
            CommandHandler("add", add_expense),
            CommandHandler("cats", manage_categories),
            CommandHandler("reports", report_menu),
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
