# Assignment 4 — Lambda Authorizer with per-tenant policy

> **Section:** 09
> **Estimated time:** 3–4 hours
> **Pass bar:** working code, passing tests, deployment runbook.

## Goal

Extend the section 9 Lambda Authorizer so that the IAM policy it
returns is **per-tenant**: only the tenant encoded in the JWT's
`tenant` claim can invoke methods that match the route
`/{tenant}/items/*`. For all other tenants, return `Deny`.

## Tasks

1. **Authorizer changes** — in `code/lambda_authorizer/lambda_authorizer.py`,
   parse the `tenant` claim and construct the policy `Resource` list
   dynamically. The input `methodArn` is of the form
   `arn:aws:execute-api:...:.../prod/GET/acme/items`; you must
   generalise it so the policy allows the same path under the
   caller's tenant and denies others.

2. **Tests** — extend `test_lambda_authorizer.py` with at least three
   new cases:
   - token with `tenant=acme`, methodArn `acme/items` -> Allow
   - token with `tenant=acme`, methodArn `globex/items` -> Deny
   - token without a `tenant` claim -> Deny

3. **Documentation** — update `code/lambda_authorizer/README.md` with
   a 1-paragraph "Per-tenant policy" section explaining the design
   choice and the security trade-off (the Lambda must inspect every
   request, so caching becomes tenant-sensitive).

4. **Runbook** — write a short `RUNBOOK.md` in
   `code/lambda_authorizer/` covering: how to deploy, how to roll
   the secret, how to disable the authorizer in an emergency, and
   how to read the relevant CloudWatch log group.

## Acceptance criteria

- `pytest -q` in `code/lambda_authorizer/` passes with the new
  cases.
- The authorizer function returns a syntactically valid
  `AuthResponse` for both the Allow and Deny paths.
- A second-author reviewer can deploy the change by following the
  runbook alone.
- No secrets are committed; the secret value is sourced from
  environment / Secrets Manager.

## Stretch goals

- Switch the signing algorithm from `HS256` to `RS256` with a JWKS
  endpoint.
- Add a CloudWatch EMF metric for `Allow` vs `Deny` decisions.
- Add a request-based authorizer variant that uses the
  `X-Tenant-Id` header as the identity source instead of the JWT
  claim.
