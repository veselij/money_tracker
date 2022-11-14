import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Expense:
    amount: int
    category_id: int
    user_id: int
    comment: str = ""


class DataBaseClient(ABC):
    @abstractmethod
    def insert(self, expense: Expense) -> int:
        ...

    @abstractmethod
    def get_expenses_total(self, start: str, user_id: int | None) -> list[Expense]:
        ...

    @abstractmethod
    def get_expenses_last(self, user_id: int) -> dict[int, Expense]:
        ...

    @abstractmethod
    def load_categories(self, categories: dict[int, str]) -> None:
        ...

    @abstractmethod
    def del_row(self, id: int) -> None:
        ...

    @abstractmethod
    def _create_database(self) -> None:
        ...


class SqliteClient(DataBaseClient):
    def __init__(self) -> None:
        self._conn = sqlite3.connect("expenses.db")
        self._cur = self._conn.cursor()
        self._create_database()

    def load_categories(self, categories: dict[int, str]) -> None:
        self._cur.execute("SELECT * from categories")
        for row in self._cur.fetchall():
            categories[row[0]] = row[1]

    def insert(self, expense: Expense) -> int:
        self._cur.execute(
            f"INSERT INTO expenses(AMOUNT, COMMENT, CATEGORY_ID, USER_ID) VALUES ({expense.amount}, '{expense.comment}', {expense.category_id}, {expense.user_id})"
        )
        self._conn.commit()
        return self._cur.lastrowid or -1

    def get_expenses_total(self, start: str, user_id: int | None) -> list[Expense]:
        if user_id:
            self._cur.execute(
                f"SELECT CATEGORY_ID, sum(AMOUNT), USER_ID FROM expenses e WHERE USER_ID = {user_id} and created_at >= '{start}' GROUP BY CATEGORY_ID, USER_ID"
            )
        else:
            self._cur.execute(
                f"SELECT CATEGORY_ID, sum(AMOUNT), -1 FROM expenses e WHERE created_at >= '{start}' GROUP BY CATEGORY_ID"
            )
        expenses = []
        for row in self._cur.fetchall():
            expenses.append(Expense(row[1], row[0], row[2]))
        return expenses

    def get_expenses_last(self, user_id: int) -> dict[int, Expense]:
        self._cur.execute(
            f"SELECT ID, AMOUNT, CATEGORY_ID, USER_ID, COMMENT FROM expenses e WHERE USER_ID = {user_id} order by created_at desc limit 10"
        )
        expenses = {}
        for row in self._cur.fetchall():
            expenses[row[0]] = Expense(row[1], row[2], row[3], row[4])
        return expenses

    def del_row(self, id: int) -> None:
        self._cur.execute(f"DELETE FROM expenses WHERE ID = {id}")
        self._conn.commit()

    def _create_database(self) -> None:
        with open("src/createdb.sql", "r") as fl:
            sql = fl.read()
        self._cur.executescript(sql)
        self._conn.commit()
