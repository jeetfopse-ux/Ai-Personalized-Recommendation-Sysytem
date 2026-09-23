import json
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, AIRecommendation, ChatMessage
from services.ai_service import generate_financial_audit, chat_with_advisor
from services.finance_service import get_financial_health_score, get_monthly_summary

ai_advisor_bp = Blueprint("ai_advisor", __name__)

@ai_advisor_bp.route("/advisor")
@login_required
def index():
    today = date.today()
    # Get latest audit
    latest_audit = AIRecommendation.query.filter_by(
        user_id=current_user.id,
        report_type="health_audit"
    ).order_by(AIRecommendation.created_at.desc()).first()

    # Get chat history
    chat_history = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.asc()).all()

    # Quick health metrics
    health = get_financial_health_score(current_user.id, today.year, today.month)
    summary = get_monthly_summary(current_user.id, today.year, today.month)

    metrics_data = None
    if latest_audit and latest_audit.key_metrics_json:
        try:
            metrics_data = json.loads(latest_audit.key_metrics_json)
        except Exception:
            metrics_data = None

    return render_template(
        "ai_advisor/index.html",
        latest_audit=latest_audit,
        chat_history=chat_history,
        health=health,
        summary=summary,
        metrics=metrics_data
    )

@ai_advisor_bp.route("/advisor/generate-audit", methods=["POST"])
@login_required
def trigger_audit():
    today = date.today()
    try:
        generate_financial_audit(current_user.id, today.year, today.month)
        flash("AI Financial Health Audit successfully generated with personalized recommendations!", "success")
    except Exception as e:
        flash(f"Error generating audit: {e}", "danger")
    return redirect(url_for("ai_advisor.index"))

@ai_advisor_bp.route("/api/advisor/chat", methods=["POST"])
@login_required
def chat():
    """AJAX endpoint for conversing with FinanceBot."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message."}), 400

    reply = chat_with_advisor(current_user.id, message)
    return jsonify({
        "reply": reply,
        "user_message": message
    })

@ai_advisor_bp.route("/api/advisor/chat/clear", methods=["POST"])
@login_required
def clear_chat():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"status": "Chat history cleared."})
