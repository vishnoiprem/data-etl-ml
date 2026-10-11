# 04_policy_cache/code — REQUEST Lambda Authorizer with Policy Cache

A reference implementation of a **REQUEST-based** Lambda Authorizer
that:

1. Reads `user` and `token` from the query string
   (`?user=alice&token=xyz`).
2. Caches the resulting policy in an in-process LRU keyed by
   `(user, token)` with TTL.
3. Returns an `Allow` policy on hit, an `Allow` policy on miss
   (after token verification), and a `Deny` policy on missing
   params or bad token.

The handler ships a `TTLCache` class — a thread-safe LRU with
per-entry TTL — that you can lift and use elsewhere.

## Layout

```
04_policy_cache/code/
├── README.md
├── param_authorizer.py           ← the function code + TTLCache class
├── test_param_authorizer.py      ← 4+ moto-free unit tests
└── requirements.txt
```

## Run the tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

Expected: **4+ passed**.

## What the tests cover

| Test | Asserts |
|---|---|
| `test_valid_params_return_allow` | `?user=alice&token=valid-alice-token` → `Effect: Allow` |
| `test_missing_user_returns_deny` | no `user` → `Effect: Deny` |
| `test_missing_token_returns_deny` | no `token` → `Effect: Deny` |
| `test_wrong_token_returns_deny` | wrong token → `Effect: Deny` |
| `test_cache_key_built_from_user_and_token` | cache key = `f"{user}|{token}"` |
| `test_cache_hit_skips_verification` | second identical request reuses the cached policy |
| `test_ttl_applied_to_cached_policy` | entry expires after TTL |
| `test_lru_evicts_oldest_when_full` | least-recently-used eviction works |
| `test_cache_is_thread_safe` | cache survives multi-threaded hammering |

## Environment variables

| Name | Default | Purpose |
|---|---|---|
| `CACHE_TTL_SECONDS` | `300` | per-entry TTL for the internal cache |
| `CACHE_MAX_SIZE` | `1024` | max number of cache entries |
| `EXPECTED_TOKENS` | demo dict | JSON-encoded `{"user": "token", …}` |

## See also

- [`../lecture_scripts/L20_end_to_end.md`](../lecture_scripts/L20_end_to_end.md)
  — the lecture that walks through this code.
- `../lecture_scripts/L19_lru_cache_ttl.md` — the cache design.