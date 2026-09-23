from datetime import date
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from services.finance_service import (
    get_monthly_summary,
    get_category_spending,
    get_budget_performance,
    get_50_30_20_breakdown,
    get_emergency_fund_status,
    get_financial_health_score
)
from models import AIRecommendation

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports/monthly")
@login_required
def monthly():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    summary = get_monthly_summary(current_user.id, selected_year, selected_month)
    category_spending = get_category_spending(current_user.id, selected_year, selected_month)
    budget_perf = get_budget_performance(current_user.id, selected_year, selected_month)
    split_50_30_20 = get_50_30_20_breakdown(current_user.id, selected_year, selected_month)
    emergency = get_emergency_fund_status(current_user.id)
    health = get_financial_health_score(current_user.id, selected_year, selected_month)

    # Latest AI Recommendation
    latest_rec = AIRecommendation.query.filter_by(user_id=current_user.id).order_by(AIRecommendation.created_at.desc()).first()

    return render_template(
        "reports/monthly.html",
        selected_year=selected_year,
        selected_month=selected_month,
        summary=summary,
        category_spending=category_spending,
        budget_perf=budget_perf,
        split_50_30_20=split_50_30_20,
        emergency=emergency,
        health=health,
        latest_rec=latest_rec
    )
