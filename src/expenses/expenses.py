from backend.db import Category, DataBaseClient, Expense, Group, User


class ExpenseManager:
    def __init__(self, db: DataBaseClient, user: User, group: Group) -> None:
        self._db = db
        self._user = user
        self._group = group

    def save_expense(self, amount: int, category: Category, comment: str) -> int:
        expense = Expense(amount, category, self._user, self._group, comment)
        id = self._db.insert(expense)
        return id

    def del_expense(self, id: int) -> None:
        self._db.del_expense(id)

    def move_expense(self, id: int, new_category: int) -> None:
        self._db.update_expense_category(id, new_category)
