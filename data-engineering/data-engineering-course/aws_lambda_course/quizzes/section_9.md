# Section 9 Quiz — API Security: Lambda Authorizer & Cognito Authorizer

> 13 questions. Answers are hidden in collapsible blocks; click to
> reveal. Recommended time: 12 minutes.

---

### Q1

Which two `type` values can a Lambda Authorizer use, and what does
each one put in the event handed to the authorizer Lambda?

<details>
<summary>Answer</summary>

`TOKEN` — API Gateway sends the raw value of the `Authorization`
header as `authorizationToken`. `REQUEST` — API Gateway sends the
full request (headers, query string, path parameters, requestContext)
so the authorizer can make policy decisions on more than just the
bearer token.
</details>

---

### Q2

What is the **minimum** valid `AuthResponse` shape API Gateway will
accept from a Lambda Authorizer that allows the call?

<details>
<summary>Answer</summary>

```json
{
  "principalId": "<some string>",
  "policyDocument": {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "execute-api:Invoke",
      "Resource": "<the methodArn from the event>"
    }]
  }
}
```

`context` is optional. The `Resource` must include the incoming
`methodArn` or a wildcard covering it.
</details>

---

### Q3

Which IAM permission does API Gateway need on the authorizer Lambda,
and where is it granted — on the function's role, or on the function
itself?

<details>
<summary>Answer</summary>

`lambda:InvokeFunction` for principal `apigateway.amazonaws.com`,
granted on the **function's resource policy** (via
`aws lambda add-permission`), not on the function's execution role.
The execution role is what the function itself uses to call AWS APIs
after it runs; the resource policy is what lets other principals
invoke the function.
</details>

---

### Q4

What does API Gateway cache for a Lambda Authorizer, and what is the
default TTL? What is the minimum? What is the maximum?

<details>
<summary>Answer</summary>

API Gateway caches the **policy** keyed on the **identity source**
(the token for TOKEN authorizers, the combination of headers /
queries for REQUEST). Default TTL is **300 seconds**, minimum
**0 seconds**, maximum **3600 seconds**. Set on the authorizer via
`authorizerResultTtlInSeconds`.
</details>

---

### Q5

A request hits the API with a syntactically valid JWT signed by the
correct HS256 secret, but the `exp` claim is in the past. What status
code does the client see, and why?

<details>
<summary>Answer</summary>

`401 Unauthorized` (from API Gateway). PyJWT raises
`ExpiredSignatureError`, the authorizer catches it and returns a
`Deny` policy. API Gateway evaluates the policy and returns 401 to
the client. The integration Lambda is never invoked.
</details>

---

### Q6

What is the difference between a Cognito **User Pool** and a Cognito
**Identity Pool**? Which one powers the API Gateway Cognito
Authorizer?

<details>
<summary>Answer</summary>

A **User Pool** is a user directory that issues OIDC ID/access/refresh
JWTs and powers the API Gateway Cognito Authorizer. An **Identity
Pool** is a federation broker that exchanges a User Pool (or third-
party) identity for **AWS IAM credentials** (`AccessKeyId` /
`SecretAccessKey` / `SessionToken`); it is used for granting AWS
service access to federated users, not for API Gateway auth. The
two solve different problems and are commonly confused only because
they share the Cognito brand.
</details>

---

### Q7

What three claims does API Gateway verify on a JWT when you use the
Cognito User Pool Authorizer?

<details>
<summary>Answer</summary>

API Gateway verifies (1) the **signature** against the User Pool's
JWKS, (2) the **`exp` (expiration)** claim, and (3) the **`iss`
(issuer)** and **`aud` / `client_id` (audience)** claims so the token
was issued by your User Pool for your App Client.
</details>

---

### Q8

You have a REST API method wired with a `COGNITO_USER_POOLS`
authorizer. A request comes in with a perfectly valid access token
that has `scope = "openid email"`, but the method requires
`scope = "read:items"`. What status code does the client see, and
why is it not 401?

<details>
<summary>Answer</summary>

