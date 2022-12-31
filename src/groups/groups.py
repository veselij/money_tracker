from telegram import Update
from telegram.ext import ContextTypes

from backend.db import db_client
from config import create_logger
from constants.userdata import UserData
from utils import make_inline_menu

logger = create_logger(__name__)


def register_user(user_id: int, username: str) -> None:
    db_client.register_user(user_id, username)


async def send_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    groups = db_client.get_user_groups(update.effective_user.id)
    menu = make_inline_menu(groups)
    context.user_data[UserData.msg_id] = await context.bot.send_message(
        update.effective_user.id, "Выберете группу", reply_markup=menu
    )


def delete_group(group_id: int, user_id: int) -> None:
    db_client.delete_group(group_id, user_id)


def add_user_to_group(group_id: int, user_id: int) -> None:
    db_client.add_user_to_group(group_id, user_id)


def delete_user_from_group(group_id: int, user_id: int) -> None:
    db_client.delete_user_from_group(group_id, user_id)
