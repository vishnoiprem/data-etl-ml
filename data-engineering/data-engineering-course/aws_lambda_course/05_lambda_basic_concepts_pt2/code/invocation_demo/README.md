# Section 5 — invocation_demo

Companion code for **L21 (AWS Lambda Invocation Model — Hands On)** in
section 5 of the AWS Lambda course.

## Files

| File | Purpose |
|---|---|
| `async_handler.py` | Lambda handler that runs in the background. When invoked with `InvocationType='Event'`, Lambda discards its return value. |
| `sync_handler.py` | Lambda handler that returns a value to the caller. Used with `InvocationType='RequestResponse'`. |
| `invoke_demo.py` | A driver script that demonstrates both invocation models: locally (no AWS) and against a real Lambda function. |
| `test_invoke_demo.py` | pytest suite for the handlers + driver using stdlib `unittest.mock` (no AWS required). |

## Quick start — no AWS needed

```bash
cd 05_lambda_basic_concepts_pt2/code/invocation_demo
python invoke_demo.py local
```

Expected output:

```
=== local sync ===
{
  "sum": 15,
  "count": 5
}
=== local async (return value is discarded by Lambda) ===
{
  "status": "ok",
  "elapsed_ms": 100,
  "job_id": "demo-1"
}
```

## Against real AWS

After deploying both Lambdas (the names below are illustrative):

```bash
python invoke_demo.py sync   my-sync-handler
python invoke_demo.py async  my-async-handler
```

`sync` blocks until the function returns the payload; `async` returns
HTTP 202 immediately with an empty `Payload`.

## Tests

```bash
pytest -q test_invoke_demo.py
```

The tests stub the boto3 Lambda client so no AWS account is needed.
