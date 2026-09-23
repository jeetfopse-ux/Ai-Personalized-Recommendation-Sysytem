from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from services.finance_service import seed_default_categories

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        currency = request.form.get("currency", "$")

        if not username or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "warning")
            return render_template("auth/register.html")

        # Create user
        user = User(
            username=username,
            email=email,
            currency=currency,
            monthly_savings_target=500.0,
            emergency_fund_target_months=6
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Ensure system categories are ready
        seed_default_categories()

        login_user(user)
        flash(f"Welcome to FinanceBot, {user.username}! Your account is ready.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/demo-login")
def demo_login():
    """Quick demo login helper for evaluation and testing."""
    demo_user = User.query.filter_by(email="demo@finance.ai").first()
    if demo_user:
        login_user(demo_user)
        flash("Logged in as Demo User with full sample financial data!", "info")
        return redirect(url_for("dashboard.index"))
    
    flash("Demo account not seeded yet. Please register an account or run seed.py.", "warning")
    return redirect(url_for("auth.login"))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("auth.login"))
