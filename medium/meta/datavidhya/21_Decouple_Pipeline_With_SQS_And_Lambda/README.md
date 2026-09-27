# 21 — Decouple a Pipeline with SQS and Lambda

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Decouple a Pipeline with SQS and Lambda."** Seven stages, eight shell
scripts that map exactly to the lab's "click in the console" instructions,
plus a pytest suite that drives the same in-memory SQS simulator. No
AWS credentials needed for verification.

```
                        ┌──────────────────────────────────┐
                        │       orders-main-queue (SQS)      │
                        │     redrivePolicy(maxReceiveCount=3)
                        └───────────────┬────────────────────┘
                                        │
                                        │  batched poll (batch=5)
                                        ▼
                        ┌──────────────────────────────────┐
                        │   orders-consumer-q21 (Lambda)    │
                        │     app.lambda_handler:            │
                        │       validate(order)              │
                        │         OK    -> ack (delete)       │
                        │         FAIL  -> raise (retry)      │
                        └───────────────┬────────────────────┘
                                        │   on 4th failure
                                        ▼
                        ┌──────────────────────────────────┐
                        │           orders-dlq               │
                        │     (parked poison messages,       │
                        │      ReceiveCount reset to 1)       │
                        └──────────────────────────────────┘
```

## Files

| Path                                                | Purpose                                  |
|-----------------------------------------------------|------------------------------------------|
| `lambda_function/app.py`                            | The Lambda handler the ESM invokes       |
| `sqs_stub.py`                                       | In-memory SQS + event-source-mapping simulator |
| `sample_data/orders.json`                           | 8 good orders + 2 poison messages       |
| `01_decouple_pipeline_with_sqs_and_lambda.py`       | Self-asserting driver (7 stages, 29 checks) |
| `scripts/00_set_lab.sh`                             | Helper: set BUCKET / ROLE_ARN / REGION    |
| `scripts/01_create_main_queue.sh` … `07_teardown.sh` | Seven stage scripts                      |
| `scripts/run_all.sh`                                | Optional: run stages 1–6 in sequence      |
| `tests/conftest.py`                                 | Pytest fixtures: simulator + queue pair  |
| `tests/test_sqs.py`                                 | 12 pytest tests, no AWS creds            |
| `README.md`                                         | This file                                |

## The 7 lab stages — mapped to artifacts

| Stage | Lab step                                                       | Artifact                                |
|-------|----------------------------------------------------------------|-----------------------------------------|
| 1     | Create the main SQS queue                                       | `01_create_main_queue.sh`, `test_stage1_*` |
| 2     | Create the dead-letter queue (DLQ)                              | `02_create_dlq.sh`, `test_stage2_*`    |
| 3     | Attach redrive policy (maxReceiveCount=3) to main              | `03_attach_redrive.sh`, `test_stage3_*` |
| 4     | Package Lambda + create ESM                                     | `04_create_lambda.sh`, `test_stage4_*` |
| 5     | Send 8 good messages; watch 2 batched invocations              | `05_send_messages.sh`, `test_stage5_*` |
| 6     | Send 2 poison messages; trace 4 retries -> DLQ                 | `06_send_poison.sh`, `test_stage6_*`   |
| 7     | Teardown (ESM → Lambda → queues)                                | `07_teardown.sh`, `test_stage7_*`      |

## Run it offline (no AWS account)

```bash
cd medium/meta/datavidhya/21_Decouple_Pipeline_With_SQS_And_Lambda/

# Self-asserting driver -- 29 checks, all PASS.
../../../.env/bin/python 01_decouple_pipeline_with_sqs_and_lambda.py

# pytest -- 12 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

The driver and tests run the **same** `lambda_function/app.py` handler
that production Lambda runs. The only thing that differs is the queue:
production uses `aws sqs`/`aws lambda`; offline uses the in-memory
`SqsSimulator` from `sqs_stub.py`. The simulator mirrors the SQS event
source mapping's poll → invoke → delete-on-success behaviour, plus the
redrive policy that moves messages past `maxReceiveCount` to the DLQ.

## Run it against a real AWS account

```bash
export BUCKET=sqs-decouple-lab-bucket-a1b2c3
export DATABASE=sqs_decouple_db
export ROLE_ARN="arn:aws:iam::123456789012:role:role/SqsDecoupleLabRole-Ab3xYz"
export AWS_REGION=us-east-1

