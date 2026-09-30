"""Create a small demo SQLite DB with a few FK-linked tables and sample rows."""
import os

from sqlalchemy import create_engine, text

DB_PATH = "demo.sqlite"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

engine = create_engine(f"sqlite:///{DB_PATH}")

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    """))
    conn.execute(text("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """))
    conn.execute(text("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    """))
    conn.execute(text("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """))

    conn.execute(text("INSERT INTO customers (id, name, email) VALUES "
                       "(1, 'Ada Lovelace', 'ada@example.com'), "
                       "(2, 'Grace Hopper', 'grace@example.com')"))
    conn.execute(text("INSERT INTO products (id, name, price) VALUES "
                       "(1, 'Widget', 9.99), (2, 'Gadget', 19.99)"))
    conn.execute(text("INSERT INTO orders (id, customer_id, order_date) VALUES "
                       "(1, 1, '2026-09-01'), (2, 2, '2026-09-15')"))
    conn.execute(text("INSERT INTO order_items (id, order_id, product_id, quantity) VALUES "
                       "(1, 1, 1, 3), (2, 1, 2, 1), (3, 2, 2, 2)"))

engine.dispose()
print(f"Created {DB_PATH}")
