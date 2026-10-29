# Section 4 Quiz — API Gateway + Cognito Authorizer

> 12 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the
> question.

---

**Q1.** On an API Gateway **REST API**, the authorizer type for a Cognito User Pool is:

- A. `JWT`
- B. `COGNITO_USER_POOLS`
- C. `COGNITO`
- D. `OIDC`

<details><summary>Show answer</summary>

**B — `COGNITO_USER_POOLS`.** REST APIs use this name. HTTP APIs use `JWT` (which is more general and accepts tokens from any OIDC IdP).

</details>

---

**Q2.** On an API Gateway **HTTP API**, the authorizer type for a Cognito User Pool is:

- A. `JWT`
- B. `COGNITO_USER_POOLS`
- C. `OIDC`
- D. `COGNITO_USER_POOL`

<details><summary>Show answer</summary>

**A — `JWT`.** HTTP API's JWT Authorizer accepts tokens from any OIDC IdP (including Cognito). The `JwtConfiguration.Audience` is the App Client ID, and `JwtConfiguration.Issuer` is the Cognito issuer URL.

</details>

---

**Q3.** In API Gateway, the **`IdentitySource`** for a Cognito User Pool Authorizer is typically:

- A. `method.request.header.Authorization`
- B. `method.request.querystring.token`
- C. `integration.request.header.Auth`
- D. Any of the above

<details><summary>Show answer</summary>

**A — `method.request.header.Authorization`** (the standard). Clients send `Authorization: Bearer <jwt>` and API Gateway extracts the token from that header.

</details>

---

**Q4.** API Gateway's Cognito User Pool Authorizer validates which of the following JWT claims by default?

- A. `exp` only
- B. `iss`, `aud`, `exp`, signature
- C. `sub`, `email`, `cognito:groups`
- D. Only the signature

<details><summary>Show answer</summary>

**B — `iss`, `aud`, `exp`, and the signature.** The authorizer fetches the pool's JWKS, verifies the RSA signature, and checks that `iss` matches the pool's issuer URL, `aud` matches the App Client ID, and `exp` is in the future.

</details>

---

**Q5.** Which of the following is the correct way to require a **scope** on a REST API method?

- A. `apigw.put_method(..., authorizationType="COGNITO_USER_POOLS", authorizationScopes=["https://api.example.com/read:items"])`
- B. `apigw.put_method(..., scopes=["openid"])`
- C. Define a Lambda authorizer that checks `event.scope`
- D. Scopes cannot be enforced on a REST API

<details><summary>Show answer</summary>

**A — `apigw.put_method(..., authorizationType="COGNITO_USER_POOLS", authorizationScopes=["https://api.example.com/read:items"])`.** API Gateway extracts the `scope` claim from the access token, splits on whitespace, and rejects requests that don't have the required scope.

</details>

---

**Q6.** To require that the caller be in the `admins` Cognito group, where should the check live?

- A. In the API Gateway method's `authorizationScopes`
- B. In your Lambda (or backend), reading `event.requestContext.authorizer.claims.get("cognito:groups", "")`
- C. In a Lambda Authorizer only
- D. Groups cannot be enforced on Cognito-issued tokens

<details><summary>Show answer</summary>

**B — In your Lambda**, reading the `cognito:groups` claim from the validated claims. The built-in Cognito User Pool Authorizer handles authentication; your code handles group-based authorization. (A Lambda Authorizer can do it too, but it's overkill for this case.)

</details>

---

**Q7.** When API Gateway forwards the validated claims to a Lambda, where do they appear in the event?

- A. `event.headers["Authorization"]`
- B. `event.requestContext.authorizer.claims` (REST) or `event.requestContext.authorizer.jwt.claims` (HTTP)
- C. `event.authorizer`
- D. `event.claims`

<details><summary>Show answer</summary>

**B — `event.requestContext.authorizer.claims`** on a REST API, or `event.requestContext.authorizer.jwt.claims`** on an HTTP API.

</details>

---

**Q8.** What's the **most security-critical line** in any JWT-validation code you write?

- A. `jwt.decode(token, key=public_key, audience=APP_CLIENT_ID, issuer=ISSUER)`
- B. `algorithms=["RS256"]`  (pinning the algorithm)
- C. `options={"require": ["exp", "iss", "aud", "sub", "token_use"]}`
- D. Caching the JWKS for 5 minutes

<details><summary>Show answer</summary>

**B — `algorithms=["RS256"]`**. Without algorithm pinning, a malicious client can submit a token with `alg: none` (no signature) or `alg: HS256` (signed with the public key as the shared secret), and `pyjwt` will accept it. Pinning `algorithms=["RS256"]` rejects both.

</details>

---

**Q9.** The **JWKS endpoint** for a Cognito User Pool is at:

- A. `https://<prefix>.auth.<region>.amazoncognito.com/.well-known/jwks.json`
- B. `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json`
- C. `https://cognito-idp.<region>.amazonaws.com/.well-known/jwks.json`
- D. The IAM role's `GetRolePolicy` endpoint

<details><summary>Show answer</summary>

**B — `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json`.** Option A is the Hosted UI's base URL (for OAuth endpoints), not the JWKS.

</details>

---

**Q10.** What's the **recommended JWKS cache TTL** for a production API?

- A. 0 (no cache; fetch per request)
- B. 5–60 minutes
- C. 1 day
- D. JWKS never rotates, so cache forever

<details><summary>Show answer</summary>

**B — 5–60 minutes.** Cognito rotates keys rarely (typically never for a given pool), so longer caches are safe. The minimum is 5 minutes to avoid DoS-able per-request fetches.

</details>

---

**Q11.** In the OAuth authorization code flow, **PKCE** is used to:

- A. Encrypt the access token
- B. Prevent authorization-code interception by binding the code to a `code_verifier` only the original client possesses
- C. Make the refresh token long-lived
- D. Replace the user pool's secret

<details><summary>Show answer</summary>

**B — Prevent authorization-code interception** by binding the code to a `code_verifier` only the original client possesses. SPAs and mobile apps use PKCE because they can't safely store a client secret.

</details>

---

**Q12.** API Gateway returns which status code if the JWT is **valid** but the request **lacks the required scope**?

- A. 401 Unauthorized
- B. 403 Forbidden
- C. 500 Internal Server Error
- D. 429 Too Many Requests

<details><summary>Show answer</summary>

**B — 403 Forbidden.** 401 is for missing or invalid tokens; 403 is for "you're authenticated, but you can't do this". A Lambda may also return 403 directly when enforcing custom authorization.

</details>
