import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app import create_app

from models import db, User, ExpenseCategory, Income, Expense, Budget, SavingsGoal
from services.finance_service import seed_default_categories

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_default_categories()
        
        # Create test user
        user = User(
            username="Test User",
            email="tester@finance.ai",
            currency="$",
            monthly_savings_target=500.0,
            emergency_fund_target_months=6
        )
        user.set_password("securepassword")
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User.query.filter_by(email="tester@finance.ai").first()
    client.post("/login", data={
        "email": "tester@finance.ai",
        "password": "securepassword"
    }, follow_redirects=True)
    return client
