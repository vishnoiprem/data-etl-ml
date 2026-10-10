# Section 10 Quiz — Generative AI: AWS Bedrock (Cohere) End-to-End

> 11 questions. Hidden answers in a collapsible block at the bottom of each question.
> Try to answer before opening the block.

---

### Q1 — Which AWS service exposes foundational models through a single API?

<details>
<summary>Answer</summary>

**AWS Bedrock.** Bedrock is a serverless managed service that exposes
multiple foundational model families (Anthropic Claude, Cohere
Command, Meta Llama, AI21 Jurassic, Stability) through one HTTP API.
</details>

---

### Q2 — What unit does AWS Bedrock charge on for on-demand inference?

<details>
<summary>Answer</summary>

**Per input token and per output token**, separately. There is no
per-minute charge, no idle cost, and no cold-start GPU spin-up fee.
Provisioned Throughput plans (per tokens-per-second) are an
alternative for high-volume workloads.
</details>

---

### Q3 — Which IAM action does the Lambda need to call Cohere Command synchronously?

<details>
<summary>Answer</summary>

**`bedrock:InvokeModel`.** (We also grant
`bedrock:InvokeModelWithResponseStream` for future streaming use, but
the synchronous call uses `InvokeModel`.)
</details>

---

### Q4 — Why is the IAM policy scoped to a specific model ARN (`arn:aws:bedrock:us-east-1::foundation-model/cohere.command-text-v14`) instead of `"Resource": "*"`?

<details>
<summary>Answer</summary>

**Least-privilege.** Bedrock calls are billed per-token, and a
wildcard resource lets the role call any model — including expensive
ones. Scoping to a single model ARN means a misconfigured Lambda or a
prompt-injection exploit cannot invoke a $0.015/output-token Claude
Sonnet or an image model by accident. The role has exactly the
permissions it needs and nothing else.
</details>

---

### Q5 — What must you click in the Bedrock console before the first `InvokeModel` call succeeds?

<details>
<summary>Answer</summary>

**Model access.** In the Bedrock console sidebar, click
**Model access → Manage model access**, tick the Cohere row, and save.
AWS flips the status to "Access granted" within a minute. Until that
toggle is on, every call returns `AccessDeniedException`.
</details>

---

### Q6 — The Cohere Command body shape uses which JSON field for the prompt? (Anthropic Claude uses `messages=[...]`.)

<details>
<summary>Answer</summary>

**`prompt`.** Cohere's body is
`{"prompt": "...", "max_tokens": 256, "temperature": 0.2, "p": 0.9, ...}`.
Anthropic Claude's body uses `messages` with a different structure.
Switching model families requires rewriting both the body and the
response parser.
</details>

---

### Q7 — In our handler, what three strategies does `_parse_model_json` try, in order?

<details>
<summary>Answer</summary>

1. Parse the **whole response** as JSON.
2. **Regex search** for the first `{...}` block in the response.
3. A **tolerant trailing-brace scan** from the last `}` back to the
   first `{`.

If all three fail, the handler raises `RuntimeError` and the Lambda
returns **502 Bad Gateway**. This defensive layering handles the
~1% of cases where Cohere emits prose instead of JSON.
</details>

---

### Q8 — Why split the prompt into a separate `prompt_template.txt` file instead of inlining it in the Python source?

<details>
<summary>Answer</summary>

**Non-coders can edit tone, safety guardrails, or enum lists without
touching Python.** Operators, QA, and product managers can iterate on
prompt wording; the file ships in the deployment package and is
loaded lazily on the first invocation. It also keeps the Python
focused on plumbing rather than copy.
</details>

---

### Q9 — Why use a REST API instead of an HTTP API for this endpoint?

<details>
<summary>Answer</summary>

**REST APIs support per-method API keys and usage plans, JSON Schema
request validation, and built-in CloudWatch access logging.** The
defect-summarizer is a B2B-style internal API that may need to be
billed per call to internal teams later. REST is the path of least
resistance for adding per-key throttling and quotas. HTTP APIs are
cheaper per request but lack these features.
</details>

---

### Q10 — What is the cheapest DDoS mitigation in this architecture?

<details>
<summary>Answer</summary>

**JSON Schema request validation in API Gateway.** A malformed
request — empty body, wrong type, missing `defect_description` — is
rejected with 400 **before the Lambda is invoked**, so Bedrock is
never called and never billed. The next-cheapest mitigation is
**stage throttling** (10 RPS) which returns 429 without invoking
the Lambda either.
</details>

---

### Q11 — A plant-floor tablet is leaking `x-api-key` headers in browser DevTools and you suspect one has been scraped. The key in question is attached to the `defect-api-prod` Usage Plan. What is the correct response?

<details>
<summary>Answer</summary>

**Rotate the key.** A leaked API key is equivalent to a leaked URL —
there is no signing, no expiry, and no built-in revocation story.
The procedure is:

1. `create_api_key` with a new name (e.g. `tablet-line-3-v2`) and
   leave the old one in place.
2. `create_usage_plan_key` to attach the new key to **both** the
   `defect-api-dev` and `defect-api-prod` plans.
3. Roll the new key out to the tablet.
4. Confirm the new key is in use (CloudWatch `AWS/ApiGateway` →
   `Count`, dimension `ApiKey=<new-id>` shows traffic).
5. Delete the old key.

You do **not** rely on Bedrock IAM to catch this — the API Key
protects the **API Gateway → caller** edge, not the Lambda → Bedrock
edge. And you do **not** rely on the 10 RPS throttle to save you; a
scraper can stay under the rate limit and still rack up a real
Bedrock bill before anyone notices.
</details>
