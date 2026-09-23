import os
import sys
from datetime import date, timedelta
from app import create_app
from models import db, User, ExpenseCategory, Income, Expense, Budget, SavingsGoal, AIRecommendation, ChatMessage
from services.finance_service import seed_default_categories
from services.ai_service import generate_financial_audit

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def seed_database():
    app = create_app()
    with app.app_context():
        print("[*] Seeding database...")
        db.create_all()
        seed_default_categories()

        # Check if demo user already exists
        demo_user = User.query.filter_by(email="demo@finance.ai").first()
        if not demo_user:
            demo_user = User(
                username="Alex Morgan",
                email="demo@finance.ai",
                currency="$",
                monthly_savings_target=800.0,
                emergency_fund_target_months=6,
                risk_tolerance="Moderate",
                preferred_ai_provider="gemini"
            )
            demo_user.set_password("password123")
            db.session.add(demo_user)
            db.session.commit()
            print("[+] Demo user created: demo@finance.ai (password: password123)")
        else:
            print("[i] Demo user already exists.")

        user_id = demo_user.id
        today = date.today()

        # Check if expenses already exist for this user
        if Expense.query.filter_by(user_id=user_id).count() == 0:
            print("📦 Populating 3 months of realistic financial transactions...")
            
            # Helper to map category name to id
            cat_map = {c.name: c.id for c in ExpenseCategory.query.all()}

            # 3 months: current, previous 1, previous 2
            months_back = [0, 1, 2]
            for mb in months_back:
                # Target month/year calculation
                y = today.year
                m = today.month - mb
                while m <= 0:
                    m += 12
                    y -= 1

                # Incomes
                d1 = date(y, m, 1)
                d15 = date(y, m, 15)
                
                db.session.add(Income(
                    user_id=user_id,
                    source="TechCorp Salary",
                    amount=3800.0,
                    date=d1,
                    is_recurring=True,
                    frequency="Monthly",
                    notes="Primary engineering paycheck"
                ))
                db.session.add(Income(
                    user_id=user_id,
                    source="UI Consulting & Freelance",
                    amount=750.0,
                    date=d15,
                    is_recurring=False,
                    frequency="One-Time",
                    notes="Frontend client project bonus"
                ))

                # Expenses for this month
                monthly_expenses_data = [
                    ("Housing & Rent", 1450.0, date(y, m, 2), "Monthly Apartment Rent", "Bank Transfer"),
                    ("Utilities & Bills", 140.0, date(y, m, 5), "High-speed Fiber Internet & Electric", "Card"),
                    ("Groceries", 210.0, date(y, m, 6), "Organic Market & Whole Foods", "Card"),
                    ("Transportation", 85.0, date(y, m, 8), "Metro Rail Monthly Transit Pass", "Card"),
                    ("Dining & Takeout", 65.0, date(y, m, 10), "Artisan Sushi Dinner", "Card"),
                    ("Entertainment & Leisure", 35.0, date(y, m, 12), "Netflix & Spotify Subscriptions", "Card"),
                    ("Groceries", 185.0, date(y, m, 16), "Trader Joe's Bi-weekly Restock", "Card"),
                    ("Dining & Takeout", 90.0, date(y, m, 18), "Weekend Brunch with Friends", "Card"),
                    ("Shopping & Lifestyle", 120.0, date(y, m, 20), "Running Shoes & Activewear", "Card"),
                    ("Healthcare & Medical", 50.0, date(y, m, 22), "Prescriptions & Dental Copay", "Card"),
                    ("Dining & Takeout", 45.0, date(y, m, 24), "Artisan Coffee & Lunch", "Card"),
                    ("Groceries", 160.0, date(y, m, 27), "Farmers Market Groceries", "Card"),
                ]

                # If current month, only add up to today's day
                for cat_name, amt, exp_date, desc, method in monthly_expenses_data:
                    if mb == 0 and exp_date > today:
                        # assign a date prior to today
                        exp_date = today - timedelta(days=(exp_date.day % max(today.day, 1)))
                    
                    cat_id = cat_map.get(cat_name)
                    if cat_id:
                        db.session.add(Expense(
                            user_id=user_id,
                            category_id=cat_id,
                            amount=amt,
                            date=exp_date,
                            description=desc,
                            payment_method=method,
                            is_recurring=(cat_name in ["Housing & Rent", "Utilities & Bills"])
                        ))

                # Budgets for this month
                budget_allocations = {
                    "Housing & Rent": 1500.0,
                    "Groceries": 600.0,
                    "Utilities & Bills": 200.0,
                    "Transportation": 150.0,
                    "Dining & Takeout": 250.0,
                    "Entertainment & Leisure": 120.0,
                    "Shopping & Lifestyle": 200.0,
                    "Healthcare & Medical": 100.0,
                    "Investments & Debt": 500.0
                }

                for cat_name, alloc in budget_allocations.items():
                    cat_id = cat_map.get(cat_name)
                    if cat_id:
                        b = Budget(
                            user_id=user_id,
                            category_id=cat_id,
                            month=m,
                            year=y,
                            allocated_amount=alloc,
                            notes="Monthly target allocation"
                        )
                        db.session.add(b)

            db.session.commit()
            print("[+] 3 Months of Transactions & Budgets populated.")

        # Savings Goals
        if SavingsGoal.query.filter_by(user_id=user_id).count() == 0:
            db.session.add(SavingsGoal(
                user_id=user_id,
                name="Emergency Safety Reserve",
                target_amount=12000.0,
                current_amount=7800.0,
                category="Emergency",
                target_date=today + timedelta(days=180),
                status="In Progress"
            ))
            db.session.add(SavingsGoal(
                user_id=user_id,
                name="Japan Summer Trip",
                target_amount=3500.0,
                current_amount=2100.0,
                category="Travel",
                target_date=today + timedelta(days=120),
                status="In Progress"
            ))
            db.session.add(SavingsGoal(
                user_id=user_id,
                name="Next-Gen Workstation",
                target_amount=2400.0,
                current_amount=2400.0,
                category="Purchase",
                target_date=today - timedelta(days=10),
                status="Completed"
            ))
            db.session.commit()
            print("[+] Savings goals seeded.")

        # Seed initial AI Audit
        if AIRecommendation.query.filter_by(user_id=user_id).count() == 0:
            print("[*] Generating initial AI financial health audit...")
            try:
                generate_financial_audit(user_id, today.year, today.month)
                print("[+] Initial AI audit generated.")
            except Exception as e:
                print(f"[!] Audit generation notice: {e}")

        # Seed Chat Message starter
        if ChatMessage.query.filter_by(user_id=user_id).count() == 0:
            db.session.add(ChatMessage(
                user_id=user_id,
                role="assistant",
                message="Hello Alex! I am your AI Finance Advisor. I have reviewed your current cash flow and savings targets. How can I help you optimize your finances today?"
            ))
            db.session.commit()
            print("[+] Welcome chat seeded.")

        print("\n[+] Seeding completed successfully!")
        print("[>] You can log in with: demo@finance.ai | password: password123\n")

if __name__ == "__main__":
    seed_database()
