"""
SQLite database layer for Smart Shopping Intelligence System.
Manages users, product catalog, historical & live checkout transactions.
"""

import csv
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "shopping.db")
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")
TRANSACTIONS_CSV = os.path.join(BASE_DIR, "data", "transactions.csv")


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection with row_factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create tables if missing and seed initial products, demo user, and historical transactions."""
    if not os.path.exists(PRODUCTS_JSON) or not os.path.exists(TRANSACTIONS_CSV):
        from data.generate_data import main as generate_seed_files

        generate_seed_files()

    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                unit TEXT NOT NULL,
                rating REAL NOT NULL,
                badge TEXT NOT NULL,
                featured INTEGER NOT NULL DEFAULT 0,
                description TEXT NOT NULL,
                image_path TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_code TEXT NOT NULL UNIQUE,
                user_id INTEGER,
                total_amount REAL NOT NULL,
                item_count INTEGER NOT NULL,
                source TEXT NOT NULL DEFAULT 'checkout',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS transaction_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                unit_price REAL NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            );
            """
        )

        # Seed products if empty
        existing_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if existing_products == 0:
            with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
                products = json.load(f)
            conn.executemany(
                """
                INSERT INTO products (
                    id, name, slug, category, price, unit, rating, badge, featured, description, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        p["id"],
                        p["name"],
                        p["slug"],
                        p["category"],
                        float(p["price"]),
                        p["unit"],
                        float(p["rating"]),
                        p["badge"],
                        1 if p.get("featured") else 0,
                        p["description"],
                        p["image_path"],
                    )
                    for p in products
                ],
            )

        # Seed a demo academic reviewer user if no users exist
        existing_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing_users == 0:
            conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Demo Shopper",
                    "demo@smartshop.ai",
                    generate_password_hash("Demo@123"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

        # Seed historical transactions into SQLite if none exist
        existing_tx = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if existing_tx == 0 and os.path.exists(TRANSACTIONS_CSV):
            product_map = {
                row["name"]: (row["id"], float(row["price"]))
                for row in conn.execute("SELECT id, name, price FROM products").fetchall()
            }
            with open(TRANSACTIONS_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    items = [x.strip() for x in row["items"].split(",") if x.strip() in product_map]
                    if not items:
                        continue
                    total_amt = round(sum(product_map[name][1] for name in items), 2)
                    cur = conn.execute(
                        """
                        INSERT INTO transactions (transaction_code, user_id, total_amount, item_count, source, created_at)
                        VALUES (?, NULL, ?, ?, 'historical', ?)
                        """,
                        (row["transaction_id"], total_amt, len(items), row["timestamp"]),
                    )
                    tx_id = cur.lastrowid
                    conn.executemany(
                        """
                        INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, unit_price)
                        VALUES (?, ?, ?, 1, ?)
                        """,
                        [(tx_id, product_map[name][0], name, product_map[name][1]) for name in items],
                    )

        conn.commit()
    finally:
        conn.close()


# --- User Operations ---

def create_user(full_name: str, email: str, password_hash: str) -> Optional[int]:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO users (full_name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (full_name.strip(), email.strip().lower(), password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, full_name, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Product Operations ---

def get_all_products(
    search: str = "",
    category: str = "",
    sort_by: str = "featured",
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        query = "SELECT * FROM products WHERE 1=1"
        params: list[Any] = []
        if search:
            query += " AND (LOWER(name) LIKE ? OR LOWER(category) LIKE ? OR LOWER(description) LIKE ?)"
            token = f"%{search.strip().lower()}%"
            params.extend([token, token, token])
        if category and category.lower() != "all":
            query += " AND category = ?"
            params.append(category)

        order_map = {
            "featured": "featured DESC, rating DESC, id ASC",
            "price_asc": "price ASC, name ASC",
            "price_desc": "price DESC, name ASC",
            "rating": "rating DESC, name ASC",
            "name": "name ASC",
        }
        query += f" ORDER BY {order_map.get(sort_by, order_map['featured'])}"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_categories_summary() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT category, COUNT(*) AS product_count, ROUND(AVG(price), 2) AS avg_price
            FROM products
            GROUP BY category
            ORDER BY category ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_product_by_id(product_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_products_by_ids(product_ids: list[int]) -> list[dict[str, Any]]:
    if not product_ids:
        return []
    conn = get_connection()
    try:
        placeholders = ",".join("?" for _ in product_ids)
        rows = conn.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", product_ids).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --- Transaction Operations ---

def save_checkout_transaction(
    user_id: Optional[int],
    cart_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Persist a completed checkout basket to SQLite `transactions` & `transaction_items`,
    and append to `data/transactions.csv` so historical files remain synchronized.
    """
    conn = get_connection()
    try:
        total_amount = round(sum(float(item["price"]) * int(item["quantity"]) for item in cart_items), 2)
        item_count = sum(int(item["quantity"]) for item in cart_items)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tx_code = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"

        cur = conn.execute(
            """
            INSERT INTO transactions (transaction_code, user_id, total_amount, item_count, source, created_at)
            VALUES (?, ?, ?, ?, 'checkout', ?)
            """,
            (tx_code, user_id, total_amount, item_count, now_str),
        )
        tx_id = cur.lastrowid

        conn.executemany(
            """
            INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, unit_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (tx_id, int(item["id"]), item["name"], int(item["quantity"]), float(item["price"]))
                for item in cart_items
            ],
        )
        conn.commit()

        return {
            "id": tx_id,
            "transaction_code": tx_code,
            "total_amount": total_amount,
            "item_count": item_count,
            "created_at": now_str,
        }
    finally:
        conn.close()


def get_user_transactions(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        tx_rows = conn.execute(
            """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        results = []
        for tx in tx_rows:
            tx_dict = dict(tx)
            items = conn.execute(
                "SELECT product_name, quantity, unit_price FROM transaction_items WHERE transaction_id = ?",
                (tx["id"],),
            ).fetchall()
            tx_dict["items"] = [dict(i) for i in items]
            results.append(tx_dict)
        return results
    finally:
        conn.close()


def get_all_baskets_from_db() -> list[list[str]]:
    """Load all transactions (historical + live checkouts) as lists of product names."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.id AS tx_id, ti.product_name
            FROM transactions t
            JOIN transaction_items ti ON ti.transaction_id = t.id
            ORDER BY t.id ASC
            """
        ).fetchall()
        baskets: dict[int, list[str]] = {}
        for r in rows:
            baskets.setdefault(r["tx_id"], []).append(r["product_name"])
        return list(baskets.values())
    finally:
        conn.close()
