# Section 1 — Foundations (L01–L04, ~50 min)

Welcome to **AWS Cognito Authorizers — Crash Course**. Section 1 is the
theoretical spine of the entire course. We don't touch AWS once in these
50 minutes — instead we lock down the four mental models every API
security engineer must internalize before they ever call `boto3`:

1. **Authentication vs Authorization** — they are different verbs with
   different security implications.
2. **OAuth 2.0** — the delegation protocol that powers "Sign in with
   Google" on half the apps you use.
3. **OpenID Connect** — the identity layer on top of OAuth 2.0.
4. **JWT** — the token format that ties everything together.

| L# | Title | Min |
|---|---|---|
| L01 | Course Introduction & Why Cognito | 8 |
| L02 | Authentication vs Authorization — The Mental Model | 12 |
| L03 | OAuth 2.0 — Roles, Flows & Tokens | 15 |
| L04 | OpenID Connect (OIDC) & JWTs | 15 |

By the end of section 1 you should be able to read any "Sign in with
X" prompt on a third-party app and trace, in your head, exactly which
protocol is being used and which party holds which token.