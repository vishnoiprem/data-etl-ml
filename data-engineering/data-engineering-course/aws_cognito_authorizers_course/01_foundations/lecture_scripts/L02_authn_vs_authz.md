---
lecture: L02
title: "Authentication vs Authorization — The Mental Model"
duration: "12:00"
section: 1
prereqs:
  - L01
---

# L02 — Authentication vs Authorization

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 1 — Foundations
> **Duration:** 12:00

## Prereqs

- Watched **L01 — Course Introduction** (recommended).

## Key terms

- **Authentication (AuthN)** — "**Who** are you?" Verifying the
  identity of a principal (user, service, machine). Examples:
  username + password, SMS code, biometric, WebAuthn.
- **Authorization (AuthZ)** — "**What** are you allowed to do?" Deciding
  whether an authenticated principal has the right to perform a given
  action. Examples: RBAC role check, ABAC policy evaluation, scope
  check on a JWT.
- **Principal** — the entity making a request. In Cognito context:
  usually a `sub` claim (user UUID) or an IAM role.
- **Least privilege** — the security principle that a principal should
  have **only** the permissions it needs to do its job and nothing
  more.
- **Bearer token** — a token that anyone who holds it can use. The token
  itself is the credential.

## Lecture

Welcome back. This lecture is the single most important 12 minutes of
the course. The distinction between **authentication** and
**authorization** is so basic that people routinely get it wrong — and
the consequences show up as security incidents, audit findings, and
embarrassing post-mortems. Let me make it impossible to confuse the two.

### The single-sentence test

Ask yourself, in order, of every request that hits your API:

1. **Who is this caller?** → That is **authentication**. If you can't
   answer it, the request must be rejected.
2. **What is this caller allowed to do?** → That is **authorization**.
   If the answer is "nothing", the request must be rejected.

Both questions need a correct answer. Authentication with **no**
authorization means you accept every request from every signed-in user.
Authorization with **no** authentication means you enforce permissions
on anonymous traffic — i.e. you have no idea who's asking.

### A worked example

Imagine a `/orders/{orderId}` endpoint in an e-commerce app. A request
comes in:

```http
GET /orders/o-12345 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJraWQiOiJrLTYz...
```

Five questions your backend has to answer:

1. Is the JWT well-formed? → signature verification (AuthN)
2. Is the JWT's signature valid for our user pool? → signature verification (AuthN)
3. Has the JWT expired? → `exp` claim (AuthN)
4. Was the JWT issued for our app? → `aud` claim (AuthN)
5. Is the user allowed to read order `o-12345`? → ABAC rule (AuthZ)

Questions 1–4 are **authentication**. Question 5 is **authorization**.
If you skip question 5 and return the order based solely on a valid
token, you've just leaked every order in the database to every
signed-in user. This is the exact bug behind several recent high-profile
breaches.

### Where Cognito fits in the mental model

| Step | Cognito's role |
|---|---|
| Sign-up (create credential) | User Pool — `SignUp` API |
| Sign-in (verify credential) | User Pool — `InitiateAuth` API |
| Issue token (post-sign-in) | User Pool — returns `IdToken`, `AccessToken`, `RefreshToken` |
| Validate token on API call | API Gateway **Cognito User Pool Authorizer** OR a Lambda Authorizer |
| Decide "what can this user do?" | **Your** backend code (the AuthZ question) |

Notice that Cognito does **not** answer question 5. Cognito verifies
the token is real and not expired; your backend decides whether the
user is allowed to read *this* order. That separation of concerns is
what makes Cognito a small, well-bounded service — and it's also why
section 5 of this course is mostly about how to **extend** Cognito
with Lambda triggers (so you can encode complex AuthZ in your own code).

### Bearer tokens and why they matter

A Cognito ID token is a **bearer token**: anyone who holds the token
can use it. This is intentional. It means your API doesn't need a
session table or a cookie store — just "did the client send a token
we trust?". But it has a sharp edge: if a token leaks (logs,
referer header, copy-paste to Slack), the holder has full access
until the token expires. Cognito's default ID token TTL is 60 minutes,
so the blast radius is bounded — but it's still 60 minutes of
unauthorized access.

Mitigations:

- **Short access tokens** (5 min) + **silent refresh** with a refresh
  token
- **Audience restriction** so a token for "web app" can't be replayed
  against "mobile app"
- **Rotation** — Cognito supports refresh-token rotation since 2024
- **Sender-constrained tokens** (mTLS, DPoP) — not yet supported by
  Cognito as of 2026

### The four anti-patterns

1. **"We just check `if user is logged in`."** That's authentication,
   not authorization. Every signed-in user can read every other
   user's data.
2. **"We put roles in the JWT and that's our authorization."** It's a
   start, but it's coarse-grained. ABAC (per-resource checks) is
   almost always required for compliance.
3. **"We trust the JWT because it's signed."** Yes, but is the *signer*
   your user pool? A JWT signed by your other app is still a valid
   signature — for that other app.
4. **"Our frontend hides the admin button."** That's UX, not security.
   Every endpoint needs server-side AuthZ.

### Section 1 mental model

By the end of this section (L04) you should be able to read this
sentence and not blink:

> "OAuth 2.0 is an **authorization** delegation framework; OpenID
> Connect adds an **authentication** layer on top; the ID token is a
> signed assertion of identity issued by the OpenID Provider after
> successful authentication; the access token is a bearer
> authorization credential used to call protected APIs."

We'll build that sentence word by word in L03 (OAuth) and L04
(OIDC/JWT).

## Hands-on

No code. Write down, for your current project:

- Which endpoints require authentication?
- Which endpoints require authorization beyond "signed in"?
- Which endpoints have **no** AuthZ today? (Be honest.)

That's your section-5 backlog.

## Quiz prep

For this lecture, focus on:

- Can you distinguish AuthN from AuthZ with one sentence?
- Which of the four anti-patterns is your team most at risk of?
- Where does Cognito fit in the AuthN/AuthZ split?

## Further reading

- OWASP Authentication Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html>
- OWASP Authorization Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
- NIST SP 800-63B (Digital Identity Guidelines): <https://pages.nist.gov/800-63-3/sp800-63b.html>
- `../../downloads/cognito_cheat_sheet.pdf` — pin it.

## What's next

Next up is **L03 — OAuth 2.0**, where we look at the delegation
protocol that powers most "Sign in with X" buttons on the web.