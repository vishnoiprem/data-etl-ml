---
title: L46 — Generative AI: End-to-End Demo
author: Prem Vishnoi <pvishnoi@avilx.com>
section: 10
duration: 1:13
---

# L46 — Generative AI: End-to-End Demo

> We POST a real defect description through API Gateway and watch
> Bedrock summarize and classify it. Total demo time on a warm
> Lambda: ~2 seconds.

## Prereqs

- L43 (IAM + model access).
- L44 (Lambda deployed).
- L45 (API Gateway REST API deployed to `prod`).

## The demo

Open three things side-by-side:

1. A terminal.
2. The CloudWatch Logs Insights tab for
   `/aws/lambda/bedrock-defect-summarizer`.
3. The API Gateway **Stages → prod → Logs** tab.

Then run:

```bash
API=https://abc123def4.execute-api.us-east-1.amazonaws.com/prod
curl -s -X POST $API/defects \
  -H "Content-Type: application/json" \
  -d @../code/sample_defects.json | jq '.'
```

Wait — that's the file. We want a single defect:

```bash
curl -s -X POST $API/defects \
  -H "Content-Type: application/json" \
  -d '{
    "defect_description": "URGENT: smoke from the main control cabinet on line 2. E-stop pressed. Fire department called. Personnel evacuated."
  }' | jq .
```

Response:

```json
{
  "statusCode": 200,
  "headers": { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  "body": {
    "summary": "Smoke from main control cabinet on line 2; e-stop pressed; fire department called; personnel evacuated.",
    "category": "electrical",
    "severity": "critical"
  }
}
```

Then send the cosmetic one:

```bash
curl -s -X POST $API/defects \
  -H "Content-Type: application/json" \
  -d '{
    "defect_description": "Cosmetic scratch on the painted top cover of unit SN-203194."
  }' | jq .
```

Response:

```json
{
  "summary": "Cosmetic scratch on painted top cover of unit SN-203194.",
  "category": "other",
  "severity": "low"
}
```

## What you should see in CloudWatch

For the URGENT request, the Lambda log group contains one
`bedrock.invoke_model:` line within ~2 seconds of the curl:

```
bedrock.invoke_model: model=cohere.command-text-v14 latency_ms=1834
                     input_chars=158 output_chars=87
```

For the cosmetic one:

```
bedrock.invoke_model: model=cohere.command-text-v14 latency_ms=1201
                     input_chars=72 output_chars=64
```

The API Gateway access log shows the matching `200` response.

## What you should *not* see

- `AccessDeniedException` — means the IAM role is wrong (re-check L43).
- `ResourceNotFoundException` on the model — usually means Bedrock
  model access has not been granted in this region.
- `429 Too Many Requests` — only if you hammered the API; back off.
- `502 Bad Gateway` with `could not parse model output as JSON` —
  Cohere returned prose instead of JSON. Either tweak the prompt or
  retry.

## Wrap-up

You have built an end-to-end **Generative AI serverless application**:

- **Public HTTPS endpoint** (API Gateway REST API, throttled, CORS, validated).
- **Stateless compute** (Lambda, Python 3.11, boto3, ~2 s round-trip).
- **Foundation model call** (Bedrock Cohere Command text, JSON-mode coercion).
- **Structured output contract** (`summary`, `category`, `severity`).
- **Cost control** (per-token billing, request throttling, env-var caps).
- **Observability** (CloudWatch logs for both the Lambda and the API).

This same architecture — POST → API Gateway → Lambda → Bedrock → JSON
back — is the starting point for the **RAG pattern** (replace the
prompt with retrieval-augmented context) and for **Bedrock Agents**
(replace the Lambda with the agent runtime and let it choose tools).

## Quiz prep

- What three things are wrong if you get `AccessDeniedException`?
- What is the typical end-to-end latency?
- Where do you look to debug a wrong category answer?

## Further reading

- AWS — [Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- AWS — [Knowledge Bases for Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- AWS — [API Gateway access logging](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html)