from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Financial profile preferences
    currency = db.Column(db.String(10), default="$")
    monthly_savings_target = db.Column(db.Float, default=500.0)
    emergency_fund_target_months = db.Column(db.Integer, default=6)
    risk_tolerance = db.Column(db.String(20), default="Moderate")  # Conservative, Moderate, Aggressive
    
    # AI preferences / overrides
    preferred_ai_provider = db.Column(db.String(20), default="gemini")  # gemini or openai
    custom_gemini_key = db.Column(db.String(255), nullable=True)
    custom_openai_key = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    incomes = db.relationship("Income", backref="user", lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy=True, cascade="all, delete-orphan")
    savings_goals = db.relationship("SavingsGoal", backref="user", lazy=True, cascade="all, delete-orphan")
    custom_categories = db.relationship("ExpenseCategory", backref="user", lazy=True, cascade="all, delete-orphan")
    recommendations = db.relationship("AIRecommendation", backref="user", lazy=True, cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class ExpenseCategory(db.Model):
    __tablename__ = "expense_categories"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # Nullable for system defaults
    name = db.Column(db.String(60), nullable=False)
    icon = db.Column(db.String(40), default="tag")
    color = db.Column(db.String(20), default="#6366f1")
    category_type = db.Column(db.String(20), default="needs")  # 'needs', 'wants', 'savings'
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship("Expense", backref="category", lazy=True)
    budgets = db.relationship("Budget", backref="category", lazy=True)

    def __repr__(self):
        return f"<ExpenseCategory {self.name}>"


class Income(db.Model):
    __tablename__ = "incomes"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source = db.Column(db.String(100), nullable=False)  # Salary, Freelance, Dividend, etc.
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    is_recurring = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(30), default="One-Time")  # Monthly, Bi-Weekly, One-Time, etc.
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Income {self.source} - {self.amount}>"


class Expense(db.Model):
    __tablename__ = "expenses"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_categories.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    payment_method = db.Column(db.String(50), default="Card")  # Card, Cash, Bank Transfer, UPI, etc.
    description = db.Column(db.String(255), nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Expense {self.description} - {self.amount}>"


class Budget(db.Model):
    __tablename__ = "budgets"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_categories.id"), nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)   # e.g., 2025
    allocated_amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "category_id", "month", "year", name="uq_user_cat_month_year"),
    )

    def __repr__(self):
        return f"<Budget {self.category_id} {self.month}/{self.year} - {self.allocated_amount}>"


class SavingsGoal(db.Model):
    __tablename__ = "savings_goals"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(50), default="Emergency")  # Emergency, Travel, Investment, Purchase, Other
    status = db.Column(db.String(30), default="In Progress")  # In Progress, Completed, Paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def progress_percentage(self) -> float:
        if not self.target_amount or self.target_amount <= 0:
            return 100.0 if self.current_amount > 0 else 0.0
        pct = (self.current_amount / self.target_amount) * 100
        return min(round(pct, 1), 100.0)

    def __repr__(self):
        return f"<SavingsGoal {self.name} - {self.current_amount}/{self.target_amount}>"


class AIRecommendation(db.Model):
    __tablename__ = "ai_recommendations"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # health_audit, budget_plan, spending_analysis, cost_cutting
    health_score = db.Column(db.Integer, nullable=True)  # 0 to 100
    summary = db.Column(db.Text, nullable=False)
    detailed_markdown = db.Column(db.Text, nullable=True)
    key_metrics_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AIRecommendation {self.report_type} Score:{self.health_score}>"


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.message[:30]}>"
