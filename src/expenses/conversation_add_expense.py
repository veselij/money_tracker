import re

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import constants.callbacks as cb
from backend.db import User, db_client
from categories.categories import Categories
from config import create_logger
from constants.states import AUTH, EXPENSE_ADD
from constants.userdata import UserData
from decorators import log
from expenses.expenses import ExpenseManager
from groups.groups import save_group, send_groups
from utils import make_inline_menu, send_message

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
async def send_groups_for_add_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    return await send_groups(update, context, send_categories, EXPENSE_ADD)


@log(logger)
async def send_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group = await save_group(update, context)
    categories = Categories(db_client, group)
    if not categories:
        await send_message(
            update, context, "у вам нет категрий для расходов, создайте через меню"
        )
        return END
    await send_message(
        update, context, "выберете категорию", make_inline_menu(categories)
    )
    return EXPENSE_ADD


@log(logger)
async def request_expense_amount_for_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    categories = Categories(db_client, context.user_data.get(UserData.group))
    category = categories[int(query.data.split()[1])]
    context.user_data[UserData.category] = category  # type: ignore
    await send_message(
        update,
        context,
        f"Напишите сумму расхода и комментарий для категории {category.name}",
    )
    return EXPENSE_ADD


@log(logger)
async def insert_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = re.match(r"(\d+)(.*)", update.message.text)

    if not text or not text.group(0) or not text.group(1):
        await update.message.reply_text("неправильный формат")
        return EXPENSE_ADD
    if not update.effective_user:
        return EXPENSE_ADD
    if not context.user_data:
        await update.message.reply_text("сначала выберете категорию")
        return EXPENSE_ADD

    category = context.user_data.get(UserData.category)
    group = context.user_data.get(UserData.group)

    expense_manger = ExpenseManager(db_client, User(update.effective_user.id), group)
    expense_manger.save_expense(
        int(text.group(1)),
        category,
        text.group(2),
    )
    await send_message(
        update,
        context,
        f"расход {text.group(1)} руб добавлен в категорию {category.name}",
    )
    return END


add_expense_conversation = ConversationHandler(
    name="add_expense",
    persistent=True,
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(send_categories, pattern=cb.groups_id),
        CallbackQueryHandler(
            request_expense_amount_for_category, pattern=cb.category_id
        ),
        MessageHandler(filters.TEXT & ~filters.COMMAND, insert_expense),
    ],
    states={
        EXPENSE_ADD: [
            CallbackQueryHandler(send_categories, pattern=cb.groups_id),
            CallbackQueryHandler(
                request_expense_amount_for_category, pattern=cb.category_id
            ),
            MessageHandler(filters.TEXT & ~filters.COMMAND, insert_expense),
        ],
    },
    map_to_parent={END: AUTH},
    fallbacks=[],
)
