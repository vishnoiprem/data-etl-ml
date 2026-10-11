# Capstone Starters — Decision Matrix

> **Pick the right capstone for your 8-week build.**

All 6 capstone templates are runnable starters — same general shape, but the **core AI technique** and the **target audience** differ. Capstones 1-5 are pitched at the **AI engineer building a SaaS** (FastAPI + Postgres + JWT pattern); capstone 6 is pitched at the **SMB owner who doesn't code** (5 copy-paste prompts + an optional 50-line Python wrapper). Pick the one that matches your audience.

---

## At-a-glance matrix

| # | Capstone | Core AI technique | Audience | Price | Your unfair advantage |
|---|---|---|---|---|---|
| 1 | [AI Document Q&A](./01-ai-doc-qa/) | RAG over PDFs | Lawyers, researchers, analysts | $19/mo | Better chunking, multi-doc reasoning |
| 2 | [AI Research Assistant](./02-ai-research-assistant/) | LangGraph ReAct + web search | Consultants, investors, journalists | $49/mo | Better synthesis, source diversity |
| 3 | [AI Sales Coach](./03-ai-sales-coach/) | Whisper + GPT-4o + function calling | Sales teams, founders, SDRs | $99/mo | Better rubrics, industry playbooks |
| 4 | [AI Data Analyst](./04-ai-data-analyst/) | Code interpreter + Pandas | Analysts, marketers, ops | $29/mo | Better sandbox, multi-step analysis |
| 5 | [AI Content Generator](./05-ai-content-generator/) | GPT-4o + Tavily + SEO scoring | Marketers, agencies, indie hackers | $39/mo | Better SERP research, brand voice |
| 6 | [**SMB Content Recycler**](./06-smb-content-recycler/) | 5 prompts + 1-page SOP (no code) | SMB owners, content creators, indie hackers | $0-47 | Better brand-voice customization |

> **Capstone 6 is different from 1-5.** It's not a SaaS; it's a workflow. The starter ships as 5 copy-paste prompts + a 1-page SOP that the SMB owner uses in ChatGPT. An optional 50-line Python wrapper is included for SMB owners who want to automate the API call. See the [SMB offer ladder](../../business/plan/smb-offer-ladder.md) for how this capstone fits the $47/$197/$497/$997 product stack.

---

## Which one should I pick?

Use the IDEAL framework (from [`../projects/ai-engineer-capstone-guide.md`](../projects/ai-engineer-capstone-guide.md)):

### Pick **AI Document Q&A** if…

- ✅ You have a domain with lots of long-form docs (legal, medical, research, compliance)
- ✅ You can name 10+ people who would pay $19/mo to "ask their docs questions"
- ✅ You have access to public datasets of docs to seed the product
- ❌ Don't pick if your target users are casual — they won't upload docs

### Pick **AI Research Assistant** if…

- ✅ Your target users do research for a living (VCs, consultants, journalists, students)
- ✅ You can name 10+ people who would pay $49/mo to "get a cited report in 60 seconds"
- ✅ You're comfortable debugging agents (LangGraph, prompt loops, tool budgets)
- ❌ Don't pick if your users want quick answers — research takes 1-2 min

### Pick **AI Sales Coach** if…

- ✅ You're in or adjacent to sales (ex-SDR, founder who does sales, sales consultant)
- ✅ You can name 10+ reps or sales managers who would pay $99/mo
- ✅ You have a way to get sample sales calls (your own, recordings, public demos)
- ❌ Don't pick if you've never done sales — the rubric will be shallow

### Pick **AI Data Analyst** if…

- ✅ Your target users live in spreadsheets but can't write code (marketing, ops, sales ops)
- ✅ You can name 10+ people who would pay $29/mo to "ask their CSV questions"
- ✅ You're comfortable with the security model (sandboxed code execution)
- ❌ Don't pick if your users need SQL — they'll just write SQL

### Pick **AI Content Generator** if…

- ✅ Your target users publish content (agencies, indie hackers, SEO consultants)
- ✅ You can name 10+ people who would pay $39/mo for "SEO articles on demand"
- ✅ You have SEO knowledge (you know what makes content rank)
- ❌ Don't pick if you're not willing to do SEO marketing — that's the only channel

### Pick **SMB Content Recycler** if…

