import sqlite3
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Expense:
    amount: int
    category_id: int
    user_id: int
    group_id: int = 0
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


class ReportType(Enum):
    group_own = 1
    group_all = 2


@dataclass(frozen=True)
class ReportRequest:
    report_type: ReportType
    user_id: int
    group_id: int
    start: str
    ordering: str


@dataclass(frozen=True)
class Group:
    id: int
    name: str


class DataBaseClient(ABC):
    @abstractmethod
    def register_user(self, user_id: int, username: str) -> None:
        ...

    @abstractmethod
    def create_group(self, user_id: int, name: str) -> None:
        ...

    @abstractmethod
    def insert(self, expense: Expense) -> int:
        ...

    @abstractmethod
    def get_expenses_total(self, request: ReportRequest) -> list[ExpenseReport]:
        ...

    @abstractmethod
    def get_expenses_last(self, request: ReportRequest) -> dict[int, ExpenseReport]:
        ...

    @abstractmethod
    def get_expenses_month_trend(
        self, request: ReportRequest
    ) -> dict[str, list[ExpenseReport]]:
        ...

    @abstractmethod
    def load_categories(self, categories: dict[int, Category], group_id: int) -> None:
        ...

    @abstractmethod
    def del_row(self, id: int, user_id: int) -> None:
        ...

    @abstractmethod
    def move_row(self, id: int, new_category: int, user_id: int) -> None:
        ...

    @abstractmethod
    def insert_category(self, category: str, group_id: int) -> None:
        ...

    @abstractmethod
    def delete_category(self, category: int, group_id: int) -> None:
        ...

    @abstractmethod
    def _create_database(self) -> None:
        ...

    @abstractmethod
    def get_user_groups(self, user_id: int) -> list[Group]:
        ...


class SqliteClient(DataBaseClient):
    def __init__(self) -> None:
        self._conn = sqlite3.connect("expenses.db")
        self._cur = self._conn.cursor()
        self._create_database()

    def register_user(self, user_id: int, username: str) -> None:
        self._cur.execute(
            f"INSERT OR IGNORE INTO users(USER_ID, USERNAME) VALUES({user_id}, '{username}')"
        )
        self._conn.commit()

    def create_group(self, user_id: int, name: str) -> None:
        self._cur.execute(f"INSERT OR IGNORE INTO groups(NAME) VALUES('{name}')")
        self._conn.commit()
        group_id = self._cur.lastrowid
        self._cur.execute(
            f"INSERT OR IGNORE INTO user_groups(USER_ID, GROUP_ID) VALUES({user_id}, {group_id})"
        )
        self._conn.commit()

    def load_categories(self, categories: dict[int, Category], group_id: int) -> None:
        self._cur.execute(
            f"SELECT id, CATEGORY from categories WHERE activerecord = 1 and group_id = {group_id}"
        )
        for row in self._cur.fetchall():
            categories[row[0]] = Category(*row)

    def insert(self, expense: Expense) -> int:
        self._cur.execute(
            f"INSERT INTO expenses(AMOUNT, COMMENT, CATEGORY_ID, USER_ID, GROUP_ID) VALUES \
        ({expense.amount}, '{expense.comment.strip()}', {expense.category_id}, {expense.user_id}, {expense.group_id})"
        )
        self._conn.commit()
        return self._cur.lastrowid or -1

    def get_expenses_total(self, request: ReportRequest) -> list[ExpenseReport]:
        if request.report_type.group_own:
            self._cur.execute(
                f"SELECT sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE USER_ID = {request.user_id} and created_at >= '{request.start}' and e.GROUP_ID = {request.group_id} \
                  GROUP BY CATEGORY \
                  ORDER BY {request.ordering}"
            )
        elif request.report_type.group_all:
            self._cur.execute(
                f"SELECT sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE created_at >= '{request.start}' and e.GROUP_ID = {request.group_id} \
                  GROUP BY CATEGORY \
                  ORDER BY {request.ordering}"
            )

        expenses = []
        for row in self._cur.fetchall():
            expenses.append(ExpenseReport(*row))
        return expenses

    def get_expenses_month_trend(
        self, request: ReportRequest
    ) -> dict[str, list[ExpenseReport]]:
        if request.report_type.group_own:
            self._cur.execute(
                f"SELECT strftime('%Y-%m-%d',created_at), sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE USER_ID = {request.user_id} and created_at >= '{request.start}' and e.GROUP_ID = {request.group_id} \
                  GROUP BY strftime('%Y-%m-%d',created_at), CATEGORY \
                  ORDER BY {request.ordering}"
            )
        elif request.report_type.group_all:
            self._cur.execute(
                f"SELECT strftime('%Y-%m-%d',created_at), sum(AMOUNT) as AMOUNT, CATEGORY FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE created_at >= '{request.start}' and e.GROUP_ID = {request.group_id} \
                  GROUP BY strftime('%Y-%m-%d',created_at), CATEGORY \
                  ORDER BY {request.ordering}"
            )

        expenses: dict[str, list[ExpenseReport]] = defaultdict(list)
        for row in self._cur.fetchall():
            expenses[row[0]].append(ExpenseReport(*row[1:]))
        return expenses

    def get_expenses_last(self, request: ReportRequest) -> dict[int, ExpenseReport]:
        if request.report_type.group_own:
            self._cur.execute(
                f"SELECT e.ID, AMOUNT, CATEGORY, COMMENT FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE USER_ID = {request.user_id} and created_at >= '{request.start}' and e.GROUP_ID = {request.group_id} \
                  ORDER BY {request.ordering}"
            )
        elif request.report_type.group_all:
            self._cur.execute(
                f"SELECT e.ID, AMOUNT, CATEGORY, COMMENT FROM expenses e \
                  LEFT JOIN categories c on e.CATEGORY_ID = c.id \
                  WHERE created_at >= '{request.start}' and e.GROUP_ID = {request.group_id} \
                  ORDER BY {request.ordering}"
            )

        expenses = {}
        for row in self._cur.fetchall():
            expenses[row[0]] = ExpenseReport(*row[1:])
        return expenses

    def del_row(self, id: int, user_id: int) -> None:
        self._cur.execute(
            f"DELETE FROM expenses WHERE ID = {id} and USER_ID = {user_id}"
        )
        self._conn.commit()

    def move_row(self, id: int, new_category: int, user_id: int) -> None:
        self._cur.execute(
            f"UPDATE expenses SET CATEGORY_ID = {new_category} WHERE id = {id} and USER_ID = {user_id}"
        )
        self._conn.commit()

    def insert_category(self, category: str, group_id: int) -> None:
        self._cur.execute(
            f"INSERT OR REPLACE INTO categories(CATEGORY, activerecord, GROUP_ID) VALUES ('{category}', 1, {group_id})"
        )
        self._conn.commit()

    def delete_category(self, category: int, group_id: int) -> None:
        self._cur.execute(
            f"UPDATE categories SET activerecord = 0 WHERE id = {category} and GROUP_ID = {group_id}"
        )
        self._conn.commit()

    def _create_database(self) -> None:
        with open("src/backend/createdb.sql", "r") as fl:
            sql = fl.read()
        self._cur.executescript(sql)
        self._conn.commit()

    def get_user_groups(self, user_id: int) -> list[Group]:
        self._cur.execute(
            f"SELECT ug.GROUP_ID, g.NAME from user_groups ug \
                LEFT JOIN groups g ON ug.GROUP_ID = g.ID \
                WHERE USER_ID = {user_id}"
        )
        groups = []
        for row in self._cur.fetchall():
            groups.append(Group(*row))
        return groups


db_client = SqliteClient()
