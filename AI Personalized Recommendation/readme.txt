================================================================================
          AI PERSONALIZED RECOMMENDATION - PERSONAL FINANCE ADVISOR BOT
================================================================================

================================================================================
1. PROJECT OVERVIEW
================================================================================
AI Personalized Recommendation is a full-stack Flask application designed to
provide intelligent personal finance tracking, budget optimization, savings
goal management, and AI-driven financial recommendations using Google Gemini /
OpenAI (with intelligent offline rule-based fallback algorithms).

Key Features:
- User Authentication & Profile Customization (Currency, Savings Targets, Risk)
- Interactive Dashboard with Real-Time KPIs & Cash Flow Visualization
- Transaction Management (Incomes, Categorized Expenses, Recurring tracking)
- 50/30/20 Budgeting Engine & Overspending Warnings
- Savings Goals & Emergency Fund Status Calculator
- AI Financial Health Audits (Comprehensive health scoring 0-100)
- AI Financial Advisor Chatbot (Context-aware personal assistant)
- Financial Report Exports (CSV format for expenses and incomes)
- Built-in Ngrok Public Tunneling for easy remote demonstrations

================================================================================
2. SYSTEM REQUIREMENTS & PREREQUISITES
================================================================================
- Python: Version 3.9, 3.10, 3.11, or newer
- Operating System: Windows, macOS, or Linux
- Internet Connection (optional: required for live Gemini/OpenAI API & Ngrok)

================================================================================
3. INSTALLATION & ENVIRONMENT SETUP
================================================================================

Step 1: Open your terminal in the project root directory:
   cd "AI Personalized Recommendation"

Step 2: (Recommended) Create and activate a Python virtual environment:
   Windows (PowerShell / Command Prompt):
      python -m venv venv
      .\venv\Scripts\activate

   macOS / Linux:
      python3 -m venv venv
      source venv/bin/activate

Step 3: Install all required project dependencies:
   pip install -r requirements.txt

Step 4: Configure environment variables:
   Copy `.env.example` to create `.env`:
   
   Windows (PowerShell):
      Copy-Item .env.example .env

   Windows (CMD):
      copy .env.example .env

   macOS / Linux:
      cp .env.example .env

   Edit `.env` as desired:
   -----------------------------------------------------------------------------
   SECRET_KEY=your-random-secret-key
   FLASK_ENV=development
   PORT=5000
   DATABASE_URL=sqlite:///finance_advisor.db
   
   # AI Configuration (Optional: if empty, built-in smart rule engine is used)
   GEMINI_API_KEY=your_google_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   DEFAULT_AI_PROVIDER=gemini

   # Ngrok Public Tunnel (Optional: for sharing online via ngrok)
   NGROK_AUTHTOKEN=your_ngrok_token_here
   -----------------------------------------------------------------------------

================================================================================
4. HOW TO SEED THE DATABASE WITH DEMO DATA
================================================================================
To populate the database with 3 months of realistic transactions, budgets,
savings goals, and an initial AI health audit:

   python seed.py

Default Demo Login Credentials:
- Email:    demo@finance.ai
- Password: password123

================================================================================
5. HOW TO RUN THE APPLICATION
================================================================================

A. Standard Local Run:
   python app.py

   Open your browser and navigate to:
   http://127.0.0.1:5000

B. Run with Public Ngrok Tunnel (Live sharing URL):
   python app.py --tunnel

   Or run the standalone tunnel script:
   python tunnel.py

C. Custom Port:
   Set PORT in your .env or run:
   Windows (PowerShell):
      $env:PORT=8000; python app.py
   macOS / Linux:
      PORT=8000 python app.py

================================================================================
6. HOW TO RUN TESTS
================================================================================

All tests can be executed seamlessly using `pytest` or directly with `python`:

A. Run the entire test suite:
   pytest

   or

   python -m pytest

B. Run with detailed verbose output:
   pytest -v

C. Run individual test files directly:
   python tests/test_auth.py
   python tests/test_finance.py
   python tests/test_ai_service.py