./scripts/run_all.sh      # stages 1-6
./scripts/07_teardown.sh  # explicit teardown
```

## What each lab stage actually does

### Stage 1 — Create the main queue

`aws sqs create-queue --queue-name orders-main-queue`. The lab provisions
nothing else; the queue starts empty.

### Stage 2 — Create the DLQ

Same call, different name (`orders-dlq`). The DLQ has **no** redrive
policy of its own -- it's a terminal parking lot, not a retry queue.

### Stage 3 — Attach the redrive policy

```bash
aws sqs set-queue-attributes --queue-url "$MAIN_URL" \
    --attributes '{"RedrivePolicy": "{\"deadLetterTargetArn\":\"'$DLQ_ARN'\",\"maxReceiveCount\":3}"}'
```

`maxReceiveCount=3` means: after the third failed `ReceiveMessage` the
message is moved to the DLQ. The lab's choice of `3` (not `1`, not
`5`) is the canonical "retry once or twice, then escalate" pattern.

### Stage 4 — Wire the queue to Lambda

The lab packages `lambda_function/app.py` into a zip, runs
`aws lambda create-function`, then:

```bash
aws lambda create-event-source-mapping \
    --function-name orders-consumer-q21 \
    --event-source-arn "$MAIN_ARN" \
    --batch-size 5
```

Lambda starts polling the queue in batches of 5.

### Stage 5 — Send 8 good messages

Each `aws sqs send-message` enqueues one order payload. The Lambda
ESM fires twice (5 + 3). CloudWatch Logs shows:
```
processing batch of 5 message(s)
order_id=2001 ... -- OK
order_id=2002 ... -- OK
...
processing batch of 3 message(s)
order_id=2006 ... -- OK
...
```

### Stage 6 — Send 2 poison messages

The handler raises on `ValueError` for `bad currency` and `missing
amount`. SQS sees the exception, **does not** delete the message, and
returns it to the queue. ReceiveCount climbs: 1, 2, 3, then on the 4th
poll ReceiveCount is `> maxReceiveCount`, the redrive policy fires,
and the message lands in the DLQ with `ReceiveCount=1` (reset).

### Stage 7 — Teardown

Order matters: ESM first (otherwise the queue keeps invoking a Lambda
that's being deleted), then Lambda, then queues.

## Traps the lab expects you to hit

- **Swallowing the exception inside the handler.** The handler's job is
  to *signal* failure, not to handle it. Wrap the handler body in a
  try/except that returns success and you silently lose poison messages.
  The handler raises; SQS owns the retry decision.
- **Deleting messages from inside the handler.** The event source mapping
  owns deletion based on the return value. Manually calling
  `delete_message` from inside the handler races the ESM and double-
  acks.
- **Setting `maxReceiveCount=1` (or `0`).** With `maxReceiveCount=1` the
  very first failure goes straight to the DLQ -- no retries. With `0`
  SQS treats every message as expired immediately. The lab uses `3`
  because transient failures (network blip, throttled downstream)
  usually resolve in 2 retries.
- **Forgetting to delete the ESM before deleting the Lambda.** SQS keeps
  invoking the function for up to 6 hours after deletion, generating
  "Function not found" errors and `EventSourceMapping` `CREATE_FAILED`
  states you have to clean up by hand.
- **Treating the DLQ as a retry queue.** The DLQ is for human
  inspection. Some teams add a second consumer to the DLQ that logs
  the bad payload to a database or a ticket. The lab doesn't do this;
  production usually does.

## Going to production

Four things to add before this leaves a lab:

1. **DLQ alarm.** CloudWatch alarm on `ApproximateNumberOfMessagesVisible`
   on the DLQ. Anything > 0 means a poison message is parked and a human
   needs to look. The lab doesn't show this.
2. **Visibility timeout tuning.** Default 30s. If the handler takes
   longer than that SQS considers the message "abandoned" and re-delivers
   it (ReceiveCount++) even though the handler is still running. Set
   `VisibilityTimeout >= 6 * handler p99 latency`.
3. **Idempotent handler.** SQS guarantees *at-least-once* delivery. If
   your handler is non-idempotent (e.g., increments a counter) a network
   blip can cause double-counting. The lab's payload-validation handler
   is naturally idempotent because it doesn't mutate downstream state;
   a "charge the credit card" handler needs a dedupe key.
4. **FIFO queue + MessageGroupId.** The lab uses a standard queue.
   Standard queues don't guarantee order. For order-preserving
   processing use `sqs.create_queue(... QueueName=... .fifo)` and
   pass `MessageGroupId` on `send_message`.

## Verification

The lab's "lab complete" check is: 8 good messages processed by the
Lambda (visible in CloudWatch), and 2 poison messages parked in the
DLQ after exactly 4 receives. The driver asserts both outcomes in
pure Python; the pytest suite isolates each invariant (batching,
redrive, validation) for fast feedback.
