# Section 1 Quiz — Foundations (Authentication, Authorization, OAuth 2.0, OIDC, JWT)

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the
> question.

---

**Q1.** What is the single-sentence difference between **authentication** and **authorization**?

- A. Authentication is for users; authorization is for services.
- B. Authentication answers "who is this caller?"; authorization answers "what is this caller allowed to do?"
- C. Authentication is performed by Cognito; authorization is performed by IAM.
- D. Authentication uses passwords; authorization uses tokens.

<details><summary>Show answer</summary>

**B — Authentication answers "who is this caller?"; authorization answers "what is this caller allowed to do?"** Both are required for a secure request. Authentication with no authorization means every signed-in user has full access; authorization with no authentication means you're enforcing policies on anonymous traffic.

</details>

---

**Q2.** Which AWS service is responsible for managing the **identity of your end users** (i.e. the people on the other side of your REST API)?

- A. IAM
- B. AWS SSO (IAM Identity Center)
- C. Amazon Cognito
- D. AWS STS

<details><summary>Show answer</summary>

**C — Amazon Cognito.** IAM is for machine identity; IAM Identity Center is for your employees; STS mints temporary credentials. Cognito is the only AWS service purpose-built for end-user identity and authentication.

</details>

---

**Q3.** In OAuth 2.0, which role is responsible for **issuing access tokens**?

- A. The Resource Owner (the user)
- B. The Client (your app)
- C. The Authorization Server
- D. The Resource Server

<details><summary>Show answer</summary>

**C — The Authorization Server.** In Cognito, the Authorization Server is the User Pool's OAuth endpoint (`https://<prefix>.auth.<region>.amazoncognito.com/oauth2/token`).

</details>

---

**Q4.** Which OAuth 2.0 grant type is **strongly recommended** for SPAs (React, Vue, Angular) and mobile apps?

- A. Implicit grant
- B. Resource Owner Password Credentials (ROPC)
- C. Authorization Code + PKCE
- D. Client Credentials

<details><summary>Show answer</summary>

**C — Authorization Code + PKCE.** SPAs and mobile apps can't safely hold a client secret. PKCE (Proof Key for Code Exchange, RFC 7636) lets them prove they're the same client that started the request without a secret. Implicit grant is deprecated; ROPC is for first-party trusted apps only; Client Credentials is for service-to-service (no user).

</details>

---

**Q5.** What is the **difference** between an OAuth 2.0 access token and an OpenID Connect ID token?

- A. They are the same; OIDC is a synonym for OAuth.
- B. The access token is for the API; the ID token is for the client and asserts user identity.
- C. The access token is signed; the ID token is encrypted.
- D. The access token is opaque; the ID token is a JWT — except in Cognito, where they are both JWTs but the ID token has a different `aud` claim.

<details><summary>Show answer</summary>

**B — The access token is for the API; the ID token is for the client and asserts user identity.** In Cognito both are JWTs, but the access token's `aud` is the API's resource server id and its purpose is authorization; the ID token's `aud` is the App Client ID and its purpose is identity assertion.

</details>

---

**Q6.** Which header in a Cognito User Pool JWT indicates the **user pool that issued the token**?

- A. `aud`
- B. `iss`
- C. `sub`
- D. `exp`

<details><summary>Show answer</summary>

**B — `iss`.** It looks like `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>`. The `aud` is the App Client ID; the `sub` is the user UUID; the `exp` is the expiry epoch.

</details>

---

**Q7.** When verifying a JWT against a Cognito User Pool, which of the following is the **most security-critical** check?

- A. `exp` (expiry)
- B. The signature, validated with the pool's public key
- C. Pinning `alg: RS256` (rejecting `alg: none` and `alg: HS256`)
- D. `iss` (issuer)

<details><summary>Show answer</summary>

**C — Pinning `alg: RS256`.** If you accept `alg: none`, anyone can forge a token. If you accept `HS256` with the public key as the shared secret, an attacker who has the public key (everyone, since it's published at the JWKS endpoint) can mint valid signatures. `pyjwt`'s `algorithms=["RS256"]` argument is the single line that prevents this entire class of attack.

</details>

---

**Q8.** Where do you fetch the public keys needed to verify Cognito-issued JWTs?

- A. `https://<domain-prefix>.auth.<region>.amazoncognito.com/.well-known/jwks.json`
- B. `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json`
- C. The IAM console
- D. The user pool's `DescribeUserPool` API

<details><summary>Show answer</summary>

**B — `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json`.** The Hosted UI base URL (A) is for OAuth endpoints (`/oauth2/authorize`, `/oauth2/token`), not for JWKS. Cache this response for at least 5 minutes.

</details>

---

**Q9.** What is the **canonical user identifier** in a Cognito JWT that you should always log?

- A. `email`
- B. `cognito:username`
- C. `sub`
- D. `client_id`

<details><summary>Show answer</summary>

**C — `sub`.** It's a UUID that's immutable for the user's lifetime. The email can change; `cognito:username` is the User Pool's internal name and can change too. Always log `sub`.

</details>

---

**Q10.** A JWT payload is what?

- A. Encrypted with the issuer's private key
- B. Signed with the issuer's private key
- C. Base64URL-encoded and **readable by anyone** who has the token; signed (not encrypted) with the issuer's private key
- D. Compressed with gzip

<details><summary>Show answer</summary>

**C — Base64URL-encoded and readable by anyone; signed (not encrypted).** The signature proves authenticity, not confidentiality. If you need both, look at JWE (RFC 7516), which Cognito does **not** use.

</details>
