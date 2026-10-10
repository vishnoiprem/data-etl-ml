# Section 4 — Request-Parameter Authorizer & Policy Caching (L16–L20)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Lectures:** 5 (~88 min)
> **Working code:** `code/param_authorizer.py` + `test_param_authorizer.py` (4+ moto-free tests)

Section 4 is where you graduate from "authorize a single bearer
token" to "authorize a request that may have identity in the
header, the query string, stage variables, or all three at once."
This is the **REQUEST** authorizer type, and the big new idea is
**policy caching** — making the Lambda run once for many requests.

By the end you'll be able to:

- read an API Gateway REQUEST authorizer event;
- build a multi-IdentitySource cache key;
- implement a thread-safe LRU cache with a TTL;
- reason about the trade-off between cache duration and stale-token
  exposure;
- test the whole thing with `pytest`.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L16 | Section Overview — Why a Request Authorizer | 6:00 | `lecture_scripts/L16_section_overview.md` |
| L17 | The API Gateway REQUEST Event (headers, query, stage vars, body) | 18:00 | `lecture_scripts/L17_request_event_shape.md` |
| L18 | IdentitySource, Multi-Identity-Source & ReauthorizeEvery | 20:00 | `lecture_scripts/L18_identity_source_cache.md` |
| L19 | Building an LRU Cache with TTL (time-bounded, thread-safe) | 24:00 | `lecture_scripts/L19_lru_cache_ttl.md` |
| L20 | End-to-End: REQUEST Authorizer with Policy Cache | 20:00 | `lecture_scripts/L20_end_to_end.md` |

## Working code

The hands-on lab lives in `code/`:

```
04_policy_cache/code/
├── README.md
├── param_authorizer.py          ← reference handler + LRU cache
├── test_param_authorizer.py     ← 4+ moto-free tests
└── requirements.txt
```

Run:

```bash
cd 04_policy_cache/code
pip install -r requirements.txt
pytest -v
```

Expected: **4+ passed**.

## Conventions

- Every lecture follows **Prereqs → Key terms → Lecture → Hands-on →
  Quiz prep → Further reading**.
- The quiz for this section is in `../quizzes/section_4.md`.