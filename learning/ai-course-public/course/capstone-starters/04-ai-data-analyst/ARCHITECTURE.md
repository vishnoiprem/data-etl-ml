# Architecture — AI Data Analyst

> **The design decisions behind the starter.** Read this before you change anything.

## System diagram

```
                        ┌─────────────────┐
                        │   React UI      │
                        │  (or HTML)      │
                        └────────┬────────┘
                                 │ HTTPS
                                 ▼
                        ┌─────────────────┐
                        │   FastAPI       │
                        │   (uvicorn)     │
                        ├─────────────────┤
                        │ /datasets       │
                        │ /analyze        │
                        │ /chart          │
                        └────┬──────┬─────┘
                             │      │
                  ┌──────────┘      └──────────┐
                  ▼                             ▼
         ┌─────────────────┐          ┌─────────────────┐
         │  PostgreSQL     │          │   Sandbox       │
         │  (Neon free)    │          │  (subprocess)   │
         ├─────────────────┤          ├─────────────────┤
         │ - users         │          │ - pandas        │
         │ - datasets      │          │ - plotly        │
         │ - analyses      │          │ - numpy         │
         └────────┬────────┘          │ - no network    │
                  │                   │ - 30s timeout   │
                  ▼                   └────────┬────────┘
         ┌─────────────────┐                  │
         │     S3 / disk   │                  ▼
         │    (CSVs)       │         ┌─────────────────┐
         └─────────────────┘         │   OpenAI API    │
                                     │  gpt-4o + mini  │
                                     └─────────────────┘
```

## Component choices

| Component | Choice | Alternative | Why we picked this |
|---|---|---|---|
| Code execution | Sandboxed subprocess | Pyodide, Docker, E2B, hosted code interpreter | Simple, no extra infra, good enough for MVP |
| LLM (code gen) | GPT-4o | Claude 3.5 Sonnet, o1-mini | Best at code, function-calling for structured output |
| LLM (insight) | GPT-4o-mini | Haiku | 30× cheaper for the plain-English summary |
| DataFrame | pandas | polars, modin | Standard, well-known, GPT-4o trained on it heavily |
| Charts | Plotly | matplotlib, Chart.js | Interactive, JSON-serializable for web |
| Storage | S3 (or local) | R2, GCS | Standard, easy to swap |
| Backend | FastAPI | Flask, Django | Async, OpenAPI, Pydantic |
| Database | Postgres (Neon) | MongoDB, SQLite | Relational + free tier |
| Auth | JWT → Clerk | Auth0, Supabase | Clerk has 5-min setup, social logins, MFA |
| Hosting | Railway | Render, Fly.io | $5/mo free tier, Postgres included |

## Sandbox security model

The starter uses a **subprocess sandbox** — not as safe as a container, but good enough for trusted users in MVP. For production, migrate to one of the production-grade options.

| Sandbox | Isolation | Setup cost | When to use |
|---|---|---|---|
| subprocess (this starter) | process-level | none | MVP, trusted users |
| Docker per execution | OS-level | medium | Single-tenant B2B |
| Pyodide (WASM) | no FS / network | low | Read-only analysis, no install |
| E2B / hosted | OS-level + remote | low | Best for production, pay-per-sandbox |
| Firecracker microVM | hardware-level | high | Multi-tenant, high-trust requirements |

The starter applies these guardrails:

- **No network** — `socket.socket()` blocked
- **No file write outside the dataset dir** — `open()` paths validated
- **No shell** — `subprocess`, `os.system`, `__import__` blocked
- **Timeout** — 30s hard kill
- **Memory cap** — 512MB RSS (enforced by outer process, not Python)
- **Code is parsed** — `ast.parse` before execution; `eval`/`exec` of dynamic strings blocked

## Data flow: ask a question

```
1. User POSTs /analyze with {dataset_id, question}
2. FastAPI loads dataset_id, reads schema from Postgres
3. dataframe_ops.infer_schema(csv_path) -> {columns: [{name, type, sample}], n_rows}
4. Build prompt: question + schema + "write pandas code using df"
5. GPT-4o generates code (function call: {code, explanation})
6. Validate code with ast.parse + linter (no banned imports)
7. code_executor.run(code, csv_path) -> subprocess runs with timeout
8. Execute: read CSV, run code, capture result DataFrame
9. Pick best chart from result shape (line / bar / scatter)
10. visualizer.render(df) -> JSON for Plotly
11. Save analysis to Postgres
12. Return {answer, code, chart, table}
```

## Capacity model

| Users | Queries/day | CSV GB stored | Compute | Storage | Monthly cost |
|---|---|---|---|---|---|
| 10 | 100 | 1 | Railway free | Neon + S3 free | $0 |
| 100 | 1K | 10 | Railway $20 | S3 $1, Neon free | $21 |
| 1K | 10K | 100 | Railway $100, 4 workers | S3 $10, Neon $15 | $125 |
| 10K | 100K | 1K | Railway $500, autoscaling | S3 $100, Neon $50 | $650 |
| 100K | 1M | 10K | Railway $2K, dedicated workers | S3 $1K, Neon $200 | $3,200 |

**Per query (avg):**
- 1 schema-inference call (cached after first) = $0 (cached)
- 1 GPT-4o code-gen call (~1.5K in + 800 out) = $0.012
- 1 GPT-4o-mini insight call (~1K in + 200 out) = $0.0003
- 1 subprocess run (avg 5s CPU) = $0.001
- S3 storage (avg 1MB per dataset × 5 datasets) = $0.0001/mo
- **Total per query = ~$0.013**

