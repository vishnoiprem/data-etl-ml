# Day 17 — Packaging and Deployment
**Module 17** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Deployment is **packing a suitcase**. Dockerfile is the list of what goes in. Compose is the labeled bag. CI is the conveyor belt that puts the bag on the plane.

Without a list, you forget your toothbrush. Without a bag, the airline loses your stuff. Without a conveyor belt, the plane never takes off.

---

## 2. Technical concepts (20 min)

- **Docker:** image = filesystem snapshot + entrypoint.
- **Compose:** multi-container orchestrator for dev.
- **Env vars:** 12-factor config.
- **Health check:** endpoint that says "I'm alive".
- **Multi-stage builds:** smaller images.

### 12-factor rules
- Code in repo, config in env.
- Stateless processes.
- Disposability: fast startup, graceful shutdown.
- Logs to stdout.

---

## 3. Coding (30 min)

Read the existing `backend/Dockerfile`, `frontend/Dockerfile`, and `docker-compose.yml`. Add a `Makefile` at the project root:

```makefile
.PHONY: dev test seed
dev:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
test:
	cd backend && source .venv/bin/activate && pytest -q
seed:
	cd backend && source .venv/bin/activate && python seed.py
```

Add a `.dockerignore` to the backend:

```
.venv
__pycache__
*.pyc
rag_traces.db
```

### Sample I/O
- `make dev` → uvicorn on :8000.
- `make test` → `14 passed`.
- `make seed` → `Inserted 10000 traces and 3000 feedback rows.`

### Line-by-line
- `.PHONY` prevents name collisions with files.
- `cd backend && ...` chains the command.

---

## 4. Debugging & tests (20 min)

### Bug 1: forgot `EXPOSE`
**Symptom:** port unreachable from outside.
**Fix:** add `EXPOSE 8000` to the Dockerfile.

### Bug 2: secrets in image
**Symptom:** API key leaks.
**Fix:** pass via `environment:` in compose, never `ARG`.

### Bug 3: `latest` tag
**Symptom:** unreproducible builds.
**Fix:** pin a specific version.

### Bug 4: SQLite in container
**Symptom:** data lost on container restart.
**Fix:** mount a volume: `volumes: - ./data:/data`.

---

## 5. Mock interview practice (20 min)

**Q1 — "Multi-stage build?"**
> A Dockerfile with multiple `FROM`s; build in one, copy artifacts to another.

**Q2 — "Health check?"**
> A command the orchestrator runs to know the container is alive.

**Q3 — "12-factor?"**
> Methodology for portable apps; config in env, stateless processes.

**Q4 — "CI pipeline?"**
> Tests + builds on every push.

**Q5 — "Reverse proxy?"**
> Nginx or Caddy in front of the app for TLS and rate limiting.

---

## 6. Success criteria check
- [ ] I can write a Dockerfile.
- [ ] I can write a docker-compose.
- [ ] I can explain 12-factor.
- [ ] I can add a healthcheck.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add a GitHub Actions workflow that runs `pytest -q` on every push.**

### Rubric (0–10)
- 0: workflow invalid
- 4: runs pytest
- 6: caches pip
- 8: uploads coverage
- 10: parallel matrix (Python 3.10, 3.11, 3.12)

### Solution
```yaml
name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest -q
```

**Time: 90 min**