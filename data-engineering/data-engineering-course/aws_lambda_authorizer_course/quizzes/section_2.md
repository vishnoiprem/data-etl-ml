# Section 2 Quiz — JWT Basics

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** How many parts does a JWT have, separated by dots?

- A. 1
- B. 2
- C. 3
- D. 4

<details><summary>Show answer</summary>

**C — 3.** Header, payload, signature. The format is
`header.payload.signature`, with each part base64url-encoded.

</details>

---

**Q2.** Which of the following is **not** an RFC-defined standard
("registered") claim?

- A. `iss`
- B. `sub`
- C. `tenant`
- D. `exp`

<details><summary>Show answer</summary>

**C — `tenant`.** The seven registered claims are `iss`, `sub`,
`aud`, `exp`, `nbf`, `iat`, and `jti`. `tenant` is a custom claim
you'd add for your own application.

</details>

---

**Q3.** Is a JWT encrypted?

- A. Yes, by default
- B. Yes, but only with the recipient's public key
- C. No — it is signed, not encrypted
- D. Only if the issuer sets a `enc` flag in the header

<details><summary>Show answer</summary>

**C — No — it is signed, not encrypted.** The payload is base64-
encoded (so it's readable to anyone who has the token), and the
signature proves the issuer minted it. To carry secrets you need
JWE, which is a separate spec.

</details>

---

**Q4.** In `pyjwt`, how do you pin the algorithm to prevent the
`alg: none` attack?

- A. `jwt.decode(token, key, verify=True)`
- B. `jwt.decode(token, key, algorithms=["RS256"])`
- C. `jwt.decode(token, key, allow_none=False)`
- D. PyJWT pins it automatically

<details><summary>Show answer</summary>

**B — `jwt.decode(token, key, algorithms=["RS256"])`.** Without
the `algorithms` argument, PyJWT will infer the algorithm from
the token's `alg` header, opening the door to `alg: none` and
algorithm-confusion attacks.

</details>

---

**Q5.** What's the difference between HS256 and RS256?

- A. HS256 is faster but the verifier needs the same secret as the issuer; RS256 is slower but the verifier only needs the public key
- B. HS256 is RSA-based; RS256 is HMAC-based
- C. HS256 is for HTTP; RS256 is for REST
- D. There is no difference — the names are aliases

<details><summary>Show answer</summary>

**A — HS256 is symmetric (same secret signs and verifies); RS256
is asymmetric (private signs, public verifies).** HS256 is fast
but requires the verifier to hold the signing secret, which makes
it unsuitable for federated systems.

</details>

---

**Q6.** What does the `kid` field in a JWT header mean?

- A. The token's expiration date
- B. The user id of the subject
- C. The key id used to look up the right public key in a JWKS
- D. A nonce that prevents replay attacks

<details><summary>Show answer</summary>

**C — The key id used to look up the right public key in a JWKS.**
When the issuer has multiple signing keys (e.g. during a
rotation), `kid` tells the verifier which public key to use.

</details>

---

**Q7.** What does the `aud` claim identify?

- A. The audience (recipient) of the token
- B. The author who wrote the token
- C. The authentication protocol used
- D. The token's audit trail

<details><summary>Show answer</summary>

**A — The audience (recipient) of the token.** The `aud` claim
should name your API. Your authorizer should reject tokens whose
`aud` doesn't include you.

</details>

---

**Q8.** What is a JWKS?

- A. A JSON Web Key Set — a JSON document with a `keys` array of public keys
- B. A Java Web Key Store
- C. A JWT Working Key Specification
- D. A JSON Web Key Signature

<details><summary>Show answer</summary>

**A — A JSON Web Key Set.** The issuer publishes its public keys
at a stable URL so verifiers can fetch them. The format is
`{"keys": [ {JWK}, {JWK}, … ]}`.

</details>

---

**Q9.** In a JWT, what is the `exp` claim?

- A. The expected lifetime, in seconds, of the token
- B. The exact UTC timestamp (numeric date) when the token expires
- C. The expiration policy name
- D. The encryption algorithm

<details><summary>Show answer</summary>

**B — The exact UTC timestamp (numeric date) when the token
expires.** Numeric date = seconds since 1970-01-01 00:00:00 UTC.
PyJWT raises `ExpiredSignatureError` when the current time is
past `exp`.

</details>

---

**Q10.** What does `options={"require": ["exp", "iat", "iss", "sub", "aud"]}` do in
`jwt.decode`?

- A. Adds the listed claims if they're missing
- B. Requires the listed claims to be present in the token, raising `MissingRequiredClaimError` if any is missing
- C. Lists the algorithms the token may use
- D. Hints to the verifier to skip the listed claims

<details><summary>Show answer</summary>

**B — Requires the listed claims to be present.** Without this
list, a token with no `exp` claim is treated as one that never
expires.

</details>

---

**Q11.** What is the algorithm-confusion attack?

- A. A token signed with HS256 but verified as RS256, using the public key as the HMAC secret
- B. A token whose algorithm is mislabeled in the header
- C. An attack against the `alg: none` case
- D. A replay attack that confuses the verifier about the request order

<details><summary>Show answer</summary>

**A — A token signed with HS256 but verified as RS256, using the
public key as the HMAC secret.** The fix is to pin the algorithm
in `jwt.decode(algorithms=[...])`.

</details>

---

**Q12.** How often should you cache a JWKS in your authorizer?

- A. Forever — the keys never change
- B. For at most a few minutes
- C. For at most a day (so you pick up rotations within 24 h)
- D. Only at cold start, never refresh

<details><summary>Show answer</summary>

**C — For at most a day.** Most IdPs rotate keys every 30 days.
A 24-hour cache means you pick up rotations within 24 h. Shorter
is fine but adds load; longer is risky.

</details>
