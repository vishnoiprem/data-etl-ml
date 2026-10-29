---
l_id: L08
title: AWS Lambda — Conceptual Understanding Review
duration: null
prereqs:
  - L03 (Section Overview)
  - L04 (Evolution from Physical Servers to AWS Lambda)
  - L05 (What is AWS Lambda and Use Cases)
  - L06 (Lambda Console Walkthrough)
  - L07 (Lambda Execution Role)
---

# L08 — AWS Lambda — Conceptual Understanding Review

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 2 — AWS Lambda Basic Concepts (Part 1)
> **Duration:** — (self-paced)

## Prereqs

- L03 — Section Overview
- L04 — Evolution from Physical Servers to AWS Lambda
- L05 — What is AWS Lambda and Use Cases
- L06 — Lambda Console Walkthrough
- L07 — Lambda Execution Role

## Key terms

- Serverless / FaaS
- Handler and event
- Four pricing dimensions (requests, duration, memory, concurrency)
- Execution role vs resource-based policy
- `AWSLambdaBasicExecutionRole`

## Lecture

This is a self-paced recap. Skim each section, then try the **Self-check**
questions without scrolling. The answers are at the bottom of the file —
resist the urge to peek.

### One-line summaries

| L# | One-line answer |
|---|---|
| **L03** | This section introduces the Lambda mental model before any code. |
| **L04** | Compute evolved from bare metal to VMs to containers to serverless; AWS Lambda launched in 2014 as Functions-as-a-Service. |
| **L05** | Lambda is event-driven serverless code; price = requests × memory × duration; great for events, glue, and bursts; bad for long-running or steady high-RPS work. |
| **L06** | In the console: Author from scratch → name/runtime/role → write handler in **Code** tab → **Test** → add trigger → inspect **Report** line in logs. |
| **L07** | The execution role's trust policy lets Lambda assume it; `AWSLambdaBasicExecutionRole` only grants CloudWatch logs write; least-privilege means scoping `Resource` to the specific ARNs you need. |

### Self-check questions

1. In what year was AWS Lambda launched, and at which AWS event?
2. What are the four dimensions on which Lambda charges you?
3. Name the two arguments every Lambda handler receives.
4. What is the format of the **Handler** configuration field, and what
   does each piece mean?
5. What does `AWSLambdaBasicExecutionRole` actually allow, and what
   does it deliberately *not* allow?
6. If your function needs to read a single S3 bucket but no other AWS
   service, what should the role's permissions policy look like?
7. Your function tries to call `s3:GetObject` and gets `AccessDenied`.
   Which of the two roles (execution role or resource-based policy on
   the function) is most likely the cause?
8. What does the `REPORT` line in CloudWatch Logs contain, and which
   pricing dimension does it tune?
9. Give two example workloads that fit Lambda well and two that do
   not.
10. In **L06**, you clicked **Add trigger → API Gateway → Create a new
    API**. Which AWS service is now allowed to invoke your function, and
    which role controls that?

### Answers

1. **2014**, at **re:Invent** (announced November 13, 2014).
2. **Requests**, **duration**, **memory**, **concurrency** (free tier
   applies to requests and duration).
3. **`event`** (a JSON document) and **`context`** (request ID,
   deadline, log stream, function name, memory limit).
4. **`file.function`** — the file name holding the handler and the
   function name inside that file (e.g. `lambda_function.lambda_handler`).
5. **Only** the three log-related actions: `logs:CreateLogGroup`,
   `logs:CreateLogStream`, `logs:PutLogEvents`. It does **not** allow
   S3, DynamoDB, SNS, SQS, KMS, or any other service — you must add
   those explicitly.
6. A custom policy with `Effect: Allow`, `Action: s3:GetObject` (and
   usually `s3:ListBucket`), and `Resource` set to that specific
   bucket ARN (and `bucket/*` for object-level actions). Do not attach
   `AmazonS3FullAccess`.
7. The **execution role**. The resource-based policy on the function
   controls who can *invoke* the function (inbound); the execution
   role controls what the function can *call* (outbound). S3 calls
   are outbound.
8. The `REPORT` line contains **Duration**, **Billed Duration**,
   **Memory Size**, and **Max Memory Used**. It is the primary tool
   for tuning the **memory** (and indirectly duration) pricing
   dimension.
9. *Fit*: image thumbnailer triggered by S3 uploads; daily DynamoDB
   cleanup triggered by EventBridge. *Don't fit*: a 4-hour video
   transcode (over the 15-minute timeout); a sustained 5 000 rps
   API behind a single ALB (cheaper on ECS/EKS with auto scaling
   groups).

   Any reasonable example that respects the timeout, event-driven, and
   bursty-traffic criteria will do.
10. **API Gateway** is allowed to invoke your function. That is
    controlled by the **resource-based policy on the function** (the
    function's **Permissions → Resource-based policy** statement),
    which is set up automatically when you add the trigger in the
    console. The execution role is separate and concerns *outbound*
    calls.

### What to do if any answer felt shaky

- **Q1, Q3, Q4** shaky → re-watch **L04** and the **Code** / handler
  discussion in **L06**.
- **Q2, Q8** shaky → re-read **L05** (pricing dimensions) and step 9 of
  **L06** (tuning memory, reading the Report).
- **Q5, Q6, Q7, Q10** shaky → re-read **L07** (execution role vs
  resource-based policy) and the AWS Glue course's
  `L05_iam_101.md` for general IAM primer.
- **Q9** shaky → re-read the "When Lambda is / is not a great fit"
  section of **L05**.

## Hands-on

If you have not already:

1. Create a fresh function in the console as in **L06**.
2. Open its execution role in IAM, confirm the trust policy and the
   managed policy match what **L07** described.
3. Delete the function. Confirm the role was **not** deleted with it
   (this is by design; we cover the cleanup pattern in Section 4).

## Quiz prep

This lecture is essentially the quiz prep. When you are ready, take
`quizzes/section_2.md` — 10 multiple-choice questions on the entire
section.

## Further reading

- `quizzes/section_2.md` — section quiz
- `02_lambda_basic_concepts/README.md` — section overview
- Section 3 — Python Basics Refresher (**L09**–**L10**), the language
  we'll write Lambda handlers in for the rest of the course.