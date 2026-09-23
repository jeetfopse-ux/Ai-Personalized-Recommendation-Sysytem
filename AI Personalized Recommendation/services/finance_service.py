from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy import func, extract, or_
from models import db, User, ExpenseCategory, Income, Expense, Budget, SavingsGoal

# Default system categories to seed
DEFAULT_CATEGORIES = [
    {"name": "Housing & Rent", "icon": "home", "color": "#6366f1", "category_type": "needs", "is_default": True},
    {"name": "Groceries", "icon": "shopping-cart", "color": "#10b981", "category_type": "needs", "is_default": True},
    {"name": "Utilities & Bills", "icon": "zap", "color": "#f59e0b", "category_type": "needs", "is_default": True},
    {"name": "Transportation", "icon": "car", "color": "#3b82f6", "category_type": "needs", "is_default": True},
    {"name": "Healthcare & Medical", "icon": "heart", "color": "#ec4899", "category_type": "needs", "is_default": True},
    {"name": "Dining & Takeout", "icon": "coffee", "color": "#f97316", "category_type": "wants", "is_default": True},
    {"name": "Entertainment & Leisure", "icon": "film", "color": "#8b5cf6", "category_type": "wants", "is_default": True},
    {"name": "Shopping & Lifestyle", "icon": "shopping-bag", "color": "#06b6d4", "category_type": "wants", "is_default": True},
    {"name": "Investments & Debt", "icon": "trending-up", "color": "#14b8a6", "category_type": "savings", "is_default": True},
    {"name": "Personal & Education", "icon": "book-open", "color": "#84cc16", "category_type": "wants", "is_default": True},
    {"name": "Miscellaneous", "icon": "more-horizontal", "color": "#64748b", "category_type": "wants", "is_default": True},
]

def seed_default_categories():
    """Ensure default categories are seeded into database."""
    for cat_data in DEFAULT_CATEGORIES:
        existing = ExpenseCategory.query.filter_by(name=cat_data["name"], is_default=True).first()
        if not existing:
            cat = ExpenseCategory(**cat_data)
            db.session.add(cat)
    db.session.commit()

def get_user_categories(user_id):
    """Retrieve all available categories (defaults + user custom)."""
    return ExpenseCategory.query.filter(
        or_(ExpenseCategory.is_default == True, ExpenseCategory.user_id == user_id)
    ).order_by(ExpenseCategory.name.asc()).all()

def get_monthly_summary(user_id, year=None, month=None):
    """Calculate summary statistics for a given month."""
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # Total Income
    total_income = db.session.query(func.coalesce(func.sum(Income.amount), 0.0)).filter(
        Income.user_id == user_id,
        extract("year", Income.date) == year,
        extract("month", Income.date) == month
    ).scalar()

    # Total Expenses
    total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
        Expense.user_id == user_id,
        extract("year", Expense.date) == year,
        extract("month", Expense.date) == month
    ).scalar()

    # Counts
    income_count = Income.query.filter(
        Income.user_id == user_id,
        extract("year", Income.date) == year,
        extract("month", Income.date) == month
    ).count()

    expense_count = Expense.query.filter(
        Expense.user_id == user_id,
        extract("year", Expense.date) == year,
        extract("month", Expense.date) == month
    ).count()

    net_savings = round(total_income - total_expenses, 2)
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

    return {
        "year": year,
        "month": month,
        "month_name": date(year, month, 1).strftime("%B %Y"),
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_savings": net_savings,
        "savings_rate": savings_rate,
        "income_count": income_count,
        "expense_count": expense_count
    }

