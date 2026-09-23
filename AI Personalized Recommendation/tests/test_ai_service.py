import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import date
from models import db, User, Income, Expense, ExpenseCategory, AIRecommendation, ChatMessage
from services.ai_service import generate_financial_audit, generate_ai_budget_recommendations, chat_with_advisor


def test_ai_audit_generation(app):
    with app.app_context():
        user = User.query.filter_by(email="tester@finance.ai").first()
        today = date.today()

        # Add income and expense
        db.session.add(Income(user_id=user.id, source="Salary", amount=4500.0, date=today))
        rent_cat = ExpenseCategory.query.filter_by(name="Housing & Rent").first()
        db.session.add(Expense(user_id=user.id, category_id=rent_cat.id, amount=1200.0, date=today, description="Rent"))
        db.session.commit()

        audit = generate_financial_audit(user.id, today.year, today.month)
        assert audit is not None
        assert "score" in audit
        assert 0 <= audit["score"] <= 100
        assert "summary" in audit
        assert "detailed_markdown" in audit

        # Verify persisted in database
        saved_rec = AIRecommendation.query.filter_by(user_id=user.id).first()
        assert saved_rec is not None
        assert saved_rec.report_type == "health_audit"

def test_ai_budget_recommendations(app):
    with app.app_context():
        user = User.query.filter_by(email="tester@finance.ai").first()
        suggestions = generate_ai_budget_recommendations(user.id, total_income=5000.0)
        
        assert len(suggestions) > 0
        total_suggested = sum(s["suggested_amount"] for s in suggestions)
        # Total suggestions should be roughly aligned with total income
        assert total_suggested > 0
        # Needs categories should be present
        cat_names = [s["category_name"] for s in suggestions]
        assert "Housing & Rent" in cat_names
        assert "Groceries" in cat_names

def test_chat_with_advisor_conversation(app):
    with app.app_context():
        user = User.query.filter_by(email="tester@finance.ai").first()
        
        reply = chat_with_advisor(user.id, "How can I start an emergency fund?")
        assert reply is not None
        assert len(reply) > 20

        # Verify chat history record exists
        user_msg = ChatMessage.query.filter_by(user_id=user.id, role="user").first()
        assistant_msg = ChatMessage.query.filter_by(user_id=user.id, role="assistant").first()
        assert user_msg is not None
        assert assistant_msg is not None
        assert "emergency" in user_msg.message.lower()

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__]))

