---
lecture: L22
title: "Lambda Triggers — Pre/Post Authentication, Pre Token Generation"
duration: "18:00"
section: 5
prereqs:
  - L21
---

# L22 — Lambda Triggers — Pre/Post Authentication, Pre Token Generation

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Advanced Patterns
> **Duration:** 18:00

## Prereqs

- Watched **L21 — Section Overview**.

## Key terms

- **Trigger event** — a JSON document Cognito sends to your Lambda.
  The schema is fixed per trigger and versioned (`version: 2`).
- **Trigger source** — a string field that tells you **which** trigger
  fired. e.g. `TokenGeneration_HostedAuth`, `PreSignUp_SignUp`,
  `PostAuthentication_Authentication`.
- **`groupConfiguration`** — the field in the trigger event that
  lists the user's groups. To add the user to a group during
  sign-up, set this in the `pre_token_generation` event.
- **`claimsOverrideDetails`** — the field you set in
  `pre_token_generation` to **inject** custom claims into the token.
- **Suppress trigger** — set in the `pre_sign_up` trigger to mark the
  user as auto-confirmed without sending a verification code.

## Lecture

In L21 I listed the 14 Lambda triggers Cognito supports. Today we
deep-dive the four most common: `pre_sign_up`, `pre_authentication`,
`post_authentication`, and `pre_token_generation`. By the end of
this lecture you'll be able to read a Cognito trigger event, identify
which trigger fired, and write the corresponding Lambda handler.

### The 4 triggers, in one table

| Trigger | When | Use case |
|---|---|---|
| `pre_sign_up` | Before a user is created (self-sign-up) | Validate email, block disposable domains, auto-confirm |
| `pre_authentication` | Before the password is checked | Block suspended users, add IP-based check |
| `post_authentication` | After successful sign-in | Audit log, update `last_seen`, notify Slack |
| `pre_token_generation` | After all checks pass, before tokens are minted | Inject custom claims |

The first three are "side-effect" hooks (they can short-circuit but
mostly they observe). The fourth is "transform" — it lets you
**modify the tokens** that come out.

### The trigger event shape

Every Cognito Lambda trigger event looks like this:

```json
{
  "version": 2,
  "triggerSource": "TokenGeneration_HostedAuth",
  "region": "us-east-1",
  "userPoolId": "us-east-1_aBcDeFgHi",
  "userName": "alice@example.com",
  "callerContext": {
    "awsSdkVersion": "aws-sdk-js-2.6.4",
    "clientId": "7a1b2c3d4e5f6g7h"
  },
  "request": {
    "userAttributes": {
      "sub": "505c1bfa-...",
      "email": "alice@example.com",
      "email_verified": true
    },
    "groupConfiguration": {
      "groupsToOverride": []
    }
  },
  "response": {}
}
```

The `triggerSource` tells you which trigger fired. The `request`
object has trigger-specific fields. The `response` object is what
your Lambda sets to influence Cognito's behavior.

### `pre_token_generation` — the most useful trigger

This is the trigger for **injecting custom claims**. The flow:

1. User signs in (any auth flow).
2. Cognito calls your Lambda.
3. Your Lambda sets
   `response.claimsOverrideDetails.claimsToAddOrOverride = { "custom:role": "admin" }`.
4. Cognito mints the ID and access tokens **with the new claim**.
5. Tokens are returned to the client.

Example Lambda:

```python
def handler(event, context):
    claims_to_add = {}

    # Look up the user in your DB
    user = db.get_user(event["userName"])
    if user.is_admin:
        claims_to_add["custom:role"] = "admin"
    claims_to_add["custom:tenant_id"] = str(user.tenant_id)

    event["response"] = {
        "claimsOverrideDetails": {
            "claimsToAddOrOverride": claims_to_add,
            "claimsToSuppress": [],   # e.g. ["email"] to strip PII
        }
    }
    return event
```

The custom claims appear in the ID token (and the access token, by
default — you can suppress them there). The Lambda runs on every
sign-in, so the claims are always fresh.

