import pytest
from app import app
from database.db import get_db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_login_page_renders(client):
    """Verify that the login page renders successfully."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in to your Spendly account" in response.data

def test_successful_login_redirects_to_profile(client):
    """Verify that logging in with correct credentials redirects to profile screen and sets session."""
    # Use seeded user credentials from database/db.py seed_db()
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Checks that it redirects to profile page
    assert b"Category Breakdown" in response.data or b"Total Spent" in response.data
    # Checks flash message
    assert b"Logged in successfully!" in response.data
    
    # Check that session is populated
    with client.session_transaction() as session:
        assert session.get("user_id") is not None
        assert session.get("user_name") == "Demo User"

def test_failed_login_shows_error(client):
    """Verify that logging in with wrong credentials displays an error and doesn't redirect."""
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "wrongpassword"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    
    # Check that session is not populated
    with client.session_transaction() as session:
        assert session.get("user_id") is None

def test_logout_clears_session(client):
    """Verify that logging out clears the session and redirects to home."""
    # Login first
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    with client.session_transaction() as session:
        assert session.get("user_id") is not None
        
    # Logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out." in response.data
    
    # Check that session is cleared
    with client.session_transaction() as session:
        assert session.get("user_id") is None


def test_profile_unauthenticated_redirects(client):
    """Verify that visiting /profile without being logged in redirects to /login."""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated_success(client):
    """Verify that visiting /profile while logged in returns HTTP 200 and renders the sections."""
    # Log in first
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    response = client.get("/profile")
    assert response.status_code == 200
    
    # Check user card content
    assert b"Demo User" in response.data
    assert b"demo@spendly.com" in response.data
    assert b"DU" in response.data  # Initials
    
    # Check summary stats
    assert b"Total Spent" in response.data
    assert b"346.24" in response.data
    assert "₹".encode("utf-8") in response.data
    assert b"8" in response.data  # Transaction count
    assert b"Bills" in response.data  # Top category
    
    # Check transaction history table
    assert b"Groceries" in response.data
    assert b"Notebook" in response.data
    assert b"New shoes" in response.data
    
    # Check transaction list order (newest-first)
    groceries_idx = response.data.index(b"Groceries")
    notebook_idx = response.data.index(b"Notebook")
    shoes_idx = response.data.index(b"New shoes")
    assert groceries_idx < notebook_idx < shoes_idx
    
    # Check category breakdown section contains all 7 categories
    assert b"Category Breakdown" in response.data
    assert b"Food" in response.data
    assert b"Health" in response.data
    assert b"Shopping" in response.data
    assert b"Bills" in response.data
    assert b"Transport" in response.data
    assert b"Entertainment" in response.data
    assert b"Other" in response.data
    
    # Check navbar displays logged-in state
    assert b"Hello, Demo User" in response.data
    assert b"Logout" in response.data


def test_custom_user_profile_email(client):
    """Verify that a custom registered user's email is correctly displayed on the profile page."""
    # Register a new user
    client.post("/register", data={
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    })
    
    # Log in with the custom user
    client.post("/login", data={
        "email": "john.doe@example.com",
        "password": "securepassword123"
    })
    
    # Get profile page
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"John Doe" in response.data
    assert b"john.doe@example.com" in response.data
    assert b"JD" in response.data  # Dynamically calculated initials


def test_logged_in_user_redirected_from_login_and_register(client):
    """Verify that a logged-in user is redirected to the profile page when visiting /login or /register."""
    # Log in first
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })

    # Try to access /login
    response = client.get("/login")
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    # Try to access /register
    response = client.get("/register")
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


def test_new_user_profile_no_expenses(client):
    """Verify that a newly registered user with no expenses can view /profile showing zero stats and empty breakdown."""
    # Register new user
    client.post("/register", data={
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    })
    
    # Log in
    client.post("/login", data={
        "email": "jane.doe@example.com",
        "password": "securepassword123"
    })
    
    # Get profile
    response = client.get("/profile")
    assert response.status_code == 200
    
    # Verify name and email
    assert b"Jane Doe" in response.data
    assert b"jane.doe@example.com" in response.data
    
    # Verify zero stats
    assert "₹0.00".encode("utf-8") in response.data
    assert b"0" in response.data
    
    # Verify empty category breakdown
    assert b"category-row" not in response.data
    assert b"progress-bar-element" not in response.data




