from datetime import datetime

from db import DataBaseClient, Expense


def calculate_date() -> str:
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if day >= 10:
        return f"{year}-{month}-10"
    else:
        return f"{year}-{month-1}-10"


class ExpenseManager:
    def __init__(self, db: DataBaseClient) -> None:
        self._db = db
        self._categories: dict[int, str] = {}
        self._load_categories()

    def save_expense(
        self, amount: int, category_id: int, comment: str, user_id: int
    ) -> int:
        expense = Expense(amount, category_id, user_id, comment)
        id = self._db.insert(expense)
        return id

    def get_expenses_total(self, user_id: int | None = None) -> list[Expense]:
        expenses = self._db.get_expenses_total(calculate_date(), user_id)
        return expenses

    def get_expenses_last(self, user_id: int) -> dict[int, Expense]:
        expenses = self._db.get_expenses_last(user_id)
        return expenses

    def del_expense(self, id: int) -> None:
        self._db.del_row(id)

    def get_categories(self) -> dict[int, str]:
        return self._categories

    def _load_categories(self) -> None:
        self._db.load_categories(self._categories)
