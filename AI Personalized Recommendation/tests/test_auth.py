import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import User


def test_register_success(client, app):
    res = client.post("/register", data={
        "username": "New User",
        "email": "newuser@finance.ai",
        "password": "password123",
        "confirm_password": "password123",
        "currency": "$"
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="newuser@finance.ai").first()
        assert user is not None
        assert user.username == "New User"
        assert user.check_password("password123") is True
        assert user.check_password("wrongpass") is False

def test_register_duplicate_email(client):
    res = client.post("/register", data={
        "username": "Duplicate User",
        "email": "tester@finance.ai",
        "password": "password123",
        "confirm_password": "password123",
        "currency": "$"
    }, follow_redirects=True)
    assert b"already exists" in res.data

def test_login_success_and_logout(client):
    res = client.post("/login", data={
        "email": "tester@finance.ai",
        "password": "securepassword"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome back" in res.data or b"Dashboard" in res.data

    # Logout
    logout_res = client.get("/logout", follow_redirects=True)
    assert b"logged out" in logout_res.data

def test_login_invalid_credentials(client):
    res = client.post("/login", data={
        "email": "tester@finance.ai",
        "password": "incorrectpassword"
    }, follow_redirects=True)
    assert b"Invalid email or password" in res.data

if __name__ == "__main__":
    import os, sys, pytest
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    sys.exit(pytest.main([__file__]))

