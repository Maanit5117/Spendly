import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

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
    if not session.get("user_id"):
        return redirect(url_for("login"))

    name = session.get("user_name", "Demo User")
    parts = name.split()
    initials = "".join([p[0] for p in parts if p]).upper()[:2] if parts else "U"

    user_data = {
        "name": name,
        "email": session.get("user_email", "demo@spendly.com"),
        "initials": initials,
        "joined_date": "March 2026"
    }

    stats = {
        "total_spent": "₹12,450.00",
        "transaction_count": 8,
        "top_category": "Bills"
    }

    recent_expenses = [
        {"date": "2026-06-13", "description": "Groceries", "category": "Food", "amount": "₹32.40"},
        {"date": "2026-06-12", "description": "Notebook", "category": "Other", "amount": "₹10.00"},
        {"date": "2026-06-10", "description": "New shoes", "category": "Shopping", "amount": "₹65.50"},
        {"date": "2026-06-09", "description": "Movie ticket", "category": "Entertainment", "amount": "₹22.00"},
        {"date": "2026-06-07", "description": "Pharmacy", "category": "Health", "amount": "₹45.00"}
    ]

    categories = [
        {"name": "Bills", "amount": "₹4,500.00", "percentage": 36},
        {"name": "Food", "amount": "₹3,232.40", "percentage": 26},
        {"name": "Health", "amount": "₹2,050.00", "percentage": 16},
        {"name": "Shopping", "amount": "₹1,800.00", "percentage": 14},
        {"name": "Other", "amount": "₹867.60", "percentage": 8}
    ]

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats,
        recent_expenses=recent_expenses,
        categories=categories
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
