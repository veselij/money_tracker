from backend.db import DataBaseClient, Expense


class ExpenseManager:
    def __init__(self, db: DataBaseClient, user_id: int, group_id: int) -> None:
        self._db = db
        self._user_id = user_id
        self._group_id = group_id

    def save_expense(self, amount: int, category_id: int, comment: str) -> int:
        expense = Expense(amount, category_id, self._user_id, self._group_id, comment)
        id = self._db.insert(expense)
        return id

    def del_expense(self, id: int) -> None:
        self._db.del_row(id, self._user_id)

    def move_expense(self, id: int, new_category: int) -> None:
        self._db.move_row(id, new_category, self._user_id)
