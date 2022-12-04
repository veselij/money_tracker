from telegram import CallbackQuery, Message

import menu.callbacks as cb
from expense_manager import expense_manger
from formater import (
    generate_chart,
    prepare_expense_message,
    prepare_expense_message_last,
)


async def get_expenses_total(
    query: CallbackQuery, user_id: int, group: bool, ordering: str
) -> Message:
    await query.delete_message()
    expenses = expense_manger.get_expenses_total(user_id, group, ordering)
    message, chart_data = prepare_expense_message(expenses, group)
    chart = generate_chart(chart_data)
    msg = await query.get_bot().send_photo(user_id, chart, message)
    return msg


async def get_expenses_list(
    query: CallbackQuery, user_id: int, group: bool, ordering: str
) -> Message:
    expenses = expense_manger.get_expenses_last(user_id, group, ordering)
    message = prepare_expense_message_last(expenses, group)
    msg = await query.edit_message_text(message)
    return msg


func_map = {cb.report_list: get_expenses_list, cb.report_total: get_expenses_total}


def get_expenses_list_with_ids(
    user_id: int, group: bool, ordering: str
) -> tuple[str, dict]:
    expenses = expense_manger.get_expenses_last(user_id, group, ordering)
    message = prepare_expense_message_last(expenses, group)
    id_map = {i: id for i, id in enumerate(expenses, 1)}
    return (message, id_map)
