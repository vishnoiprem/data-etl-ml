# Working Prototypes

Small, working code prototypes for the AI course business. Each one solves a specific problem and runs in minutes.

## 4 Prototypes Built

### 1. `landing-page/` — Sales Landing Page (HTML/CSS/JS)
**No build needed.** Just open `index.html` in your browser.

```
open landing-page/index.html
```

**What it does:**
- Hero section with email signup
- Problem → Solution → Testimonials → Pricing → FAQ → CTA
- Form saves emails to localStorage (swap for ConvertKit in production)
- Fully responsive (mobile + desktop)
- Loads in <2 seconds

**Use it for:** Your actual sales page. Deploy to Carrd, Vercel, or Netlify for free.

---

### 2. `prompt-tool/` — AI Prompt Generator (Python CLI)
**Run:** `python prompt_generator.py`

**What it does:**
- 12 ready-to-use prompts across 4 categories (marketing, customer service, operations, strategy)
- User fills in variables (e.g., business_type, customer_question)
- Generates copy-paste prompts for ChatGPT/Claude
- Saves every prompt generated to a log file
- Can be called from other tools via `list_all()` or `generate_prompt()`

**Use it for:** The free lead magnet on your landing page. Or as the core of a paid prompt-pack product.

---

### 3. `course-site/` — Course Delivery Platform (FastAPI + JS)
**Run:**
```bash
pip install fastapi uvicorn
cd course-site
python server.py
```
Opens at http://localhost:8000

**What it does:**
- Sign up form → get "course access"
- 5-module course with 12 lessons (videos load in iframe)
- Mark lessons complete → progress tracked per user
- Leaderboard of top students (gamification)
- Lesson progress saved to local JSON

**Use it for:** A real course platform. Replace the JSON storage with a database (PostgreSQL/SQLite) and the placeholder videos with your own.

---

### 4. `full-stack/` — Complete Mini-Business (FastAPI + 4 pages)
**Run:**
```bash
cd full-stack
python app.py
```
Then visit:
- 🌐 http://localhost:8000 — Landing page
- 🧰 http://localhost:8000/prompts — Free prompt tool
- 💰 http://localhost:8000/pricing — Course pricing + checkout
- 🔒 http://localhost:8000/admin — Dashboard with all metrics
- 📚 http://localhost:8000/docs — API documentation

**What it does:**
- **Landing page** with email capture
- **Prompt tool** (the lead magnet) with 12 prompts and variable substitution
- **Pricing page** with 3 tiers and mock checkout
- **Admin dashboard** showing signups, sales, revenue, conversion rate, AOV
- All data persisted to local JSON files
- Auto-refreshing admin dashboard
- Includes a REST API for all operations

**Use it for:** A complete prototype to validate your idea before building with real tools.

---

## Test the Full-Stack Prototype

```bash
cd full-stack
python app.py

# In another terminal:
curl http://localhost:8000/api/products          # List products
curl http://localhost:8000/api/prompts           # List all prompts
curl -X POST http://localhost:8000/api/signup \  # Capture email
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","name":"You"}'

curl -X POST http://localhost:8000/api/checkout \  # Mock sale
  -H "Content-Type: application/json" \
  -d '{"email":"buyer@example.com","product":"main"}'

curl http://localhost:8000/admin/api/stats         # See revenue!
```

**Tested output:**
```json
{"total_signups":1,"total_sales":1,"total_revenue":197,...}
```

---

## What to Build Next (Priority Order)

### Week 1: Replace placeholders
1. **Landing page** → swap localStorage for ConvertKit/EmailOctopus
2. **Checkout** → swap mock for Stripe Checkout
3. **Videos** → upload real course videos (Mux, Vimeo, or Loom)

### Week 2: Replace JSON with database
- Swap JSON files for SQLite (simple) or PostgreSQL (production)
- Add user authentication (Clerk, Supabase Auth)
- Add progress emails (when users haven't completed in 7 days)

### Week 3: Add features
- Course community (Discord webhook, Circle, Skool)
- Affiliate tracking (Rewardful, Tolt)
- Analytics (PostHog, Plausible)
- Customer support (Intercom, Crisp)

### Week 4: Deploy
- Frontend → Vercel, Netlify, or Cloudflare Pages
- Backend → Railway, Render, or Fly.io
- Database → Supabase, Neon, or PlanetScale
- Domain → Namecheap + Cloudflare

---

## File Structure

```
prototypes/
├── README.md                  ← You are here
├── requirements.txt           ← Python deps
├── landing-page/              ← Prototype 1: Sales page
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── prompt-tool/               ← Prototype 2: AI prompts
│   └── prompt_generator.py
├── course-site/               ← Prototype 3: Course platform
│   ├── server.py
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── app.js
└── full-stack/                ← Prototype 4: Complete business
    ├── app.py
    ├── README.md
    └── static/
        ├── index.html         ← Landing page
        ├── prompts.html       ← Free prompts
        ├── pricing.html       ← Checkout
        ├── admin.html         ← Dashboard
        ├── style.css
        └── data/              ← Auto-created JSON
            ├── signups.json
            └── sales.json
```

---

## Common Customizations

### Add a new prompt
Edit `prompt-tool/prompt_generator.py` (or `full-stack/app.py` for the full-stack version), add to the relevant category.

### Change pricing
Edit the `PRODUCTS` dict in `full-stack/app.py` or the HTML in `landing-page/index.html`.

### Add a new course module
Edit the `COURSE` dict in `course-site/server.py`.

### Change colors/branding
All CSS files use CSS variables at the top:
```css
:root {
  --primary: #2C3E50;   /* Dark blue */
  --accent: #3498DB;    /* Bright blue */
  --success: #27AE60;   /* Green */
  ...
}
```

---

## Next Steps

1. **Pick one prototype to start with** (I recommend `full-stack/` for the most complete starting point)
2. **Customize the branding** (logo, colors, copy)
3. **Replace placeholder data** with your real course content
4. **Deploy to production** (free hosting exists for everything)
5. **Replace mock checkout** with real Stripe when ready

**Total cost to run in production:** $0-50/month (most tools have free tiers).

---

Built for the AIForBiz course business · Tested and working as of [Date]
