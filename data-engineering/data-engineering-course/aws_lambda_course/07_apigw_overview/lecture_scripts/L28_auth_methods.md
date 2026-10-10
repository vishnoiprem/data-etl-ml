---
id: L28
title: "API Gateway — Authentication and Authorization Methods"
section: 7
duration: "6:48"
author: "Prem Vishnoi <prem.vishnoi@example.com>"
udemy_id: 28
---

# L28 — API Gateway — Authentication and Authorization Methods

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 7 — API Gateway Overview
> **Lecture duration target:** 6:48

## Prereqs

- L25, L26, L27. You should know what a REST API is, what a method is,
  and what an API key is (and is *not* — namely, it is not an
  authentication mechanism).
- Basic familiarity with IAM users, roles, and policies (section 4 of
  the AWS Glue course or any IAM 101 material is enough).
- A vague idea of what an OAuth2 / OIDC flow is. If you have ever
  signed into a third-party app with "Sign in with Google," you have
  used it.

## Key terms

- **Authentication** — proving *who* the caller is.
- **Authorization** — proving they are *allowed* to do what they are
  asking. In API Gateway, "authorization" is the per-method decision
  that comes after the identity is established.
- **IAM auth** — caller signs the request with AWS SigV4 using IAM
  credentials. The policy attached to those credentials must allow
  `execute-api:Invoke` on the method.
- **Cognito User Pool** — a managed user directory. You federate
  users in, you get back an OIDC ID/access token, you pass that
  token to API Gateway.
- **Cognito Identity Pool** — exchanges a token (Cognito, Google,
  Facebook, etc.) for *temporary* AWS credentials. Used when the
  caller needs to call AWS services directly, not just API Gateway.
- **Lambda Authorizer** — you write a Lambda that receives the
  request headers (or a bearer token from them) and returns an IAM
  policy. Use this for opaque auth tokens, custom JWT validation, or
  any non-standard scheme.
- **API Key** — covered in L27. Identifies the caller, does not
  authenticate them.

## Lecture

API Gateway supports five different mechanisms for authenticating and
authorizing a request. They are not mutually exclusive in a single API
but you should pick exactly one for any given method, because the
mechanisms run in a defined order and the first one that succeeds
short-circuits the rest. Picking the right one is the most important
architectural decision you make about your API, so L28 walks through
each and the decision points.

### 1. No auth (`NONE`)

The default. Anyone who can reach the URL can call the method. Useful
for internal health-check endpoints or purely public data APIs, but
should be your last choice for anything that touches user data or
incurs cost. In Use Case 2 in section 8 we will start with `NONE` to
get the integration working, then layer auth on top.

### 2. API Key

Covered in L27. The key is sent in the `x-api-key` header. API Gateway
looks up the key, checks whether it is attached to a usage plan, and
enforces the plan's throttling and quota. **This is identification,
not authentication.** The client could be anyone, but if you know
which key they used, you know which plan's limits to apply.

Use API Key when: you want to identify a *tenant* (a customer
account) and apply a rate limit, and you are willing to trust that
the client keeps the key secret. The key is usually distributed
out-of-band (the customer pastes it into their config file) and you
rotate it by issuing a new key and deactivating the old one.

### 3. IAM auth

The client signs the request with AWS Signature Version 4 using
long-term IAM credentials (an access key + secret) or, more commonly,
short-term credentials from STS (an assumed role). API Gateway calls
`sts:GetCallerIdentity` (under the hood, `iam:PassRole`-style
checks) to validate the signature, then evaluates the IAM policy
attached to the credentials. The policy must allow
`execute-api:Invoke` on the method's ARN.

Use IAM auth when: the client is another AWS service in your
account, or another AWS account that you trust, and you want
cryptographic request signing (no shared secret to leak). This is
the right answer for service-to-service APIs inside one
organization.

### 4. Cognito User Pool

