# Section 5 Quiz — Advanced Patterns

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the
> question.

---

**Q1.** How many Lambda triggers does Cognito support?

- A. 4
- B. 7
- C. 14
- D. 32

<details><summary>Show answer</summary>

**C — 14.** They split into 3 categories: sign-up (3), authentication (8), and migration (1), plus the custom email/SMS sender and KMS-related triggers. In practice you'll use 3–5 of them.

</details>

---

**Q2.** The Lambda trigger for **injecting custom claims** (e.g. `custom:tenant_id`) into the ID token is:

- A. `pre_sign_up`
- B. `pre_authentication`
- C. `post_authentication`
- D. `pre_token_generation`

<details><summary>Show answer</summary>

**D — `pre_token_generation`.** You set `event.response.claimsOverrideDetails.claimsToAddOrOverride` in the Lambda; Cognito merges those claims into the ID and access tokens before returning them to the client.

</details>

---

**Q3.** To **block a suspended user** before the password is even checked, which trigger should you use?

- A. `pre_token_generation` (raise an exception)
- B. `pre_authentication` (raise an exception)
- C. `post_authentication` (raise an exception)
- D. `post_confirmation`

<details><summary>Show answer</summary>

**B — `pre_authentication`** and raise an exception. The exception is converted to a `NotAuthorizedException` and surfaced to the client as 401. The `pre_token_generation` trigger runs **after** the password check, so it's too late if you want to skip the password check.

</details>

---

**Q4.** The `CustomMessage` trigger is used to:

- A. Replace Cognito's email sender entirely
- B. Customize the body (and subject) of the verification / welcome / MFA / reset email
- C. Send SMS via Twilio
- D. Configure the Hosted UI's CSS

<details><summary>Show answer</summary>

**B — Customize the body and subject of the verification / welcome / MFA / reset email.** The trigger event includes a `code` and a `triggerSource` (which message it is). To replace the sender itself, use `CustomEmailSender` or `CustomSmsSender`.

</details>

---

**Q5.** The `CustomEmailSender` and `CustomSmsSender` triggers require which additional configuration?

- A. An SES verified domain
- B. A `KMSKeyID` so Cognito can encrypt the OTP before passing it to your Lambda
- C. An IAM role with `ses:SendEmail` permissions
- D. A Twilio account

<details><summary>Show answer</summary>

**B — A `KMSKeyID`**. Cognito encrypts the one-time code under your key before passing it to your custom sender. Without it, the trigger fails with a `KMSAccessDeniedException`. The other items (A, C) are good practice but not strictly required by Cognito.

</details>

---

**Q6.** In a SAML federation setup, which party is the **Service Provider (SP)** when Cognito is in the picture?

- A. The user's browser
- B. The corporate IdP (Okta, Azure AD)
- C. Cognito
- D. The user's app

<details><summary>Show answer</summary>

**C — Cognito.** It trusts the assertions issued by the IdP. Cognito is the SP; the corporate IdP is the IdP. (In L25 OIDC federation, the roles are analogous: Cognito is the relying party, the external IdP is the OP.)

</details>

---

**Q7.** In SAML, the **NameID** is typically mapped to which Cognito user attribute?

- A. `email`
- B. `name`
- C. `sub` (or `email`, depending on your mapping)
- D. `phone_number`

<details><summary>Show answer</summary>

**C — `sub` (or `email`)** depending on your attribute mapping. The NameID is the SAML field that uniquely identifies the user; you map it to whatever Cognito attribute should be the canonical user identifier. Most teams map it to `sub`.

</details>

---

**Q8.** Which OIDC field is the **JWT-verification key set** for an OIDC IdP?

- A. `issuer`
- B. `client_id`
- C. `jwks_uri`
- D. `authorize_url`

<details><summary>Show answer</summary>

**C — `jwks_uri`**. It's one of the URLs in the OIDC discovery document at `/.well-known/openid-configuration`. Cognito fetches it when you register an OIDC provider and uses the public keys to verify the IdP's ID tokens.

</details>

---

**Q9.** When you wire **multiple IdPs** (Cognito + Google + Okta SAML) in a single User Pool, where does the user pick which one to use?

- A. The Hosted UI shows a button per IdP; the user picks
- B. The client app must redirect to the right `/oauth2/authorize?provider=...` URL
- C. The pool picks based on the email domain
- D. Multi-IdP setups are not supported

<details><summary>Show answer</summary>

**A — The Hosted UI shows a button per IdP; the user picks.** (You can also redirect to a specific provider with `?provider=Google` in the authorize URL, but the default is the button-per-IdP UI.)

</details>

---

**Q10.** The single **best resource** to learn Cognito's Lambda trigger event shapes is:

- A. The Cognito GitHub repo
- B. The official AWS docs page "Lambda triggers" with the per-trigger example JSON
- C. Stack Overflow
- D. This course (which is great, but you should still read the official docs)

<details><summary>Show answer</summary>

**B (and D, but mainly B).** The official AWS docs have a "Lambda triggers" page with example JSON for every trigger. Use it as the reference; the trigger event schemas change with Cognito API versions, and the docs are the source of truth.

</details>
