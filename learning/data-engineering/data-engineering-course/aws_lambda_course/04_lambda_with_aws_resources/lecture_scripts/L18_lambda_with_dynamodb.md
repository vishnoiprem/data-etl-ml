---
l_id: L18
title: AWS Lambda with DynamoDB (Create Table and Put Items)
duration_min: 10.52
prereqs: [L13, L15]
---

# L18 — AWS Lambda with DynamoDB: Create Table and Put Items

> **Author:** Prem Vishnoi &lt;prem.vishnoi.example.com&gt;
> **Section:** 4 — AWS Lambda with S3, EC2, DynamoDB
> **Duration target:** 10:52

## Prereqs

- L13 — the S3 handler pattern (idempotent, structured response,
  region from env). DynamoDB is similar.
- L15 — the paginator pattern, although DynamoDB pagination is
  different and we will only briefly touch it here.

## Key terms

- **DynamoDB table** — a NoSQL key-value store. Every item is a
  map of attributes identified by its *primary key*.
- **Primary key** — either a *partition key* (single attribute,
  `HASH`) or a *composite key* (partition key + sort key,
  `HASH + RANGE`).
- **Attribute types** — `S` (string), `N` (number), `B` (binary),
  `BOOL`, `NULL`, `M` (map), `L` (list), `SS`/`NS`/`BS` (sets).
- **`put_item` vs `update_item`** — `put_item` *replaces* the item
  with the same key (full overwrite). `update_item` is a partial
  update. We use `put_item` in this lecture; the next use case
  (Section 6) uses `update_item` with `if_not_exists`.
- **`ResourceInUseException`** — the `ClientError` code raised when
  you try to create a table that already exists.
- **On-demand vs provisioned** — billing mode. We use
  `PAY_PER_REQUEST` (on-demand) so the demo doesn't need a
  capacity plan.

## Lecture

> "DynamoDB is the third service we point Lambda at. The shape of
> the handler is the same as S3: read from `event`, build a boto3
> client, do the work, return a structured dict. The new
> vocabulary is *primary keys*, *attribute types*, and the
> `ResourceInUseException` error code. We end the lecture with a
> working table and three items in it — ready for Section 6, where
> we replace the synchronous `put_item` with an S3 event-driven
> pipeline."

### The handler

```python
import json
import logging
import os
import time
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def _table_exists(ddb_client, table_name: str) -> bool:
    try:
        ddb_client.describe_table(TableName=table_name)
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
            return False
        raise


def _create_table(ddb_client, table_name: str, partition_key: str = "id") -> str:
    """Create the table (or no-op if it exists). Returns 'created'|'exists'."""
    if _table_exists(ddb_client, table_name):
        return "exists"
    try:
        ddb_client.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": partition_key, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": partition_key, "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ResourceInUseException":
            return "exists"  # race with another invoker
        raise

    # Wait until the table is ACTIVE before returning.
    waiter = ddb_client.get_waiter("table_exists")
    waiter.wait(TableName=table_name)
    return "created"


def _coerce_floats(item: dict) -> dict:
    """DynamoDB rejects native floats; convert to Decimal."""
    out = {}
    for k, v in item.items():
        if isinstance(v, float):
            out[k] = Decimal(str(v))
        else:
            out[k] = v
    return out


def _put_items(ddb_client, table_name: str, items: list[dict]) -> int:
    """Put each item, returning the number of writes performed."""
    written = 0
    for item in items:
        ddb_client.put_item(TableName=table_name, Item=_coerce_floats(item))
        written += 1
    return written


def handler(event, context):
    """Create a DynamoDB table (idempotent) and put items into it.

    Expected event:
        {
          "table_name": "orders",
          "partition_key": "id",                  # optional, default "id"
          "items": [
            {"id": "o-1", "customer": "alice", "total": 19.99},
            {"id": "o-2", "customer": "bob",   "total": 42.00}
          ]
        }
    """
    LOG.info("received event: %s", json.dumps(event, default=str))

    table_name = event["table_name"]
    partition_key = event.get("partition_key", "id")
    items = event.get("items", [])
    region = event.get("region") or os.environ.get("AWS_REGION", "us-east-1")

    ddb = boto3.client("dynamodb", region_name=region)
    table_status = _create_table(ddb, table_name, partition_key)
    written = _put_items(ddb, table_name, items) if items else 0

    LOG.info("table=%s status=%s items_written=%d", table_name, table_status, written)
    return {
        "table": table_name,
        "table_status": table_status,
        "items_written": written,
        "region": region,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = {
        "table_name": "demo-orders",
        "partition_key": "id",
        "items": [
            {"id": "o-1", "customer": "alice", "total": 19.99},
            {"id": "o-2", "customer": "bob",   "total": 42.00},
            {"id": "o-3", "customer": "carol", "total": 7.50},
        ],
    }
    print(handler(sample, None))
    time.sleep(0)  # keep the linter from removing the import
```

