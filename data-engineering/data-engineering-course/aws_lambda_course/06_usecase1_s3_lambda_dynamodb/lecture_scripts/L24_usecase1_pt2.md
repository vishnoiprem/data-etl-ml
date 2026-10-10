# L24 — Enterprise Use Case using S3, AWS Lambda and DynamoDB — Part 2

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 06 — Enterprise Use Case 1
> **Duration:** 8:27
> **Prereqs:** L23 (architecture, data model, IAM role, S3 event notification)

## What you will learn

By the end of this lecture you will be able to:

1. read the `s3_to_dynamodb_lambda.handler` line by line and explain what
   each block does;
2. describe how the handler makes DynamoDB writes **idempotent** using
   `ConditionExpression`;
3. identify the three error paths (malformed record, S3 read failure,
   DynamoDB write failure) and how the handler reports them;
4. read structured JSON CloudWatch logs and pull a per-invocation trace
   with a single `parse` query;
5. run the `moto`-backed test suite locally and explain each of the three
   tests.

## Key terms

- **`boto3.resource` vs `boto3.client`** — the resource API is
  higher-level and returns native Python objects (`Table.put_item(Item=...)`);
  the client API is the 1-to-1 mapping of the AWS JSON API. We use
  `resource` for the write, `client` for `GetObject`.
- **`Decimal`** — DynamoDB does not accept Python `float`. You must wrap
  any decimal number in `boto3.dynamodb.types.Decimal` (or a plain
  `decimal.Decimal` constructed from a string) before sending.
- **`ConditionalCheckFailedException`** — the error DynamoDB returns when
  a write-time condition fails. In our pipeline this is the *expected*
  way to detect a duplicate.
- **Structured logging** — emitting `json.dumps({...})` from `logging`
  so each log line is a queryable record, not a free-form string.

## The handler, top to bottom

The full source is at `code/lambda_function/s3_to_dynamodb_lambda.py`. We
walk through it in five blocks.

### Block 1 — module-level setup

```python
TABLE_NAME = os.environ.get("TABLE_NAME", "transactions")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(TABLE_NAME)
```

Two important idioms here.

First, **configuration via environment variables**. The table name and
log level are *not* hard-coded in the handler. They are environment
variables on the function configuration (set in the console or in your
IaC). That way the same code runs in `dev`, `staging` and `prod` with
different targets.

Second, **boto3 clients are built once, at import time**. boto3 clients
are thread-safe and Lambda re-uses the same container across
invocations, so building them once is both faster and idiomatic. If you
re-`boto3.resource(...)` inside the handler, you are paying a TLS
handshake and a credential lookup on every invocation for no reason.

### Block 2 — the `_log_event` helper

```python
def _log_event(level, event, **fields):
    payload = {"event": event, **fields}
    logger.log(level, json.dumps(payload, default=str))
```

Every log line we emit is a JSON object with at least an `event` key
identifying *what kind of thing happened* (`record.persisted`,
`record.duplicate`, `invoke.start`, ...). The `**fields` capture
*per-event details* (request id, transaction id, error code, ...).

The payoff is in CloudWatch Logs Insights. Instead of grepping a soup
of free-form strings, you can run:

```
fields @timestamp, event, transaction_id, error
| filter event = "record.persisted"
| sort @timestamp desc
| limit 20
```

…and get the last 20 successful writes as a table. The
`json.dumps(..., default=str)` is what lets us pass a `Decimal` (or any
non-JSON-native type) without crashing.

### Block 3 — the handler signature and the outer loop

```python
def handler(event, context):
    request_id = getattr(context, "aws_request_id", "local")
    _log_event(logging.INFO, "invoke.start",
               request_id=request_id,
               record_count=len(event.get("Records", [])))

    processed = skipped = errors = 0
    for record in event.get("Records", []):
        ...
```

The handler is invoked once per S3 event, but each event can contain
*multiple* `Records` (S3 batches up to ~100 events per Lambda
invocation when you turn on batching, though we will not use that in
this section). The loop iterates each record independently and
accumulates a single summary at the end. This is what lets one Lambda
invocation process, say, 3 files at once and still return one tidy
result.

`getattr(context, "aws_request_id", "local")` lets the same function
work under `moto` and `pytest` (where `context` is a `MagicMock` or
`None`) without special-casing tests.

### Block 4 — the inner per-record flow

For each record we:

1. **extract the bucket and key** from the S3 event payload;
2. **`GetObject`** the JSON file from S3 (we use the low-level client
   because `get_object` returns a streaming body — we `read().decode`
   the body once and parse it);
3. **validate the payload shape** — the top-level object must have a
   `transactions` key holding a list;
4. **iterate each transaction**:
   - if `transaction_id` is missing, increment `skipped` and continue
     (we do *not* raise — one bad row must not fail the whole batch);
   - else call `_table.put_item(...)` with the idempotency condition.

```python
_table.put_item(
    Item=_coerce_for_dynamodb(tx),
    ConditionExpression="attribute_not_exists(transaction_id)",
)
```

This is the heart of the lecture. The `ConditionExpression` tells
DynamoDB: "perform this write *only if* there is no item with this
`transaction_id` already." Two consequences:

- on the first call for a given id, the condition succeeds, the row is
  written, and `processed` goes up by one;
- on any subsequent call for the same id (S3 retry, duplicate upload,
  your own retry loop), the condition fails, DynamoDB raises
  `ConditionalCheckFailedException`, and we log `record.duplicate`
  without incrementing `errors`.

That is **at-least-once delivery turned into effectively-once writes**.
You can re-run the function a thousand times against the same event and
the table ends up with exactly the rows that were in the file.

