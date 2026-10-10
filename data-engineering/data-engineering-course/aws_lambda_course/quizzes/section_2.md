# Quiz — Section 2: AWS Lambda Basic Concepts (Part 1)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — AWS Lambda Basic Concepts (Part 1) (L03–L08)
> **Questions:** 10 multiple-choice
> **Pass bar:** 7 / 10

Ten questions covering L03 through L08. Each answer is in a
collapsible block — click **Show answer** only after you have committed
to your answer.

---

### Q1

In what year was AWS Lambda launched, and at which AWS event?

- A) 2008, at AWS Summit San Francisco
- B) 2012, at re:Invent
- C) 2014, at re:Invent
- D) 2017, at AWS re:Mars
- E) 2020, at AWS Global Summits

<details><summary>Show answer</summary>

**C) 2014, at re:Invent.**

AWS Lambda was announced on November 13, 2014, at the annual re:Invent
conference in Las Vegas.

</details>

---

### Q2

Which of the following are the four dimensions on which AWS Lambda
charges you? (Choose four.)

- A) Requests (number of invocations)
- B) Duration (wall-clock time your handler runs)
- C) Memory (RAM allocated to the function)
- D) Concurrency (number of parallel environments)
- F) Storage (GB-month of code artifacts in Lambda's internal store)
- G) Data transfer (bytes leaving the AWS network)

<details><summary>Show answer</summary>

**A, B, C, D** — Requests, Duration, Memory, and Concurrency (the
latter only when you opt into **Provisioned Concurrency**, covered in
Section 11, **L49**).

Storage (F) and data transfer (G) are AWS charges in general but are
*not* part of the Lambda pricing model.

</details>

---

### Q3

What two arguments does every Lambda handler receive?

- A) `request` and `response`
- B) `event` and `context`
- C) `input` and `output`
- D) `payload` and `headers`
- E) `body` and `params`

<details><summary>Show answer</summary>

**B) `event` and `context`.**

The `event` is a JSON document whose structure depends on the trigger
(S3, API Gateway, EventBridge, SQS, …). The `context` object
contains runtime metadata: request ID, deadline, log group, log
stream, function name, memory limit, and more.

</details>

---

### Q4

In the console, the **Handler** field is set to
`lambda_function.lambda_handler`. What does each part mean?

- A) `lambda_function` is the S3 bucket and `lambda_handler` is the
  object key.
- B) `lambda_function` is the Python module (`.py` file) and
  `lambda_handler` is the callable inside it.
- C) `lambda_function` is the IAM role and `lambda_handler` is the
  trust principal.
- E) The field is decorative; Lambda ignores it and uses defaults.

<details><summary>Show answer</summary>

**B) `lambda_function` is the Python module (`.py` file) and
`lambda_handler` is the callable inside it.**

The format is `file.function`. If you rename the file or the function,
you must update the **Handler** field. The `.py` extension is omitted
from the file portion.

</details>

---

### Q5

What does the `AWSLambdaBasicExecutionRole` managed policy grant?

- A) Read/write access to every S3 bucket in the account.
- B) Administrator access to the account.
- C) Permission to write only to CloudWatch Logs
  (`logs:CreateLogGroup`, `logs:CreateLogStream`,
  `logs:PutLogEvents`).
- D) Permission to invoke any Lambda function in the account.
- E) Permission to assume any IAM role.

<details><summary>Show answer</summary>

**C) Permission to write only to CloudWatch Logs.**

This is deliberately minimal. It lets the function emit log lines; it
does *not* allow S3, DynamoDB, SNS, SQS, KMS, or any other service.
You must add additional permissions to the role before the function
can call those services.

</details>

---

### Q6

You want a function to read objects from a single specific bucket
`my-banking-feed`. Which permissions policy is the *most* appropriate?

- A) Attach `AmazonS3FullAccess` so the function definitely works.
- B) Attach `AdministratorAccess` so nothing else will fail later.
- C) A custom inline policy that allows `s3:GetObject` and
  `s3:ListBucket` on
  `arn:aws:s3:::my-banking-feed` and `arn:aws:s3:::my-banking-feed/*`.
- D) No policy — Lambda functions can access S3 by default.
- E) A custom policy with `Resource: "*"` for `s3:GetObject`.

