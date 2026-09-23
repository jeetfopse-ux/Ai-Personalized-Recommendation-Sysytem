import os
import sys
from datetime import datetime, date
from flask import Flask, redirect, url_for
from flask_login import LoginManager

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import config_by_name
from models import db, User
from services.finance_service import seed_default_categories

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access your financial dashboard."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.transactions import transactions_bp
    from routes.budgets import budgets_bp
    from routes.savings import savings_bp
    from routes.ai_advisor import ai_advisor_bp
    from routes.reports import reports_bp
    from routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(ai_advisor_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(profile_bp)

    # Template filters and context processors
    @app.context_processor
    def inject_global_vars():
        return {
            "current_year": date.today().year,
            "current_month": date.today().month,
            "now": datetime.utcnow()
        }

    @app.template_filter("currency")
    def format_currency(val, symbol="$"):
        if val is None:
            val = 0.0
        return f"{symbol}{float(val):,.2f}"

    @app.template_filter("pct")
    def format_pct(val):
        if val is None:
            val = 0.0
        return f"{float(val):.1f}%"

    # Initialize tables and seed defaults within app context
    with app.app_context():
        db.create_all()
        seed_default_categories()

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    
    # Check if --tunnel argument passed
    if "--tunnel" in sys.argv:
        from tunnel import start_tunnel
        public_url = start_tunnel(port)
        print(f"\n[+] Ngrok Tunnel Active: {public_url}\n")
    
    print(f"\n[*] Personal Finance Advisor Bot running on http://127.0.0.1:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
