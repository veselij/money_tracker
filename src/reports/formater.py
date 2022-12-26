import io
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

import matplotlib.pyplot as plt

from backend.db import ExpenseReport
from config import MONTH_START_DAY


@dataclass
class TrendData:
    categories: set[str]
    months: list[str]
    accomulted_expenses: list[dict[str, int]]

    def get_chart_data(self) -> tuple[list[str], list[list[int]]]:
        chart_data = []
        labels = []
        for cat in self.categories:
            cat_month_expense = []
            for exp in self.accomulted_expenses:
                cat_month_expense.append(exp.get(cat, 0))
            chart_data.append(cat_month_expense)
            labels.append(cat)
        return labels, chart_data


def get_init_message(group: bool) -> str:
    today = datetime.today().strftime("%d-%m-%Y")
    if not group:
        message = f"Тобой потрачено с {MONTH_START_DAY} числа месяца по {today}:\n\n"
    else:
        message = f"Вместе потрачено с {MONTH_START_DAY} числа месяца по {today}:\n\n"
    return message


def prepare_expense_message(
    expenses: list[ExpenseReport], group: bool = False
) -> tuple[str, dict[str, int]]:
    message = get_init_message(group)
    total = 0
    chart_data: dict[str, int] = defaultdict(int)
    for expense in expenses:
        message += f"{expense.category}: {expense.amount} руб\n"
        total += expense.amount
        chart_data[expense.category] += expense.amount
    message += f"\nВсего потрачено: {total:n} руб"
    return message, chart_data


def prepare_expense_message_last(
    expenses: dict[int, ExpenseReport], group: bool = False
) -> str:
    message = get_init_message(group)
    for i, (_, expense) in enumerate(expenses.items(), 1):
        if expense.comment:
            message += f"{i:03}. {expense.category}: {expense.amount/1000:0.1f} т.р. ({expense.comment})\n"
        else:
            message += f"{i:03}. {expense.category}: {expense.amount/1000:0.1f} т.р.\n"

    return message


def prepare_expense_message_month_trend(
    trend_expenses: TrendData, group: bool = False
) -> str:
    message = get_init_message(group)

    for month, expenses in zip(
        trend_expenses.months, trend_expenses.accomulted_expenses
    ):
        amount = sum(expenses.values())
        message += f"{month}: {amount} руб\n"

    return message


def generate_trend_chart(trend_expenses: TrendData) -> bytes:
    labels, series = trend_expenses.get_chart_data()
    fig, ax = plt.subplots()
    fig.set_facecolor("lightgrey")
    bottom = [0] * len(series[0])
    bar_width = 0.4
    ax.bar(trend_expenses.months, series[0], bar_width, label=labels[0])
    for i, (label, data) in enumerate(zip(labels[1:], series[1:])):
        bottom = [sum(value) for value in zip(bottom, series[i])]
        ax.bar(trend_expenses.months, data, bar_width, label=label, bottom=bottom)
    table = plt.table(
        cellText=series,
        rowLabels=labels,
        colLabels=trend_expenses.months,
        loc="bottom",
    )
    table.set_fontsize(7)
    plt.subplots_adjust(left=0.2, bottom=0.4)
    plt.xticks([])

    file = _generate_file_chart()
    plt.close()
    return file


def generate_chart(data: dict[str, int]) -> bytes:
    fig, ax = plt.subplots()
    fig.set_facecolor("lightgrey")
    ax.pie(list(data.values()), labels=list(data.keys()))
    ax.axis("equal")
    file = _generate_file_chart()
    plt.close()
    return file


def _generate_file_chart() -> bytes:
    b = io.BytesIO()
    plt.savefig(b, format="png")
    b.seek(0)
    file = b.read()
    return file
