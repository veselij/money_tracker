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

    def get_expenses_total(self, user_id: int) -> str:
        expenses = self._db.get_expenses_total(user_id, calculate_date())
        message = self._prepare_expense_message(expenses)
        return message

    def get_expenses_last(self, user_id: int) -> str:
        expenses = self._db.get_expenses_last(user_id)
        message = self._prepare_expense_message_last(expenses)
        return message

    def del_expense(self, id: int) -> None:
        self._db.del_row(id)

    def _load_categories(self) -> None:
        self._db.load_categories(self._categories)

    def _prepare_expense_message(self, expenses: list[Expense]) -> str:
        message = "*Всего потрачено с начала месяца*:\n"
        total = 0
        for expense in expenses:
            message += (
                f"{self._categories[expense.category_id]}: {expense.amount} руб\n"
            )
            total += expense.amount
        message += f"*Всего потрачено*: {total} руб"
        return message

    def _prepare_expense_message_last(self, expenses: dict[int, Expense]) -> str:
        message = "*Последние 10 расходов*:\n"
        for id, expense in expenses.items():
            message += f"{self._categories[expense.category_id]} {expense.comment}: {expense.amount} руб удалить /del{id}\n"
        return message
