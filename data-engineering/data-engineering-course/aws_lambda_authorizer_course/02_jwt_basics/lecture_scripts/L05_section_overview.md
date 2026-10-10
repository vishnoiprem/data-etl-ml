---
lecture: L05
title: "Section Overview — Why JWTs"
duration: "4:00"
section: 2
prereqs: ["L04"]
---

# L05 — Section Overview — Why JWTs

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 2 — JWT Basics
> **Duration:** 4:00

## Prereqs

- L04 — IAM policy anatomy.

## Key terms

- **JWT (JSON Web Token)** — a compact, URL-safe string of three
  base64url-encoded JSON parts separated by dots. Defined in
  [RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519).
- **`Bearer` token** — the conventional way to carry a JWT in an HTTP
  `Authorization` header. The server doesn't care that the token is a
  JWT; it cares that the *bearer* of the token is allowed in.
- **Stateless authentication** — the alternative to a server-side
  session. The token itself encodes the identity and (often) the
  authorization, so the API doesn't need to look anything up in a
  database to know who the caller is.
- **`pyjwt`** — the de-facto Python library for signing and verifying
  JWTs. We use it throughout this course.

## Lecture

A Lambda Authorizer is a function that **verifies a token and returns
a policy**. To write that function you first need to understand what
a token *is*. This section is the deep dive on that single question.

In the next six lectures we cover:

- **L06 — JWT structure** — what the three dot-separated parts are and
  what each one contains.
- **L07 — Standard claims** — the seven RFC-defined claims every JWT
  should have and what each one means.
- **L08 — Signing algorithms** — HS256 vs RS256 vs ES256; the security
  trade-offs; when to pick which.
- **L09 — JWKS rotation** — how to verify a token signed by a key
  you've never seen before (and how to roll keys without downtime).
- **L10 — Verifying in Python** — the working demo. Generate a keypair,
  sign a JWT, verify it, decode the payload, reject expired and
  tampered tokens.

By the end of L10 you'll have a script that can replace a third-party
JWT library in a pinch, and you'll understand enough about JWTs to
debug a real-world verification failure.

### Why JWTs won

You might ask: why not just encrypt the user id and put it in a
cookie? Two reasons:

1. **Verification is local.** A JWT is *signed*, not *encrypted* —
   the payload is base64-encoded, not scrambled. The recipient
   doesn't need to call back to the issuer; the signature alone
   proves the issuer minted the token. This matters at the edge
   (CloudFront Lambda@Edge, section 5) where round-trips to the
   issuer are expensive.
2. **The payload is portable.** Because the claims are just JSON, any
   service in any language can read them. A JWT minted by an
   Express.js auth service can be verified by a Python Lambda
   Authorizer, a Go micro-service, or a CloudFront edge function
   with no shared library other than a base64 decoder.

### Why JWTs are tricky

The same properties that make JWTs powerful make them dangerous:

- **The payload is *visible* to anyone who intercepts the token.** A
  JWT is *signed*, not *encrypted*. Don't put secrets in claims
  (no passwords, no API keys, no PII).
- **`alg: none` is a real attack.** Older libraries would honor an
  unsigned token if the header said `alg: none`. Always pin the
  algorithm you expect, never let the token choose.
- **Compromise of a signing key is a compromise of every token
  signed with it.** HS256 with a shared secret is a single point of
  failure; RS256 with key rotation is more forgiving.

These are the failure modes L08 and L09 are designed to keep you out
of.

## Hands-on

No code yet. Just install the libraries we'll use throughout the
section:

```bash
pip install 'pyjwt>=2.8.0' 'cryptography>=42.0'
```

## Quiz prep

- Is a JWT encrypted? (No, only signed — the payload is readable.)
- What's the single biggest rule for the `alg` header? (Pin it.
  Never let the token choose.)
- How many sections of this lecture are conceptual vs hands-on?
  (5 conceptual, 1 hands-on.)

## Further reading

- Download: [`../../downloads/jwt_cheat_sheet.pdf`](../../downloads/jwt_cheat_sheet.pdf)
- RFC 7519 — the JWT spec.

## What's next

**L06 — JWT Structure** — we crack open a real token and look at the
three parts.
