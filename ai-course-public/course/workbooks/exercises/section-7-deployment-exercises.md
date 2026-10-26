# Codebook Exercises — Section 7: Deployment Patterns

> **Paired exercises for [`../ai-engineer-codebook.md` § 7](../ai-engineer-codebook.md#section-7-deployment-patterns).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 7 (Deployment)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, deploy something, watch it fail, fix it

**Time per exercise:** 30-60 min.
**Total time for this section:** 6-10 hours.

---

## Snippet 7.1 — FastAPI Production App

**Reference:** [`../ai-engineer-codebook.md#71-fastapi-production-app`](../ai-engineer-codebook.md#71-fastapi-production-app)

### Exercise 7.1.1: Add request validation

```python
# TODO: Every endpoint should have Pydantic models for request and response.
# - Reject extra fields (forbid)
# - Reject None for required fields
# - Use Field() for constraints (min_length, max_length, ge, le)
# - Add a custom validator for complex logic (e.g., email format)
# Test with 50 valid + 50 invalid inputs.
```

### Exercise 7.1.2: Add structured error responses

```python
# TODO: Replace bare HTTPException with structured errors:
# {
#   "error_code": "INVALID_INPUT",
#   "message": "Email is required",
#   "field": "email",
#   "request_id": "..."
# }
# Use FastAPI's exception_handler. Test that the response is consistent across all errors.
```

### Exercise 7.1.3: Add request IDs and tracing

```python
# TODO: Middleware that:
# - Reads X-Request-ID from headers, or generates a UUID
# - Stores it in a context var
# - Includes it in every log line and every response header
# - Returns it in the error response
# Now you can grep logs for a specific request.
```

### Exercise 7.1.4: Add CORS, rate limiting, request size limits

```python
# TODO: Production-grade FastAPI needs:
# - CORS: allow_origins=[your-domain.com], not *
# - Rate limiting: 100 req/min per user, 429 with Retry-After header
# - Request size limit: reject > 10MB
# - Timeout: 30s per request
# Use slowapi for rate limiting. Use a middleware for the rest.
```

### Exercise 7.1.5: Health check + readiness + liveness

```python
# TODO: Three endpoints:
# - /health: liveness (am I running?) — 200 always
# - /ready: readiness (can I serve traffic?) — checks DB, OpenAI
# - /startup: startup probe (have I initialized?) — checks model loaded
# Kubernetes uses these to decide when to send traffic.
```

---

## Snippet 7.2 — Docker Setup

**Reference:** [`../ai-engineer-codebook.md#72-docker-setup`](../ai-engineer-codebook.md#72-docker-setup)

### Exercise 7.2.1: Multi-stage build for size

```dockerfile
# TODO: Original Dockerfile is ~1.2GB (full Python + your deps + ffmpeg).
# Multi-stage: builder stage installs + compiles, runtime stage copies artifacts only.
# Target: <300MB.
# Measure: docker images ls, before and after.
```

### Exercise 7.2.2: Non-root user

```dockerfile
# TODO: Run the app as a non-root user inside the container.
# - Create a "app" user
# - chown the /app directory
# - USER app in the runtime stage
# Defense in depth: even if the app is exploited, attacker isn't root in the container.
```

### Exercise 7.2.3: Health check in Dockerfile

```dockerfile
# TODO: HEALTHCHECK in Dockerfile:
# - curl /health every 30s
# - 10s timeout
# - 3 retries before declaring unhealthy
# - Docker / k8s will restart the container if unhealthy
```

### Exercise 7.2.4: Pin versions for reproducibility

```dockerfile
# TODO: Use python:3.11.6-slim (not 3.11-slim).
# Pin every dep in requirements.txt with ==.
# Why: "latest" today != "latest" tomorrow. Reproducibility.
```

---

## Snippet 7.3 — Environment Variables

**Reference:** [`../ai-engineer-codebook.md#73-environment-variables`](../ai-engineer-codebook.md#73-environment-variables)

### Exercise 7.3.1: pydantic-settings for typed env

```python
from pydantic_settings import BaseSettings
# TODO: Replace os.getenv() with a typed Settings class:
# class Settings(BaseSettings):
#     openai_api_key: str
#     database_url: str = "sqlite:///./app.db"
#     jwt_secret: str
#     log_level: str = "INFO"
# This catches missing vars at startup, not at request time.
```

### Exercise 7.3.2: Secrets in production (NOT in .env)

```python
# TODO: For production:
# - Railway: use their secret store
# - AWS: use Secrets Manager or Parameter Store
# - Vercel: encrypted env vars
# - Local dev: .env (gitignored)
# NEVER commit .env, NEVER log env vars, NEVER include them in error responses.
```

### Exercise 7.3.3: Config validation at startup

```python
# TODO: At app startup, validate that all required env vars are set.
# If anything is missing, FAIL FAST with a clear error message.
# Better to crash on boot than to fail mysteriously on the 100th request.
```

### Exercise 7.3.4: Multi-environment config

```python
# TODO: Support dev/staging/prod configs:
# - DATABASE_URL different per env
# - LOG_LEVEL different per env
# - OPENAI_API_KEY different per env
# - DEBUG mode only in dev
# Use a .env.development, .env.production pattern, or env-based config.
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Deploy to Railway

```bash
# TODO: 
# 1. Push your code to GitHub
# 2. Sign up at railway.app
# 3. New project from GitHub repo
# 4. Add Postgres plugin
# 5. Set env vars in Railway dashboard
# 6. Deploy
# 7. Get a public URL
# 8. Test from another machine
# 9. Set up auto-deploy on push to main
```

### Challenge B: Zero-downtime deploy

```python
# TODO: Blue-green deploy:
# - Run 2 instances (blue + green)
# - Deploy to green
# - Health-check green
# - Switch traffic to green
# - Kill blue
# Implement: railway can do this natively. For k8s, use rolling update.
# Verify: no failed requests during deploy.
```

### Challenge C: Observability in production

```python
# TODO: Add to your production app:
# - Structured logging (JSON)
# - Request tracing (OpenTelemetry)
# - Error tracking (Sentry)
# - LLM tracing (LangSmith or Helicone)
# - Uptime monitoring (BetterStack or UptimeRobot)
# - Cost tracking per request
# Verify: you can find a specific user's request across all these tools.
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **Where do you host?** (Railway, Render, Fly.io, AWS, Vercel — when to pick which)
2. **How do you handle secrets?** (env vars, secrets manager, never in code)
3. **What's your request validation strategy?** (Pydantic everywhere, custom error format)
4. **How do you deploy?** (CI/CD, manual, auto on push)
5. **Zero-downtime deploys?** (blue-green, rolling, or "good enough")
6. **Observability stack?** (logs, metrics, traces, errors, LLM-specific)
7. **Health checks?** (liveness, readiness, startup — all three?)
8. **Auto-scaling?** (CPU-based, queue-depth-based, time-of-day)
9. **Cost monitoring?** (per-request, per-user, alert on anomaly)
10. **Incident response?** (runbook, on-call, who gets paged)

Save these answers. Deploying a toy is easy. Deploying a product is hard.

---

## What's next

- Pair with [`../../practice/level-7-deployment/`](../../practice/level-7-deployment/) for the deeper labs
- Move to `section-8-observability-exercises.md` for observability patterns
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path