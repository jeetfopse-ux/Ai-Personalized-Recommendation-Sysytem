from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        action = request.form.get("action", "update_preferences")

        if action == "update_preferences":
            username = request.form.get("username", "").strip()
            currency = request.form.get("currency", "$")
            savings_target_str = request.form.get("monthly_savings_target", "500")
            emergency_target_str = request.form.get("emergency_fund_target_months", "6")
            risk_tolerance = request.form.get("risk_tolerance", "Moderate")

            if username:
                current_user.username = username
            current_user.currency = currency
            try:
                current_user.monthly_savings_target = max(0.0, float(savings_target_str))
                current_user.emergency_fund_target_months = max(1, int(emergency_target_str))
            except ValueError:
                pass
            current_user.risk_tolerance = risk_tolerance

            # AI Settings
            preferred_ai = request.form.get("preferred_ai_provider", "gemini")
            custom_gemini = request.form.get("custom_gemini_key", "").strip()
            custom_openai = request.form.get("custom_openai_key", "").strip()

            current_user.preferred_ai_provider = preferred_ai
            if custom_gemini:
                current_user.custom_gemini_key = custom_gemini
            if custom_openai:
                current_user.custom_openai_key = custom_openai

            db.session.commit()
            flash("Financial profile and AI preferences updated successfully!", "success")
            return redirect(url_for("profile.index"))

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_user.check_password(current_password):
                flash("Incorrect current password.", "danger")
                return redirect(url_for("profile.index"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("profile.index"))

            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return redirect(url_for("profile.index"))

            current_user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("profile.index"))

    return render_template("profile/index.html")
