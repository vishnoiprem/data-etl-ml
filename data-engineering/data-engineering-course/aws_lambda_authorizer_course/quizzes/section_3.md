# Section 3 Quiz — Token-Based Lambda Authorizer

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** What is the difference between a TOKEN authorizer and a
REQUEST authorizer?

- A. TOKEN authorizers only see the `Authorization` header; REQUEST authorizers see the full event
- B. TOKEN is for HTTP; REQUEST is for REST
- C. TOKEN is faster
- D. There is no difference

<details><summary>Show answer</summary>

**A — TOKEN authorizers only see the `Authorization` header;
REQUEST authorizers see the full event.** For a TOKEN authorizer,
the event is `{type, authorizationToken, methodArn}`. For a
REQUEST authorizer, the event includes `headers`, `queryStringParameters`,
`pathParameters`, `stageVariables`, and `requestContext`.

</details>

---

**Q2.** Does API Gateway strip the `Bearer ` prefix from the
`authorizationToken` before invoking the authorizer?

- A. Yes, always
- B. No — the authorizer receives the raw value of the `Authorization` header
- C. Only if the token is a JWT
- D. Only in `us-east-1`

<details><summary>Show answer</summary>

**B — No.** A well-behaved authorizer strips the `Bearer ` prefix
itself before verifying the token.

</details>

---

**Q3.** What is `methodArn`?

- A. The ARN of the authorizer function
- B. The ARN of the method being invoked, e.g. `arn:aws:execute-api:us-east-1:111:abcd/prod/GET/orders`
- C. The CloudFront distribution ARN
- D. The Lambda function ARN

<details><summary>Show answer</summary>

**B — The ARN of the method being invoked.** This is the canonical
`Resource` for the Allow policy.

</details>

---

**Q4.** What is the minimum valid Allow policy document?

- A. `{ "Action": "*", "Resource": "*" }`
- B. `{ "Version": "2012-10-17", "Statement": [{ "Effect": "Allow", "Action": "execute-api:Invoke", "Resource": "<methodArn>" }] }`
- C. `{ "Allow": true }`
- D. The empty object

<details><summary>Show answer</summary>

**B — The minimum valid Allow policy.** The `Version` must be
`"2012-10-17"`, the `Effect` must be `Allow`, the `Action` must
be `execute-api:Invoke`, and the `Resource` must be the method
ARN (or a wildcarded version of it).

</details>

---

**Q5.** What is `principalId` in the authorizer response?

- A. The IAM user's ARN
- B. The identity the policy is for, surfaced as `event.requestContext.authorizer.principalId` in the integration
- C. The same as `sub`
- D. A random string API Gateway assigns

<details><summary>Show answer</summary>

**B — The identity the policy is for, surfaced as
`event.requestContext.authorizer.principalId` in the integration.**
Most teams set it to the JWT's `sub` claim.

</details>

---

**Q6.** Why must the `context` map be flat?

- A. To keep CloudWatch logs readable
- B. Because API Gateway only carries a flat map of string-keyed, string-valued entries
- C. To prevent injection attacks
- D. To save money on Lambda invocations

<details><summary>Show answer</summary>

**B — Because API Gateway only carries a flat map of string-keyed,
string-valued entries.** Violating this rule causes API Gateway
to return 500 to the client without invoking the integration.

</details>

---

**Q7.** What should you return when a JWT's `exp` is in the past?

- A. An Allow policy
- B. A Deny policy
- C. A 500 Internal Server Error
- D. A custom 401 response

<details><summary>Show answer</summary>

**B — A Deny policy.** Expired tokens must always be rejected.

</details>

---

**Q8.** In a production authorizer, where should the JWT secret be
loaded from?

- A. Hard-coded in the source
- B. An environment variable set at deploy time
- C. AWS Secrets Manager or SSM Parameter Store
- D. The CloudWatch log group

<details><summary>Show answer</summary>

**C — AWS Secrets Manager or SSM Parameter Store.** Environment
variables work for some teams but are visible in the Lambda
console and are tricky to rotate. Secrets Manager is the standard.

</details>

---

**Q9.** What's the safest default for the Allow policy's `Resource`?

- A. `*` (allow everything)
- B. The `methodArn` from the event, unchanged
- C. A static ARN
- D. The empty string

<details><summary>Show answer</summary>

**B — The `methodArn` from the event, unchanged.** This means "I
allow this request for the method the client asked for, and no
more." Expanding the resource is a refinement, not a default.

</details>

---

**Q10.** What is the right way to handle a `PyJWTError` in the
authorizer?

- A. Re-raise it so API Gateway returns 500
- B. Catch it and return a Deny policy
- C. Log it and return an Allow policy
- D. Translate it to a custom 401 response

<details><summary>Show answer</summary>

**B — Catch it and return a Deny policy.** Any PyJWT exception —
`ExpiredSignatureError`, `InvalidSignatureError`, `MissingRequiredClaimError`,
etc. — means the token is invalid. The right response is Deny.

</details>

---

**Q11.** Which of these is the right `Resource` pattern for a
scope-based policy that grants admin access to all methods?

- A. `*`
- B. The `methodArn` from the event
- C. `f"{method_arn.rsplit('/', 2)[0]}/*"` — wildcard the resource and method
- D. The empty string

<details><summary>Show answer</summary>

**C — `f"{method_arn.rsplit('/', 2)[0]}/*"`.** This strips the
last two segments (the HTTP method and the resource path) and
appends `/*` to allow all methods under the same API and stage.

</details>

---

**Q12.** What does API Gateway do with a `Deny` policy that has
`principalId: "unauthorized"`?

- A. Invokes the integration with the unauthorized identity
- B. Returns 403 to the client; the integration is not invoked
- C. Returns 401
- D. Throws an internal error

<details><summary>Show answer</summary>

**B — Returns 403 to the client; the integration is not invoked.**
`principalId` is not used on a Deny — it's just for log lines.

</details>
