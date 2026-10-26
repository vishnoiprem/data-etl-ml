# Section 2 Quiz — Cognito User Pools

> 12 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the
> question.

---

**Q1.** A Cognito User Pool consists of how many **sub-components**?

- A. 1 — it's just a user database
- B. 2 — schema and directory
- C. 4 — schema, IdP list, directory, app clients (plus optional resource servers, groups, and domain)
- D. 5 — schema, IdP list, directory, app clients, and the Hosted UI

<details><summary>Show answer</summary>

**C — 4 — schema, IdP list, directory, app clients** (plus optional resource servers, groups, and a Hosted UI domain). The schema defines the attributes; the IdP list says who can authenticate the users; the directory is the actual user store; the app clients are the per-app configurations.

</details>

---

**Q2.** You're building a React SPA. Which app-client setting should you **never** set to `True`?

- A. `AllowedOAuthFlows` includes `code`
- B. `GenerateSecret`
- C. `AllowedOAuthFlowsUserPoolClient`
- D. `PreventUserExistenceErrors`

<details><summary>Show answer</summary>

**B — `GenerateSecret`.** SPAs run in the browser; their code is fully visible to the user. Generating a client secret and embedding it in the SPA bundle means anyone can extract the secret. For SPAs and mobile apps, always use `GenerateSecret: False` and rely on PKCE for security.

</details>

---

**Q3.** Which `PasswordPolicy` setting is **most strongly recommended** by NIST 800-63B (and is the only single-knob you should care about)?

- A. `RequireSymbols: True`
- B. `RequireUppercase: True`
- C. `MinimumLength: 12`
- D. `RequireNumbers: True`

<details><summary>Show answer</summary>

**C — `MinimumLength: 12`.** NIST 800-63B (and the modern security community) recommends length over complexity. A 12-character password with no other complexity rules is stronger than an 8-character `P@ssw0rd!` and is much easier to remember.

</details>

---

**Q4.** You're using the `pre_token_generation` Lambda trigger to inject a `custom:tenant_id` claim. When does the trigger run?

- A. Before the user enters their password
- B. After successful authentication but before Cognito mints the ID/access tokens
- C. After the ID/access tokens have been issued
- D. Only on the first sign-in, not on subsequent ones

<details><summary>Show answer</summary>

**B — After successful authentication but before Cognito mints the ID/access tokens.** This is what makes it the right hook for injecting custom claims. The `event.response.claimsOverrideDetails.claimsToAddOrOverride` dict you set will appear in the ID and access tokens.

</details>

---

**Q5.** What is the difference between `USER_SRP_AUTH` and `USER_PASSWORD_AUTH`?

- A. `USER_SRP_AUTH` uses the Secure Remote Password protocol; the password never leaves the client. `USER_PASSWORD_AUTH` sends the password (over TLS) to the server.
- B. `USER_SRP_AUTH` is for server-side apps; `USER_PASSWORD_AUTH` is for SPAs.
- C. `USER_PASSWORD_AUTH` is more secure than `USER_SRP_AUTH`.
- D. They are the same flow with different names.

<details><summary>Show answer</summary>

**A — `USER_SRP_AUTH` uses the Secure Remote Password protocol; the password never leaves the client. `USER_PASSWORD_AUTH` sends the password (over TLS) to the server.** SRP is the recommended client-side flow because a server breach never leaks the password. ROPC (`USER_PASSWORD_AUTH`) is acceptable only for first-party server-side apps where you control the wire.

</details>

---

**Q6.** The `cognito:groups` claim in an ID token is populated from what?

- A. Custom attributes on the user
- B. Cognito User Pool **groups** the user belongs to (administered via `admin_add_user_to_group`)
- C. The App Client's `AllowedOAuthScopes`
- D. The user's email domain

<details><summary>Show answer</summary>

**B — Cognito User Pool groups** administered via `admin_add_user_to_group` (or the console). The groups become the RBAC building blocks; you can attach IAM roles to them and they appear as the `cognito:groups` claim in the ID token.

</details>

---

**Q7.** Which two `PasswordPolicy` settings are part of the **Cognito default** and are often **unchanged** but should be reviewed for your app's threat model?

- A. `MinimumLength` and `TemporaryPasswordValidityDays`
- B. `RequireUppercase` and `RequireLowercase`
- C. `RequireNumbers` and `RequireSymbols`
- D. All of the above

<details><summary>Show answer</summary>

**A — `MinimumLength` (default 8) and `TemporaryPasswordValidityDays` (default 7).** Per NIST 800-63B, you should raise the min length to 12 and disable the complexity booleans. The temp password validity is a knob that affects forced-password-change flows.

</details>

---

**Q8.** What's the role of `MfaConfiguration` in a User Pool?

- A. It picks the MFA method (SMS, TOTP, or email)
- B. It enables MFA at the pool level: `OFF`, `OPTIONAL`, or `ON` (mandatory for all users)
- C. It defines the MFA TOTP secret
- D. It enables the Have-I-Been-Pwned check

<details><summary>Show answer</summary>

**B — It enables MFA at the pool level: `OFF`, `OPTIONAL`, or `ON`.** Combined with `EnabledMfas: ["SMS_MFA", "SOFTWARE_TOKEN_MFA"]`, it controls which users must enroll in MFA and which methods are available.

</details>

---

**Q9.** Your User Pool has `MfaConfiguration: ON` but you have legacy users who haven't enrolled. What happens on their first sign-in?

- A. They are rejected with 401.
- B. Cognito returns the `SOFTWARE_TOKEN_MFA` challenge; your app must call `associate_software_token` and `verify_software_token` to enroll them.
- C. Cognito auto-enrolls them in SMS MFA.
- D. The pool errors out.

<details><summary>Show answer</summary>

**B — Cognito returns the `SOFTWARE_TOKEN_MFA` challenge; your app must call `associate_software_token` and `verify_software_token` to enroll them.** The flow is: challenge → associate → user scans QR → user enters code → verify. The user is then signed in and enrolled for future sign-ins.

</details>

---

**Q10.** You create a custom attribute `plan` and set it on a user. In the user's next ID token, what is the attribute's name?

- A. `plan`
- B. `custom:plan`
- C. `attribute:plan`
- D. `user.plan`

<details><summary>Show answer</summary>

**B — `custom:plan`.** Cognito prefixes all custom attributes with `custom:` in JWTs and API calls. The schema name is the bare name; the JWT/API name is `custom:<bare>`.

</details>

---

**Q11.** What's the most secure way to send a user's email attribute from your backend to your frontend?

- A. In a query parameter
- B. In a custom HTTP header
- C. From the validated ID token claims (`event.requestContext.authorizer.claims.email`)
- D. From the `userAttributes` query parameter

<details><summary>Show answer</summary>

**C — From the validated ID token claims.** The claims are signed by Cognito; if you read them from the validated event, you know they're authentic. Sending the email in a query parameter or a custom header is spoofable.

</details>

---

**Q12.** Which field in the `pre_token_generation` event is the right place to **inject** custom claims?

- A. `event.request.userAttributes`
- B. `event.response.claimsOverrideDetails.claimsToAddOrOverride`
- C. `event.callerContext.clientId`
- D. `event.response.userAttributes`

<details><summary>Show answer</summary>

**B — `event.response.claimsOverrideDetails.claimsToAddOrOverride`.** The dict you set there is merged into the ID and access tokens. Use `claimsToSuppress` to strip claims (e.g. `email`) for privacy.

</details>
