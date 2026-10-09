# Capstone Starters — Decision Matrix

> **Pick the right capstone for your 8-week build.**

All 5 capstone templates are runnable starters — same folder structure, same Dockerfile, same FastAPI + Postgres + JWT pattern. The difference is the **core AI technique** and the **target audience**.

---

## At-a-glance matrix

| # | Capstone | Core AI technique | Audience | Price | Your unfair advantage |
|---|---|---|---|---|---|
| 1 | [AI Document Q&A](./01-ai-doc-qa/) | RAG over PDFs | Lawyers, researchers, analysts | $19/mo | Better chunking, multi-doc reasoning |
| 2 | [AI Research Assistant](./02-ai-research-assistant/) | LangGraph ReAct + web search | Consultants, investors, journalists | $49/mo | Better synthesis, source diversity |
| 3 | [AI Sales Coach](./03-ai-sales-coach/) | Whisper + GPT-4o + function calling | Sales teams, founders, SDRs | $99/mo | Better rubrics, industry playbooks |
| 4 | [AI Data Analyst](./04-ai-data-analyst/) | Code interpreter + Pandas | Analysts, marketers, ops | $29/mo | Better sandbox, multi-step analysis |
| 5 | [AI Content Generator](./05-ai-content-generator/) | GPT-4o + Tavily + SEO scoring | Marketers, agencies, indie hackers | $39/mo | Better SERP research, brand voice |

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

---

## Technical difficulty

| # | Capstone | Code complexity | AI complexity | Ops complexity | Total |
|---|---|---|---|---|---|
| 1 | Doc Q&A | Medium | Medium | Low | **Medium** |
| 2 | Research Assistant | High | High | Medium | **High** |
| 3 | Sales Coach | Medium | Medium | Low (Whisper) | **Medium** |
| 4 | Data Analyst | High (sandbox) | Medium | Medium | **High** |
| 5 | Content Generator | Low | Medium | Low | **Low–Medium** |

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

---

## Course technique coverage

| Course topic | #1 | #2 | #3 | #4 | #5 |
|---|---|---|---|---|---|
| LLM APIs | ✓ | ✓ | ✓ | ✓ | ✓ |
| Prompt engineering | ✓ | ✓ | ✓ | ✓ | ✓ |
| RAG | ✓✓ | – | – | – | – |
| Agents | – | ✓✓ | – | ✓ | – |
| Multimodal (Whisper) | – | – | ✓✓ | – | – |
| Code interpreter | – | – | – | ✓✓ | – |
| Function calling | – | – | ✓✓ | – | – |
| Web search / SERP | – | ✓ | – | – | ✓✓ |
| SEO / domain-specific | – | – | – | – | ✓✓ |
| Streaming / SSE | – | ✓ | – | – | – |

Legend: ✓ = used, ✓✓ = primary technique

If your goal is **breadth** across course topics, do #1 + #5. If you want **depth** in one area, do #2 (agents) or #4 (code interpreter).

---

## Common patterns across all 5 starters

Every starter has the same skeleton, so once you learn one, you can read the others:

```
capstone-XX/
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
```

When you change one starter, you've learned the pattern for all five.

---

## What's next

1. **Pick one** using the matrix above
2. **Run the starter** end-to-end (`uvicorn app:app --reload`)
3. **Follow the 8-week build path** in the README
4. **Get 10 users** before you polish
5. **Demo on day 56** at cohort Demo Day

For the full 8-week schedule, IDEAL framework, and grading rubric, see [`../projects/ai-engineer-capstone-guide.md`](../projects/ai-engineer-capstone-guide.md).

Ship it. 🚀
