import menu.callbacks as cb
from expense_manager import expense_manger
from formater import (
    generate_chart,
    prepare_expense_message,
    prepare_expense_message_last,
)


def get_expenses_total(
    user_id: int, group: bool, ordering: str
) -> tuple[str, bytes | dict]:
    expenses = expense_manger.get_expenses_total(user_id, group, ordering)
    message, chart_data = prepare_expense_message(expenses, group)
    chart = generate_chart(chart_data)
    return message, chart


def get_expenses_list(
    user_id: int, group: bool, ordering: str
) -> tuple[str, bytes | dict]:
    expenses = expense_manger.get_expenses_last(user_id, group, ordering)
    message, id_mapping = prepare_expense_message_last(expenses, group)
    return message, id_mapping


func_map = {cb.report_list: get_expenses_list, cb.report_total: get_expenses_total}
