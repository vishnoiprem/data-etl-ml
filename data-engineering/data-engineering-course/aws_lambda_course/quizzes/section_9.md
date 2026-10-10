# Section 9 Quiz — API Security: Lambda Authorizer & Cognito Authorizer

> 10 questions. Answers are hidden in collapsible blocks; click to
> reveal. Recommended time: 10 minutes.

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
