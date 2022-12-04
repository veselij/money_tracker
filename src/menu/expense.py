import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from categories import categories
from expense_manager import expense_manger
from menu.states import AUTH
from menu.utils import delete_old_message, make_category_inline_menu

logger = logging.getLogger(__name__)


async def send_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_old_message(update, context)
    replay_markup = make_category_inline_menu(categories)
    msg = await update.message.reply_text(
        "Выберет категорию", reply_markup=replay_markup
    )
    context.user_data["msg"] = int(msg.id)
    return AUTH


async def request_expense_anount_for_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    id = int(query.data)
    await query.answer()

    await delete_old_message(update, context)

    context.user_data["category"] = id  # type: ignore
    category = categories[id]
    msg = await query.message.reply_text(
        "Напишите сумму расхода и комментарий для категории {0}".format(category.name)
    )
    context.user_data["msg"] = int(msg.id)
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
    expense_manger.save_expense(
        int(text.group(1)), category, text.group(2), update.effective_user.id
    )
    cat = categories[category]
    await delete_old_message(update, context)
    msg = await update.message.reply_text(
        "расход {0} руб добавлен в категорию {1}".format(text.group(1), cat.name)
    )
    context.user_data.clear()
    context.user_data["msg"] = int(msg.id)
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