### Block 5 — the return value

```python
summary = {"processed": processed, "skipped": skipped, "errors": errors}
_log_event(logging.INFO, "invoke.done", request_id=request_id, **summary)
return summary
```

We return the summary, and we also log it. The summary is the
**asynchronous invoke response** if you wire the function up to anything
downstream; the log line is the human/operator view.

The `errors` counter only goes up for *unexpected* failures (S3 read
error, JSON parse error, unknown DynamoDB error). A skipped row
(missing `transaction_id`) and a duplicate row (`ConditionalCheckFailed`)
are both *expected* outcomes, not errors. Conflating them is how
on-call pages go off at 3 a.m. for healthy pipelines.

## Idempotency, in one paragraph

S3 event notifications are at-least-once. So is any retried HTTP call.
So is the processor itself if a human at the bank hits "replay" on the
SFTP drop. The function will be invoked more than once for the same
file, period. The only correct way to write to DynamoDB from such a
source is with a write-time guard, and `attribute_not_exists` on the
partition key is the cheapest, fastest guard there is. The test in
`test_s3_to_dynamodb_lambda.py::test_handler_is_idempotent` runs the
handler twice against the same event and asserts the row count is
unchanged — that is the contract we ship to the bank.

## Reading the CloudWatch logs

After a real run, open CloudWatch → Log groups →
`/aws/lambda/s3_to_dynamodb_lambda` → the most recent log stream. You
will see one line per call to `_log_event`, all valid JSON. The most
useful queries in Logs Insights:

| Question | Query |
|---|---|
| "How many rows did the last run write?" | `stats sum(if(event = "record.persisted", 1, 0))` |
| "What failed in the last hour?" | `filter event = "invoke.done" and errors > 0 \| fields @timestamp, processed, skipped, errors` |
| "Has this transaction id ever been seen?" | `filter transaction_id = "TXN-1001" \| fields @timestamp, event` |
| "Trace one invocation end-to-end" | `filter request_id = "<id-from-summary>" \| sort @timestamp asc` |

The third query is the one you reach for during an incident. A
customer calls and says "my transaction is missing"; you grab the
`transaction_id` from their statement, paste it into the query, and
in 5 seconds you can see whether the file ever arrived, whether the
row was persisted, or whether it was a duplicate.

## The test suite, in plain English

`code/lambda_function/test_s3_to_dynamodb_lambda.py` has three tests
and they collectively prove the design works:

1. **`test_handler_persists_every_record`** — the happy path. We create
   a moto S3 bucket, drop the sample file in it, create a moto DynamoDB
   table with the same key schema as production, and invoke the handler
   with a synthetic S3 event. We assert the summary is
   `{processed: 5, skipped: 0, errors: 0}` and that all five
   `transaction_id`s are now in the table.

2. **`test_handler_is_idempotent`** — we invoke the handler *twice*
   with the same event. The first call writes five rows; the second
   call sees all five `ConditionalCheckFailed` responses (logged as
   `record.duplicate`), writes nothing, and the table still has
   exactly five rows. This is the only test that proves the design's
   most important property.

3. **`test_handler_skips_rows_missing_transaction_id`** — we upload a
   small file with three records, one of which has no `transaction_id`.
   The handler writes the two valid rows, logs `record.skipped` for
   the bad one, and the summary is `{processed: 2, skipped: 1, errors: 0}`.

The whole suite runs in under a second and requires no AWS account,
no Docker, no SAM. You can wire it into a pre-commit hook.

Run it:

```bash
cd code/lambda_function
pip install boto3 moto pytest
pytest -v
```

Expected output:

```
test_handler_is_idempotent PASSED
test_handler_persists_every_record PASSED
test_handler_skips_rows_missing_transaction_id PASSED
3 passed
```

## Hands-on

You have two options for this lecture. Pick the one that matches your
time budget.

**Option A — 10 min: just run the tests.**

```bash
cd 06_usecase1_s3_lambda_dynamodb/code/lambda_function
python -m venv .venv && source .venv/bin/activate
pip install boto3 moto pytest
pytest -v
```

If the three tests pass, the handler is correct against the spec. Move
on.

**Option B — 45 min: full deploy to your AWS account.**

Follow `code/deploy_notes.md` "Path A" end-to-end. Create the DynamoDB
table, the S3 bucket, the IAM role, the Lambda function, and the event
notification. Then upload `sample_transactions.json` to the `raw/`
prefix and watch the CloudWatch log stream fill with the JSON lines
described above.

## Quiz prep

- Why do we build the boto3 client at import time, not inside the
  handler?
- What is the difference between `s3:GetObject` on the bucket vs on a
  specific prefix ARN? Why does the IAM policy scope to the prefix?
- What happens if a record is missing `transaction_id`? Why do we
  increment `skipped` and not `errors`?
- What is the `boto3.resource` / `boto3.client` distinction in this
  function, and why do we use both?
- Why is `attribute_not_exists` cheaper than a "read then write" check
  for idempotency?
- A row gets a `ConditionalCheckFailedException`. Is that an error?
  How do we tell?
- You see `record.duplicate` in the logs but no row was added. Is the
  pipeline broken? What do you check first?

## Further reading

- AWS docs: [Handling errors and exceptions in AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/python-exceptions.html)
- AWS docs: [DynamoDB conditional writes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)
- AWS docs: [Querying CloudWatch Logs using Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- `code/lambda_function/s3_to_dynamodb_lambda.py` — the full handler
- `code/lambda_function/test_s3_to_dynamodb_lambda.py` — the test suite
- `code/deploy_notes.md` — full deploy steps for the console and boto3
