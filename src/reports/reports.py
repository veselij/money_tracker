from collections import defaultdict
from datetime import datetime

from telegram import CallbackQuery, Message

import constants.callbacks as cb
from backend.db import ReportRequest, ReportType, db_client
from config import MONTH_START_DAY
from reports.formater import (
    TrendData,
    generate_chart,
    generate_trend_chart,
    prepare_expense_message,
    prepare_expense_message_last,
    prepare_expense_message_month_trend,
)


def calculate_date() -> str:
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if day >= MONTH_START_DAY:
        return f"{year}-{month}-{MONTH_START_DAY}"
    else:
        return f"{year}-{month-1}-{MONTH_START_DAY}"


def _get_expenses_month_trend(report: ReportRequest) -> TrendData:
    expenses = db_client.get_expenses_month_trend(report)
    categories = set()
    accomulted_expenses = []
    months = []

    curr_month = 0
    month_expenses: dict[str, int] = defaultdict(int)
    for date, values in expenses.items():
        _, month, day = [int(d) for d in date.split("-")]
        if day >= MONTH_START_DAY and month > curr_month:
            accomulted_expenses.append(month_expenses)
            months.append(str(month - 1))
            month_expenses = defaultdict(int)
            curr_month = month
        for expense in values:
            month_expenses[expense.category] += expense.amount
            categories.add(expense.category)

    accomulted_expenses.append(month_expenses)
    months.append("current")

    return TrendData(categories, months, accomulted_expenses)


def _make_report_request(
    user_id: int, group_id: int, all: bool, ordering: str
) -> ReportRequest:
    if all:
        return ReportRequest(
            ReportType.group_all, user_id, group_id, calculate_date(), ordering
        )
    else:
        return ReportRequest(
            ReportType.group_own, user_id, group_id, calculate_date(), ordering
        )


async def get_expenses_total(
    query: CallbackQuery, user_id: int, group_id: bool, all: bool, ordering: str
) -> Message:
    report = _make_report_request(user_id, group_id, all, ordering)
    expenses = db_client.get_expenses_total(report)
    message, chart_data = prepare_expense_message(expenses, all)
    chart = generate_chart(chart_data)
    msg = await query.get_bot().send_photo(user_id, chart, message)
    return msg


async def get_expenses_list(
    query: CallbackQuery, user_id: int, group_id: int, all: bool, ordering: str
) -> Message:
    report = _make_report_request(user_id, group_id, all, ordering)
    expenses = db_client.get_expenses_last(report)
    message = prepare_expense_message_last(expenses, all)
    msg = await query.get_bot().send_message(user_id, message)
    return msg


async def get_expenses_trend(
    query: CallbackQuery, user_id: int, group_id: int, all: bool, ordering: str
) -> Message:
    report = _make_report_request(user_id, group_id, all, ordering)
    expenses = _get_expenses_month_trend(report)
    message = prepare_expense_message_month_trend(expenses, all)
    chart = generate_trend_chart(expenses)
    msg = await query.get_bot().send_photo(user_id, chart, message)
    return msg


func_map = {
    cb.report_list: get_expenses_list,
    cb.report_total: get_expenses_total,
    cb.report_trend: get_expenses_trend,
}


def get_expenses_list_with_ids(
    user_id: int, group_id: int, all: bool, ordering: str
) -> tuple[str, dict]:
    report = _make_report_request(user_id, group_id, all, ordering)
    expenses = db_client.get_expenses_last(report)
    message = prepare_expense_message_last(expenses, all)
    id_map = {i: id for i, id in enumerate(expenses, 1)}
    return (message, id_map)
