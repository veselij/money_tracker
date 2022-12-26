from telegram import Update
from telegram.ext import ContextTypes

from backend.db import db_client
from config import create_logger
from constants.userdata import UserData
from utils import make_inline_menu

logger = create_logger(__name__)


def register_user(user_id: int, username: str) -> None:
    db_client.register_user(user_id, username)


async def send_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    groups = db_client.get_user_groups(update.effective_user.id)
    menu = make_inline_menu(groups)

    context.user_data[UserData.msg_id] = await context.bot.send_message(
        update.effective_user.id, "Выберет группу", reply_markup=menu
    )