<details><summary>Show answer</summary>

**C) A custom inline policy scoped to the specific bucket.**

This is the textbook application of **least privilege** — the
function can read this bucket and nothing else. Option (A) is too
broad; (B) is dangerous; (D) is wrong (Lambda has no default S3
permissions); (E) is broad again and would be flagged by any
security review.

</details>

---

### Q7

Your handler tries to call `s3:GetObject` and receives an
`AccessDenied` exception. Which role is most likely the cause?

- A) The execution role — it controls the function's *outbound*
  calls.
- B) The function's resource-based policy — it controls
  *inbound* invocations.
- C) The trust policy of the function's role — it controls who can
  assume the role, not what the role can do.
- D) The AWS account root user's password policy.

<details><summary>Show answer</summary>

**A) The execution role.**

`AccessDenied` on an outbound API call means the *caller* — your
function, via its execution role — is not authorized to perform that
action. The resource-based policy on the function controls
*inbound* invocations (who can call this function). The trust policy
controls *who* can assume the role.

</details>

---

### Q8

What does the `REPORT` line emitted to CloudWatch Logs at the end of
every invocation tell you?

- A) The full request body and response body.
- B) Duration, Billed Duration, Memory Size, and Max Memory Used.
- C) The list of IAM policies attached to the execution role.
- D) The list of all triggers on the function.
- E) The current AWS stock price.

<details><summary>Show answer</summary>

**B) Duration, Billed Duration, Memory Size, and Max Memory Used.**

This is the primary tool for tuning the **memory** pricing dimension:
raise memory to get more CPU and shorter Duration, and the `REPORT`
line lets you see the trade-off in real numbers.

</details>

---

### Q9

Which workload is the **best** fit for AWS Lambda?

- A) A long-running video transcoding job that takes 4 hours per file.
- B) A 24/7 HTTP API that handles a sustained 5 000 requests per
  second with no end-of-stream semantics.
- C) A function that fires when a JSON file lands in S3, parses it,
  and writes items to DynamoDB — 200 events per day, mostly business
  hours.
- D) A database server that holds 64 GB of in-memory state and
  requires a custom kernel module.
- E) A desktop GUI application.

<details><summary>Show answer</summary>

**C) The S3-event-driven DynamoDB pipeline.**

This is the textbook Lambda shape: event-driven, short-lived,
sporadic, and glueing two AWS services together — and it is the
exact pattern we build end-to-end in Section 6 (**L23**–**L24**).
(A) exceeds the 15-minute timeout; (B) is sustained high-RPS;
(D) needs persistent state and custom kernel modules; (E) is not
a cloud workload.

</details>

---

### Q10

In the **L06** walkthrough you added an **API Gateway** trigger to
your function. What was created in addition to the function, and what
controls which AWS services are allowed to invoke that function?

- A) A new S3 bucket; access controlled by a bucket policy.
- B) A new REST API in API Gateway; the function's
  **resource-based policy** authorizes API Gateway to invoke it.
- C) A new VPC and subnet; access controlled by a network ACL.
- D) A new SNS topic; access controlled by a topic policy.
- E) Nothing — triggers are purely cosmetic.

<details><summary>Show answer</summary>

**B) A new REST API in API Gateway; the function's resource-based
policy authorizes API Gateway to invoke it.**

The console automatically writes the `lambda:InvokeFunction`
permission into the function's resource-based policy when you click
**Add trigger**. This is the inbound counterpart to the execution
role's outbound permissions, and is the same kind of policy we
declare by hand in CloudFormation (**L67**) and CDK.

</details>

---

## Score key

| Score | Interpretation |
|---|---|
| 9–10 | Strong. Move on to Section 3. |
| 7–8  | Pass. Re-read the lectures you missed on, then move on. |
| 5–6  | Borderline. Re-watch L05, L06, and L07 end-to-end before moving on. |
| 0–4  | Re-read the section overview (`02_lambda_basic_concepts/README.md`) and rerun the L06 console walkthrough. |

After you pass, head to:

- **L09** — Python Basics Refresher, Part 1 (Section 3)
- `02_lambda_basic_concepts/code/` — sample handler stubs (when
  populated)