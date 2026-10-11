# 02_jwt_basics/code — JWT verify demo

A pure-Python + PyJWT demo that signs and verifies a JWT with both
HS256 and RS256, and demonstrates the four common failure modes
(expired, wrong key, missing claim, tampered payload).

## Layout

```
02_jwt_basics/code/
├── README.md
├── jwt_verify.py            ← the demo script
├── test_jwt_verify.py       ← 5 moto-free tests
└── requirements.txt
```

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the demo
python3 jwt_verify.py

# Run the tests
pytest -v
```

Expected test output: **5 passed**.

## What the demo shows

```text
== HS256 ==
  token : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEiLC…
  header: {"alg": "HS256", "typ": "JWT"}
  claims: {"aud": "api.example.com", "exp": …, "iat": …, "iss": "https://auth.example.com",
           "sub": "user-1", "tenant": "acme", "scope": "read"}

== RS256 ==
  token : eyJhbGciOiJSUzI1NiIsImtpZCI6ImFiY2QtMTIzNCIsInR5cCI6IkpXVCJ9.ey…
  header: {"alg": "RS256", "kid": "abcd-1234", "typ": "JWT"}
  claims: {"aud": "api.example.com", "exp": …, "iat": …, "iss": "https://auth.example.com",
           "sub": "user-1", "tenant": "acme", "scope": "admin"}
```

## What the tests cover

| Test | Asserts |
|---|---|
| `test_round_trip_hs256_signs_and_verifies` | sign + verify with HS256, claims intact |
| `test_round_trip_rs256_signs_and_verifies` | sign + verify with RS256, `kid` in header |
| `test_expired_token_rejected` | `exp_in=-10` → `ExpiredSignatureError` |
| `test_wrong_key_rejected` | different HS secret → `InvalidSignatureError` |
| `test_missing_required_claim_rejected` | no `aud` → `MissingRequiredClaimError` |
| `test_tampered_payload_rejected` | flip one byte of payload → `InvalidSignatureError` |

## Notes

- `jwt_verify.py` generates an in-memory RSA keypair on import. In a
  real authorizer you'd load the public key from a JWKS endpoint (see
  L09).
- The HS256 secret is hard-coded for the demo. In a real Lambda it
  would be loaded from `os.environ["JWT_SECRET"]` or AWS Secrets
  Manager.
- See `../lecture_scripts/L10_verifying_in_python.md` for the lecture
  that walks through this code.
