import sqlite3
import os
from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP("ExpenseTrackerServer")

DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, "expenses.db")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


init_db()


def get_db_connection():
    return sqlite3.connect(DB_NAME, timeout=10.0)


@mcp.tool
def add_expense(
    title: str, amount: float, category: str = "General", created_at: str = None
) -> str:
    """
    Add a new expense.

    created_at format:
    YYYY-MM-DD HH:MM:SS
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if created_at is None:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO expenses (title, amount, category, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (title, amount, category, created_at),
    )

    conn.commit()
    conn.close()

    return f"✅ Expense added: {title} - {amount} ({category}) on {created_at}"


@mcp.tool
def list_expenses() -> list:
    """List all expenses."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, amount, category, created_at
        FROM expenses
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "amount": row[2],
            "category": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


@mcp.tool
def delete_expense(expense_id: int) -> str:
    """Delete an expense by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
    expense = cursor.fetchone()

    if not expense:
        conn.close()
        return f"Expense with ID {expense_id} not found."

    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

    return f"Expense with ID {expense_id} deleted successfully."


@mcp.tool
def total_expenses() -> float:
    """Get total expense amount."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]
    conn.close()

    return total if total else 0.0


@mcp.tool
def expenses_by_category(category: str) -> list:
    """Get expenses filtered by category."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title, amount, created_at
        FROM expenses
        WHERE category = ?
        ORDER BY created_at DESC
        """,
        (category,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "amount": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


if __name__ == "__main__":
# Run with HTTP transport
    mcp.run(transport="http", host="0.0.0.0", port=9000)