**Scaling cliffs:**

- **100 users**: Need to add Redis for schema caching (avoid re-prompting for known CSVs)
- **1K users**: Need to move code execution to a worker pool (subprocess blocks the request thread)
- **10K users**: Need to migrate from subprocess to E2B or Docker (security + concurrency)
- **100K users**: Need to consider running pandas in a query engine (DuckDB) for >1M-row datasets

## Cost model (per 1K queries)

Assumes: avg 1.5K input + 800 output per code-gen, 1K+200 per insight, 5s CPU.

| Component | Cost per 1K queries |
|---|---|
| GPT-4o code generation | $12 |
| GPT-4o-mini insight | $0.30 |
| Subprocess CPU (5s × 1K = 5000s ≈ 1.4 CPU-hr) | $1 |
| S3 storage (10GB avg) | $1 |
| Postgres writes | $1 |
| **Total per 1K queries** | **$15.30** |

At $29/mo per user with 10 queries/day = 300 queries/month = $0.10 per query. Cost $0.013. **87% margin.**

## Security checklist

- [x] JWT tokens with expiry (replace with Clerk for refresh tokens)
- [x] Per-user data isolation (user_id filter on every query)
- [x] Input validation (Pydantic, file size, file type)
- [x] AST-validated code before execution
- [x] Banned-import check (subprocess, os.system, socket, etc.)
- [x] 30s execution timeout
- [x] No network access in sandbox
- [ ] Migrate to Docker / E2B for production (week 4)
- [ ] Rate limiting per user (add in week 4)
- [ ] Per-query resource limits (memory, CPU) enforced by outer runtime
- [ ] PII detection on uploaded CSVs (warn user, suggest redaction)
- [ ] HTTPS only (handled by hosting platform)
- [ ] CORS restricted to your domain
- [ ] Virus scan uploads (CSVs can contain formula injection: `=cmd|...`)

## Observability checklist

- [x] Structured logs (JSON, request_id, user_id, timing)
- [x] Every LLM call logged with token counts + cost
- [x] Every code execution logged with duration, output size, errors
- [x] Schema cache hit/miss logged
- [ ] Add LangSmith for end-to-end trace (week 3)
- [ ] Add Sentry for error tracking (week 3)
- [ ] Add PostHog for product analytics (week 4)
- [ ] Add an eval pipeline: held-out set of (question, expected code) pairs (week 5)
- [ ] Add uptime monitoring (week 4)

## Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| CSV too large (>100MB) | size check at upload | Reject with 413; suggest chunking |
| CSV malformed | pandas read_csv exception | Return error to user with line number |
| LLM generates bad code | ast.parse fails | Retry once with "fix this" prompt |
| LLM generates code that times out | 30s subprocess timeout | Retry once with "be faster" prompt |
| Sandbox escapes | (catastrophic) | Migrate to E2B/Docker before this happens |
| User uploads malicious CSV (formula injection) | openpyxl/pandas warning | Reject, warn user |
| User uploads 10K-column CSV | OOM in prompt | Reject > 100 columns, suggest pivoting |
| User's code returns 100MB result | OOM in chart gen | Truncate to 5K rows, sample |
| User asks 1000 questions in a minute | rate limit | 429 with retry-after |

## When to migrate off this stack

| Trigger | Migration |
|---|---|
| >1K queries/day | Move subprocess to a worker pool (Celery + Redis) |
| >$500/mo on subprocess CPU | Migrate to E2B hosted sandboxes |
| >10K users | Move auth to Clerk, add team workspaces, add scheduled reports |
| >100MB CSVs common | Add chunked CSV reader (dask) or migrate to DuckDB |
| >10M-row datasets | Move to a query engine (DuckDB, BigQuery) instead of pandas |
| EU users | Move to EU region (OpenAI EU, EU S3) |
| Need on-prem | Self-host Llama 3 70B for code gen; keep OpenAI for insight |

## Trade-off log (ADRs)

- **ADR-001**: Subprocess over Pyodide for MVP — subprocess supports pip packages, Pyodide doesn't. Pyodide would be a stretch goal.
- **ADR-002**: GPT-4o over Claude for code gen — empirically best at pandas code; well-represented in training. Use Claude for long-context analysis.
- **ADR-003**: Schema-aware prompting — pass column types + 3 sample rows to GPT-4o, so it doesn't hallucinate column names.
- **ADR-004**: Plotly over matplotlib — Plotly outputs JSON, which the frontend renders directly. matplotlib outputs PNG, which is heavier and less interactive.
- **ADR-005**: Auto-visualization — pick chart from result shape (1 numeric col = bar, 2 numeric cols = scatter, time index = line). Saves the LLM a step.
- **ADR-006**: Cache schemas in Postgres — schema doesn't change between queries, no need to re-infer.

## Future work

- [ ] Add multi-file analysis (join across CSVs)
- [ ] Add database connections (Postgres, MySQL, BigQuery)
- [ ] Add scheduled reports (weekly email digest)
- [ ] Add team workspaces (shared datasets)
- [ ] Add an "analyst agent" that can run multi-step analyses
- [ ] Add PDF export of analysis reports
- [ ] Add saved queries / query library
- [ ] Add Notion / Google Sheets export
- [ ] Add a "code review" UI (let user edit the LLM-generated code before running)
- [ ] Add multi-language support for natural language questions
- [ ] Add chart annotations and customization
