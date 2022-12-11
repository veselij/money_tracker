from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from config import MONTH_START_DAY
from db import DataBaseClient, Expense, ExpenseReport, db_client


def calculate_date() -> str:
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if day >= MONTH_START_DAY:
        return f"{year}-{month}-{MONTH_START_DAY}"
    else:
        return f"{year}-{month-1}-{MONTH_START_DAY}"


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


class ExpenseManager:
    def __init__(self, db: DataBaseClient) -> None:
        self._db = db

    def save_expense(
        self, amount: int, category_id: int, comment: str, user_id: int
    ) -> int:
        expense = Expense(amount, category_id, user_id, comment)
        id = self._db.insert(expense)
        return id

    def get_expenses_total(
        self, user_id: int, group: bool, ordering: str
    ) -> list[ExpenseReport]:
        expenses = self._db.get_expenses_total(
            calculate_date(), user_id, group, ordering
        )
        return expenses

    def get_expenses_month_trend(
        self, user_id: int, group: bool, ordering: str
    ) -> TrendData:
        expenses = self._db.get_expenses_month_trend(
            user_id, group, "2022-01-01", ordering
        )
        categories = set()
        accomulted_expenses = []
        months = []

        curr_month = 0
        month_expenses: dict[str, int] = defaultdict(int)
        for date, values in expenses.items():
            _, month, day = [int(d) for d in date.split("-")]
            for expense in values:
                month_expenses[expense.category] += expense.amount
                categories.add(expense.category)
            if day >= MONTH_START_DAY and month > curr_month:
                accomulted_expenses.append(month_expenses)
                months.append(str(month))
                month_expenses = defaultdict(int)
                curr_month = month

        accomulted_expenses.append(month_expenses)
        months.append("current")

        return TrendData(categories, months, accomulted_expenses)

    def get_expenses_last(
        self, user_id: int, group: bool, ordering: str
    ) -> dict[int, ExpenseReport]:
        expenses = self._db.get_expenses_last(
            user_id, group, calculate_date(), ordering
        )
        return expenses

    def del_expense(self, id: int) -> None:
        self._db.del_row(id)

    def move_expense(self, id: int, new_category: int) -> None:
        self._db.move_row(id, new_category)


expense_manger = ExpenseManager(db_client)
