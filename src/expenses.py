from datetime import datetime

from config import MONTH_START_DAY
from db import DataBaseClient, Expense, ExpenseReport


def calculate_date() -> str:
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if day >= MONTH_START_DAY:
        return f"{year}-{month}-{MONTH_START_DAY}"
    else:
        return f"{year}-{month-1}-{MONTH_START_DAY}"


class ExpenseManager:
    def __init__(self, db: DataBaseClient) -> None:
        self._db = db

    def save_expense(
        self, amount: int, category_id: int, comment: str, user_id: int
    ) -> int:
        expense = Expense(amount, category_id, user_id, comment)
        id = self._db.insert(expense)
        return id

    def get_expenses_total(self, user_id: int | None = None) -> list[ExpenseReport]:
        expenses = self._db.get_expenses_total(calculate_date(), user_id)
        return expenses

    def get_expenses_last(self, user_id: int | None = None) -> dict[int, ExpenseReport]:
        expenses = self._db.get_expenses_last(user_id, calculate_date())
        return expenses

    def del_expense(self, id: int) -> None:
        self._db.del_row(id)
