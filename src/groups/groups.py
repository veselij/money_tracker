from telegram import Update
from telegram.ext import ContextTypes

from backend.db import Group, User, db_client
from config import create_logger
from constants.userdata import UserData
from utils import make_inline_menu

logger = create_logger(__name__)


def register_user(user_id: int, username: str) -> None:
    db_client.register_user(user_id, username)


async def send_groups(
    update: Update, context: ContextTypes.DEFAULT_TYPE, func, state: int
) -> int:
    user_id = update.effective_user.id  # type: ignore
    groups = db_client.get_user_groups(user_id)
    if len(groups) == 1:
        context.user_data[UserData.group] = Group(groups.pop().id)
        return await func(update, context)
    elif not groups:
        message = "У вас нет групп, создайте группу"
        menu = None
    else:
        message = "Выберете группу"
        menu = make_inline_menu(groups)
    context.user_data[UserData.msg_id] = await context.bot.send_message(  # type: ignore
        user_id, message, reply_markup=menu  # type: ignore
    )
    return state


async def save_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Group:
    query = update.callback_query
    if query:
        await query.answer()
        context.user_data[UserData.group] = Group(int(query.data.split()[1]))
    return context.user_data[UserData.group]


def delete_group(group: Group) -> None:
    db_client.delete_group(group)


def add_user_to_group(group: Group, user: User) -> bool:
    if db_client.is_user_registred(user):
        db_client.add_user_to_group(group, user)
        return True
    return False


def delete_user_from_group(group: Group, user: User) -> None:
    db_client.delete_user_from_group(group, user)
