# Section 1 Quiz — Foundations

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** In the API Gateway request lifecycle, at which step is the
Lambda Authorizer invoked?

- A. Before TLS termination
- B. After route resolution, before the integration is invoked
- C. After the integration returns
- D. Only on the 4xx error path

<details><summary>Show answer</summary>

**B — After route resolution, before the integration is invoked.**
API Gateway matches the request to a method on a resource, then
invokes the authorizer (if one is attached), then either rejects
with 403 (Deny) or forwards to the integration (Allow).

</details>

---

**Q2.** Which of the following is **not** one of the four built-in
authentication patterns in API Gateway?

- A. IAM (SigV4)
- B. Cognito User Pool
- C. Lambda Authorizer
- D. LDAP Authorizer

<details><summary>Show answer</summary>

**D — LDAP Authorizer.** API Gateway's four built-in patterns are
IAM, Cognito User Pool, Lambda Authorizer, and API Key. LDAP is
not a built-in; if you need it, you'd implement a Lambda Authorizer
that talks to your LDAP server.

</details>

---

**Q3.** Which field in the Lambda Authorizer response is the *identity*
the policy is for?

- A. `policyDocument.Statement[0].Resource`
- B. `context`
- C. `principalId`
- D. `methodArn`

<details><summary>Show answer</summary>

**C — `principalId`.** This is the identity API Gateway forwards as
`event.requestContext.authorizer.principalId` to the integration.

</details>

---

**Q4.** What is the only valid `Action` in an API Gateway authorizer
policy?

- A. `s3:GetObject`
- B. `execute-api:Invoke`
- C. `lambda:InvokeFunction`
- D. `apigateway:GET`

<details><summary>Show answer</summary>

**B — `execute-api:Invoke`.** Any other action will be rejected
silently (or break the request with a 500).

</details>

---

**Q5.** What is the maximum `timeout` you can set on a Lambda
Authorizer?

- A. 5 seconds
- B. 15 seconds
- C. 30 seconds
- D. 5 minutes

<details><summary>Show answer</summary>

**C — 30 seconds.** The default is 5 s, but you can configure up
to 30 s. Going higher would let one slow authorizer block many
concurrent requests.

</details>

---

**Q6.** What does the Lambda Authorizer return when the policy is
`Deny`?

- A. HTTP 401 Unauthorized
- B. HTTP 403 Forbidden
- C. The authorizer throws an exception
- D. The integration is invoked and the integration decides

<details><summary>Show answer</summary>

**B — HTTP 403 Forbidden.** API Gateway rejects with 403 and does
*not* invoke the integration.

</details>

---

**Q7.** Which version string is valid for an API Gateway authorizer
policy document?

- A. `"2008-10-17"`
- B. `"2012-10-17"`
- C. `"2016-08-01"`
- D. `null` (the field is optional)

<details><summary>Show answer</summary>

**B — `"2012-10-17"`.** API Gateway rejects `"2008-10-17"` even
though that value is valid for IAM user policies. The other
strings aren't valid IAM policy versions at all.

</details>

---

**Q8.** Which of the following is **not** an authentication pattern,
but rather a metering / throttling mechanism?

- A. IAM (SigV4)
- B. Cognito User Pool
- C. Lambda Authorizer
- D. API Key

<details><summary>Show answer</summary>

**D — API Key.** An API Key is a static opaque string that the
client sends in an `x-api-key` header. API Gateway checks the key
against a Usage Plan and applies the plan's throttle and quota. It
is not authentication.

</details>

---

**Q9.** In a Lambda Authorizer response, what two rules apply to the
`context` map?

- A. It must be a JSON object and may be nested
- B. It must be flat and all values must be strings
- C. It must be a list and all values must be strings
- D. It must be a JSON object with at most 10 keys

<details><summary>Show answer</summary>

**B — Flat and all values must be strings.** Violating either rule
causes API Gateway to return 500 to the client without invoking
the integration.

</details>

---

**Q10.** What's the difference between authentication (AuthN) and
authorization (AuthZ)?

- A. AuthN checks identity; AuthZ checks permission
- B. AuthN checks permission; AuthZ checks identity
- C. They are synonyms
- D. AuthN is for browsers; AuthZ is for mobile

<details><summary>Show answer</summary>

**A — AuthN checks identity; AuthZ checks permission.** A Lambda
Authorizer typically does both: it verifies the token (AuthN) and
returns a policy that allows or denies the request (AuthZ).

</details>
