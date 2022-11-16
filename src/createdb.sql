create table if not exists categories (ID INTEGER PRIMARY KEY, CATEGORY TEXT NOT NULL UNIQUE, activerecord INTEGER DEFAULT 1);

create table if not exists expenses (ID INTEGER PRIMARY KEY, CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP, AMOUNT INTEGER, COMMENT TEXT, CATEGORY_ID INTEGER, USER_ID INTEGER, CONSTRAINT categories_expenses_fk FOREIGN KEY (CATEGORY_ID)  REFERENCES categories (ID));

insert or ignore into categories(CATEGORY) values
        ("Машина"),
        ("Продукты"),
        ("Кружки"),
        ("Коммуналка"),
        ("Красота"),
        ("Кафе"),
        ("Одежда и обувь"),
        ("Алко"),
        ("Офис"),
        ("Прочее");

alter table categories add column if not exists activerecord INTEGER DEFAULT 1;
