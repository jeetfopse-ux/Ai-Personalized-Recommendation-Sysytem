import os
import json
import logging
from datetime import date
from models import db, User, ExpenseCategory, AIRecommendation, ChatMessage
from services.finance_service import (
    get_monthly_summary,
    get_category_spending,
    get_budget_performance,
    get_50_30_20_breakdown,
    get_emergency_fund_status,
    get_financial_health_score,
    get_user_categories
)

logger = logging.getLogger(__name__)

def get_active_ai_client(user: User):
    """Determine the active AI provider and credentials."""
    # Check user override first, then system environment
    provider = (user.preferred_ai_provider or os.getenv("DEFAULT_AI_PROVIDER", "gemini")).lower()
    
    gemini_key = user.custom_gemini_key or os.getenv("GEMINI_API_KEY", "")
    openai_key = user.custom_openai_key or os.getenv("OPENAI_API_KEY", "")

    if provider == "gemini" and gemini_key:
        return "gemini", gemini_key
    elif provider == "openai" and openai_key:
        return "openai", openai_key
    elif gemini_key:
        return "gemini", gemini_key
    elif openai_key:
        return "openai", openai_key
    return None, None

def call_llm(user: User, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    """Invokes the configured LLM (Gemini or OpenAI) with fallback."""
    provider, api_key = get_active_ai_client(user)
    
    if not provider or not api_key:
        return ""

    if provider == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Try newer model first, fall back to gemini-pro if needed
            model_name = "gemini-1.5-flash"
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt
                )
                response = model.generate_content(user_prompt)
                return response.text
            except Exception:
                model = genai.GenerativeModel("gemini-pro")
                combined = f"{system_prompt}\n\nUser Request:\n{user_prompt}"
                response = model.generate_content(combined)
                return response.text
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
            return ""

    elif provider == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
            return ""

    return ""

def _build_financial_context(user_id: int, year: int = None, month: int = None) -> dict:
    """Build a comprehensive context dictionary of user's finances."""
    today = date.today()
    y = year or today.year
    m = month or today.month

    user = db.session.get(User, user_id)
    summary = get_monthly_summary(user_id, y, m)
    categories = get_category_spending(user_id, y, m)
    budget = get_budget_performance(user_id, y, m)
    split_50_30_20 = get_50_30_20_breakdown(user_id, y, m)
    emergency = get_emergency_fund_status(user_id)
    health = get_financial_health_score(user_id, y, m)

    currency = user.currency if user else "$"
    
    return {
        "user_name": user.username if user else "User",
        "currency": currency,
        "period": f"{date(y, m, 1).strftime('%B %Y')}",
        "income": summary["total_income"],
        "expenses": summary["total_expenses"],
        "net_savings": summary["net_savings"],
        "savings_rate": summary["savings_rate"],
        "categories": categories,
        "budget_allocated": budget["total_allocated"],
        "budget_utilization": budget["overall_utilization"],
        "overbudget_categories": [c["category_name"] for c in budget["overbudget_items"]],
        "split_50_30_20": split_50_30_20,
        "emergency_runway_months": emergency["runway_months"],
        "emergency_current_saved": emergency["current_saved"],
        "emergency_target": emergency["target_amount"],
        "algorithmic_score": health["score"],
        "health_rating": health["rating"]
    }

