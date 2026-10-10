# Section 10 — Generative AI: AWS Bedrock (Cohere) End-to-End (L40–L46, 40 min)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** 7 lectures, 1 hands-on enterprise use case, 1 quiz
> **Industry:** Manufacturing

This section is the **manufacturing industry use case** advertised on the
course landing page: factory floor sensors and line operators generate
free-text **defect reports**; an HTTP API allows operations staff to POST a
defect description; AWS API Gateway invokes AWS Lambda; Lambda calls
**AWS Bedrock's Cohere Command** foundational model to summarize and
classify the defect; the structured summary is returned to the caller.

By the end of section 10 you will be able to:

- Explain what AWS Bedrock is, what model families it exposes, and how
  it is priced.
- Wire a Lambda function's IAM execution role with the minimum
  permissions Bedrock requires (`bedrock:InvokeModel`,
  `bedrock:InvokeModelWithResponseStream`).
- Engineer a production prompt that forces Cohere to return
  **structured JSON** (summary, category, severity).
- Wrap the Lambda behind an API Gateway REST API with CORS and
  throttling.
- Run an end-to-end demo: `curl` a defect, get a structured summary
  back in under three seconds.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L40 | Section Overview | 0:26 | [`lecture_scripts/L40_section_overview.md`](lecture_scripts/L40_section_overview.md) |
| L41 | Generative AI — Use Case and Architecture | 4:01 | [`lecture_scripts/L41_use_case_architecture.md`](lecture_scripts/L41_use_case_architecture.md) |
| L42 | Generative AI — AWS Bedrock Overview | 2:24 | [`lecture_scripts/L42_bedrock_overview.md`](lecture_scripts/L42_bedrock_overview.md) |
| L43 | Generative AI — AWS Lambda Prerequisites | 5:50 | [`lecture_scripts/L43_lambda_prereqs.md`](lecture_scripts/L43_lambda_prereqs.md) |
| L44 | Generative AI — Write AWS Lambda Function to access Bedrock | 20:36 | [`lecture_scripts/L44_lambda_bedrock.md`](lecture_scripts/L44_lambda_bedrock.md) |
| L45 | Generative AI — Create REST API using API Gateway to access Bedrock | 5:34 | [`lecture_scripts/L45_apigw_bedrock.md`](lecture_scripts/L45_apigw_bedrock.md) |
| L46 | Generative AI — End to End Demo | 1:13 | [`lecture_scripts/L46_e2e_demo.md`](lecture_scripts/L46_e2e_demo.md) |

## Working code (`code/`)

```
code/
├── lambda_function/
│   ├── bedrock_lambda.py            # the production Lambda handler
│   └── test_bedrock_lambda.py       # pytest suite (uses boto3 stub)
├── prompt_template.txt              # system + user prompt template
├── iam_policy.json                  # minimum Bedrock permissions
└── sample_defects.json              # 5 example defect descriptions
```

## How to use

```bash
cd 10_generative_ai_bedrock/code
python -m pytest lambda_function/ -v          # run the test suite offline
```

The Lambda handler ships with a `__main__` block so you can invoke it
locally with a fake event before deploying:

```bash
python lambda_function/bedrock_lambda.py
```

## Quiz

[`../../quizzes/section_10.md`](../../quizzes/section_10.md) — 10 questions.
