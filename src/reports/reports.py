from collections import defaultdict

from telegram import CallbackQuery, Message

import constants.callbacks as cb
from backend.db import Category, Expense, ReportRequest, db_client
from config import MONTH_START_DAY
from reports.formater import (
    TrendData,
    generate_chart,
    generate_trend_chart,
    prepare_expense_message,
    prepare_expense_message_last,
    prepare_expense_message_month_trend,
)


def _get_expenses_month_trend(report: ReportRequest) -> TrendData:
    expenses = db_client.get_expenses_month_trend(report)

    categories: set[Category] = set()
    accomulted_expenses: list[dict[Category, list[Expense]]] = []
    months = []

    curr_month = 0
    month_expenses: dict[Category, list[Expense]] = defaultdict(list)
    for date, values in expenses.items():
        _, month, day = [int(d) for d in date.split("-")]
        if day >= MONTH_START_DAY and month > curr_month:
            accomulted_expenses.append(month_expenses)
            months.append(str(month - 1))
            month_expenses = defaultdict(list)
            curr_month = month
        for expense in values:
            month_expenses[expense.category].append(expense)
            categories.add(expense.category)

    accomulted_expenses.append(month_expenses)
    months.append("current")

    return TrendData(categories, months, accomulted_expenses)


async def get_expenses_total(query: CallbackQuery, report: ReportRequest) -> Message:
    expenses = db_client.get_expenses_total(report)
    message, chart_data = prepare_expense_message(expenses, report.user, report.all)
    chart = generate_chart(chart_data)
    msg = await query.get_bot().send_photo(report.user.id, chart, message)
    return msg


async def get_expenses_list(query: CallbackQuery, report: ReportRequest) -> Message:
    expenses = db_client.get_expenses_last(report)
    message = prepare_expense_message_last(expenses, report.user, report.all)
    msg = await query.get_bot().send_message(report.user.id, message)
    return msg


async def get_expenses_trend(query: CallbackQuery, report: ReportRequest) -> Message:
    expenses = _get_expenses_month_trend(report)
    message = prepare_expense_message_month_trend(expenses, report.user, report.all)
    chart = generate_trend_chart(expenses, report.user, report.all)
    msg = await query.get_bot().send_photo(report.user.id, chart, message)
    return msg


func_map = {
    cb.report_list: get_expenses_list,
    cb.report_total: get_expenses_total,
    cb.report_trend: get_expenses_trend,
}


def get_expenses_list_with_ids(report: ReportRequest) -> tuple[str, dict]:
    expenses = db_client.get_expenses_last(report)
    message = prepare_expense_message_last(expenses, report.user, report.all)
    id_map = {i: id for i, id in enumerate(expenses, 1)}
    return (message, id_map)
