import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-finance-bot-2025")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # AI settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "gemini")
    
    # Ngrok settings
    NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")
    PORT = int(os.getenv("PORT", 5000))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'finance_advisor.db')}")
    # Handle postgres:// vs postgresql:// standard in SQLAlchemy 1.4+
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'finance_advisor.db')}")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
