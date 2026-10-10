---
title: L59 — Lambda — Environment Variables
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 11
duration: 4:42
---

# L59 — Lambda — Environment Variables

> Environment variables are how you keep configuration out of your
> code. They live on the function (or version), are 4 KB total, and
> can reference AWS Secrets Manager / SSM Parameter Store so that
> secrets are not stored in plain text in the function definition.

## Prereqs

- L57 (versions), L58 (aliases).

## Key terms

- **Environment variable** — a `KEY=VALUE` string set on the function,
  visible to the handler as `os.environ["KEY"]`.
- **KMS key** — used to encrypt env vars at rest. Default is an
  AWS-managed key, `aws/lambda`.
- **Secrets Manager** — AWS service for storing secrets. The Lambda
  service can resolve an env var *reference* to the secret value
  before invoking your code.
- **SSM Parameter Store** — AWS service for typed (String/StringList/SecureString) parameters. Same resolution pattern.
- **`/aws/lambda`** — the default KMS key alias used by Lambda.

## 1. Plain env vars

```python
import boto3
lam = boto3.client("lambda", region_name="us-east-1")
lam.update_function_configuration(
    FunctionName="my-api",
    Environment={
        "Variables": {
            "STAGE": "prod",
            "LOG_LEVEL": "INFO",
            "FEATURE_FLAG": "new_billing",
        }
    },
)
```

In code:

```python
import os
STAGE = os.environ["STAGE"]
```

Plain env vars are fine for non-secret config. They are visible in
the Lambda console and in the function configuration JSON — *don't*
put secrets here.

## 2. Why you should not store secrets in env vars

Even though the function config is encrypted at rest, every developer
with `lambda:GetFunctionConfiguration` can see the env var values.
A service like GitHub Actions that deploys the function will also
typically see them. **Use Secrets Manager or SSM SecureString
instead.**

## 3. Env var reference → Secrets Manager

Set the variable to a structured reference:

```python
lam.update_function_configuration(
    FunctionName="my-api",
    Environment={
        "Variables": {
            "DB_PASSWORD": "{{resolve:secretsmanager:arn:aws:secretsmanager:us-east-1:111122223333:secret:db-password-XXXXXX}}"
        }
    },
    KMSKeyArn="arn:aws:kms:us-east-1:111122223333:key/<your-key-id>",  # optional
)
```

When the function boots, Lambda resolves the placeholder by calling
Secrets Manager under the function's IAM role. The handler sees
`os.environ["DB_PASSWORD"]` as the *real* secret value.

Requirements:

- The function's execution role needs
  `secretsmanager:GetSecretValue` on the secret ARN.
- The Lambda service must be able to call Secrets Manager from the
  region.

> **Caching caveat.** Lambda caches resolved env values for the
> lifetime of the execution environment. If you rotate the secret,
> the running function may keep the old value until it is recycled
> (idle > 15 min or forced). Production code that depends on quick
> secret rotation should fetch the secret at handler start with
> `client.get_secret_value` instead.

## 4. Env var reference → SSM Parameter Store

Same shape, different service:

```python
"DB_HOST": "{{resolve:ssm:/myapp/db/host:1}}"
```

For SecureString parameters, add `WithDecryption`:

```python
"DB_PASSWORD": "{{resolve:ssm-secure:/myapp/db/password:1}}"
```

IAM: `ssm:GetParameter` and `kms:Decrypt` on the parameter / KMS key.

## 5. Read env vars safely in code

```python
import os

def get_required(name: str) -> str:
    val = os.environ.get(name)
    if val is None:
        raise RuntimeError(f"missing required env var {name}")
    return val

def get_int(name: str, default: int | None = None) -> int:
    raw = os.environ.get(name)
    if raw is None:
        if default is not None:
            return default
        raise RuntimeError(f"missing required int env var {name}")
    return int(raw)

STAGE = os.environ.get("STAGE", "prod")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
MAX_RETRIES = get_int("MAX_RETRIES", 3)
DB_PASSWORD = get_required("DB_PASSWORD")  # from Secrets Manager
```

## 6. Per-version, per-alias

Like memory and timeout, env vars are part of the function
*configuration*. A new version captures the env vars in effect at
publish time. A new alias inherits the function's current config.
So you can have:

- Alias `dev` → version 12 with `STAGE=dev` env
- Alias `staging` → version 14 with `STAGE=staging` env
- Alias `prod` → version 17 with `STAGE=prod` env

by republishing each version with its own env, then pointing the
alias at it. (This is the only sane way to keep one codebase across
stages.)

## Lecture summary

- Plain env vars are for non-secret config.
- Use `{{resolve:secretsmanager:...}}` and `{{resolve:ssm:...}}` for
  secrets.
- Function role needs `GetSecretValue` / `GetParameter` IAM
  permissions.
- Env vars are versioned automatically with `publish_version`.

## Hands-on (≈ 4 minutes)

```bash
# 1. Add a plain env var
python 11_lambda_advanced_concepts/code/env_var_set.py \
    --function my-api --key STAGE --value prod

# 2. Wire a Secrets Manager reference
python 11_lambda_advanced_concepts/code/env_var_secret.py \
    --function my-api --key DB_PASSWORD \
    --secret-arn arn:aws:secretsmanager:us-east-1:111122223333:secret:db-pw-XXXX

# 3. Verify
aws lambda get-function-configuration --function-name my-api \
    --query 'Environment.Variables'
```

## Quiz prep

- What's the size limit on env vars?
- How do you reference a Secrets Manager secret in an env var?
- Why might a freshly rotated secret still appear stale inside a
  warm Lambda?

## Further reading

- AWS — [Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- AWS — [Using Secrets Manager with Lambda](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html)
- AWS — [SSM Parameter Store references in Lambda](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-su-organize.html)
