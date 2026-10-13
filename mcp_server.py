import os
import sqlite3
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("SpendlySQLite")

# Resolve absolute path to the spendly.db database file
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "spendly.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool()
def list_tables() -> str:
    """
    List all user tables in the Spendly database.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        rows = cursor.fetchall()
        tables = [row["name"] for row in rows]
        if not tables:
            return "No tables found in the database."
        return "Tables in Spendly database:\n" + "\n".join(f"- {table}" for table in tables)
    except Exception as e:
        return f"Error listing tables: {e}"
    finally:
        conn.close()

@mcp.tool()
def describe_table_schema(table_name: str) -> str:
    """
    Describe the columns and schema definition of a specified table (e.g. 'expenses' or 'users').
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if table exists and get its SQL creation query
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        table_row = cursor.fetchone()
        if not table_row:
            return f"Table '{table_name}' does not exist in the database."
        
        # Get detailed column information
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        col_desc = []
        for col in columns:
            pk = " (PRIMARY KEY)" if col["pk"] else ""
            notnull = " NOT NULL" if col["notnull"] else ""
            default = f" DEFAULT {col['dflt_value']}" if col["dflt_value"] is not None else ""
            col_desc.append(f"  - {col['name']} ({col['type']}){notnull}{default}{pk}")
            
        schema_text = f"Table: {table_name}\n"
        schema_text += "Columns:\n" + "\n".join(col_desc) + "\n\n"
        schema_text += f"SQL Schema Definition:\n{table_row['sql']}"
        return schema_text
    except Exception as e:
        return f"Error describing table '{table_name}': {e}"
    finally:
        conn.close()

@mcp.tool()
def total_spending_by_category() -> str:
    """
    Show total spending and transaction counts grouped by category in the Spendly database.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as total_spent, COUNT(*) as transaction_count
            FROM expenses
            GROUP BY category
            ORDER BY total_spent DESC;
        """)
        rows = cursor.fetchall()
        if not rows:
            return "No expenses recorded in the database."
            
        header = f"{'Category':<18} | {'Total Spent':<12} | {'Transactions':<12}"
        separator = "-" * len(header)
        lines = [header, separator]
        for row in rows:
            amount_str = f"₹{row['total_spent']:,.2f}"
            lines.append(f"{row['category']:<18} | {amount_str:<12} | {row['transaction_count']:<12}")
            
        # Calculate overall total spent and count
        cursor.execute("SELECT SUM(amount) as total, COUNT(*) as count FROM expenses;")
        total_row = cursor.fetchone()
        overall_total = total_row["total"] if total_row["total"] is not None else 0
        overall_count = total_row["count"] if total_row["count"] is not None else 0
        total_str = f"₹{overall_total:,.2f}"
        lines.append(separator)
        lines.append(f"{'TOTAL':<18} | {total_str:<12} | {overall_count:<12}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error showing category breakdown: {e}"
    finally:
        conn.close()

if __name__ == "__main__":
    mcp.run(transport="stdio")