def generate_financial_audit(user_id: int, year: int = None, month: int = None) -> dict:
    """Generates a complete AI Financial Health Audit and persists it."""
    ctx = _build_financial_context(user_id, year, month)
    user = db.session.get(User, user_id)

    curr = ctx["currency"]
    categories_text = "\n".join([
        f"- {c['category_name']}: Spent {curr}{c['spent']} (Budget: {curr}{c['allocated']}, Status: {c['status']})"
        for c in ctx["categories"]
    ]) or "No expense records yet."

    system_prompt = (
        "You are a Certified Financial Planner (CFP) and AI Personal Finance Advisor. "
        "Your advice is pragmatic, empathetic, data-driven, and highly actionable. "
        "Analyze the provided personal financial data and return clear, structured guidance."
    )

    user_prompt = f"""
Analyze the following personal finance snapshot for {ctx['user_name']} for {ctx['period']}:
- Currency: {curr}
- Monthly Income: {curr}{ctx['income']}
- Total Expenses: {curr}{ctx['expenses']}
- Net Cash Flow: {curr}{ctx['net_savings']} (Savings Rate: {ctx['savings_rate']}%)
- Budget Allocated: {curr}{ctx['budget_allocated']} (Utilization: {ctx['budget_utilization']}%)
- Overbudget Categories: {', '.join(ctx['overbudget_categories']) if ctx['overbudget_categories'] else 'None'}
- 50/30/20 Rule:
  * Needs: {curr}{ctx['split_50_30_20']['needs']['amount']} ({ctx['split_50_30_20']['needs']['pct']}%) vs 50% target
  * Wants: {curr}{ctx['split_50_30_20']['wants']['amount']} ({ctx['split_50_30_20']['wants']['pct']}%) vs 30% target
  * Savings: {curr}{ctx['split_50_30_20']['savings']['amount']} ({ctx['split_50_30_20']['savings']['pct']}%) vs 20% target
- Emergency Fund: {curr}{ctx['emergency_current_saved']} saved ({ctx['emergency_runway_months']} months of living expenses; Target: {curr}{ctx['emergency_target']})

Category Breakdown:
{categories_text}

Provide:
1. An Executive Summary (2-3 concise sentences).
2. Financial Health Score (a number between 0 and 100).
3. 3-4 Key Strengths & Vulnerabilities.
4. 4 Prioritized Actionable Recommendations with estimated potential monthly savings.

Format your output in clean Markdown with headers and bullet points.
"""

    llm_output = call_llm(user, system_prompt, user_prompt)

    # If LLM is available, use output; otherwise use intelligent heuristic fallback
    if llm_output:
        score = ctx["algorithmic_score"]
        # Try to extract score if LLM specified a number
        import re
        score_match = re.search(r"Financial Health Score[:\s]+(\d{1,3})", llm_output, re.IGNORECASE)
        if score_match:
            try:
                extracted = int(score_match.group(1))
                if 0 <= extracted <= 100:
                    score = extracted
            except ValueError:
                pass
        
        summary = f"Financial Health Assessment for {ctx['period']} completed. Your current savings rate is {ctx['savings_rate']}% with an emergency fund runway of {ctx['emergency_runway_months']} months."
        # Extract first paragraph as summary if possible
        first_para = [p.strip() for p in llm_output.split("\n\n") if p.strip() and not p.startswith("#")]
        if first_para:
            summary = first_para[0][:240] + "..."

        detailed_md = llm_output
    else:
        # Heuristic Generator
        score = ctx["algorithmic_score"]
        rating = ctx["health_rating"]
        summary = (
            f"Your financial health score is {score}/100 ({rating}). "
            f"You saved {curr}{ctx['net_savings']} ({ctx['savings_rate']}%) this month with "
            f"{ctx['emergency_runway_months']} months of emergency reserve."
        )

        top_cats = ctx["categories"][:3]
        top_cat_names = ", ".join([c["category_name"] for c in top_cats]) if top_cats else "None"
        overspent = ctx["overbudget_categories"]

        detailed_md = f"""
### Executive Summary
{summary}

### Key Strengths & Vulnerabilities
* **Cash Flow**: {'Positive net cash flow allows consistent investing and debt repayment.' if ctx['net_savings'] >= 0 else 'Negative cash flow detected! Expenses exceeded monthly earnings.'}
* **50/30/20 Adherence**: Needs ({ctx['split_50_30_20']['needs']['pct']}%), Wants ({ctx['split_50_30_20']['wants']['pct']}%), Savings ({ctx['split_50_30_20']['savings']['pct']}%).
* **Emergency Runway**: Currently at {ctx['emergency_runway_months']} months of living expenses (Target: 6 months).
* **Spending Concentration**: Highest expenditures concentrated in **{top_cat_names}**.

### Prioritized Actionable Recommendations
1. **{'Rebalance Overbudget Areas' if overspent else 'Cap Discretionary Spending'}**:
   {'Review limits for ' + ', '.join(overspent) + ' to eliminate budget leakages.' if overspent else 'Keep dining and entertainment within 30% of total income.'}
   * *Potential Monthly Savings*: {curr}{round(ctx['expenses'] * 0.08, 2)}
2. **Automate Emergency Reserve**:
   Direct at least 15% of each paycheck into a dedicated high-yield savings account until you reach {curr}{ctx['emergency_target']}.
   * *Action*: Set up automatic transfer on income deposit day.
3. **Audit Recurring Subscriptions & Utility Tariffs**:
   Review card transactions for inactive streaming, gym, or software memberships.
   * *Potential Monthly Savings*: {curr}30 - {curr}75
4. **Target 50/30/20 Alignment**:
   Adjust category allocations so essential needs remain below 50% of take-home pay, freeing up more for investment growth.
"""

    # Persist in DB
    rec = AIRecommendation(
        user_id=user_id,
        report_type="health_audit",
        health_score=score,
        summary=summary,
        detailed_markdown=detailed_md,
        key_metrics_json=json.dumps(ctx)
    )
    db.session.add(rec)
    db.session.commit()

    return {
        "id": rec.id,
        "score": score,
        "summary": summary,
        "detailed_markdown": detailed_md,
        "metrics": ctx,
        "created_at": rec.created_at
    }