You create a Cognito User Pool (a managed user directory that
supports sign-up, sign-in, password reset, MFA, and federated
identity providers like Google and Facebook). Your app signs the
user in, gets back an OIDC ID token, and sends the token in the
`Authorization: Bearer <token>` header. API Gateway validates the
token against the User Pool's JWKS endpoint automatically. You can
also configure "token claims" mapping to filter by group or other
claims (e.g. only users in the `admin` group can call `DELETE`).

Use Cognito User Pool when: you have end users with usernames and
passwords (or you want to federate them through Google/Facebook/etc.)
and you want the user-management story to be fully managed.

### 5. Cognito Identity Pool

Cognito Identity Pools are different. They are not user directories.
They take a token (from Cognito User Pool, from Google, from
Facebook, from a custom auth provider) and *exchange it for
temporary AWS credentials*. You use an Identity Pool when the
caller needs to call AWS services directly with those credentials
(e.g. upload to S3, write to DynamoDB) rather than call API
Gateway.

A REST API method can be wired directly to a Cognito Identity Pool
as the auth mechanism. The client sends the Identity Pool's
temporary credentials, signs the request with them, and the
underlying IAM role determines what they can do.

Use Cognito Identity Pool when: the client is a mobile or browser
app that needs to talk to multiple AWS services (not just your
API) and you want short-lived, automatically-rotating AWS
credentials instead of long-term access keys.

### 6. Lambda Authorizer (formerly "Custom Authorizer")

You write a Lambda function that API Gateway invokes *before* your
backend Lambda. The authorizer Lambda receives the request (or
just the headers / a bearer token from them), does whatever
validation you need — check a JWT signature against your own
issuer's public key, call out to a third-party auth service,
inspect a custom header — and returns an IAM policy document
that says "allow" or "deny" plus optional context that flows
into the backend event.

Use Lambda Authorizer when: the auth scheme is not natively
supported by API Gateway (custom JWT, opaque tokens, third-party
identity providers, machine-to-machine client credentials). This
is the most flexible option and is what you will use when you
need fine-grained, custom logic.

### Decision framework

| Scenario | Pick |
|---|---|
| Public, unauthenticated read-only data | `NONE` |
| Identify a tenant, apply a rate limit, no user identity needed | API Key |
| Service-to-service inside your AWS org | IAM auth |
| End users with username/password or social login | Cognito User Pool |
| Mobile/browser app calling multiple AWS services | Cognito Identity Pool |
| Custom JWT, third-party IdP, or non-standard scheme | Lambda Authorizer |

For Use Case 2 (section 8) we will start with `NONE`, then add an API
Key. For the GenAI Bedrock API in section 10 we will leave it
`NONE` for simplicity but apply a usage plan. For the Lambda
Authorizer deep-dive in section 9 we will build a custom JWT
validator; the Cognito User Pool hands-on in L38–L39 will exercise
the federated user-pool path.

## Hands-on

Conceptual. The hands-on for the auth mechanisms covered in this
lecture lives in section 9 (Lambda Authorizer — L36/L37) and
section 9 (Cognito Authorizer — L38/L39). For L28 specifically,
your task is to map each "real-world scenario" you have personally
encountered onto the six mechanisms above, and to memorize the
trade-off: API Key is *not* authentication, Cognito User Pool is
*not* the same thing as Cognito Identity Pool, and Lambda
Authorizer is the escape hatch for anything AWS does not natively
support.

## Quiz prep

1. Why is an API Key not considered an authentication mechanism?
2. What is the difference between Cognito User Pool and Cognito
   Identity Pool?
3. When would you reach for a Lambda Authorizer instead of the
   native mechanisms?
4. For service-to-service APIs inside your own AWS organization,
   which auth mechanism is the most natural fit, and why?
5. If a client needs to call S3 directly *and* call your API,
   which mechanism gives them temporary AWS credentials?

## Further reading

- AWS Docs — *Control access to a REST API*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html
- AWS Docs — *Use API Gateway Lambda authorizers*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
- AWS Docs — *Use Amazon Cognito user pool as authorizer*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html
- L36–L39 (section 9) — the full hands-on for Lambda and Cognito
  authorizers.