def get_category_spending(user_id, year=None, month=None):
    """Get category-wise spending and budget status for the given month."""
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    categories = get_user_categories(user_id)
    cat_ids = [c.id for c in categories]

    # Query actual spending grouped by category
    spent_query = db.session.query(
        Expense.category_id,
        func.coalesce(func.sum(Expense.amount), 0.0).label("total_spent"),
        func.count(Expense.id).label("tx_count")
    ).filter(
        Expense.user_id == user_id,
        extract("year", Expense.date) == year,
        extract("month", Expense.date) == month
    ).group_by(Expense.category_id).all()

    spent_dict = {item.category_id: (round(item.total_spent, 2), item.tx_count) for item in spent_query}

    # Query budgets for the month
    budgets = Budget.query.filter(
        Budget.user_id == user_id,
        Budget.year == year,
        Budget.month == month
    ).all()
    budget_dict = {b.category_id: round(b.allocated_amount, 2) for b in budgets}

    results = []
    for cat in categories:
        spent, tx_count = spent_dict.get(cat.id, (0.0, 0))
        allocated = budget_dict.get(cat.id, 0.0)

        utilization = round((spent / allocated * 100), 1) if allocated > 0 else 0.0
        remaining = round(allocated - spent, 2) if allocated > 0 else 0.0

        if allocated <= 0:
            status = "unbudgeted" if spent > 0 else "inactive"
        elif spent > allocated:
            status = "overbudget"
        elif utilization >= 85:
            status = "critical"
        elif utilization >= 70:
            status = "warning"
        else:
            status = "safe"

        # Only include if there is activity or budget
        if spent > 0 or allocated > 0:
            results.append({
                "category_id": cat.id,
                "category_name": cat.name,
                "icon": cat.icon,
                "color": cat.color,
                "category_type": cat.category_type,
                "spent": spent,
                "tx_count": tx_count,
                "allocated": allocated,
                "remaining": remaining,
                "utilization": utilization,
                "status": status
            })

    # Sort by spent descending
    results.sort(key=lambda x: x["spent"], reverse=True)
    return results

def get_budget_performance(user_id, year=None, month=None):
    """Aggregate budget vs actual metrics."""
    category_data = get_category_spending(user_id, year, month)
    
    total_allocated = sum(item["allocated"] for item in category_data)
    total_spent_in_budgeted = sum(item["spent"] for item in category_data if item["allocated"] > 0)
    all_spent = sum(item["spent"] for item in category_data)
    
    overbudget_categories = [item for item in category_data if item["status"] == "overbudget"]
    warning_categories = [item for item in category_data if item["status"] in ("warning", "critical")]

    overall_utilization = round((total_spent_in_budgeted / total_allocated * 100), 1) if total_allocated > 0 else 0.0

    return {
        "total_allocated": round(total_allocated, 2),
        "total_spent_in_budgeted": round(total_spent_in_budgeted, 2),
        "all_spent": round(all_spent, 2),
        "remaining_budget": round(total_allocated - total_spent_in_budgeted, 2),
        "overall_utilization": overall_utilization,
        "overbudget_count": len(overbudget_categories),
        "overbudget_items": overbudget_categories,
        "warning_count": len(warning_categories),
        "warning_items": warning_categories,
        "categories": category_data
    }

def get_50_30_20_breakdown(user_id, year=None, month=None):
    """Calculates distribution across Needs (50%), Wants (30%), and Savings (20%)."""
    summary = get_monthly_summary(user_id, year, month)
    category_data = get_category_spending(user_id, year, month)
    income = summary["total_income"]

    needs_spent = sum(item["spent"] for item in category_data if item["category_type"] == "needs")
    wants_spent = sum(item["spent"] for item in category_data if item["category_type"] == "wants")
    savings_spent = sum(item["spent"] for item in category_data if item["category_type"] == "savings")
    actual_saved = max(summary["net_savings"], 0.0) + savings_spent

    if income > 0:
        needs_pct = round((needs_spent / income * 100), 1)
        wants_pct = round((wants_spent / income * 100), 1)
        savings_pct = round((actual_saved / income * 100), 1)
    else:
        needs_pct, wants_pct, savings_pct = 0.0, 0.0, 0.0

    return {
        "income": income,
        "needs": {"amount": round(needs_spent, 2), "pct": needs_pct, "target_pct": 50, "target_amount": round(income * 0.50, 2)},
        "wants": {"amount": round(wants_spent, 2), "pct": wants_pct, "target_pct": 30, "target_amount": round(income * 0.30, 2)},
        "savings": {"amount": round(actual_saved, 2), "pct": savings_pct, "target_pct": 20, "target_amount": round(income * 0.20, 2)},
    }