`403 Forbidden`. The token is valid, so the user *is* authenticated
— 401 would imply they are not. But API Gateway enforces the OAuth
scope check at the method level, and the token does not carry the
required scope, so the call is forbidden. Use 401 to signal "no
valid credentials" and 403 to signal "valid credentials, but the
caller is not allowed to do this."
</details>

---

### Q9

Your Lambda Authorizer integration returns the right policy, but the
downstream integration Lambda sees `event["requestContext"]["authorizer"]`
as an empty dict. Which field in the `AuthResponse` did you most
likely forget, and what does it need to look like?

<details>
<summary>Answer</summary>

You forgot the **`context`** field. It must be a flat
`{string: string}` map (no nested objects, no numbers, no booleans).
API Gateway drops anything that is not a string and silently forwards
an empty context to the integration.
</details>

---

### Q10

You are protecting an internal service-to-service API. The clients
are AWS Lambda functions in another account. The token format is OIDC
JWTs, and the IdP is AWS Cognito. Should you reach for a Lambda
Authorizer or a Cognito User Pool Authorizer? Justify in one
sentence.

<details>
<summary>Answer</summary>

Use the **Cognito User Pool Authorizer** — the IdP is already
Cognito, the token format is OIDC JWT, and the managed authorizer
gives you free JWKS validation, scope enforcement, and zero Lambda
invocations on the auth path. Reserve the Lambda Authorizer for
non-OIDC tokens or for cases where you need to embed business
context into the IAM policy at request time.
</details>

---

### Q11

You have a REST API with two resources, `/public/{proxy+}` and
`/internal/{proxy+}`. The `/public/*` resource is wired to a
Cognito User Pool Authorizer, the `/internal/*` resource is wired
to a Lambda Authorizer. A single integration Lambda serves both
routes. Which field on the proxy event should the handler inspect
to decide *which* authorizer ran, and why is that field the right
choice (vs. e.g. `path`)?

<details>
<summary>Answer</summary>

Inspect `event["requestContext"]["resourcePath"]` — the **matched
resource definition** (e.g. `/internal/{proxy+}` or `/public/{proxy+}`).
This is set by API Gateway from the resource tree at request time
and is unaffected by the URL the caller typed. `path` reflects the
raw URL and is unreliable for routing decisions because path
parameter values can be anything (e.g. `/internal/../public/...`).
</details>

---

### Q12

You attach a `COGNITO_USER_POOLS` authorizer to `GET /public/items`
and call the method with a valid access token. The integration
Lambda reads `event["requestContext"]["authorizer"]["claims"]["scope"]`
and gets a single space-separated string like
`"demo-pool/read:items demo-pool/write:items"`. Why is the value a
single string and not a list, and how do you would split it back
into a list in Python?

<details>
<summary>Answer</summary>

API Gateway flattens **all** JWT claims into a `string → string`
map before forwarding the event. Array / object claims are joined
into a single string — for space-separated values like OAuth
`scope`, you can split with `claim.split()`. (For comma-separated
claims, split on `,`. The exact separator is part of the claim's
specification.) If the claim is missing, the key is absent — it
is *not* present with an empty string.
</details>

---

### Q13

You add an API Key + Usage Plan to the secured Use Case 2 API and
enable `API Key Required = true` on `GET /public/{proxy+}`. A
client sends a request with a perfectly valid Cognito access token
but no `x-api-key` header. The client gets `403 Forbidden`. Which
layer returned the 403 — Cognito, the Usage Plan, or the
integration Lambda? Justify in one sentence.

<details>
<summary>Answer</summary>

The **Usage Plan / API Key** check returned the 403. The order of
operations is: authorizer first (token validates), then API Key
(required but missing), then throttle/quota, then the integration.
Because the token is valid the authorizer passes; because the key
is missing the method-level `apiKeyRequired=true` check rejects
the request before the integration is invoked. The Cognito
authorizer would have returned 401 (not 403) if the token were the
problem, and the integration is never reached when the key check
fails.
</details>
