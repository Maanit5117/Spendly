import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method not in ["GET", "POST"]:
        abort(405)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Server-side validation:
        # 1. All fields are non-empty
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.")
            return render_template("register.html")

        # 2. password == confirm_password
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        # 3. Email is not already registered
        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            flash("Email already registered.")
            return render_template("register.html")

        # On success, flash a success message and redirect to url_for('login')
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Server-side validation:
        if not email or not password:
            flash("All fields are required.", "error")
            return render_template("login.html")

        # Fetch user
        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash("Logged in successfully!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Invalid email or password.", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    import datetime
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user_db = get_user_by_id(user_id)
    if not user_db:
        session.clear()
        return redirect(url_for("login"))

    name = user_db["name"]
    parts = name.split()
    initials = "".join([p[0] for p in parts if p]).upper()[:2] if parts else "U"

    user_data = {
        "name": name,
        "email": user_db["email"],
        "initials": initials,
        "joined_date": user_db["member_since"]
    }

    # Date range filtering logic
    active_filter = request.args.get("filter", "all_time")
    start_date = None
    end_date = None
    custom_start = request.args.get("start_date", "").strip()
    custom_end = request.args.get("end_date", "").strip()
    
    today = datetime.date.today()
    if active_filter == "last_month":
        start_date = (today - datetime.timedelta(days=30)).isoformat()
        end_date = today.isoformat()
    elif active_filter == "last_3_months":
        start_date = (today - datetime.timedelta(days=90)).isoformat()
        end_date = today.isoformat()
    elif active_filter == "last_6_months":
        start_date = (today - datetime.timedelta(days=180)).isoformat()
        end_date = today.isoformat()
    elif active_filter == "custom":
        if custom_start:
            start_date = custom_start
        if custom_end:
            end_date = custom_end

    db_stats = get_summary_stats(user_id, start_date=start_date, end_date=end_date)
    stats = {
        "total_spent": f"₹{db_stats['total_spent']:,.2f}",
        "transaction_count": db_stats["transaction_count"],
        "top_category": db_stats["top_category"]
    }

    db_recent = get_recent_transactions(user_id, limit=10, start_date=start_date, end_date=end_date)
    recent_expenses = [
        {
            "date": r["date"],
            "description": r["description"],
            "category": r["category"],
            "amount": f"₹{r['amount']:,.2f}"
        }
        for r in db_recent
    ]

    db_categories = get_category_breakdown(user_id, start_date=start_date, end_date=end_date)
    categories = [
        {
            "name": cat["name"],
            "amount": f"₹{cat['amount']:,.2f}",
            "percentage": cat["pct"]
        }
        for cat in db_categories
    ]

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats,
        recent_expenses=recent_expenses,
        categories=categories,
        active_filter=active_filter,
        start_date=custom_start,
        end_date=custom_end
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