def generate_ai_budget_recommendations(user_id: int, total_income: float) -> list:
    """Generates suggested budget limits for all user categories based on income and 50/30/20 rule."""
    user = db.session.get(User, user_id)
    categories = get_user_categories(user_id)
    curr = user.currency if user else "$"

    if total_income <= 0:
        total_income = 3000.0  # sensible fallback base

    # Rule allocations: 50% Needs, 30% Wants, 20% Savings
    needs_pool = total_income * 0.50
    wants_pool = total_income * 0.30
    savings_pool = total_income * 0.20

    needs_cats = [c for c in categories if c.category_type == "needs"]
    wants_cats = [c for c in categories if c.category_type == "wants"]
    savings_cats = [c for c in categories if c.category_type == "savings"]

    # Specific weightings for needs
    weights = {
        "Housing & Rent": 0.55,
        "Groceries": 0.22,
        "Utilities & Bills": 0.12,
        "Transportation": 0.11,
        "Healthcare & Medical": 0.08,
    }

    # Specific weightings for wants
    wants_weights = {
        "Dining & Takeout": 0.35,
        "Entertainment & Leisure": 0.25,
        "Shopping & Lifestyle": 0.25,
        "Personal & Education": 0.15,
        "Miscellaneous": 0.10,
    }

    suggestions = []

    # Needs
    for cat in needs_cats:
        w = weights.get(cat.name, 1.0 / max(len(needs_cats), 1))
        alloc = round((needs_pool * w), 2)
        suggestions.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "category_type": cat.category_type,
            "color": cat.color,
            "icon": cat.icon,
            "suggested_amount": alloc,
            "reason": f"Essential living expense ({round(alloc/total_income*100, 1)}% of total income)"
        })

    # Wants
    for cat in wants_cats:
        w = wants_weights.get(cat.name, 1.0 / max(len(wants_cats), 1))
        alloc = round((wants_pool * w), 2)
        suggestions.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "category_type": cat.category_type,
            "color": cat.color,
            "icon": cat.icon,
            "suggested_amount": alloc,
            "reason": f"Discretionary allocation ({round(alloc/total_income*100, 1)}% of income)"
        })

    # Savings
    for cat in savings_cats:
        alloc = round(savings_pool / max(len(savings_cats), 1), 2)
        suggestions.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "category_type": cat.category_type,
            "color": cat.color,
            "icon": cat.icon,
            "suggested_amount": alloc,
            "reason": f"Long-term wealth building ({round(alloc/total_income*100, 1)}% of income)"
        })

    return suggestions

