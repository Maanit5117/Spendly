import pytest
import re
from app import app
from database.db import get_db, create_user
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)

@pytest.fixture(scope="module")
def setup_users():
    db = get_db()
    try:
        # Get or create seed user
        user = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
        if user:
            demo_user_id = user["id"]
        else:
            demo_user_id = create_user("Demo User", "demo@spendly.com", "demo123")
            
        # Create a new user with no expenses
        no_expense_user = db.execute("SELECT id FROM users WHERE email = ?", ("noexpenses@spendly.com",)).fetchone()
        if no_expense_user:
            no_expense_user_id = no_expense_user["id"]
        else:
            no_expense_user_id = create_user("No Expense User", "noexpenses@spendly.com", "password123")
            
        return {
            "demo_user_id": demo_user_id,
            "no_expense_user_id": no_expense_user_id
        }
    finally:
        db.close()

def test_get_user_by_id_valid(setup_users):
    user_id = setup_users["demo_user_id"]
    user = get_user_by_id(user_id)
    assert user is not None
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    # member_since should format as "Month YYYY" (e.g. "June 2026")
    assert re.match(r"^[A-Z][a-z]+ \d{4}$", user["member_since"])

def test_get_user_by_id_non_existent():
    assert get_user_by_id(999999) is None

def test_get_summary_stats_with_expenses(setup_users):
    user_id = setup_users["demo_user_id"]
    stats = get_summary_stats(user_id)
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"
    assert stats["total_spent"] > 0
    db = get_db()
    try:
        expected_total = db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,)).fetchone()[0]
        assert stats["total_spent"] == expected_total
    finally:
        db.close()

def test_get_summary_stats_no_expenses(setup_users):
    user_id = setup_users["no_expense_user_id"]
    stats = get_summary_stats(user_id)
    assert stats == {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

def test_get_recent_transactions_with_expenses(setup_users):
    user_id = setup_users["demo_user_id"]
    txs = get_recent_transactions(user_id, limit=5)
    assert len(txs) == 5
    for i in range(len(txs) - 1):
        assert txs[i]["date"] >= txs[i+1]["date"]
    for tx in txs:
        assert "date" in tx
        assert "description" in tx
        assert "category" in tx
        assert "amount" in tx

def test_get_recent_transactions_no_expenses(setup_users):
    user_id = setup_users["no_expense_user_id"]
    txs = get_recent_transactions(user_id)
    assert txs == []

def test_get_category_breakdown_with_expenses(setup_users):
    user_id = setup_users["demo_user_id"]
    breakdown = get_category_breakdown(user_id)
    assert len(breakdown) > 0
    for i in range(len(breakdown) - 1):
        assert breakdown[i]["amount"] >= breakdown[i+1]["amount"]
    total_pct = sum(item["pct"] for item in breakdown)
    assert total_pct == 100
    for item in breakdown:
        assert isinstance(item["pct"], int)

def test_get_category_breakdown_no_expenses(setup_users):
    user_id = setup_users["no_expense_user_id"]
    breakdown = get_category_breakdown(user_id)
    assert breakdown == []


def test_queries_with_date_range(setup_users):
    user_id = setup_users["demo_user_id"]
    # Range that includes: 2026-06-05 through 2026-06-10
    start_date = "2026-06-05"
    end_date = "2026-06-10"
    
    # 1. Summary stats
    stats = get_summary_stats(user_id, start_date=start_date, end_date=end_date)
    assert stats["transaction_count"] == 4
    assert stats["total_spent"] == 252.50
    assert stats["top_category"] == "Bills"
    
    # 2. Recent transactions
    txs = get_recent_transactions(user_id, limit=10, start_date=start_date, end_date=end_date)
    assert len(txs) == 4
    assert txs[0]["date"] == "2026-06-10"
    assert txs[-1]["date"] == "2026-06-05"
    
    # 3. Category breakdown
    breakdown = get_category_breakdown(user_id, start_date=start_date, end_date=end_date)
    # Categories: Bills (120.00), Shopping (65.50), Health (45.00), Entertainment (22.00)
    # Total spent: 252.50
    # Percentages:
    # Bills: 120 / 252.5 = 47.52% -> 48%
    # Shopping: 65.5 / 252.5 = 25.94% -> 26%
    # Health: 45 / 252.5 = 17.82% -> 18%
    # Entertainment: 22 / 252.5 = 8.71% -> 9%
    # Sum: 48 + 26 + 18 + 9 = 101% -> adjustment makes Bills 47%
    assert len(breakdown) == 4
    assert breakdown[0]["name"] == "Bills"
    assert breakdown[0]["pct"] == 47
    assert breakdown[1]["name"] == "Shopping"
    assert breakdown[1]["pct"] == 26
    assert breakdown[2]["name"] == "Health"
    assert breakdown[2]["pct"] == 18
    assert breakdown[3]["name"] == "Entertainment"
    assert breakdown[3]["pct"] == 9
    
    total_pct = sum(item["pct"] for item in breakdown)
    assert total_pct == 100

