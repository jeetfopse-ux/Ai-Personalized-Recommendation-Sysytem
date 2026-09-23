import csv
import io
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from sqlalchemy import extract
from models import db, Income, Expense, ExpenseCategory
from services.finance_service import get_user_categories

transactions_bp = Blueprint("transactions", __name__)

# --- INCOME ROUTES ---

@transactions_bp.route("/income", methods=["GET", "POST"])
@login_required
def income_list():
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        amount_str = request.form.get("amount", "0")
        date_str = request.form.get("date", str(date.today()))
        frequency = request.form.get("frequency", "One-Time")
        is_recurring = bool(request.form.get("is_recurring"))
        notes = request.form.get("notes", "").strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            inc_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            flash(f"Invalid input: {e}", "danger")
            return redirect(url_for("transactions.income_list"))

        income = Income(
            user_id=current_user.id,
            source=source,
            amount=amount,
            date=inc_date,
            frequency=frequency,
            is_recurring=is_recurring,
            notes=notes
        )
        db.session.add(income)
        db.session.commit()
        flash(f"Income of {current_user.currency}{amount:,.2f} from '{source}' added successfully!", "success")
        return redirect(url_for("transactions.income_list"))

    # Filtering
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    query = Income.query.filter_by(user_id=current_user.id)
    if selected_year:
        query = query.filter(extract("year", Income.date) == selected_year)
    if selected_month:
        query = query.filter(extract("month", Income.date) == selected_month)

    incomes = query.order_by(Income.date.desc(), Income.id.desc()).all()
    total_income = sum(i.amount for i in incomes)

    return render_template(
        "transactions/income.html",
        incomes=incomes,
        total_income=total_income,
        selected_year=selected_year,
        selected_month=selected_month,
        today_str=str(today)
    )

@transactions_bp.route("/income/delete/<int:income_id>", methods=["POST"])
@login_required
def delete_income(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    flash("Income record deleted.", "info")
    return redirect(url_for("transactions.income_list"))


# --- EXPENSE ROUTES ---

@transactions_bp.route("/expenses", methods=["GET", "POST"])
@login_required
def expense_list():
    categories = get_user_categories(current_user.id)

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        amount_str = request.form.get("amount", "0")
        category_id = request.form.get("category_id", type=int)
        date_str = request.form.get("date", str(date.today()))
        payment_method = request.form.get("payment_method", "Card")
        is_recurring = bool(request.form.get("is_recurring"))
        tags = request.form.get("tags", "").strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            exp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            flash(f"Invalid input: {e}", "danger")
            return redirect(url_for("transactions.expense_list"))

        category = db.session.get(ExpenseCategory, category_id)
        if not category:
            flash("Please select a valid expense category.", "danger")
            return redirect(url_for("transactions.expense_list"))

        expense = Expense(
            user_id=current_user.id,
            category_id=category_id,
            description=description,
            amount=amount,
            date=exp_date,
            payment_method=payment_method,
            is_recurring=is_recurring,
            tags=tags
        )
        db.session.add(expense)
        db.session.commit()
        flash(f"Expense '{description}' of {current_user.currency}{amount:,.2f} recorded!", "success")
        return redirect(url_for("transactions.expense_list"))

    # Filtering
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)
    selected_category = request.args.get("category_id", type=int)

    query = Expense.query.filter_by(user_id=current_user.id)
    if selected_year:
        query = query.filter(extract("year", Expense.date) == selected_year)
    if selected_month:
        query = query.filter(extract("month", Expense.date) == selected_month)
    if selected_category:
        query = query.filter(Expense.category_id == selected_category)

    expenses = query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    total_expenses = sum(e.amount for e in expenses)

    return render_template(
        "transactions/expenses.html",
        expenses=expenses,
        categories=categories,
        total_expenses=total_expenses,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_category=selected_category,
        today_str=str(today)
    )

@transactions_bp.route("/expenses/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Expense record deleted.", "info")
    return redirect(url_for("transactions.expense_list"))


# --- CUSTOM CATEGORIES ---

@transactions_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_type = request.form.get("category_type", "wants")
        color = request.form.get("color", "#6366f1")
        icon = request.form.get("icon", "tag")

        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for("transactions.categories"))

        custom_cat = ExpenseCategory(
            user_id=current_user.id,
            name=name,
            category_type=category_type,
            color=color,
            icon=icon,
            is_default=False
        )
        db.session.add(custom_cat)
        db.session.commit()
        flash(f"Custom category '{name}' created!", "success")
        return redirect(url_for("transactions.categories"))

    all_categories = get_user_categories(current_user.id)
    return render_template("transactions/categories.html", categories=all_categories)

@transactions_bp.route("/categories/delete/<int:cat_id>", methods=["POST"])
@login_required
def delete_category(cat_id):
    cat = ExpenseCategory.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    # Ensure it's not a default category
    if cat.is_default:
        flash("Default categories cannot be deleted.", "warning")
        return redirect(url_for("transactions.categories"))
    
    db.session.delete(cat)
    db.session.commit()
    flash(f"Category '{cat.name}' removed.", "info")
    return redirect(url_for("transactions.categories"))


# --- CSV EXPORT ---

@transactions_bp.route("/transactions/export/csv")
@login_required
def export_csv():
    export_type = request.args.get("type", "expenses")
    si = io.StringIO()
    writer = csv.writer(si)

    if export_type == "income":
        writer.writerow(["ID", "Source", "Amount", "Currency", "Date", "Frequency", "Recurring", "Notes"])
        incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
        for i in incomes:
            writer.writerow([i.id, i.source, i.amount, current_user.currency, i.date, i.frequency, i.is_recurring, i.notes or ""])
        filename = f"income_export_{date.today()}.csv"
    else:
        writer.writerow(["ID", "Category", "Description", "Amount", "Currency", "Date", "Payment Method", "Recurring", "Tags"])
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
        for e in expenses:
            writer.writerow([e.id, e.category.name if e.category else "", e.description, e.amount, current_user.currency, e.date, e.payment_method, e.is_recurring, e.tags or ""])
        filename = f"expenses_export_{date.today()}.csv"

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
