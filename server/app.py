"""
Database access layer for the Library Agent.
Every public function maps to an agent tool or chat-persistence operation.
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "library-agent.db")


# ── helpers ──────────────────────────────────────────────────────────────

def _conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _rows(rows):
    return [dict(r) for r in rows]


def init_db():
    """Create tables and seed data if books table is empty."""
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")
    with open(os.path.join(ROOT, "db", "tables.sql")) as f:
        conn.executescript(f.read())
    count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if count == 0:
        with open(os.path.join(ROOT, "db", "seed.sql")) as f:
            conn.executescript(f.read())
        print("✅ Database seeded")
    conn.close()


# ── domain functions (agent tools) ──────────────────────────────────────

def find_books(q: str, by: str = "title"):
    """Search books by title or author (partial, case-insensitive)."""
    col = "author" if by == "author" else "title"
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT isbn, title, author, genre, price, stock FROM books WHERE {col} LIKE ?",
            (f"%{q}%",),
        ).fetchall()
    return _rows(rows)


def create_order(customer_id: int, items: list):
    """Create an order, reduce stock. items = [{"isbn": "...", "qty": N}]."""
    with _conn() as conn:
        cust = conn.execute("SELECT id, name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not cust:
            return {"error": f"Customer {customer_id} not found."}

        for item in items:
            book = conn.execute("SELECT isbn, title, stock FROM books WHERE isbn = ?", (item["isbn"],)).fetchone()
            if not book:
                return {"error": f"Book with ISBN {item['isbn']} not found."}
            if book["stock"] < item["qty"]:
                return {"error": f"Not enough stock for '{book['title']}' (have {book['stock']}, need {item['qty']})."}

        cur = conn.execute("INSERT INTO orders (customer_id) VALUES (?)", (customer_id,))
        order_id = cur.lastrowid

        stock_updates = []
        for item in items:
            price_row = conn.execute("SELECT price FROM books WHERE isbn = ?", (item["isbn"],)).fetchone()
            conn.execute(
                "INSERT INTO order_items (order_id, isbn, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, item["isbn"], item["qty"], price_row["price"]),
            )
            conn.execute("UPDATE books SET stock = stock - ? WHERE isbn = ?", (item["qty"], item["isbn"]))
            new = conn.execute("SELECT title, stock FROM books WHERE isbn = ?", (item["isbn"],)).fetchone()
            stock_updates.append({"isbn": item["isbn"], "title": new["title"], "new_stock": new["stock"]})
        conn.commit()
    return {"order_id": order_id, "customer": dict(cust), "stock_updates": stock_updates}


def restock_book(isbn: str, qty: int):
    """Add qty copies to a book's stock."""
    with _conn() as conn:
        book = conn.execute("SELECT isbn, title, stock FROM books WHERE isbn = ?", (isbn,)).fetchone()
        if not book:
            return {"error": f"Book with ISBN {isbn} not found."}
        conn.execute("UPDATE books SET stock = stock + ? WHERE isbn = ?", (qty, isbn))
        conn.commit()
        new = conn.execute("SELECT stock FROM books WHERE isbn = ?", (isbn,)).fetchone()
    return {"isbn": isbn, "title": book["title"], "old_stock": book["stock"], "new_stock": new["stock"]}


def update_price(isbn: str, price: float):
    """Set a new price for a book."""
    with _conn() as conn:
        book = conn.execute("SELECT isbn, title, price FROM books WHERE isbn = ?", (isbn,)).fetchone()
        if not book:
            return {"error": f"Book with ISBN {isbn} not found."}
        conn.execute("UPDATE books SET price = ? WHERE isbn = ?", (price, isbn))
        conn.commit()
    return {"isbn": isbn, "title": book["title"], "old_price": book["price"], "new_price": price}


def order_status(order_id: int):
    """Return full summary of an order."""
    with _conn() as conn:
        order = conn.execute(
            "SELECT o.id, o.customer_id, c.name AS customer_name, o.order_date, o.status "
            "FROM orders o JOIN customers c ON c.id = o.customer_id WHERE o.id = ?",
            (order_id,),
        ).fetchone()
        if not order:
            return {"error": f"Order {order_id} not found."}
        items = conn.execute(
            "SELECT oi.isbn, b.title, oi.quantity, oi.unit_price "
            "FROM order_items oi JOIN books b ON b.isbn = oi.isbn WHERE oi.order_id = ?",
            (order_id,),
        ).fetchall()
    total = sum(r["quantity"] * r["unit_price"] for r in items)
    return {
        "order_id": order["id"],
        "customer": order["customer_name"],
        "date": order["order_date"],
        "status": order["status"],
        "items": _rows(items),
        "total": round(total, 2),
    }


def inventory_summary():
    """List low-stock books (stock < 5) and totals."""
    with _conn() as conn:
        low = conn.execute(
            "SELECT isbn, title, author, stock FROM books WHERE stock < 5 ORDER BY stock"
        ).fetchall()
        totals = conn.execute("SELECT COUNT(*) AS cnt, SUM(stock) AS total FROM books").fetchone()
    return {
        "total_titles": totals["cnt"],
        "total_copies": totals["total"],
        "low_stock_books": _rows(low),
    }


# ── chat persistence ────────────────────────────────────────────────────

def save_message(session_id: str, role: str, content: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()


def save_tool_call(session_id: str, name: str, args_json: str, result_json: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO tool_calls (session_id, name, args_json, result_json) VALUES (?, ?, ?, ?)",
            (session_id, name, args_json, result_json),
        )
        conn.commit()


def get_messages(session_id: str):
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return _rows(rows)


def get_sessions():
    """Return sessions with first user message as preview."""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT session_id,
                      MIN(created_at) AS started_at,
                      (SELECT content FROM messages m2
                       WHERE m2.session_id = m.session_id AND m2.role='user'
                       ORDER BY m2.id LIMIT 1) AS preview
               FROM messages m GROUP BY session_id ORDER BY MIN(created_at) DESC"""
        ).fetchall()
    return _rows(rows)


def delete_session(session_id: str):
    with _conn() as conn:
        conn.execute("DELETE FROM tool_calls WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
