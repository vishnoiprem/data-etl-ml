# Section 3 — Simple Token-Based Lambda Authorizer (L11–L15)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Lectures:** 5 (~84 min)
> **Working code:** `code/token_authorizer.py` + `test_token_authorizer.py` (6 moto-free tests)

This is the section where everything from sections 1 and 2 comes
together. You take the JWT verifier from `02_jwt_basics/code/`,
wrap it in a Lambda handler, and return an IAM policy document that
API Gateway accepts.

By the end you'll be able to:

- read an API Gateway TOKEN authorizer event;
- verify the token against `iss`, `aud`, `exp`;
- build the `Allow` policy document with the right `Resource` and
  `Action`;
- return claims through the `context` map;
- test the whole handler with `pytest` (no moto needed).

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L11 | Section Overview — TOKEN Authorizer Event Shape | 6:00 | `lecture_scripts/L11_section_overview.md` |
| L12 | The API Gateway TOKEN Event (authorizationToken, methodArn, type) | 14:00 | `lecture_scripts/L12_token_event_shape.md` |
| L13 | Building the Allow Policy (Resource = methodArn, Action = execute-api:Invoke) | 16:00 | `lecture_scripts/L13_allow_policy.md` |
| L14 | Returning Claims via the `context` Map | 14:00 | `lecture_scripts/L14_context_map.md` |
| L15 | End-to-End: TOKEN Authorizer with HS256 JWT | 34:00 | `lecture_scripts/L15_end_to_end.md` |

## Working code

The hands-on lab lives in `code/`:

```
03_simple_authorizer/code/
├── README.md
├── token_authorizer.py        ← reference handler
├── test_token_authorizer.py   ← 6 moto-free tests
└── requirements.txt
```

Run:

```bash
cd 03_simple_authorizer/code
pip install -r requirements.txt
pytest -v
```

Expected: **6 passed**.

## Conventions

- Every lecture follows **Prereqs → Key terms → Lecture → Hands-on →
  Quiz prep → Further reading**.
- The quiz for this section is in `../quizzes/section_3.md`.