def get_monthly_trends(user_id, num_months=6):
    """Retrieve historical monthly trends for charts."""
    today = date.today()
    trends = []

    for i in range(num_months - 1, -1, -1):
        # Calculate year and month
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1

        summary = get_monthly_summary(user_id, y, m)
        trends.append({
            "month_label": date(y, m, 1).strftime("%b %Y"),
            "year": y,
            "month": m,
            "income": summary["total_income"],
            "expenses": summary["total_expenses"],
            "net": summary["net_savings"]
        })

    return trends

def get_emergency_fund_status(user_id):
    """Calculate emergency fund runway and health."""
    user = db.session.get(User, user_id)
    target_months = user.emergency_fund_target_months if user and user.emergency_fund_target_months else 6
    
    # Calculate average expenses over the last 3 months
    today = date.today()
    expense_sum = 0.0
    valid_months = 0
    for i in range(3):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        m_summary = get_monthly_summary(user_id, y, m)
        if m_summary["total_expenses"] > 0:
            expense_sum += m_summary["total_expenses"]
            valid_months += 1

    avg_monthly_burn = round(expense_sum / valid_months, 2) if valid_months > 0 else 0.0

    # Total emergency fund currently saved
    emergency_goals = SavingsGoal.query.filter(
        SavingsGoal.user_id == user_id,
        or_(SavingsGoal.category == "Emergency", SavingsGoal.name.ilike("%Emergency%"))
    ).all()
    
    current_saved = sum(g.current_amount for g in emergency_goals)
    target_amount = round(avg_monthly_burn * target_months, 2) if avg_monthly_burn > 0 else round(user.monthly_savings_target * target_months, 2)

    runway_months = round(current_saved / avg_monthly_burn, 1) if avg_monthly_burn > 0 else 0.0
    progress_pct = round((current_saved / target_amount * 100), 1) if target_amount > 0 else 0.0

    return {
        "avg_monthly_burn": avg_monthly_burn,
        "target_months": target_months,
        "target_amount": target_amount,
        "current_saved": round(current_saved, 2),
        "runway_months": runway_months,
        "progress_pct": min(progress_pct, 100.0)
    }

def get_financial_health_score(user_id, year=None, month=None):
    """Compute an algorithmic financial health score (0-100)."""
    summary = get_monthly_summary(user_id, year, month)
    budget = get_budget_performance(user_id, year, month)
    emergency = get_emergency_fund_status(user_id)
    split = get_50_30_20_breakdown(user_id, year, month)

    score = 50  # Baseline

    # 1. Savings rate component (+/- 25 pts)
    savings_rate = summary["savings_rate"]
    if savings_rate >= 20:
        score += 25
    elif savings_rate >= 10:
        score += 15
    elif savings_rate > 0:
        score += 5
    else:
        score -= 20  # Burning more than earning

    # 2. Budget adherence component (+/- 15 pts)
    if budget["total_allocated"] > 0:
        if budget["overbudget_count"] == 0 and budget["overall_utilization"] <= 95:
            score += 15
        elif budget["overbudget_count"] <= 1 and budget["overall_utilization"] <= 100:
            score += 5
        else:
            score -= 15

    # 3. Emergency fund runway component (+/- 10 pts)
    if emergency["runway_months"] >= emergency["target_months"]:
        score += 10
    elif emergency["runway_months"] >= 3:
        score += 5
    elif emergency["runway_months"] < 1:
        score -= 10

    score = max(0, min(100, score))
    
    if score >= 80:
        rating = "Excellent"
        color = "#10b981"
    elif score >= 65:
        rating = "Good"
        color = "#3b82f6"
    elif score >= 50:
        rating = "Fair"
        color = "#f59e0b"
    else:
        rating = "Needs Attention"
        color = "#ef4444"

    return {
        "score": score,
        "rating": rating,
        "color": color,
        "savings_rate": savings_rate,
        "utilization": budget["overall_utilization"],
        "runway_months": emergency["runway_months"]
    }
