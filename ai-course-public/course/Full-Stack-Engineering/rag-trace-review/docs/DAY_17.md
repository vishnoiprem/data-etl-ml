# Day 17 — Packaging and Deployment

## 1. Analogy
Deployment is **packing a suitcase**. Dockerfile is the list of what goes in. Compose is the labeled bag. CI is the conveyor belt.

## 2. Technical concept
- **Docker:** image = filesystem snapshot + entrypoint.
- **Compose:** multi-container orchestrator for dev.
- **Env vars:** 12-factor config.
- **Health check:** endpoint that says "I'm alive".

## 3. Why
Reproducible builds. Same image runs on your laptop and prod.

## 4. Data flow
`docker compose up` → builds images → starts containers → healthcheck passes → traffic.

## 5. Example (Dockerfile + compose already in repo)

## 6. Line-by-line
- `FROM python:3.11-slim` — minimal base.
- `WORKDIR /app` — predictable paths.
- `CMD ["uvicorn", ...]` — production server.

## 7. I/O
- `docker compose up` → `http://localhost:8000` (API) and `:5173` (UI).

## 8. Bugs
- Forgetting `EXPOSE` → port unreachable.
- Baking secrets into the image → leaks.
- Using `latest` tag → unreproducible builds.

## 9. Tests
- CI runs `pytest` on every PR.
- CI builds the Docker image.

## 10. Performance
- Multi-stage builds for smaller images.
- Use `gunicorn` or `uvicorn --workers N` for CPU-bound.

## 11. Five Q&As
1. **What is a multi-stage build?** A Dockerfile with multiple `FROM`s; build in one, copy artifacts to another.
2. **What is a health check?** A command the orchestrator runs to know the container is alive.
3. **What is 12-factor?** A methodology for portable apps; config in env, stateless processes, etc.
4. **What is a CI pipeline?** Tests + builds on every push.
5. **What is a reverse proxy?** Nginx or Caddy in front of the app for TLS and rate limiting.

## 12. Coding assignment
Add a `Makefile` with `make dev`, `make test`, `make seed`.

## 13. Solution
```makefile
.PHONY: dev test seed
dev:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
test:
	cd backend && source .venv/bin/activate && pytest -q
seed:
	cd backend && source .venv/bin/activate && python seed.py
```
- 0: doesn't parse
- 4: dev works
- 6: test works
- 8: seed works
- 10: parallel targets

**Time: 90 min**