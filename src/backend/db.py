import sqlite3
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from config import MONTH_START_DAY


def calculate_date() -> str:
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if day >= MONTH_START_DAY:
        return f"{year}-{month}-{MONTH_START_DAY}"
    else:
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        return f"{year}-{month}-{MONTH_START_DAY}"


@dataclass(frozen=True)
class Category:
    id: int
    name: str = ""


@dataclass(frozen=True)
class Group:
    id: int
    name: str = ""


@dataclass(frozen=True)
class User:
    id: int


@dataclass(frozen=True)
class Expense:
    amount: int
    category: Category
    user: User
    group: Group
    comment: str = ""


@dataclass(frozen=True)
class ReportRequest:
    user: User
    group: Group
    ordering: str
    start: str = calculate_date()
    all: bool = False


class DataBaseClient(ABC):
    @abstractmethod
    def register_user(self, user_id: int, username: str) -> None:
        ...

    @abstractmethod
    def is_user_registred(self, user: User) -> bool:
        ...

    @abstractmethod
    def create_group(self, user_id: int, name: str) -> None:
        ...

    @abstractmethod
    def delete_group(self, group: Group) -> None:
        ...

    @abstractmethod
    def add_user_to_group(self, group: Group, user: User) -> None:
        ...

    @abstractmethod
    def delete_user_from_group(self, group: Group, user: User) -> None:
        ...

    @abstractmethod
    def insert(self, expense: Expense) -> int:
        ...

    @abstractmethod
    def get_expenses_total(
        self, request: ReportRequest
    ) -> dict[Category, list[Expense]]:
        ...

    @abstractmethod
    def get_expenses_last(self, request: ReportRequest) -> dict[int, Expense]:
        ...

    @abstractmethod
    def get_expenses_month_trend(
        self, request: ReportRequest
    ) -> dict[str, list[Expense]]:
        ...

    @abstractmethod
    def load_categories(self, categories: dict[int, Category], group: Group) -> None:
        ...

    @abstractmethod
    def del_expense(self, id: int) -> None:
        ...

    @abstractmethod
    def update_expense_category(
        self, current_category_id: int, new_category: int
    ) -> None:
        ...

    @abstractmethod
    def insert_category(self, category: str, group: Group) -> None:
        ...

    @abstractmethod
    def delete_category(self, category: int, group: Group) -> None:
        ...

    @abstractmethod
    def _create_database(self) -> None:
        ...

    @abstractmethod
    def get_user_groups(self, user_id: int) -> list[Group]:
        ...

    @abstractmethod
    def get_user(self, user_id: int) -> User | None:
        ...

    @abstractmethod
    def get_group(self, group_id: int) -> Group | None:
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

    def is_user_registred(self, user: User) -> bool:
        self._cur.execute(f"SELECT ID FROM users WHERE USER_ID = {user.id}")
        return len(self._cur.fetchall()) > 0

    def create_group(self, user_id: int, name: str) -> None:
        self._cur.execute(
            f"INSERT OR REPLACE INTO groups(NAME, CREATOR, activerecord) VALUES('{name}', {user_id}, 1)"
        )
        self._conn.commit()
        group_id = self._cur.lastrowid
        self._cur.execute(
            f"INSERT OR IGNORE INTO user_groups(USER_ID, GROUP_ID) VALUES({user_id}, {group_id})"
        )
        self._conn.commit()

    def delete_group(self, group: Group) -> None:
        self._cur.execute(f"UPDATE groups SET activerecord = 0 WHERE id = {group.id}")
        self._conn.commit()

    def add_user_to_group(self, group: Group, user: User) -> None:
        self._cur.execute(
            f"INSERT OR IGNORE INTO user_groups(USER_ID, GROUP_ID) VALUES({user.id}, {group.id})"
        )
        self._conn.commit()

    def delete_user_from_group(self, group: Group, user: User) -> None:
        self._cur.execute(
            f"DELETE FROM user_groups WHERE group_id = {group.id} and USER_ID = {user.id}"
        )
        self._conn.commit()

    def load_categories(self, categories: dict[int, Category], group: Group) -> None:
        self._cur.execute(
            f"SELECT id, CATEGORY from categories WHERE activerecord = 1 and group_id = {group.id}"
        )
        for row in self._cur.fetchall():
            categories[row[0]] = Category(*row)

    def insert(self, expense: Expense) -> int:
        self._cur.execute(
            f"INSERT INTO expenses(AMOUNT, COMMENT, CATEGORY_ID, USER_ID, GROUP_ID) VALUES \
        ({expense.amount}, '{expense.comment.strip()}', {expense.category.id}, {expense.user.id}, {expense.group.id})"
        )
        self._conn.commit()
        return self._cur.lastrowid or -1

    def get_expenses_total(
        self, request: ReportRequest
    ) -> dict[Category, list[Expense]]:
        self._cur.execute(
            f"SELECT sum(AMOUNT) as AMOUNT, c.id, c.CATEGORY, e.user_id, e.group_id FROM expenses e \
              LEFT JOIN categories c on e.CATEGORY_ID = c.id \
              WHERE created_at >= '{request.start}' and e.GROUP_ID = {request.group.id} \
              GROUP BY c.id, c.CATEGORY, e.user_id, e.group_id \
              ORDER BY {request.ordering}"
        )

        expenses = defaultdict(list)
        for row in self._cur.fetchall():
            expenses[Category(row[1], row[2])].append(
                Expense(
                    row[0],
                    Category(row[1], row[2]),
                    User(row[3]),
                    Group(row[4]),
                )
            )
        return expenses

    def get_expenses_month_trend(
        self, request: ReportRequest
    ) -> dict[str, list[Expense]]:
        self._cur.execute(
            f"SELECT strftime('%Y-%m-%d',created_at), sum(AMOUNT) as AMOUNT, c.id, c.CATEGORY, e.user_id, e.group_id FROM expenses e \
              LEFT JOIN categories c on e.CATEGORY_ID = c.id \
              WHERE e.GROUP_ID = {request.group.id} \
              GROUP BY strftime('%Y-%m-%d',created_at), c.id, c.CATEGORY, e.user_id, e.group_id \
              ORDER BY {request.ordering}"
        )

        expenses: dict[str, list[Expense]] = defaultdict(list)
        for row in self._cur.fetchall():
            expenses[row[0]].append(
                Expense(
                    row[1],
                    Category(row[2], row[3]),
                    User(row[4]),
                    Group(row[5]),
                )
            )
        return expenses

    def get_expenses_last(self, request: ReportRequest) -> dict[int, Expense]:
        self._cur.execute(
            f"SELECT e.ID, AMOUNT,c.id, c.CATEGORY, e.user_id, e.group_id, COMMENT FROM expenses e \
              LEFT JOIN categories c on e.CATEGORY_ID = c.id \
              WHERE created_at >= '{request.start}' and e.GROUP_ID = {request.group.id} \
              ORDER BY {request.ordering}"
        )

        expenses = {}
        for row in self._cur.fetchall():
            expenses[row[0]] = Expense(
                row[1],
                Category(row[2], row[3]),
                User(row[4]),
                Group(row[5]),
                row[6],
            )
        return expenses

    def del_expense(self, id: int) -> None:
        self._cur.execute(f"DELETE FROM expenses WHERE ID = {id}")
        self._conn.commit()

    def update_expense_category(
        self, current_category_id: int, new_category: int
    ) -> None:
        self._cur.execute(
            f"UPDATE expenses SET CATEGORY_ID = {new_category} WHERE id = {current_category_id}"
        )
        self._conn.commit()

    def insert_category(self, category: str, group: Group) -> None:
        self._cur.execute(
            f"INSERT OR REPLACE INTO categories(CATEGORY, activerecord, GROUP_ID) VALUES ('{category}', 1, {group.id})"
        )
        self._conn.commit()

    def delete_category(self, category: int, group: Group) -> None:
        self._cur.execute(
            f"UPDATE categories SET activerecord = 0 WHERE id = {category} and GROUP_ID = {group.id}"
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
                WHERE USER_ID = {user_id} and g.activerecord = 1"
        )
        groups = []
        for row in self._cur.fetchall():
            groups.append(Group(*row))
        return groups

    def get_user(self, user_id: int) -> User | None:
        self._cur.execute(
            f"SELECT user_id, username from users WHERE USER_ID ={user_id} "
        )
        data = self._cur.fetchone()
        return User(*data) if data else None

    def get_group(self, group_id: int) -> Group | None:
        self._cur.execute(f"SELECT id, name from groups WHERE id = {group_id} ")
        data = self._cur.fetchone()
        return Group(*data) if data else None


db_client = SqliteClient()
