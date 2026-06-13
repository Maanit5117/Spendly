import datetime
from database.db import get_db

def format_member_since(created_at_str):
    if not created_at_str:
        return ""
    # Try various common SQLite datetime formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.datetime.strptime(created_at_str, fmt)
            return dt.strftime("%B %Y")
        except ValueError:
            continue
    # Fallback to manual parsing if formats don't match
    try:
        parts = created_at_str.split(" ")[0].split("-")
        if len(parts) >= 2:
            year = int(parts[0])
            month = int(parts[1])
            dt = datetime.datetime(year, month, 1)
            return dt.strftime("%B %Y")
    except Exception:
        pass
    return created_at_str

def get_user_by_id(user_id):
    """
    Retrieves a user's details by id.
    Returns a dict with 'name', 'email', and 'member_since' (formatted as Month YYYY)
    or None if the user does not exist.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, created_at FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": format_member_since(row["created_at"])
        }
    finally:
        conn.close()

def get_summary_stats(user_id, start_date=None, end_date=None):
    """
    Retrieves summary stats for a user's expenses.
    Returns a dict with 'total_spent', 'transaction_count', and 'top_category'.
    If the user has no expenses, returns zeros/hyphen defaults.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = "SELECT SUM(amount) as total_spent, COUNT(*) as transaction_count FROM expenses WHERE user_id = ?"
        params = [user_id]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        
        total_spent = row["total_spent"] if row["total_spent"] is not None else 0
        transaction_count = row["transaction_count"] if row["transaction_count"] is not None else 0
        
        if transaction_count == 0:
            return {
                "total_spent": 0,
                "transaction_count": 0,
                "top_category": "—"
            }
            
        # Top category query (highest single-category total sum of amount)
        cat_query = "SELECT category, SUM(amount) as cat_total FROM expenses WHERE user_id = ?"
        cat_params = [user_id]
        if start_date:
            cat_query += " AND date >= ?"
            cat_params.append(start_date)
        if end_date:
            cat_query += " AND date <= ?"
            cat_params.append(end_date)
            
        cat_query += " GROUP BY category ORDER BY cat_total DESC, category ASC LIMIT 1;"
        
        cursor.execute(cat_query, tuple(cat_params))
        cat_row = cursor.fetchone()
        top_category = cat_row["category"] if cat_row else "—"
        
        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category
        }
    finally:
        conn.close()

def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    """
    Retrieves the most recent transactions for a user.
    Returns a list of dicts ordered newest-first.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = "SELECT date, description, category, amount FROM expenses WHERE user_id = ?"
        params = [user_id]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        query += " ORDER BY date DESC, id DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [
            {
                "date": r["date"],
                "description": r["description"],
                "category": r["category"],
                "amount": r["amount"]
            }
            for r in rows
        ]
    finally:
        conn.close()

def get_category_breakdown(user_id, start_date=None, end_date=None):
    """
    Retrieves category breakdown for a user's expenses.
    Returns a list of dicts, each with 'name', 'amount', and 'pct'.
    Percentage values are rounded integers summing to 100.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = "SELECT category as name, SUM(amount) as amount FROM expenses WHERE user_id = ?"
        params = [user_id]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        query += " GROUP BY category ORDER BY amount DESC;"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        if not rows:
            return []
            
        breakdown = [{"name": r["name"], "amount": r["amount"]} for r in rows]
        total_spent = sum(item["amount"] for item in breakdown)
        
        if total_spent == 0:
            for item in breakdown:
                item["pct"] = 0
            return breakdown
            
        # Calculate percentage using integer rounding
        sum_pct = 0
        for item in breakdown:
            pct = int(round((item["amount"] / total_spent) * 100))
            item["pct"] = pct
            sum_pct += pct
            
        # Adjust the largest category to absorb any rounding remainder
        # Since the query is ordered by amount DESC, breakdown[0] is the largest category
        remainder = 100 - sum_pct
        if remainder != 0 and breakdown:
            breakdown[0]["pct"] += remainder
            
        return breakdown
    finally:
        conn.close()
