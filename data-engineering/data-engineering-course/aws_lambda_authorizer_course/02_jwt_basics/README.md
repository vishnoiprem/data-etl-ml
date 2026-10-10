# Section 2 — JWT Basics (L05–L10)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** 6 (~88 min)
> **Working code:** `code/jwt_verify.py` + `test_jwt_verify.py` (5 moto-free tests)

This section builds the JWT foundation the rest of the course depends
on. By the end you'll be able to:

- decode a JWT by hand (header, payload, signature);
- name the seven standard claims and what each one is for;
- pick the right signing algorithm for the job (HS256 vs RS256);
- explain how JWKS rotation works;
- verify a JWT in pure Python with `pyjwt`.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L05 | Section Overview — Why JWTs | 4:00 | `lecture_scripts/L05_section_overview.md` |
| L06 | JWT Structure — Header, Payload, Signature (base64url) | 14:00 | `lecture_scripts/L06_jwt_structure.md` |
| L07 | Standard Claims — iss, sub, aud, exp, nbf, iat, jti | 16:00 | `lecture_scripts/L07_standard_claims.md` |
| L08 | Signing Algorithms — HS256 (HMAC) vs RS256 (RSA) | 16:00 | `lecture_scripts/L08_signing_algorithms.md` |
| L09 | JWK and JWKS — Rotating Public Keys | 18:00 | `lecture_scripts/L09_jwks_rotation.md` |
| L10 | Verifying a JWT in Pure Python (pyjwt) | 20:00 | `lecture_scripts/L10_verifying_in_python.md` |

## Working code

The hands-on lab lives in `code/`:

```
02_jwt_basics/code/
├── README.md
├── jwt_verify.py        # generate RSA keypair, sign + verify a JWT
├── test_jwt_verify.py   # 5 moto-free tests
└── requirements.txt
```

Run:

```bash
cd 02_jwt_basics/code
pip install -r requirements.txt
python -m pytest test_jwt_verify.py -v
```

Expected: **5 passed**.

## Conventions

- Every lecture follows **Prereqs → Key terms → Lecture → Hands-on →
  Quiz prep → Further reading**.
- The quiz for this section is in `../quizzes/section_2.md`.
- All code uses **PyJWT 2.8+** and **`cryptography` 42+** for RS256
  and ES256 support.