Test Suite Structure:
- tests/test_auth.py: Tests user registration, duplicate email prevention, login/logout.
- tests/test_finance.py: Tests financial calculation engine, 50/30/20 breakdown, budget alerts.
- tests/test_ai_service.py: Tests AI financial health audits, budget suggestions, and chat responses.

================================================================================
7. TROUBLESHOOTING & DEBUGGING GUIDE
================================================================================

Q1: Error: `ModuleNotFoundError: No module named 'models'` when running test files
--------------------------------------------------------------------------------
Reason: Running test scripts directly from subdirectories can omit the root
directory from Python's search path.
Solution:
- Run `pytest` or `python -m pytest` from the project root.
- All test scripts and `pytest.ini` are now preconfigured with root path resolution,
  so you can also run `python tests/test_auth.py` directly.

Q2: What happens if I do not have a Gemini or OpenAI API key?
--------------------------------------------------------------------------------
The application includes a resilient, rule-based fallback finance advisor engine.
If no API keys are provided in `.env`, the system automatically computes:
- Health scores based on savings rate, budget adherence, and emergency reserves.
- Detailed markdown analysis and actionable financial recommendations.
- Interactive financial chat answers using expert rule-based advice.
Adding `GEMINI_API_KEY` or `OPENAI_API_KEY` upgrades this to live LLM generation.

Q3: How do I reset or wipe the local database?
--------------------------------------------------------------------------------
1. Delete the SQLite database file: `finance_advisor.db` (or `instance/finance_advisor.db` if present).
2. Run `python seed.py` to recreate all tables and repopulate demo data.

Q4: Port 5000 is already in use
--------------------------------------------------------------------------------
Change the port in your `.env` file (`PORT=5001`) or specify it when launching:
   $env:PORT="5001"; python app.py

Q5: Database locked / Permission errors
--------------------------------------------------------------------------------
Ensure no other instance of `python app.py` or database viewer tool is holding
a write lock on `finance_advisor.db`.

================================================================================
8. PROJECT DIRECTORY ARCHITECTURE
================================================================================
.
|-- app.py                  # Application factory, blueprint registrations, app launcher
|-- config.py               # Environment configurations (Dev, Test, Prod)
|-- models.py               # SQLAlchemy database models (User, Income, Expense, Budget, etc.)
|-- seed.py                 # Database populator script for 3-month sample history
|-- tunnel.py               # Ngrok public tunnel wrapper
|-- pytest.ini              # Pytest configuration with pythonpath set to root
|-- requirements.txt        # Python package dependencies
|-- .env.example            # Template for environment configuration
|-- readme.txt              # Complete operating & debugging manual
|
|-- routes/                 # Blueprint Route Handlers
|   |-- auth.py             # User signup, login, logout
|   |-- dashboard.py        # Main dashboard & KPI aggregations
|   |-- transactions.py     # Income & Expense CRUD, filtering, CSV exports
|   |-- budgets.py          # Category budget limits & 50/30/20 monitoring
|   |-- savings.py          # Savings goals & emergency fund tracker
|   |-- ai_advisor.py       # AI Health audit & Advisor chat endpoints
|   |-- reports.py          # Monthly breakdown & financial analytics
|   |-- profile.py          # User settings & preferences
|
|-- services/               # Business Logic & Core Algorithms
|   |-- finance_service.py  # Financial calculations, KPIs, 50/30/20 rules
|   |-- ai_service.py       # Gemini/OpenAI integrations & rule-based fallbacks
|
|-- templates/              # Jinja2 HTML Templates (Modern Dark/Glass UI)
|-- static/                 # Static Assets (CSS, JS, Icons)
`-- tests/                  # Pytest Unit & Integration Test Suite
    |-- conftest.py         # Pytest test fixtures & in-memory test database
    |-- test_auth.py        # Authentication test cases
    |-- test_finance.py     # Financial logic test cases
    `-- test_ai_service.py  # AI recommendation & Chat test cases
================================================================================
