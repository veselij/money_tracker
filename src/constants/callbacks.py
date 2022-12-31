import re

from backend.db import Category, Group

nums = re.compile(r"\d+")


category_id = re.compile(rf"{Category.__name__.lower()} \d+")
category_delete = "category_delete"
category_add = "category_add"

report_list = "report_list"
report_total = "report_total"
report_trend = "report_trend"
report_my = "report_my"
report_all = "report_all"

report_by_date = "created_at"
report_by_amount = "category, amount desc"

manage_move_expense = "manage_move_expense"
manage_delete_expense = "manage_delete_expense"

groups_id = re.compile(rf"{Group.__name__.lower()} \d+")
groups_create = "groups_create"
groups_delete = "groups_delete"
groups_add_user = "groups_add_user"
groups_remove_user = "groups_remove_user"