### Walkthrough

1. **Why the floats-to-Decimal coercion + TypeSerializer.** DynamoDB
   does *not* accept Python `float` and the low-level *client* API
   (`put_item`) does *not* accept native Python types. There are two
   steps:
   - `_coerce_floats` walks the item dict and converts any `float`
     to `Decimal(str(v))`. The `str(v)` round-trip is important —
     `Decimal(19.99)` actually constructs from a `float` and
     inherits its binary rounding error. `Decimal(str(19.99))` is
     exact. If you skip this step, boto3 raises
     `TypeError: Float types are not supported. Use Decimal types
     instead.`
   - `_serialize_item` then converts the native-Python item into the
     low-level DynamoDB format (`{'S': '...'}`, `{'N': '...'}`, …)
     using `boto3.dynamodb.types.TypeSerializer`. This is what the
     *client* `put_item` API expects. The *resource* API
     (`boto3.resource('dynamodb').Table(name).put_item(...)`) does
     this conversion for you. We use the client + serializer to
     keep the API uniform with the rest of section 4.

2. **`describe_table` for idempotency.** Before we attempt to create
   the table, we check if it already exists. If it does, we skip
   the create and return `"exists"`. We also catch
   `ResourceInUseException` *inside* `create_table` to handle the
   race where two invokers check the table at the same time and
   both decide to create it.

3. **Waiter.** `create_table` returns when the table is in
   `CREATING` state. The `table_exists` waiter polls until the
   status is `ACTIVE`. Without the waiter, a subsequent `put_item`
   could race with the create and fail.

4. **Why no `boto3.resource` here.** You can use
   `boto3.resource("dynamodb")` and write `table.put_item(Item=...)`
   — that API is friendlier and does the Decimal coercion for you.
   We use the `client` here because (a) it's the API every other
   lecture in this section uses and (b) it makes the Decimal
   coercion explicit, which is a thing you need to know about
   *once* before it bites you in production.

5. **Return value.** `table_status` is `"created"` or `"exists"`,
   `items_written` is the count. Useful for tests, useful for
   CloudWatch metrics.

### IAM permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDDB",
      "Effect": "Allow",
      "Action": [
        "dynamodb:CreateTable",
        "dynamodb:DescribeTable",
        "dynamodb:PutItem",
        "dynamodb:ListTables"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/<your-table-name>"
    }
  ]
}
```

`Resource` is scoped to the specific table name. DynamoDB IAM does
*not* support `Resource: "*"` for `PutItem` — every write needs a
specific table ARN.

## Hands-on

```bash
cd 04_lambda_with_aws_resources/code/dynamodb_create
pytest test_script.py -v
```

You should see at least 3 tests:
- `test_handler_creates_table` — happy path, no items
- `test_handler_puts_items_into_new_table` — happy path with items
- `test_handler_is_idempotent_on_existing_table` — second call
  returns `"exists"` and still puts items

## Quiz prep

- DynamoDB rejects Python `float`. Use `Decimal` (or `boto3.resource`
  which coerces for you).
- The primary key can be a partition key alone (HASH) or a
  partition + sort key composite (HASH + RANGE).
- `ResourceInUseException` means the table already exists. Treat
  it as success for idempotency.
- The waiter for a table being created is `table_exists` (not
  `table_active`).

## Further reading

- AWS docs: [CreateTable API](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_CreateTable.html)
- AWS docs: [PutItem API](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_PutItem.html)
- AWS docs: [DynamoDB data types](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html)
- `code/dynamodb_create/README.md`
- `code/dynamodb_create/create_table_put_items.py` — the full module

## Section 4 wrap-up

> "That's the section. Six handlers, one wrapper, one IAM permission
> set per service. In Section 5 we go back to Lambda theory —
> invocation model and the timeout limit. In Section 6 we take the
> S3 and DynamoDB pieces and wire them into a real pipeline: a bank
> drops a JSON file in S3, a Lambda picks it up, parses it, and
> writes the rows into DynamoDB. The handlers you wrote in L13 and
> L18 are 80% of that pipeline."
