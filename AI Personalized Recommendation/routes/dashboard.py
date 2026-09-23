from datetime import date
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import Income, Expense, AIRecommendation
from services.finance_service import (
    get_monthly_summary,
    get_category_spending,
    get_budget_performance,
    get_50_30_20_breakdown,
    get_emergency_fund_status,
    get_financial_health_score,
    get_monthly_trends
)

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    summary = get_monthly_summary(current_user.id, year, month)
    category_spending = get_category_spending(current_user.id, year, month)
    budget_perf = get_budget_performance(current_user.id, year, month)
    split_50_30_20 = get_50_30_20_breakdown(current_user.id, year, month)
    emergency = get_emergency_fund_status(current_user.id)
    health = get_financial_health_score(current_user.id, year, month)

    # Recent transactions (combine latest 5 incomes and latest 5 expenses)
    recent_incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc(), Income.id.desc()).limit(5).all()
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc(), Expense.id.desc()).limit(8).all()

    # Latest AI Recommendation
    latest_rec = AIRecommendation.query.filter_by(user_id=current_user.id).order_by(AIRecommendation.created_at.desc()).first()

    return render_template(
        "dashboard/index.html",
        year=year,
        month=month,
        summary=summary,
        category_spending=category_spending,
        budget_perf=budget_perf,
        split_50_30_20=split_50_30_20,
        emergency=emergency,
        health=health,
        recent_expenses=recent_expenses,
        recent_incomes=recent_incomes,
        latest_rec=latest_rec
    )

@dashboard_bp.route("/api/dashboard/charts")
@login_required
def charts_data():
    """Returns JSON payload for Chart.js interactive charts."""
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    # 1. Category Expense Doughnut
    category_data = get_category_spending(current_user.id, year, month)
    expense_labels = [c["category_name"] for c in category_data if c["spent"] > 0]
    expense_values = [c["spent"] for c in category_data if c["spent"] > 0]
    expense_colors = [c["color"] for c in category_data if c["spent"] > 0]

    # 2. 6-Month Income vs Expense Trend
    trends = get_monthly_trends(current_user.id, num_months=6)
    trend_labels = [t["month_label"] for t in trends]
    trend_incomes = [t["income"] for t in trends]
    trend_expenses = [t["expenses"] for t in trends]
    trend_savings = [t["net"] for t in trends]

    # 3. 50/30/20 Breakdown
    split = get_50_30_20_breakdown(current_user.id, year, month)

    return jsonify({
        "category_chart": {
            "labels": expense_labels,
            "data": expense_values,
            "colors": expense_colors
        },
        "trend_chart": {
            "labels": trend_labels,
            "incomes": trend_incomes,
            "expenses": trend_expenses,
            "savings": trend_savings
        },
        "split_50_30_20": split
    })
