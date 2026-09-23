from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, SavingsGoal
from services.finance_service import get_emergency_fund_status

savings_bp = Blueprint("savings", __name__)

@savings_bp.route("/savings", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        target_amount_str = request.form.get("target_amount", "0")
        current_amount_str = request.form.get("current_amount", "0")
        category = request.form.get("category", "Emergency")
        target_date_str = request.form.get("target_date")

        try:
            target_amount = float(target_amount_str)
            current_amount = float(current_amount_str or 0)
            if target_amount <= 0:
                raise ValueError("Target amount must be greater than zero.")
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date() if target_date_str else None
        except ValueError as e:
            flash(f"Invalid input: {e}", "danger")
            return redirect(url_for("savings.index"))

        goal = SavingsGoal(
            user_id=current_user.id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date,
            category=category,
            status="Completed" if current_amount >= target_amount else "In Progress"
        )
        db.session.add(goal)
        db.session.commit()
        flash(f"Savings goal '{name}' created!", "success")
        return redirect(url_for("savings.index"))

    goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.created_at.desc()).all()
    total_target = sum(g.target_amount for g in goals)
    total_saved = sum(g.current_amount for g in goals)
    overall_progress = round((total_saved / total_target * 100), 1) if total_target > 0 else 0.0

    emergency_status = get_emergency_fund_status(current_user.id)

    return render_template(
        "savings/index.html",
        goals=goals,
        total_target=total_target,
        total_saved=total_saved,
        overall_progress=min(overall_progress, 100.0),
        emergency=emergency_status
    )

@savings_bp.route("/savings/<int:goal_id>/deposit", methods=["POST"])
@login_required
def deposit(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    amount_str = request.form.get("amount", "0")

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
    except ValueError:
        flash("Please enter a valid deposit amount.", "danger")
        return redirect(url_for("savings.index"))

    goal.current_amount += amount
    if goal.current_amount >= goal.target_amount:
        goal.status = "Completed"
    db.session.commit()

    flash(f"Deposited {current_user.currency}{amount:,.2f} to '{goal.name}'! (Now {current_user.currency}{goal.current_amount:,.2f})", "success")
    return redirect(url_for("savings.index"))

@savings_bp.route("/savings/<int:goal_id>/delete", methods=["POST"])
@login_required
def delete_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash(f"Savings goal '{goal.name}' removed.", "info")
    return redirect(url_for("savings.index"))
