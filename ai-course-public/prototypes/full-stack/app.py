"""
AIForBiz Mini-Business - Complete prototype in one file
Run: python app.py
Opens at http://localhost:8000
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from pathlib import Path
from typing import Optional
import json
import secrets
from datetime import datetime


app = FastAPI(title="AIForBiz Mini-Business")
static_dir = Path(__file__).parent / "static"
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

SIGNUPS_FILE = data_dir / "signups.json"
SALES_FILE = data_dir / "sales.json"

# --- Data layer ---
def load(path, default):
    if not path.exists(): return default
    try: return json.loads(path.read_text())
    except: return default

def save(path, data):
    path.write_text(json.dumps(data, indent=2, default=str))

def get_next_id(items):
    return (max((i["id"] for i in items), default=0)) + 1

# --- Prompt library (subset, full version in prompt-tool/) ---
PROMPTS = {
    "marketing": [
        {"title": "30-Day Content Calendar", "category": "marketing",
         "prompt": "Create a 30-day social media calendar for {business_type}. Each day: platform, topic, hook, 3-sentence caption, 3 hashtags."},
        {"title": "LinkedIn Post Generator", "category": "marketing",
         "prompt": "Write a LinkedIn post about {topic}. Structure: hook, story, 3 takeaways, CTA question. Under 200 words, conversational tone."},
        {"title": "Email Subject Lines (10)", "category": "marketing",
         "prompt": "Write 10 email subject lines for {campaign_goal}. Under 50 chars each, varied approaches, no spam words."},
    ],
    "customer_service": [
        {"title": "Customer Email Reply", "category": "customer_service",
         "prompt": "Reply to this customer email for {business_type}: \"{customer_question}\". Empathetic, helpful, under 150 words."},
        {"title": "Refund Response", "category": "customer_service",
         "prompt": "Write a refund approval email. Acknowledge issue, explain process (3-5 days), offer 20% next-order discount, warm tone."},
        {"title": "FAQ Generator", "category": "customer_service",
         "prompt": "Generate 20 FAQs for {business_type}. Group by: Orders, Products, Returns, Account. Each: question + 2-sentence answer."},
    ],
    "operations": [
        {"title": "Process Documentation", "category": "operations",
         "prompt": "Document this process: {process}. Output: goal, owner per step, step-by-step, tools, common errors, time estimate."},
        {"title": "Meeting Agenda", "category": "operations",
         "prompt": "Agenda for {meeting_type} meeting. 60 min. Pre-read items, time allocations, discussion questions, action template."},
    ],
    "strategy": [
        {"title": "Competitor Analysis", "category": "strategy",
         "prompt": "Analyze {competitor}: positioning, pricing, marketing, 3 strengths, 3 weaknesses, 3 tactical moves I can make this month."},
        {"title": "90-Day Plan", "category": "strategy",
         "prompt": "90-day plan to achieve {goal}. 3 monthly phases with objectives, milestones, metrics, pitfalls."},
    ],
}

PRODUCTS = {
    "mini": {"name": "Mini Course", "price": 47, "description": "5 modules, 50 prompts, workbook"},
    "main": {"name": "Main Course", "price": 197, "description": "8 modules, 100+ prompts, community, templates"},
    "premium": {"name": "Premium", "price": 497, "description": "Everything + 1-on-1 setup call, custom AI system, 90-day support"},
}

# --- Models ---
class Signup(BaseModel):
    email: str
    name: Optional[str] = None
    source: Optional[str] = "website"

class Checkout(BaseModel):
    email: str
    product: str  # mini, main, premium
    payment_token: Optional[str] = "mock_token"

# --- Routes: Public ---
@app.get("/", response_class=FileResponse)
def home():
    return static_dir / "index.html"

@app.get("/prompts", response_class=FileResponse)
def prompts_page():
    return static_dir / "prompts.html"

@app.get("/pricing", response_class=FileResponse)
def pricing_page():
    return static_dir / "pricing.html"

@app.get("/admin", response_class=FileResponse)
def admin_page():
    return static_dir / "admin.html"

# --- Routes: API ---
@app.post("/api/signup")
def signup(data: Signup):
    """Capture email"""
    signups = load(SIGNUPS_FILE, [])
    if any(s["email"] == data.email for s in signups):
        return {"message": "Already subscribed", "status": "existing"}
    entry = {
        "id": get_next_id(signups),
        "email": data.email,
        "name": data.name,
        "source": data.source,
        "timestamp": datetime.now().isoformat(),
        "ip": "logged_in_production",
    }
    signups.append(entry)
    save(SIGNUPS_FILE, signups)
    return {"message": "Welcome!", "status": "new", "id": entry["id"]}

@app.post("/api/checkout")
def checkout(data: Checkout):
    """Mock checkout (replace with Stripe in production)"""
    if data.product not in PRODUCTS:
        raise HTTPException(400, "Invalid product")
    sales = load(SALES_FILE, [])
    product = PRODUCTS[data.product]
    sale = {
        "id": get_next_id(sales),
        "email": data.email,
        "product": data.product,
        "product_name": product["name"],
        "amount": product["price"],
        "currency": "USD",
        "payment_token": data.payment_token,
        "timestamp": datetime.now().isoformat(),
        "status": "completed_mock",
    }
    sales.append(sale)
    save(SALES_FILE, sales)
    return {
        "message": "🎉 Purchase complete (MOCK - replace with Stripe in production!)",
        "sale": sale,
        "next_steps": "Check your email for course access link.",
    }

@app.get("/api/prompts")
def list_prompts(category: Optional[str] = None):
    if category:
        return PROMPTS.get(category, [])
    return {cat: [{"title": p["title"]} for p in items] for cat, items in PROMPTS.items()}

@app.get("/api/prompts/{category}/{title}")
def get_prompt(category: str, title: str, **kwargs):
    for p in PROMPTS.get(category, []):
        if p["title"].lower() == title.lower():
            final = p["prompt"]
            for k, v in kwargs.items():
                final = final.replace("{" + k + "}", str(v))
            return {"title": p["title"], "prompt": final}
    raise HTTPException(404, "Prompt not found")

@app.get("/api/products")
def list_products():
    return PRODUCTS

# --- Routes: Admin ---
@app.get("/admin/api/signups")
def admin_signups():
    return load(SIGNUPS_FILE, [])

@app.get("/admin/api/sales")
def admin_sales():
    sales = load(SALES_FILE, [])
    total = sum(s["amount"] for s in sales)
    return {
        "count": len(sales),
        "total_revenue": total,
        "sales": sales,
    }

@app.get("/admin/api/stats")
def admin_stats():
    signups = load(SIGNUPS_FILE, [])
    sales = load(SALES_FILE, [])
    total_rev = sum(s["amount"] for s in sales)
    by_product = {}
    for s in sales:
        by_product[s["product_name"]] = by_product.get(s["product_name"], 0) + 1
    return {
        "total_signups": len(signups),
        "total_sales": len(sales),
        "total_revenue": total_rev,
        "by_product": by_product,
        "conversion_rate": (len(sales) / len(signups) * 100) if signups else 0,
        "average_order_value": (total_rev / len(sales)) if sales else 0,
    }

# --- HTML helpers ---
def render_simple(content: str, title: str = "Admin"):
    """Simple HTML wrapper (for inline admin if needed)"""
    return HTMLResponse(f"""
<!DOCTYPE html>
<html><head><title>{title}</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:0 20px;}}
h1{{color:#2C3E50}}.stat{{display:inline-block;padding:20px;margin:8px;background:#F7F9FC;border-radius:8px;}}
.stat strong{{display:block;font-size:32px;color:#3498DB}}</style></head>
<body>{content}</body></html>
""")

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(" 🚀 AIForBiz Mini-Business ".center(60, "="))
    print("=" * 60)
    print(" 🌐 Landing:  http://localhost:8000")
    print(" 🧰 Prompts:  http://localhost:8000/prompts")
    print(" 💰 Pricing:  http://localhost:8000/pricing")
    print(" 🔒 Admin:    http://localhost:8000/admin")
    print(" 📚 API docs: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
