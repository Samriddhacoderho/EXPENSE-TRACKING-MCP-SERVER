import sqlite3
import os
from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP("ExpenseTrackerServer")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "expenses.db")
# Convert path to a proper URI format for advanced SQLite flags
DB_URI = f"file:{DB_NAME}?mode=rw"


def init_db():
    # For initialization, we create the file if it doesn't exist (rwc = read/write/create)
    conn = sqlite3.connect(f"file:{DB_NAME}?mode=rwc", uri=True)
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


# Initialize the database file
init_db()


def get_db_connection():
    """Helper to return a connection strictly locked in Read-Write mode with a timeout."""
    # uri=True allows us to use the 'mode=rw' flag to force write capability
    conn = sqlite3.connect(DB_URI, uri=True, timeout=10.0)

    # Enable WAL mode so HTTP server reads don't block tool writes
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# add expense tool
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

    return f"Expense added: {title} - {amount} ({category}) on {created_at}"


# list expenses tool
@mcp.tool
def list_expenses() -> list:
    """
    List all expenses.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, amount, category, created_at
    FROM expenses
    ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    expenses = []
    for row in rows:
        expenses.append(
            {
                "id": row[0],
                "title": row[1],
                "amount": row[2],
                "category": row[3],
                "created_at": row[4],
            }
        )

    return expenses


@mcp.tool
def delete_expense(expense_id: int) -> str:
    """
    Delete an expense by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
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
    """
    Get total expense amount.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]
    conn.close()

    return total if total else 0.0


@mcp.tool
def expenses_by_category(category: str) -> list:
    """
    Get expenses filtered by category.
    """
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

    results = []
    for row in rows:
        results.append(
            {"id": row[0], "title": row[1], "amount": row[2], "created_at": row[3]}
        )

    return results


if __name__ == "__main__":
    # Run with HTTP transport
    mcp.run(transport="http", host="127.0.0.1", port=9000)

