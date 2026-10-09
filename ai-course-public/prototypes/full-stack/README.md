# AIForBiz Mini-Business - One-Command Setup

The smallest possible prototype of your AI course business:
- Lead-capture landing page
- AI prompt generator (lead magnet)
- Mock checkout
- Admin dashboard

All in one Python file, runs in your browser.

## Run it

```bash
cd ai-course-public/prototypes/full-stack
pip install fastapi uvicorn
python app.py
```

Then open: **http://localhost:8000**

## What it does

**Public side:**
- `/` — Landing page with email signup
- `/prompts` — Free AI prompt generator (the lead magnet)
- `/pricing` — Course pricing + mock checkout

**Admin side:**
- `/admin` — View signups, sales, leads
- `/admin/api/signups` — JSON list of all emails
- `/admin/api/sales` — JSON list of all sales

**API:**
- `POST /api/signup` — capture email
- `POST /api/checkout` — mock purchase
- `GET /api/prompts/{category}` — get prompts

## Files
- `app.py` — full backend (FastAPI)
- `static/index.html` — landing page
- `static/prompts.html` — prompt tool
- `static/pricing.html` — checkout
- `static/admin.html` — admin dashboard
- `data/` — auto-created: stores signups + sales as JSON

## Why it's useful

This is the **smallest possible business** that:
- Captures leads (emails)
- Provides value (free prompts)
- Closes sales (course checkout)
- Tracks everything (admin)

You can deploy this in an afternoon. Then replace each piece with real tools (ConvertKit, Stripe, etc.) as you grow.
