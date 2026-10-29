# Section 8 Quiz — Enterprise Use Case 2: API Gateway, Lambda, S3

> **Source:** lectures L30–L35, L31a
> **Pass bar:** 8 / 12
> Answers are hidden in collapsible blocks. Try the questions first, then
> reveal only one at a time.

---

**1. Which three AWS services make up Enterprise Use Case 2?**

- A) Lambda, SQS, DynamoDB
- B) API Gateway, AWS Lambda, S3
- C) API Gateway, Step Functions, S3
- D) CloudFront, Lambda, DynamoDB

<details><summary>Show answer</summary>

**B)** API Gateway, AWS Lambda, S3. The stack is a public HTTPS API
that proxies to Lambda, which reads/writes S3.

</details>

---

**2. In API Gateway, what does the resource path `/{proxy+}` mean?**

- A) An optional query string parameter named `proxy`
- B) A greedy path variable that matches one or more path segments
- C) A header named `proxy`
- D) A path that is rejected by API Gateway as invalid

<details><summary>Show answer</summary>

**B)** `{proxy+}` is a greedy path variable — it matches one or more
segments so any URL reaches your method. The `+` makes it greedy (vs.
the default `{proxy}` which only matches one segment and does not
include slashes).

</details>

---

**3. Where in a Lambda proxy event does API Gateway put query string
parameters?**

- A) `event.headers`
- B) `event.pathParameters`
- C) `event.queryStringParameters`
- D) `event.body`

<details><summary>Show answer</summary>

**C)** `event.queryStringParameters` is a dict of single-valued
parameters. For multi-valued parameters use
`event.multiValueQueryStringParameters`.

</details>

---

**4. What HTTP status code does API Gateway return when a caller
exceeds a Usage Plan quota?**

- A) `403 Forbidden`
- B) `429 Too Many Requests`
- C) `503 Service Unavailable`
- D) `402 Payment Required`

<details><summary>Show answer</summary>

**B)** `429` is returned for both throttled (`Rate Exceeded`) and
quota-exceeded (`Quota Exceeded`) requests. `403` is for invalid /
missing API keys.

</details>

---

**5. Is an API Key an authentication mechanism?**

- A) Yes — it authenticates the caller.
- B) No — it's only a metering / throttling identifier.

<details><summary>Show answer</summary>

**B)** API Keys identify the *caller* for metering and throttling. They
do **not** authenticate. For real authentication use IAM auth, Lambda
Authorizer, Cognito Authorizer, or mTLS.

</details>

---

**6. In the `api_get_object` handler, if both `?key=` and the `{proxy+}`
path are populated, which wins?**

- A) The `{proxy+}` path
- B) The `?key=` query string
- C) Whichever is alphabetically first
- D) API Gateway rejects the request

<details><summary>Show answer</summary>

**B)** The handler prefers `?key=` over the path. The lecture notes
that the path is normally reserved for resource names, so the query
string is the "real" key.

</details>

---

**7. What's the main reason for the Lambda execution role in Use Case 2?**

- A) To authenticate the client
- B) To allow API Gateway to invoke the Lambda
- C) To grant the Lambda permission to read/write S3 and write CloudWatch logs
- D) To replace VPC networking

<details><summary>Show answer</summary>

**C)** The execution role is the IAM role Lambda *assumes* to make AWS
API calls (S3 in this case) and to write CloudWatch logs. The
**invoke permission** (a separate resource policy on the Lambda) is
what allows API Gateway to invoke the function.

</details>

---

**8. What's special about a *Velocity* mapping template?**

- A) It's a Python script that runs inside the Lambda.
- B) It's a server-side template (API Gateway v1 only) that transforms
  the integration request before it hits the backend.
- C) It's a JSON Schema for validating request bodies.
- D) It's a CloudFormation template.

<details><summary>Show answer</summary>

**B)** Velocity mapping templates transform the integration request (or
response) before it hits the backend. They are only available in REST
API (v1) and are absent from HTTP APIs (v2).

</details>

---

**9. In the L34 boto3 script, why is the script *idempotent*?**

- A) Because boto3 retries failed calls automatically.
- B) Because the script always uses the same AWS region.
- C) Because every step looks up the existing resource first, then
  updates it instead of always creating a new one.
- D) Because Lambda is serverless.

<details><summary>Show answer</summary>

**C)** Each helper (`ensure_api_key`, `ensure_usage_plan`,
`attach_key_to_plan`) checks for the existing resource by name and
updates it if present. Re-running the script is therefore safe and
useful in CI/CD pipelines.

</details>

---

**10. Which of the following is the correct 2026 architecture for an
agentic AI system on AWS that uses Use Case 2 as one of its tools?**

- A) Replace API Gateway with a queue, then add a Lambda that polls it.
- B) Wrap the L30–L34 API Gateway + Lambda + S3 stack as a tool,
  expose it to a Bedrock Agent or Strands agent, and let the model
  decide when to call it.
- C) Move the S3 bucket into a private VPC, then add an EC2 proxy.
- D) Re-implement S3 reads/writes as direct Bedrock model calls.

<details><summary>Show answer</summary>

**B)** The Use Case 2 stack is the *plumbing* of an agentic AI system.
The only new ingredient is the model and the agent loop. Wrapping the
existing API as a tool is the canonical 2026 pattern — and it works
identically whether the agent runtime is Bedrock Agents, Strands, or a
custom one.

</details>

---

**11. What HTTP status code does API Gateway return when a Lambda
backend throws an unhandled exception?**

- A) `400 Bad Request`
- B) `403 Forbidden`
- C) `500 Internal Server Error`
- D) `503 Service Unavailable`

<details><summary>Show answer</summary>

**C)** An unhandled Lambda exception is mapped to `500 Internal Server
Error` by API Gateway. Lambda timeouts surface as `502 Bad Gateway` or
`504 Gateway Timeout`, but ordinary exceptions become `500`. The full
traceback lands in the Lambda's CloudWatch Logs log group — *not* in
the API Gateway access log — which is why the L31a lecture insists you
check the function log group first when a 5xx appears.

</details>

---

**12. Where does the API Gateway access log go by default?**

- A) It is off by default; once enabled, it goes to the CloudWatch
  Logs log group `API-Gateway-Execution-Logs_<api-id>/<stage>`.
- B) It is written to the Lambda's CloudWatch log group automatically.
- C) It is streamed to S3 via a CloudTrail data event.
- D) It is shown in the API Gateway dashboard "Logs" tab only.

<details><summary>Show answer</summary>

**A)** API Gateway access logging is **off** by default. To turn it on,
open the stage in the console (or call `update_stage`), pick a CW Logs
ARN, and enable access logging. The logs land in a log group named
`API-Gateway-Execution-Logs_<api-id>/<stage>` — a *different* log
group from the Lambda's. The Lambda's CloudWatch log group gets its
own stream from the Lambda service. The two are intentionally separate
so you can give API Gateway engineers IAM access to edge logs without
giving them access to application logs.

</details>