**Performance tip:** the trigger runs on every sign-in. Cache
expensive lookups (e.g. database calls) in a Lambda layer or use
DAX/ElastiCache to keep latency low.

### `pre_sign_up` — validation + auto-confirm

Use case: block disposable email domains, auto-confirm internal
users.

```python
BLOCKED_DOMAINS = {"mailinator.com", "tempmail.com", "10minutemail.com"}

def handler(event, context):
    email = event["request"]["userAttributes"]["email"]
    domain = email.split("@")[1]

    if domain in BLOCKED_DOMAINS:
        raise Exception(f"Email domain {domain!r} is not allowed")

    # Auto-confirm (skip email verification)
    event["response"] = {
        "autoConfirmUser": True,
        # Auto-verify the email attribute
        "autoVerifyEmail": True,
    }
    return event
```

**Critical:** to reject, raise an exception. To allow, set
`event["response"]`. To auto-confirm, set
`event["response"]["autoConfirmUser"] = True`.

### `pre_authentication` — block before the password check

Use case: short-circuit suspended accounts without even checking the
password.

```python
def handler(event, context):
    user_sub = event["userName"]
    if is_suspended(user_sub):
        raise Exception("Account suspended. Contact support.")

    return event
```

The exception is converted to a `UserNotConfirmedException` /
`NotAuthorizedException` and surfaced to the client as a 401.

### `post_authentication` — observability

Use case: audit logging, last-seen timestamp, "user signed in"
event for downstream analytics.

```python
def handler(event, context):
    user_sub = event["userName"]
    metrics.increment("cognito.signin", tags={"user": user_sub})
    db.update_last_seen(user_sub, when=datetime.utcnow())
    return event
```

Note: this trigger cannot fail the sign-in. The user is already
authenticated. If you need to fail the sign-in, use `pre_authentication`
or `pre_token_generation` (raise inside the Lambda; the sign-in
fails).

### Wiring the trigger to the pool

In boto3:

```python
cognito.update_user_pool(
    UserPoolId=pool_id,
    LambdaConfig={
        "PreSignUp":            "arn:aws:lambda:us-east-1:123456789012:function:cognito-pre-signup",
        "PreAuthentication":    "arn:aws:lambda:us-east-1:123456789012:function:cognito-pre-auth",
        "PostAuthentication":   "arn:aws:lambda:us-east-1:123456789012:function:cognito-post-auth",
        "PreTokenGeneration":   "arn:aws:lambda:us-east-1:123456789012:function:cognito-pre-token",
        "PostConfirmation":     "arn:aws:lambda:us-east-1:123456789012:function:cognito-post-confirm",
    },
)
```

The Lambda's **resource-based policy** must allow Cognito to invoke
it:

```python
lambda_.add_permission(
    FunctionName="cognito-pre-token",
    StatementId="AllowCognitoInvoke",
    Action="lambda:InvokeFunction",
    Principal="cognito-idp.amazonaws.com",
    SourceArn=f"arn:aws:cognito-idp:us-east-1:123456789012:userpool/{pool_id}",
)
```

Without this, Cognito silently can't invoke your Lambda and you get
mysterious 500 errors.

### Versioning

Cognito trigger events are versioned. `version: 2` is the current
standard. If you write `version: 1` (e.g. you copy from an old
tutorial), Cognito may accept it but the schema is different —
`event.request.userAttributes` becomes
`event.request.validationData` etc.

**Always use `version: 2`.**

### A combined example

A real production setup might have:

- `pre_sign_up`: validate email domain, suppress welcome email
- `pre_authentication`: check `last_failed_attempts` against a
  threshold
- `post_authentication`: log to CloudWatch, update `last_seen`
- `pre_token_generation`: inject `custom:tenant_id` and
  `custom:role`

That's the "small SaaS app" trigger setup. Anything more elaborate
gets a Lambda Authorizer (L19) instead.

### What's coming

L23 — the **custom message** and **custom email/SMS sender** triggers.
The remaining 3 most-useful triggers.