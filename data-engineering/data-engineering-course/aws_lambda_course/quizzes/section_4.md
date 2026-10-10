# Section 4 Quiz — AWS Lambda with S3, EC2, DynamoDB

> 10 questions, multi-choice, single answer. The answer key is at the bottom.
> Covers L11–L18.

---

**Q1.** What is the required signature of a Python Lambda function's handler in this course?

- A. `def handler(context, event):`
- B. `def handler(event, context):`
- C. `def lambda_handler(event, context, region):`
- D. Any function name is fine; AWS calls whichever function is set in the console.

---

**Q2.** You create an S3 bucket from a Lambda and the request fails with `InvalidLocationConstraint`. Which is the most likely cause?

- A. The bucket name is already taken globally.
- B. You passed `CreateBucketConfiguration={"LocationConstraint": "us-east-1"}` — `us-east-1` does not accept a LocationConstraint.
- C. The execution role is missing `s3:ListBucket`.
- D. The Lambda timeout is too short.

---

**Q3.** Which `boto3` call do you use to find every S3 bucket in the calling AWS account?

- A. `s3.list_buckets()`
- B. `s3.get_all_buckets()`
- C. `s3.describe_buckets()`
- D. `s3.list_buckets_paginated()`

---

**Q4.** You call `s3.delete_bucket(Bucket="my-bucket")` and AWS returns an error. The bucket has 12 objects in it but versioning is disabled. What is the most likely cause, and what do you do?

- A. The IAM role is missing `s3:DeleteBucket`. Add it.
- B. S3 will not delete a non-empty bucket. First list and delete all the objects, then call `delete_bucket`.
- C. The bucket name is invalid. Rename it.
- D. The Lambda is in the wrong region. Re-deploy.

---

**Q5.** You want your Lambda to start an EC2 instance every weekday at 8am UTC and stop it every weekday at 8pm UTC. Which AWS service do you wire up?

- A. CloudWatch Alarms
- B. EventBridge scheduled rules (`cron(0 8 ? * MON-FRI *)` and `cron(0 20 ? * MON-FRI *)`)
- C. Step Functions state machines
- D. SNS topics

---

**Q6.** Your EC2 start/stop Lambda is wired to an EventBridge rule but the rule never invokes it. Which is the most likely cause?

- A. EventBridge is not enabled in the region.
- B. The Lambda's execution role is missing `ec2:StartInstances`.
- C. The Lambda is missing a *resource-based* `lambda:InvokeFunction` permission granting `events.amazonaws.com`.
- D. CloudWatch Logs is disabled.

---

**Q7.** In the EC2 lifecycle handler, you catch `ClientError` with code `IncorrectInstanceState` when calling `start_instances` or `stop_instances`. Why?

- A. The instance does not exist.
- B. The IAM role is wrong.
- C. For idempotency: starting an already-running instance (or stopping an already-stopped one) is a no-op, but boto3 raises this code. Catching it makes the handler safe to call repeatedly.
- D. The region is wrong.

---

**Q8.** You want to insert an item with a numeric total into DynamoDB from a Lambda. Which data type must you use?

- A. Python `int` is fine; DynamoDB converts.
- B. Python `float` is fine; DynamoDB stores it as a Number.
- C. `boto3.dynamodb.types.Decimal` (or `decimal.Decimal`) — DynamoDB rejects native Python floats.
- D. JSON `Number` — boto3 serializes the event payload directly.

---

**Q9.** Your DynamoDB create-table handler runs twice. The first call returns `table_status="created"`, the second returns `table_status="exists"`. Which pattern makes this safe?

- A. Catch `ResourceInUseException` and treat it as success; also pre-check with `describe_table`.
- B. Add a `time.sleep(60)` between calls.
- C. Use `boto3.resource` instead of `boto3.client`.
- D. Move the handler into a Step Function.

---

**Q10.** You write a Lambda that lists S3 buckets but the response is missing the *region* of each bucket. Why, and how do you fix it?

- A. `list_buckets` does not return the region. Call `get_bucket_location(Bucket=name)` per bucket; coerce an empty `LocationConstraint` to `"us-east-1"`.
- B. Add `region` to the `list_buckets` call.
- C. The Lambda is in the wrong region; re-deploy.
- D. `list_buckets` is region-scoped, so the result only shows buckets in the Lambda's region.

---

# Answer Key

1. **B** — `def handler(event, context):`. The first argument is the event payload, the second is the runtime context object. This is the AWS-defined handler contract for Python.
2. **B** — `us-east-1` is the only region where you must **omit** `CreateBucketConfiguration`. For every other region it is required.
3. **A** — `s3.list_buckets()`. Returns a dict with a `Buckets` list and an `Owner`. (B) and (C) are not real APIs; (D) is a misremembered paginator.
4. **B** — S3 refuses to delete a non-empty bucket. You must list (and, for versioned buckets, list versions) and delete every object first, then call `delete_bucket`. L14's `_force_empty` helper does exactly this.
5. **B** — EventBridge scheduled rules with cron expressions. CloudWatch Alarms trigger on thresholds, not times; Step Functions is for orchestration, not scheduling; SNS is a pub/sub bus.
6. **C** — EventBridge needs a *resource-based* `lambda:InvokeFunction` permission on the Lambda to invoke it. Without it, the rule silently fails. The execution role is the *other* permission (Lambda -> EC2), which is unrelated to the trigger wiring.
7. **C** — Idempotency. `start_instances` raises `IncorrectInstanceState` if the instance is already `running`; `stop_instances` raises it if the instance is already `stopped`. Catching it makes the handler safe to call on every EventBridge tick.
8. **C** — DynamoDB rejects native Python `float`. Use `Decimal` (the `decimal` module, or `boto3.dynamodb.types.Decimal`). The `boto3.resource` API coerces for you, but the `client` API does not.
9. **A** — The "describe-then-create" pattern with `ResourceInUseException` as a fallback for the race where two invokers check the table at the same time. `sleep` is fragile; resource vs client is a style choice, not a correctness fix; Step Functions is overkill.
10. **A** — `list_buckets` is account-wide but does not include the bucket's region. You must call `get_bucket_location` per bucket. An empty `LocationConstraint` means `us-east-1` — coerce accordingly. (D) is a misconception: `list_buckets` returns buckets in *all* regions.