import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path(__file__).with_name("finance.db")

class DataBase:
    def __init__(self, db_path: Path | str = DB_FILE):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS User (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS Account (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL,
                balance  INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Category (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                user_id  INTEGER,
                type     INTEGER NOT NULL,          -- 0 = расход, 1 = доход
                FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Operation (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id  INTEGER NOT NULL,
                type        INTEGER NOT NULL,       -- 0 = расход, 1 = доход
                amount      INTEGER NOT NULL,       -- храним в копейках / центах
                category_id INTEGER,
                date        DATETIME NOT NULL,
                note        TEXT,                   -- описание (доп. к диаграмме)
                FOREIGN KEY (account_id)  REFERENCES Account(id)  ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES Category(id) ON DELETE SET NULL
            );
            """
        )
        self.conn.commit()

    def ensure_default_user(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM User LIMIT 1;")
        row = cur.fetchone()
        if row:
            return row["id"]

        cur.execute(
            "INSERT INTO User (username, password) VALUES (?, ?);",
            ("local", "local"),
        )
        self.conn.commit()
        return cur.lastrowid

    def ensure_default_account(self, user_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM Account WHERE user_id = ? LIMIT 1;", (user_id,))
        row = cur.fetchone()
        if row:
            return row["id"]

        cur.execute(
            "INSERT INTO Account (user_id, balance) VALUES (?, 0);",
            (user_id,),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_categories(self, user_id: int, cat_type: int | None = None) -> list[sqlite3.Row]:
        sql = "SELECT * FROM Category WHERE user_id = ?"
        params: list = [user_id]
        if cat_type is not None:
            sql += " AND type = ?"
            params.append(cat_type)
        cur = self.conn.execute(sql + " ORDER BY name;", params)
        return cur.fetchall()

    def add_category(self, user_id: int, name: str, cat_type: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO Category (name, user_id, type) VALUES (?, ?, ?);",
            (name, user_id, cat_type),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_operation(
        self,
        account_id: int,
        op_type: int,
        amount: float,
        category_id: int | None,
        date: datetime,
        note: str | None = None,
    ) -> int:
        amount_int = int(round(amount * 100))
        cur = self.conn.execute(
            """
            INSERT INTO Operation (account_id, type, amount, category_id, date, note)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (account_id, op_type, amount_int, category_id, date.isoformat(), note),
        )
        self.conn.commit()

        sign = 1 if op_type else -1
        self.conn.execute(
            "UPDATE Account SET balance = balance + ? WHERE id = ?;",
            (sign * amount_int, account_id),
        )
        self.conn.commit()

        return cur.lastrowid

    def delete_operation(self, op_id: int) -> None:
        row = self.conn.execute(
            "SELECT account_id, type, amount FROM Operation WHERE id = ?;", (op_id,)
        ).fetchone()
        if not row:
            return
        sign = 1 if row["type"] else -1
        self.conn.execute(
            "UPDATE Account SET balance = balance - ? WHERE id = ?;",
            (sign * row["amount"], row["account_id"]),
        )
        self.conn.execute("DELETE FROM Operation WHERE id = ?;", (op_id,))
        self.conn.commit()

    def list_operations(self, account_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT o.id,
                   o.date,
                   o.amount,
                   o.type,
                   o.note,
                   c.name  AS category_name
            FROM Operation o
            LEFT JOIN Category c ON c.id = o.category_id
            WHERE o.account_id = ?
            ORDER BY o.date DESC;
            """,
            (account_id,),
        ).fetchall()

    def get_account_balance(self, account_id: int) -> int:
        cur = self.conn.execute(
            "SELECT balance FROM Account WHERE id = ?;", (account_id,)
        ).fetchone()
        return cur["balance"] if cur else 0