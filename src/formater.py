import io
from collections import defaultdict

import matplotlib.pyplot as plt
from telegram import PhotoSize

from db import Expense


def prepare_expense_message(
    expenses: list[Expense], categories: dict[int, str]
) -> tuple[str, dict[str, int]]:
    message = "*Всего потрачено с начала месяца*:\n"
    total = 0
    chart_data: dict[str, int] = defaultdict(int)
    for expense in expenses:
        message += f"{categories[expense.category_id]}: {expense.amount} руб\n"
        total += expense.amount
        chart_data[categories[expense.category_id]] += expense.amount
    message += f"*Всего потрачено*: {total} руб"
    return message, chart_data


def prepare_expense_message_last(
    expenses: dict[int, Expense], categories: dict[int, str]
) -> str:
    message = "*Последние 10 расходов*:\n"
    for id, expense in expenses.items():
        message += f"{categories[expense.category_id]} {expense.comment}: {expense.amount} руб удалить /del{id}\n\n"
    return message


def generate_chart(data: dict[str, int]) -> bytes:
    fig, ax = plt.subplots()
    ax.pie(list(data.values()), labels=list(data.keys()))
    ax.axis("equal")
    b = io.BytesIO()
    plt.savefig(b, format="png")
    b.seek(0)
    plt.close()
    file = b.read()
    return file
