# api_pt3_handlers

Unified Lambda handler that serves both `GET` and `DELETE` on the
`/{proxy+}` resource from L31/L32. Closes out Use Case 2 by collapsing
the "one Lambda per verb" pattern from L31 into the "one Lambda per
resource" pattern that real APIs use.

## What this unifies

| Lecture | Lambda              | Verb(s)               |
|---------|--------------------|-----------------------|
| L31     | `api_get_object`   | `GET /{proxy+}`       |
| L31     | `api_put_object`   | `POST /{proxy+}`      |
| L32     | (refactor of L31)  | `GET` with `?key=`    |
| L31a   | `api_objects`      | `GET`, `DELETE`       |

In other words, `api_objects` is the unified "read/delete" handler
for `/{proxy+}`. The `POST` verb stays on `api_put_object` from L31
because the request/response shapes are different (binary vs. JSON
body, base64 decoding). You can collapse further if you want, but a
read-only handler is cleaner to reason about for the security
lectures in section 9.

## Files

- `lambda_function.py` — unified handler.
- `test_lambda_function.py` — `moto.mock_aws`-backed pytest suite
  (8 tests, runs offline).

## Run the tests

```bash
cd code/api_pt3_handlers
python -m pytest -v
```

All eight tests should pass without an AWS account. They cover GET 200,
GET 404, DELETE 204, DELETE 404, the 4xx/5xx split, the query-string
wins-over-path precedence from L32, the 400 for missing key, and CORS
headers on every response.

## Deploy

The handler expects the following environment variable:

| Name         | Required | Example                  |
|--------------|----------|--------------------------|
| `BUCKET_NAME`| yes      | `usecase2-objects-prem`  |

The Lambda's execution role needs (extending the L31 policy):

```json
{
  "Action": ["s3:GetObject", "s3:DeleteObject"],
  "Resource": "arn:aws:s3:::<BUCKET_NAME>/*",
  "Effect": "Allow"
}
```

## API Gateway wiring

Two methods on the same `/{proxy+}` resource, both pointing at this
single function:

| Method   | Integration type        | Lambda       |
|----------|-------------------------|--------------|
| `GET`    | Lambda Proxy Integration | `api_objects`|
| `DELETE` | Lambda Proxy Integration | `api_objects`|
| `OPTIONS`| Mock                    | (none)       |

The `OPTIONS` method is the CORS preflight — answer it with the same
three `Access-Control-Allow-*` headers the handler already emits, and
redeploy. With that in place, browsers will be able to call `GET` and
`DELETE` cross-origin without the Lambda being invoked twice.

## Why one handler for two verbs?

Three reasons:

1. **Smaller deployable.** One function, one IAM role, one alarm. The
   two methods share 80% of their code anyway (the "resolve the key"
   and "map errors to status codes" logic).
2. **Easier to secure.** When we add the Lambda Authorizer in L36–L37,
   we only have to add one invoke permission to one function.
3. **Cleaner CloudWatch.** A single log group means a single metric
   filter for "5xx rate" instead of two per-verb ones.

The pattern generalises: if you find yourself adding a third verb
(`HEAD`, `LIST`, …), keep it in the same handler until the file
crosses ~150 lines, then extract.