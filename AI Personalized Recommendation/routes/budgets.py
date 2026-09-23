from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Budget, ExpenseCategory
from services.finance_service import (
    get_user_categories,
    get_category_spending,
    get_budget_performance,
    get_monthly_summary
)
from services.ai_service import generate_ai_budget_recommendations

budgets_bp = Blueprint("budgets", __name__)

@budgets_bp.route("/budgets", methods=["GET", "POST"])
@login_required
def index():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    categories = get_user_categories(current_user.id)

    if request.method == "POST":
        category_id = request.form.get("category_id", type=int)
        allocated_amount_str = request.form.get("allocated_amount", "0")
        notes = request.form.get("notes", "").strip()

        try:
            allocated_amount = float(allocated_amount_str)
            if allocated_amount < 0:
                raise ValueError("Allocated amount cannot be negative.")
        except ValueError:
            flash("Please provide a valid non-negative budget amount.", "danger")
            return redirect(url_for("budgets.index", year=selected_year, month=selected_month))

        category = db.session.get(ExpenseCategory, category_id)
        if not category:
            flash("Invalid category selected.", "danger")
            return redirect(url_for("budgets.index", year=selected_year, month=selected_month))

        # Check if budget entry already exists for user/category/month/year
        budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category_id,
            month=selected_month,
            year=selected_year
        ).first()

        if budget:
            budget.allocated_amount = allocated_amount
            budget.notes = notes
            flash(f"Updated budget for '{category.name}' to {current_user.currency}{allocated_amount:,.2f}.", "success")
        else:
            budget = Budget(
                user_id=current_user.id,
                category_id=category_id,
                month=selected_month,
                year=selected_year,
                allocated_amount=allocated_amount,
                notes=notes
            )
            db.session.add(budget)
            flash(f"Set budget for '{category.name}' to {current_user.currency}{allocated_amount:,.2f}.", "success")

        db.session.commit()
        return redirect(url_for("budgets.index", year=selected_year, month=selected_month))

    category_spending = get_category_spending(current_user.id, selected_year, selected_month)
    budget_perf = get_budget_performance(current_user.id, selected_year, selected_month)
    summary = get_monthly_summary(current_user.id, selected_year, selected_month)

    # Get AI recommendations preview for modal
    ai_suggestions = generate_ai_budget_recommendations(current_user.id, summary["total_income"])

    return render_template(
        "budgets/index.html",
        categories=categories,
        category_spending=category_spending,
        budget_perf=budget_perf,
        summary=summary,
        ai_suggestions=ai_suggestions,
        selected_year=selected_year,
        selected_month=selected_month
    )

@budgets_bp.route("/budgets/ai-apply", methods=["POST"])
@login_required
def ai_apply():
    """Apply AI generated budget plan to the selected month."""
    today = date.today()
    selected_year = request.form.get("year", today.year, type=int)
    selected_month = request.form.get("month", today.month, type=int)

    summary = get_monthly_summary(current_user.id, selected_year, selected_month)
    income = summary["total_income"]
    suggestions = generate_ai_budget_recommendations(current_user.id, income)

    for item in suggestions:
        cat_id = item["category_id"]
        suggested_amt = item["suggested_amount"]

        budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=cat_id,
            month=selected_month,
            year=selected_year
        ).first()

        if budget:
            budget.allocated_amount = suggested_amt
            budget.notes = "AI 50/30/20 Recommended"
        else:
            budget = Budget(
                user_id=current_user.id,
                category_id=cat_id,
                month=selected_month,
                year=selected_year,
                allocated_amount=suggested_amt,
                notes="AI 50/30/20 Recommended"
            )
            db.session.add(budget)

    db.session.commit()
    flash("AI 50/30/20 Budget Plan successfully applied across all categories!", "success")
    return redirect(url_for("budgets.index", year=selected_year, month=selected_month))

@budgets_bp.route("/budgets/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    y, m = budget.year, budget.month
    db.session.delete(budget)
    db.session.commit()
    flash("Budget allocation removed.", "info")
    return redirect(url_for("budgets.index", year=y, month=m))