- ✅ You (or your customer) is a non-technical SMB owner who writes 1 long-form piece a week
- ✅ You want to ship in 7 days, not 8 weeks
- ✅ You don't want to build a SaaS; you want a workflow
- ✅ You want to teach the workflow (it's the foundation of a $47/$197 course)
- ❌ Don't pick if your customers expect a hosted product — this is a workflow, not a SaaS

---

## Technical difficulty

| # | Capstone | Code complexity | AI complexity | Ops complexity | Total |
|---|---|---|---|---|---|
| 1 | Doc Q&A | Medium | Medium | Low | **Medium** |
| 2 | Research Assistant | High | High | Medium | **High** |
| 3 | Sales Coach | Medium | Medium | Low (Whisper) | **Medium** |
| 4 | Data Analyst | High (sandbox) | Medium | Medium | **High** |
| 5 | Content Generator | Low | Medium | Low | **Low–Medium** |
| 6 | SMB Content Recycler | None (Tier 1) / Low (Tier 2) | Low (5 prompts) | None | **None** |

**Easiest to ship in 7 days:** #6 (no code required; just copy-paste a prompt)
**Easiest to ship in 8 weeks:** #1 or #5
**Hardest:** #2 (multi-agent state machine is debug-heavy) or #4 (security model)

---

## Time-to-first-user

| Capstone | Week 1 demo | Week 2 MVP | First 10 users (week 5-6) |
|---|---|---|---|
| Doc Q&A | Upload PDF, get answer | Auth + multi-user | Twitter, IndieHackers |
| Research Assistant | Ask question, get report | Auth + history | LinkedIn (consultants) |
| Sales Coach | Upload call, get feedback | Auth + team view | Sales communities |
| Data Analyst | Upload CSV, get chart | Auth + saved queries | Marketing communities |
| Content Generator | Generate article | Auth + publish | SEO communities |
| SMB Content Recycler | Run the prompt, get 30 posts | Refine the prompt with engagement data | Yourself, then your team |

---

## Course technique coverage

| Course topic | #1 | #2 | #3 | #4 | #5 | #6 |
|---|---|---|---|---|---|---|
| LLM APIs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (optional Tier 2) |
| Prompt engineering | ✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ (the whole capstone) |
| RAG | ✓✓ | – | – | – | – | – |
| Agents | – | ✓✓ | – | ✓ | – | – |
| Multimodal (Whisper) | – | – | ✓✓ | – | – | – |
| Code interpreter | – | – | – | ✓✓ | – | – |
| Function calling | – | – | ✓✓ | – | – | – |
| Web search / SERP | – | ✓ | – | – | ✓✓ | – |
| SEO / domain-specific | – | – | – | – | ✓✓ | – |
| Streaming / SSE | – | ✓ | – | – | – | – |
| **No-code workflow design** | – | – | – | – | – | ✓✓ |

Legend: ✓ = used, ✓✓ = primary technique

If your goal is **breadth** across course topics, do #1 + #5. If you want **depth** in one area, do #2 (agents) or #4 (code interpreter). If you want to teach SMB owners, do #6.

---

## Common patterns across all 6 starters

Capstones 1-5 share the same FastAPI + Postgres + JWT skeleton, so once you learn one, you can read the others. Capstone 6 is the exception — it's a no-code-first workflow (Tier 1) with an optional Python wrapper (Tier 2) for automation.

```
capstone-01..05/
├── README.md           # what you start with + 8-week build path
├── ARCHITECTURE.md     # system diagram, capacity model, cost model, ADRs
├── app.py              # FastAPI entry point
├── <technique>.py      # the AI logic (RAG, agent, analyzer, executor, etc.)
├── frontend/index.html # minimal UI (replace with React in week 5)
├── tests/              # pytest suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example

capstone-06/
├── README.md           # the 5 prompts + the 1-page SOP + the 7-day ramp
├── recycler.py         # optional 50-line Python wrapper
└── tests/
    └── test_recycler.py  # tests for parse_posts()
```

When you change one of capstones 1-5, you've learned the pattern for all five. Capstone 6 is a different shape: workflow-first, code-optional.

---

## What's next

1. **Pick one** using the matrix above
2. **Run the starter** end-to-end (`uvicorn app:app --reload` for 1-5; copy-paste the master prompt for 6)
3. **Follow the build path** in the README (8 weeks for 1-5; 7 days for 6)
4. **Get 10 users** before you polish (1-5) or **get 10 posts in a week** before you refine (6)
5. **Demo on day 56** at cohort Demo Day (1-5) or **document the SOP for an employee on day 30** (6)

For the full 8-week schedule, IDEAL framework, and grading rubric, see [`../projects/ai-engineer-capstone-guide.md`](../projects/ai-engineer-capstone-guide.md). For the SMB 7-day ramp and the 5 guardrails, see [`../ai-fde/phase-6-interview-prep/generative-ai/companion-courses/intro-to-ai-agents/s09-ai-agents-in-business/L9-4-the-smb-first-7-days.md`](../ai-fde/phase-6-interview-prep/generative-ai/companion-courses/intro-to-ai-agents/s09-ai-agents-in-business/L9-4-the-smb-first-7-days.md).

Ship it. 🚀
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
