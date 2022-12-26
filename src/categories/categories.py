from backend.db import Category, DataBaseClient


class Categories:
    def __init__(self, db: DataBaseClient, group_id: int) -> None:
        self._db = db
        self._categories: dict[int, Category] = {}
        self._categories_reversed: dict[str, int]
        self._group_id = group_id
        self._load_categories()

    def append(self, category: str) -> None:
        self._db.insert_category(category, self._group_id)
        self._load_categories()

    def __delitem__(self, category: int) -> None:
        self._db.delete_category(category, self._group_id)
        self._load_categories()

    def __getitem__(self, value: int) -> Category:
        return self._categories[value]

    def __iter__(self):
        for cat in self._categories.values():
            yield cat

    def get_category_id(self, category: str) -> int:
        return self._categories_reversed[category]

    def _load_categories(self) -> None:
        self._categories = {}
        self._db.load_categories(self._categories, self._group_id)
        self._categories_reversed = {
            cat.name: cat.id for cat in self._categories.values()
        }

    def __len__(self) -> int:
        return len(self._categories)