def chat_with_advisor(user_id: int, user_message: str) -> str:
    """Conversational Financial Assistant that answers questions with user's financial context."""
    user = db.session.get(User, user_id)
    if not user:
        return "User not found."

    ctx = _build_financial_context(user_id)
    curr = ctx["currency"]

    # Save user message
    user_msg_record = ChatMessage(user_id=user_id, role="user", message=user_message)
    db.session.add(user_msg_record)
    db.session.commit()

    # Retrieve last 6 chat history messages
    history = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.created_at.desc()).limit(6).all()
    history.reverse()

    top_expenses = ", ".join([f"{c['category_name']} ({curr}{c['spent']})" for c in ctx["categories"][:4]])

    system_prompt = f"""
You are "FinanceBot", an intelligent, empathetic, and knowledgeable AI Financial Planning Assistant.
You have direct, confidential access to {ctx['user_name']}'s live financial metrics:
- Currency: {curr}
- Monthly Income: {curr}{ctx['income']}
- Monthly Expenses: {curr}{ctx['expenses']}
- Net Savings: {curr}{ctx['net_savings']} (Savings Rate: {ctx['savings_rate']}%)
- Overbudget Categories: {', '.join(ctx['overbudget_categories']) if ctx['overbudget_categories'] else 'None'}
- Top Spending Categories: {top_expenses or 'No spending recorded yet'}
- Emergency Fund: {curr}{ctx['emergency_current_saved']} ({ctx['emergency_runway_months']} months of expenses)
- Financial Health Score: {ctx['algorithmic_score']}/100

Guidelines:
1. Be helpful, concise, practical, and clear.
2. When answering, reference their real numbers when relevant (e.g. income, savings rate, emergency fund).
3. Do not give risky speculative investment advice; focus on budgeting, saving, debt payoff, and emergency resilience.
4. Keep responses readable with bullet points or bold text where appropriate.
"""

    history_text = "\n".join([f"{m.role.capitalize()}: {m.message}" for m in history[:-1]])
    user_prompt = f"""
Conversation History:
{history_text}

User: {user_message}
FinanceBot:
"""

    reply = call_llm(user, system_prompt, user_prompt, temperature=0.5)

    if not reply:
        # Heuristic fallback responder
        msg_lower = user_message.lower()
        if "save" in msg_lower or "saving" in msg_lower:
            reply = (
                f"Based on your current monthly income of {curr}{ctx['income']} and expenses of {curr}{ctx['expenses']}, "
                f"your net savings is {curr}{ctx['net_savings']} ({ctx['savings_rate']}% savings rate).\n\n"
                f"**Top savings opportunities for you:**\n"
                f"1. **Discretionary Capping**: Top spending is in {top_expenses}. Trimming non-essential dining/shopping by 15% can recover ~{curr}{round(ctx['expenses']*0.08, 2)} every month.\n"
                f"2. **Pay Yourself First**: Set up an automated recurring deposit of {curr}{user.monthly_savings_target} on pay day.\n"
                f"3. **Target 20% Savings**: An ideal 20% savings target for your income is {curr}{round(ctx['income']*0.20, 2)}/month."
            )
        elif "budget" in msg_lower:
            reply = (
                f"Your budget utilization this month is at {ctx['budget_utilization']}%. "
                f"{'Overbudget categories: ' + ', '.join(ctx['overbudget_categories']) + '.' if ctx['overbudget_categories'] else 'All budgeted categories are currently within limits!'}\n\n"
                f"Using the 50/30/20 rule, your target allocation should be:\n"
                f"- **Needs (50%)**: {curr}{round(ctx['income']*0.50, 2)}\n"
                f"- **Wants (30%)**: {curr}{round(ctx['income']*0.30, 2)}\n"
                f"- **Savings & Debt (20%)**: {curr}{round(ctx['income']*0.20, 2)}\n"
                f"You can auto-apply this in the **Budgets** tab with one click!"
            )
        elif "emergency" in msg_lower:
            reply = (
                f"You currently have {curr}{ctx['emergency_current_saved']} in your emergency reserve, "
                f"which represents **{ctx['emergency_runway_months']} months** of runway based on your average living expenses.\n\n"
                f"For optimal financial security, I recommend building towards a 6-month safety buffer of {curr}{ctx['emergency_target']}. "
                f"Keep this in an easily accessible High-Yield Savings Account (HYSA)."
            )
        elif "score" in msg_lower or "health" in msg_lower:
            reply = (
                f"Your Financial Health Score is **{ctx['algorithmic_score']}/100** ({ctx['health_rating']}).\n\n"
                f"- **Savings Rate**: {ctx['savings_rate']}% (Target: 20%+)\n"
                f"- **Budget Adherence**: {ctx['budget_utilization']}% utilized\n"
                f"- **Emergency Buffer**: {ctx['emergency_runway_months']} months\n\n"
                f"You can generate a full detailed AI Audit in the **AI Advisor** tab anytime!"
            )
        else:
            reply = (
                f"Hello {ctx['user_name']}! I am your AI Financial Advisor. "
                f"This month, you have earned {curr}{ctx['income']} and spent {curr}{ctx['expenses']}, "
                f"leaving you with a savings rate of {ctx['savings_rate']}%. "
                f"Feel free to ask me about creating an optimal budget, cutting expenses, reaching your savings goals, "
                f"or calculating your emergency fund runway!"
            )

    # Save assistant response
    bot_msg_record = ChatMessage(user_id=user_id, role="assistant", message=reply)
    db.session.add(bot_msg_record)
    db.session.commit()

    return reply
