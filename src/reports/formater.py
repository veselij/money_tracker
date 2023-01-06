import io
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

import matplotlib.pyplot as plt

from backend.db import Category, Expense, User
from config import MONTH_START_DAY


@dataclass
class TrendData:
    categories: set[Category]
    months: list[str]
    accomulted_expenses: list[dict[Category, list[Expense]]]

    def get_chart_data(
        self, user: User, all: bool
    ) -> tuple[list[str], list[list[float]]]:
        chart_data = []
        labels = []
        for category in self.categories:
            month_expense_for_category = []
            for expenses in self.accomulted_expenses:
                expense = _filter_user_expenses(expenses.get(category, []), user, all)
                month_expense_for_category.append(expense)
            chart_data.append(month_expense_for_category)
            labels.append(category.name)
        return labels, chart_data


def _filter_user_expenses(expenses: list[Expense], user: User, all: bool) -> float:
    if not all:
        return sum(exp.amount for exp in expenses if exp.user == user) / 1000
    return sum(exp.amount for exp in expenses) / 1000


def get_init_message(user: User | None) -> str:
    today = datetime.today().strftime("%d-%m-%Y")
    if user:
        message = f"Тобой потрачено с {MONTH_START_DAY} числа месяца по {today}:\n\n"
    else:
        message = f"Вместе потрачено с {MONTH_START_DAY} числа месяца по {today}:\n\n"
    return message


def prepare_expense_message(
    expenses: dict[Category, list[Expense]], user: User, all: bool
) -> tuple[str, dict[str, float]]:
    message = get_init_message(user)
    chart_data: dict[str, float] = defaultdict(float)
    for category, expense in expenses.items():
        amount = _filter_user_expenses(expense, user, all)
        message += f"{category.name}: {amount} руб\n"
        chart_data[category.name] = amount
    message += f"\nВсего потрачено: {sum(chart_data.values()):n} т.руб"
    return message, chart_data


def prepare_expense_message_last(expenses: dict[int, Expense], user: User) -> str:
    message = get_init_message(user)
    for i, (_, expense) in enumerate(expenses.items(), 1):
        if not user or user == expense.user:
            if expense.comment:
                message += f"{i:03}. {expense.category.name}: {expense.amount/1000:0.1f} т.р. ({expense.comment})\n"
            else:
                message += f"{i:03}. {expense.category.name}: {expense.amount/1000:0.1f} т.р.\n"

    return message


def prepare_expense_message_month_trend(
    trend_expenses: TrendData, user: User, all: bool
) -> str:
    message = get_init_message(user)

    for month, expenses in zip(
        trend_expenses.months, trend_expenses.accomulted_expenses
    ):
        amount = 0.0
        for expenses_per_category in expenses.values():
            amount += _filter_user_expenses(expenses_per_category, user, all)
        message += f"{month}: {amount:n} тыс.руб\n"

    return message


def generate_trend_chart(trend_expenses: TrendData, user: User, all: bool) -> bytes:
    labels, series = trend_expenses.get_chart_data(user, all)
    plt.tight_layout()
    fig, ax = plt.subplots()
    fig.set_facecolor("lightgrey")
    bottom = [0.0] * len(series[0])
    bar_width = 0.4
    ax.bar(trend_expenses.months, series[0], bar_width, label=labels[0])
    for i, (label, data) in enumerate(zip(labels[1:], series[1:])):
        bottom = [sum(value) for value in zip(bottom, series[i])]
        ax.bar(trend_expenses.months, data, bar_width, label=label, bottom=bottom)
    ax.legend()
    table = plt.table(
        cellText=series, rowLabels=labels, colLabels=trend_expenses.months, loc="bottom"
    )
    table.scale(1, 1.5)
    plt.subplots_adjust(left=0.2, bottom=0.4)
    plt.xticks([])

    file = _generate_file_chart()
    plt.close()
    return file


def generate_chart(data: dict[str, float]) -> bytes:
    fig, ax = plt.subplots()
    fig.set_facecolor("lightgrey")
    ax.pie(list(data.values()), labels=list(data.keys()))
    ax.axis("equal")
    file = _generate_file_chart()
    plt.close()
    return file


def _generate_file_chart() -> bytes:
    b = io.BytesIO()
    plt.savefig(b, format="png", dpi=300)
    b.seek(0)
    file = b.read()
    return file
