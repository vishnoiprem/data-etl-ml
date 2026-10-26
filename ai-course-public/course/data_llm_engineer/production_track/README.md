# Production Track — Deploy LLMs & Agents at Scale

> **Companion to the LLM Engineering core track.** 4 weeks: Vercel → AWS,
> Terraform, Bedrock/SageMaker, observability and guardrails.
>
> **This is not a separate course directory.** It lives inside
> `data_llm_engineer/` because it is the same instructor's follow-on to the
> same pricer/agent artifacts the core track builds in weeks 6–8. Keeping it
> separate would have split one curriculum across two trees.

---

## Why only two projects here

The core track already contains eight weeks of runnable material: the brochure
generator, the Gradio airline agent, the RAG knowledge worker, the pricer
capstone, the QLoRA fine-tune, and the Modal agent fleet. The Production track
teaches **deployment of those artifacts**, not new ML.

So rather than rebuild eight projects, this directory holds the two pieces the
core track genuinely lacks and that are expensive to get wrong:

| Project | What it is | Why it belongs here |
|---|---|---|
| `01-vercel-to-aws` | FastAPI backend with SSE token streaming, narrow CORS, env-var config | The deployable surface. Weeks 6–8 build *models*; nothing in the repo has a production HTTP surface to deploy. |
| `02-terraform-multi-env` | Validated Terraform for ECR + App Runner + IAM + autoscaling, scoped dev/test/prod | The core track has no IaC at all. This is the course's Week 1 Day 5 → Week 2 Day 4 arc. |

**Both are verified, not sketched:**

```
$ pytest                      # 01-vercel-to-aws
4 passed

$ terraform validate          # 02-terraform-multi-env
Success! The configuration is valid.
```

---

## The Terraform schema traps (this is the actual content)

I wrote this config wrong **three times** before getting it to validate. Every
mistake is a real trap, and all are commented in `main.tf`:

| What I wrote | The error | The truth |
|---|---|---|
| `repository_name = aws_ecr_repository.app.name` | `An argument named "repository_name" is not expected here` | It's `image_identifier`, and it takes the full repo URI |
| `runtime = "PYTHON"` inside `image_configuration` | `An argument named "runtime" is not expected here` | There is no runtime arg. App Runner infers it from the image |
| `auto_scaling_configuration { }` nested in the service | `Blocks of type "auto_scaling_configuration" are not expected here` | It's a **separate resource**: `aws_apprunner_auto_scaling_configuration_version` — and it's **flat**, `min_size` is a top-level arg |
| `authentication_configuration` inside `image_repository` | `Blocks of type "authentication_configuration" are not expected here` | It's a **sibling** under `source_configuration` |
| `ip_address_type = "IPV4_ONLY"` | `An argument named "ip_address_type" is not expected here` | It lives in `network_configuration` and takes `IPV4`/`DUAL_STACK`, not `IPV4_ONLY` |

The reason I got them wrong: I wrote plausible-looking HCL from memory and
trusted it. **Guessing provider schemas is how you ship infrastructure that
doesn't apply.** The fix that actually worked was dumping the real schema:

```bash
terraform providers schema -json > schema.json
# note: this requires the backend block removed, or it fails with
# "Backend initialization required". Copy to a scratch dir and strip it.
```

Then reading `image_repository` → `['image_identifier', 'image_repository_type']`
settled in one shot what three rounds of guessing had not.

---

## Prerequisites before `terraform apply`

**You must create these by hand first.** They cannot be managed by the stack
that depends on them:

```bash
# 1. State backend — one bucket + lock table for the whole org, forever.
aws s3api create-bucket --bucket my-terraform-state-us-east-1 --region us-east-1
aws dynamodb create-table \
  --table-name my-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 2. The API key secret — out of band, so the value never enters state.
aws secretsmanager create-secret --name dev/openai \
  --secret-string '{"OPENAI_API_KEY":"sk-..."}'
```

Put the resulting ARNs into `envs/dev.tfvars` (copy from `envs/example.tfvars`).

Then:

```bash
cp envs/example.tfvars envs/dev.tfvars   # edit it
terraform init
terraform plan  -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars
```

`envs/*.tfvars` is gitignored for the same reason state is — account IDs and
secret ARNs shouldn't be in your history.

---

## Cost controls built in

This is the part student infrastructure usually omits:

- **ECR lifecycle policy** — keep 30 tagged images, expire untagged after 7
  days. Without it, a CI loop that pushes per merge fills the account with
  thousands of untagged layers.
- **`min_instances = 0` in dev** — scales to zero, costs nothing when idle.
  The variable validation forces `min_instances >= 0`; set it to `1` only in
  prod, where a cold start on a user-facing request is a support ticket.
- **Log retention** — 14 days dev, 90 days prod, enforced by creating the log
  group explicitly (App Runner's default is "never expire").
- **`allowed_account_ids`** on the provider — a mis-authenticated CLI fails at
  plan time instead of creating resources in the wrong account.

---

## What this is NOT

- **Not applied.** No AWS account was touched. Everything is validated, not
  deployed — `terraform validate` proves the config parses and type-checks, it
  does not prove the plan applies cleanly against a real account.
- **Not the whole production track.** Weeks 3–4 (Bedrock, SageMaker,
  multi-cloud, Langfuse observability, prompt-injection defence) are not here.
  They're the largest remaining gap and would need live cloud accounts to
  validate honestly.
- **Not VPC-secured.** Ingress defaults to public in non-prod. VPC ingress
  requires an `aws_apprunner_vpc_connector` to exist first; that's a
  deliberate follow-on, not an oversight.
- **Not auth'd.** Week 1 Day 3 of the course adds Clerk. `app/main.py` has a
  `Header()` placeholder that is deliberately unused — a stub auth that looks
  real is worse than none.

---

**Last updated:** 2026-10-21
**License:** MIT