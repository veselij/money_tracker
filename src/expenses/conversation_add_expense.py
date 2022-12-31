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
from backend.db import db_client
from categories.categories import Categories
from config import create_logger
from constants.states import AUTH, EXPENSE_ADD, EXPENSE_INSERT
from constants.userdata import UserData
from decorators import delete_old_message, log
from expenses.expenses import ExpenseManager
from groups.groups import send_groups
from utils import make_inline_menu

logger = create_logger(__name__)
END = ConversationHandler.END


@log(logger)
@delete_old_message(logger)
async def send_groups_for_add_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await send_groups(update, context)
    return EXPENSE_ADD


@log(logger)
async def send_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[UserData.group_id] = int(query.data.split()[1])

    categories = Categories(db_client, context.user_data[UserData.group_id])
    replay_markup = make_inline_menu(categories)

    context.user_data[UserData.msg_id] = await query.edit_message_text(
        "Выберет категорию", reply_markup=replay_markup
    )

    return EXPENSE_INSERT


@log(logger)
async def request_expense_anount_for_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    id = int(query.data.split()[1])
    await query.answer()

    context.user_data[UserData.category_id] = id  # type: ignore
    categories = Categories(db_client, context.user_data.get(UserData.group_id))
    category = categories[id]
    context.user_data[UserData.msg_id] = await query.message.reply_text(
        "Напишите сумму расхода и комментарий для категории {0}".format(category.name)
    )

    return EXPENSE_INSERT


@log(logger)
@delete_old_message(logger)
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
    category = context.user_data.get(UserData.category_id)
    group_id = context.user_data.get(UserData.group_id)
    expense_manger = ExpenseManager(db_client, update.effective_user.id, group_id)
    expense_manger.save_expense(
        int(text.group(1)),
        category,
        text.group(2),
    )
    categories = Categories(db_client, group_id)
    cat = categories[category]
    context.user_data[UserData.msg_id] = await update.message.reply_text(
        "расход {0} руб добавлен в категорию {1}".format(text.group(1), cat.name)
    )
    return END


@log(logger)
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
    categories = Categories(db_client, update.effective_user.id)
    try:
        expense_manger = ExpenseManager(db_client, update.effective_user.id, False)
        id = expense_manger.save_expense(
            int(amount),
            categories.get_category_id(category.strip()),
            comment.strip(),
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


add_expense_conversation = ConversationHandler(
    name="add_expense",
    persistent=True,
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(send_categories, pattern=cb.groups_id),
    ],
    states={
        EXPENSE_INSERT: [
            CallbackQueryHandler(send_categories, pattern=cb.groups_id),
            CallbackQueryHandler(
                request_expense_anount_for_category, pattern=cb.category_id
            ),
            MessageHandler(filters.TEXT & ~filters.COMMAND, insert_expense),
        ],
    },
    map_to_parent={END: AUTH},
    fallbacks=[],
)
