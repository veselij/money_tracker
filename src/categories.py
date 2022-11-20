import logging

from db import Category, DataBaseClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Categories:
    def __init__(self, db: DataBaseClient) -> None:
        self._db = db
        self._categories: dict[int, Category] = {}
        self._load_categories()

    def append(self, category: str) -> None:
        self._db.insert_category(category)
        self._load_categories()

    def __delitem__(self, category: str) -> None:
        self._db.delete_category(category)
        self._load_categories()

    def __getitem__(self, value: slice | int) -> list[Category]:
        if isinstance(value, slice):
            return list(self._categories.values())[value]
        else:
            return [self._categories[value]]

    def __iter__(self):
        for cat in self._categories.values():
            yield cat

    def get_category(self, id: int) -> Category:
        return self._categories[id]

    def _load_categories(self) -> None:
        self._categories = {}
        self._db.load_categories(self._categories)

    def __len__(self) -> int:
        return len(self._categories)
