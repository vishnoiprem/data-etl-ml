# Section 5 Quiz — Advanced Patterns

> 8 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** When does a Lambda@Edge function run?

- A. In the API Gateway service
- B. In a CloudFront edge location, close to the user
- C. In the VPC of the API
- D. In the user's browser

<details><summary>Show answer</summary>

**B — In a CloudFront edge location, close to the user.** Lambda@Edge
functions run in ~13 AWS regions globally. Regular Lambda runs
in a single region.

</details>

---

**Q2.** What's the difference between viewer-request and
origin-request events?

- A. Viewer-request runs after the request is forwarded to origin
- B. Viewer-request runs before the request reaches origin; origin-request runs after
- C. They are the same
- D. Viewer-request is for WebSocket; origin-request is for REST

<details><summary>Show answer</summary>

**B — Viewer-request runs before the request reaches origin;
origin-request runs after.** Auth typically happens at
viewer-request so the bad traffic never reaches origin.

</details>

---

**Q3.** Which of the following is **not** a constraint of
Lambda@Edge?

- A. No environment variables
- B. No VPC
- C. No layers
- D. No CloudWatch logs

<details><summary>Show answer</summary>

**D — No CloudWatch logs.** Lambda@Edge functions *do* log to
CloudWatch, but the logs always go to `us-east-1` regardless of
where the function ran.

</details>

---

**Q4.** For a WebSocket API, the auth for the `$connect` route is
typically:

- A. IAM auth (SigV4) on every message
- B. A Lambda Authorizer attached to `$connect`
- C. A static API Key in the URL
- D. No auth — WebSockets are public

<details><summary>Show answer</summary>

**B — A Lambda Authorizer attached to `$connect`.** The
authorizer runs once at connect time; per-message auth is then
done in the integration Lambda if needed.

</details>

---

**Q5.** What is the `IdentitySource` path prefix for a WebSocket
API?

- A. `method.request.*`
- B. `route.request.*`
- C. `request.*`
- D. `websocket.request.*`

<details><summary>Show answer</summary>

**B — `route.request.*`.** REST APIs use `method.request.*`;
WebSocket APIs use `route.request.*`. A common source of bugs.

</details>

---

**Q6.** What is OIDC's `id_token` for, vs `access_token`?

- A. They are synonyms
- B. `id_token` proves identity; `access_token` proves permission to call an API
- C. `id_token` is for HTTP; `access_token` is for REST
- D. `id_token` is for admins; `access_token` is for users

<details><summary>Show answer</summary>

**B — `id_token` proves identity; `access_token` proves permission
to call an API.** Your authorizer should verify `access_token`s
on the server side, and check `token_use == "access"` for
Cognito.

</details>

---

**Q7.** Which of the following is **not** a reason to use a Lambda
Authorizer?

- A. The client uses a custom token format
- B. You need custom authorization logic
- C. You need to integrate with a third-party IdP
- D. Your API is internal to your AWS account and you only need IAM auth

<details><summary>Show answer</summary>

**D — Your API is internal to your AWS account and you only need
IAM auth.** For internal AWS APIs, IAM (SigV4) is the right
choice — zero code, zero cost, zero latency. The Lambda
Authorizer is for when you need *more* than what IAM offers.

</details>

---

**Q8.** For a high-volume internal API at 1M MAU, which option is
cheapest?

- A. Cognito User Pool Authorizer
- B. Lambda Authorizer
- C. IAM (SigV4) auth
- D. API Key + Usage Plan

<details><summary>Show answer</summary>

**C — IAM (SigV4) auth.** IAM is free. Cognito is $0.15 per MAU
above 50k ($142k/month at 1M MAU). A Lambda Authorizer at
1M invocations/day is ~$6/month plus compute. API Keys have no
MAU cost.

</details>
