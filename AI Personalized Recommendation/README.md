# AI Personalized Recommendation - Personal Finance Advisor Bot

A full-stack Flask application providing intelligent personal finance tracking, budget optimization, savings goal management, and AI-driven financial recommendations using **Google Gemini / OpenAI** (with resilient offline rule-based fallback algorithms).

---

## 🌟 Key Features

- **User Authentication & Profile**: Multi-currency support, custom savings targets, and risk tolerance profiles.
- **Interactive Financial Dashboard**: Real-time KPI summaries, cash flow breakdown, and health tracking.
- **Transaction Management**: Incomes, categorized expenses, recurring items, and CSV export.
- **Budgeting & 50/30/20 Rule**: Visual category budgeting with overspending warnings.
- **Savings Goals & Emergency Fund**: Goal timeline tracker and emergency fund status.
- **AI Financial Health Audits**: Automatic financial health scoring (0–100) with detailed recommendations.
- **AI Financial Chatbot**: Context-aware advisor chat backed by Gemini, OpenAI, or local financial rule engine.
- **Ngrok Public Tunnel**: Built-in support to expose the local app to a public URL for remote access.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Setup
Copy [.env.example](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/.env.example) to `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

### 3. Seed Sample Database
Populate 3 months of realistic transactions, budgets, savings goals, and an initial AI health audit:
```bash
python seed.py
```
> **Default Demo Login:**
> - Email: `demo@finance.ai`
> - Password: `password123`

### 4. Run Application
```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

#### Running with Public Ngrok Tunnel:
```bash
python app.py --tunnel
```

---

## 🧪 Running Tests

Run the complete test suite:
```bash
pytest
```
Or run individual test modules:
```bash
python tests/test_auth.py
python tests/test_finance.py
python tests/test_ai_service.py
```

---

## 🔧 Troubleshooting & Debugging

| Issue | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'models'` | Running scripts from subdirectory without root in `PYTHONPATH` | Run `pytest` or `python -m pytest`. All test files and `pytest.ini` now automatically include the root path. |
| No Gemini / OpenAI API Key | Missing key in `.env` | The app includes a built-in rule-based financial advisor fallback. No key is required for core functionality, but adding one enables live LLM generation. |
| Port 5000 already in use | Another process running on port 5000 | Set `PORT=5001` in `.env` or run `$env:PORT="5001"; python app.py`. |
| Reset Database | Clear existing demo/test data | Delete `finance_advisor.db` and run `python seed.py`. |

---

## 📁 Project Architecture

- [app.py](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/app.py): Application factory and entrypoint.
- [config.py](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/config.py): Environment settings (Dev, Test, Prod).
- [models.py](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/models.py): Database models (User, Income, Expense, Budget, SavingsGoal, etc.).
- [seed.py](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/seed.py): Database seeder script.
- [tunnel.py](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/tunnel.py): Ngrok tunnel helper.
- [pytest.ini](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/pytest.ini): Pytest configuration.
- [routes/](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/routes): Blueprint routes (auth, dashboard, transactions, budgets, savings, ai_advisor, reports, profile).
- [services/](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/services): Core financial logic ([finance_service.py](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/services/finance_service.py)) and AI recommendations ([ai_service.py](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/services/ai_service.py)).
- [tests/](file:///c:/Users/jeetf/OneDrive/Documents/First%20AI%20Internship%20PMS%20Robtics/AI%20Personalized%20Recommendation/tests): Unit and integration tests.
