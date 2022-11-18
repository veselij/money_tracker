import io
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt

from config import MONTH_START_DAY
from db import ExpenseReport


def prepare_expense_message(
    expenses: list[ExpenseReport], user_id: int | None = None
) -> tuple[str, dict[str, int]]:
    today = datetime.today().strftime("%d-%m-%Y")
    if user_id:
        message = f"Тобой потрачено с {MONTH_START_DAY} числа месяца по {today}:\n\n"
    else:
        message = f"Вместе потрачено с {MONTH_START_DAY} числа месяца по {today}:\n\n"
    total = 0
    chart_data: dict[str, int] = defaultdict(int)
    for expense in expenses:
        message += f"{expense.category}: {expense.amount} руб\n"
        total += expense.amount
        chart_data[expense.category] += expense.amount
    message += f"\nВсего потрачено: {total:n} руб"
    return message, chart_data


def prepare_expense_message_last(expenses: dict[int, ExpenseReport]) -> str:
    message = "*Расходы за  месяц*:\n\n"
    for i, (id, expense) in enumerate(expenses.items(), 1):
        if expense.comment:
            message += f"{i}.*{expense.category}*: {expense.amount/1000:0.1f}кр \\({expense.comment}\\)/del{id}\n"
        else:
            message += (
                f"{i}.*{expense.category}*: {expense.amount/1000:0.1f}кр /del{id}\n"
            )
    message = message.replace(".", "\\.")

    return message


def generate_chart(data: dict[str, int]) -> bytes:
    fig, ax = plt.subplots()
    ax.pie(list(data.values()), labels=list(data.keys()))
    ax.axis("equal")
    b = io.BytesIO()
    fig.set_facecolor("lightgrey")
    plt.savefig(b, format="png")
    b.seek(0)
    plt.close()
    file = b.read()
    return file
