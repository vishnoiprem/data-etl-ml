# Day 14 — Authentication and Security

## 1. Analogy
Auth is a **building pass**. Sessions are temporary wristbands. JWTs are tamper-evident ID cards.

## 2. Technical concept
- **Session cookie:** server stores the session, sends a session ID.
- **JWT:** server signs a token; the token itself contains the claims.
- **CORS:** browser-level access control.
- **CSRF:** cross-site request forgery — mitigated with SameSite cookies + CSRF tokens.
- **Input validation:** reject what we don't expect.

## 3. Why
Internal tools handle user data. A missing check leaks data to the wrong tenant.

## 4. Data flow
Login → set cookie → browser sends cookie on every request → backend validates → returns scoped data.

## 5. Example (input validation)
```python
class FeedbackIn(BaseModel):
    rating: str = Field(pattern="^(up|down)$")
    note: Optional[str] = Field(max_length=500)
```

## 6. Line-by-line
- `pattern` rejects bad ratings.
- `max_length` prevents a user from posting a 1MB note.

## 7. I/O
- `{"rating":"up"}` → 200.
- `{"rating":"meh"}` → 422.
- `{"note":"a" * 1_000_000}` → 422.

## 8. Bugs
- Storing passwords in plain text.
- Logging sensitive data.
- Rendering user content as HTML (XSS).

## 9. Tests
- Assert 422 on bad input.
- Assert 401/403 on missing auth.
- Assert responses never contain passwords.

## 10. Performance
- Bcrypt is slow; use Argon2id in production.
- Cache validated sessions in Redis.

## 11. Five Q&As
1. **What's CSRF?** Forging a request from another site.
2. **What's XSS?** Injecting JS via stored user content.
3. **What's a JWT?** A signed JSON token.
4. **What's SameSite?** A cookie attribute preventing cross-site sends.
5. **What's a secrets manager?** Vault, AWS Secrets Manager — never `.env` in git.

## 12. Coding assignment
Add a `redact_pii` function that masks emails in a string before logging.

## 13. Solution
```python
import re
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
def redact_pii(s: str) -> str:
    return EMAIL.sub("[REDACTED]", s)
```
- 0: doesn't compile
- 4: replaces simple emails
- 6: handles `+` aliases
- 8: handles international TLDs
- 10: also masks phone numbers

**Time: 90 min**