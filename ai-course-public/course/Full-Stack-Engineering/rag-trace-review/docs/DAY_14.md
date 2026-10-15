# Day 14 — Authentication and Security
**Module 14** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Auth is a **building pass**. Sessions are temporary wristbands. JWTs are tamper-evident ID cards. CORS is the rule that says "I only let in visitors from this address." CSRF is a thief holding a copy of your wristband.

---

## 2. Technical concepts (20 min)

- **Session cookie:** server stores the session; client gets a session ID.
- **JWT:** server signs a token; the token itself contains the claims.
- **CORS:** browser-level access control.
- **CSRF:** cross-site request forgery — mitigated with `SameSite=Strict` cookies + CSRF tokens.
- **XSS:** injecting JS via stored user content — escaped by React by default.
- **Input validation:** reject what we don't expect.

### Where to validate
- Client: UX, fail fast.
- Server: security, last line of defense.

### PII redaction
- Never log passwords, emails, tokens.
- Redact in middleware.

---

## 3. Coding (30 min)

Add a `redact_pii` function in `backend/app/main.py`:

```python
import re
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"\+?\d[\d\s\-]{7,}\d")

def redact_pii(s: str) -> str:
    s = EMAIL.sub("[REDACTED_EMAIL]", s)
    s = PHONE.sub("[REDACTED_PHONE]", s)
    return s
```

Add a Pydantic validator that limits `note` length:

```python
class FeedbackIn(BaseModel):
    rating: str = Field(pattern="^(up|down)$")
    note: Optional[str] = Field(max_length=500, default=None)
```

### Sample I/O
- Input: `"contact me at john@example.com or +1 555-123-4567"`
- Output: `"contact me at [REDACTED_EMAIL] or [REDACTED_PHONE]"`

### Line-by-line
- `re.sub` replaces matches.
- `Field(max_length=500)` is enforced by Pydantic; 422 on overflow.

---

## 4. Debugging & tests (20 min)

### Bug 1: passwords in logs
**Fix:** redact in middleware; never log raw request bodies.

### Bug 2: HTML in user content
**Fix:** React escapes by default; never use `dangerouslySetInnerHTML`.

### Bug 3: cookies without `SameSite`
**Fix:** set `SameSite=Lax` or `Strict`.

### Bug 4: weak JWT secret
**Fix:** use 256 bits of entropy; never commit to git.

### Test
```python
def test_redact_pii():
    assert redact_pii("a@b.com") == "[REDACTED_EMAIL]"
    assert redact_pii("+1 555-123-4567") == "[REDACTED_PHONE]"

def test_feedback_note_too_long():
    r = client.put("/traces/t001/feedback", json={"rating":"up", "note":"a"*501})
    assert r.status_code == 422
```

---

## 5. Mock interview practice (20 min)

**Q1 — "CSRF?"**
> Forging a request from another site.

**Q2 — "XSS?"**
> Injecting JS via stored user content.

**Q3 — "JWT?"**
> A signed JSON token.

**Q4 — "SameSite?"**
> Cookie attribute preventing cross-site sends.

**Q5 — "What is a secrets manager?"**
> Vault, AWS Secrets Manager; never `.env` in git.

---

## 6. Success criteria check
- [ ] I can write a Pydantic validator with `max_length`.
- [ ] I can redact PII in a string.
- [ ] I can list 4 attack classes.
- [ ] I can test that PII is redacted.

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
**Add a middleware that logs every request with the method, path, status, duration, and redacted PII.**

### Rubric (0–10)
- 0: doesn't compile
- 4: logs method+path
- 6: includes status + duration
- 8: redacts PII
- 10: structured JSON + request id

### Solution
```python
@app.middleware("http")
async def log_requests(request, call_next):
    t0 = time.perf_counter()
    r = await call_next(request)
    ms = int((time.perf_counter()-t0)*1000)
    log.info(json.dumps({"m": request.method, "p": request.url.path, "s": r.status_code, "ms": ms, "rid": str(uuid4())}))
    return r
```

**Time: 90 min**