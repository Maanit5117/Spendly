# Database Setup Implementation Plan

This plan describes the implementation details for setting up the SQLite database and integrating it with the Spendly application.

## Proposed Changes

We will implement the SQLite database connection, schema creation, and seeding logic, and then integrate it into Flask's application context on startup.

### Database Component

#### [MODIFY] [db.py](file:///Users/maanitmittra/Desktop/expense-tracker/database/db.py)
We will implement the following functions in `database/db.py`:
- `get_db()`: Open a connection to `spendly.db` in the project root, set `row_factory = sqlite3.Row`, enable foreign keys using `PRAGMA foreign_keys = ON`, and return the connection.
- `init_db()`: Create the `users` and `expenses` tables using `CREATE TABLE IF NOT EXISTS` commands.
- `seed_db()`: Insert a demo user with a password hashed using `werkzeug.security` and 8 sample expenses covering all categories, ensuring no duplicates are created if run multiple times.

#### [MODIFY] [app.py](file:///Users/maanitmittra/Desktop/expense-tracker/app.py)
We will:
- Import `get_db`, `init_db`, and `seed_db` from `database.db`.
- Run `init_db()` and `seed_db()` within the Flask `app.app_context()` during startup to ensure the database schema and sample data exist.

---

## Verification Plan

### Automated Tests
We can run `pytest` to see if there are any existing unit tests. If there are none, we will write a temporary script to test the functions.
- Run `pytest`

### Manual Verification
1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Verify that the file `spendly.db` is created in the project root.
3. Query the database using the SQLite CLI or a simple script to verify:
   - The `users` table has the demo user.
   - The `expenses` table has 8 expenses.
   - Run startup again and verify no duplicate records are added.
