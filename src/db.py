import sqlite3
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Expense:
    amount: int
    category_id: int
    user_id: int
    comment: str = ""


@dataclass(frozen=True)
class ExpenseReport:
    amount: int
    category: str
    comment: str = ""


@dataclass(frozen=True)
class Category:
    id: int
    name: str


class DataBaseClient(ABC):
    @abstractmethod
    def insert(self, expense: Expense) -> int:
        ...

    @abstractmethod
    def get_expenses_total(
        self, start: str, user_id: int, group: bool, ordering: str
    ) -> list[ExpenseReport]:
        ...

    @abstractmethod
    def get_expenses_last(
        self, user_id: int, group: bool, start: str, ordering: str
    ) -> dict[int, ExpenseReport]:
        ...

    @abstractmethod
    def get_expenses_month_trend(
        self, user_id: int, group: bool, start: str, ordering: str
    ) -> dict[str, list[ExpenseReport]]:
        ...

    @abstractmethod
    def load_categories(self, categories: dict[int, Category]) -> None:
        ...

    @abstractmethod
    def del_row(self, id: int) -> None:
        ...

    @abstractmethod
    def move_row(self, id: int, new_category: int) -> None:
        ...

    @abstractmethod
    def insert_category(self, category: str) -> None:
        ...

    @abstractmethod
    def delete_category(self, category: int) -> None:
        ...

    @abstractmethod
    def _create_database(self) -> None:
        ...


class SqliteClient(DataBaseClient):
    def __init__(self) -> None:
        self._conn = sqlite3.connect("expenses.db")
        self._cur = self._conn.cursor()
        self._create_database()

    def load_categories(self, categories: dict[int, Category]) -> None:
        self._cur.execute("SELECT id, CATEGORY from categories WHERE activerecord = 1")
        for row in self._cur.fetchall():
            categories[row[0]] = Category(*row)

    def insert(self, expense: Expense) -> int:
        self._cur.execute(
            f"INSERT INTO expenses(AMOUNT, COMMENT, CATEGORY_ID, USER_ID) \
              VALUES ({expense.amount}, '{expense.comment.strip()}', {expense.category_id}, {expense.user_id})"
        )
        self._conn.commit()
        return self._cur.lastrowid or -1

    def get_expenses_total(
        self, start: str, user_id: int, group: bool, ordering: str
    ) -> list[ExpenseReport]:
        if not group:
            self._cur.execute(
                f"SELECT sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE USER_ID = {user_id} and created_at >= '{start}' \
                  GROUP BY CATEGORY \
                  ORDER BY {ordering}"
            )
        else:
            self._cur.execute(
                f"SELECT sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE created_at >= '{start}' \
                  GROUP BY CATEGORY \
                  ORDER BY {ordering}"
            )
        expenses = []
        for row in self._cur.fetchall():
            expenses.append(ExpenseReport(*row))
        return expenses

    def get_expenses_month_trend(
        self, user_id: int, group: bool, start: str, ordering: str
    ) -> dict[str, list[ExpenseReport]]:
        if not group:
            self._cur.execute(
                f"SELECT strftime('%Y-%m-%d',created_at), sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE USER_ID = {user_id} and created_at >= '{start}' \
                  GROUP BY strftime('%Y-%m-%d',created_at), CATEGORY \
                  ORDER BY {ordering}"
            )
        else:
            self._cur.execute(
                f"SELECT strftime('%Y-%m-%d',created_at), sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE created_at >= '{start}' \
                  GROUP BY strftime('%Y-%m-%d',created_at), CATEGORY \
                  ORDER BY {ordering}"
            )
        expenses: dict[str, list[ExpenseReport]] = defaultdict(list)
        for row in self._cur.fetchall():
            expenses[row[0]].append(ExpenseReport(*row[1:]))
        return expenses

    def get_expenses_last(
        self, user_id: int, group: bool, start: str, ordering: str
    ) -> dict[int, ExpenseReport]:
        if not group:
            self._cur.execute(
                f"SELECT e.ID, AMOUNT, CATEGORY, COMMENT FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE USER_ID = {user_id} and created_at >= '{start}' \
                  ORDER BY {ordering}"
            )
        else:
            self._cur.execute(
                f"SELECT e.ID, AMOUNT, CATEGORY, COMMENT FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE created_at >= '{start}' \
                  ORDER BY {ordering}"
            )
        expenses = {}
        for row in self._cur.fetchall():
            expenses[row[0]] = ExpenseReport(*row[1:])
        return expenses

    def del_row(self, id: int) -> None:
        self._cur.execute(f"DELETE FROM expenses WHERE ID = {id}")
        self._conn.commit()

    def move_row(self, id: int, new_category: int) -> None:
        self._cur.execute(
            f"UPDATE expenses SET CATEGORY_ID = {new_category} WHERE id = {id}"
        )
        self._conn.commit()

    def insert_category(self, category: str) -> None:
        self._cur.execute(
            f"INSERT OR REPLACE INTO categories(CATEGORY, activerecord) VALUES ('{category}', 1)"
        )
        self._conn.commit()

    def delete_category(self, category: int) -> None:
        self._cur.execute(
            f"UPDATE categories SET activerecord = 0 WHERE id = {category}"
        )
        self._conn.commit()

    def _create_database(self) -> None:
        with open("src/createdb.sql", "r") as fl:
            sql = fl.read()
        self._cur.executescript(sql)
        self._conn.commit()


db_client = SqliteClient()
