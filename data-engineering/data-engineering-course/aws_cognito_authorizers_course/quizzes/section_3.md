# Section 3 Quiz — Cognito Identity Pools

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the
> question.

---

**Q1.** An **Identity Pool** is best described as:

- A. A managed user directory
- B. A token-exchange broker that trades a token (User Pool JWT, OIDC, SAML, social) for temporary AWS credentials
- C. A Lambda authorizer for API Gateway
- D. A CloudFront origin

<details><summary>Show answer</summary>

**B — A token-exchange broker.** Identity Pools do not authenticate; they federate. They take a token from a User Pool, an OIDC IdP, a SAML IdP, or a social IdP, and trade it for STS temporary credentials that can call S3, DynamoDB, Lambda, etc.

</details>

---

**Q2.** Which AWS service actually mints the temporary AWS credentials handed out by an Identity Pool?

- A. Cognito Identity
- B. AWS IAM
- C. AWS STS
- D. EC2 Instance Metadata Service

<details><summary>Show answer</summary>

**C — AWS STS.** Identity Pools call `sts:AssumeRoleWithWebIdentity` on your behalf, with the user's token, to mint credentials scoped to the IAM role you attached to the pool. The resulting credentials have a TTL of 1 hour by default.

</details>

---

**Q3.** Which **trust policy principal** is correct for an IAM role that a Cognito Identity Pool should be allowed to assume?

- A. `arn:aws:iam::123456789012:role/cognito-identity.amazonaws.com`
- B. `cognito-identity.amazonaws.com` (the Federated principal)
- C. `arn:aws:cognito-identity:::identity-pool/us-east-1:abc`
- D. `cognito-idp.<region>.amazonaws.com`

<details><summary>Show answer</summary>

**B — `cognito-identity.amazonaws.com`** (written as `{"Federated": "cognito-identity.amazonaws.com"}` in the trust policy). C and D are identity pool / user pool IDs, not principals; A is an ARN that doesn't make sense in a trust policy.

</details>

---

**Q4.** A condition block on a trust policy that scopes the role to **your** identity pool looks like:

- A. `"Condition": {"StringEquals": {"aws:RequestedRegion": "us-east-1"}}`
- B. `"Condition": {"StringEquals": {"cognito-identity.amazonaws.com:aud": "<identity-pool-id>"}}`
- C. `"Condition": {"StringEquals": {"sts:RoleSessionName": "alice"}}`
- D. There is no way to scope the trust policy to a specific pool.

<details><summary>Show answer</summary>

**B — `"Condition": {"StringEquals": {"cognito-identity.amazonaws.com:aud": "<identity-pool-id>"}}`.** Without this condition, **any** Cognito Identity Pool could assume your role — a serious cross-tenant risk.

</details>

---

**Q5.** Which policy variable lets you write a **per-user** S3 policy where each user can only access their own prefix?

- A. `${aws:username}`
- B. `${cognito-identity.amazonaws.com:sub}`
- C. `${cognito-identity.amazonaws.com:email}`
- D. `${s3:prefix}`

<details><summary>Show answer</summary>

**B — `${cognito-identity.amazonaws.com:sub}`.** It's the user's Identity ID (a UUID). You use it in `Resource` and `Condition.StringLike.s3:prefix` to scope per-user.

</details>

---

**Q6.** An Identity Pool's **`AllowUnauthenticatedIdentities`** flag, when set to `True`, allows:

- A. Anyone to call the API
- B. Anonymous users to obtain an Identity ID and assume the **guest role** you attach to the pool
- C. Multi-region replication
- D. The pool to call STS without an identity

<details><summary>Show answer</summary>

**B — Anonymous users can obtain an Identity ID and assume the guest role.** Use it for public read-only content. Always scope the guest role's permissions narrowly.

</details>

---

**Q7.** Which of the following `boto3` calls is **not implemented** by `moto` 5.x (and is therefore skipped or documented in the course's tests)?

- A. `cognito-identity:CreateIdentityPool`
- B. `cognito-identity:DescribeIdentityPool`
- C. `cognito-identity:SetIdentityPoolRoles`
- D. `cognito-identity:ListIdentityPools`

<details><summary>Show answer</summary>

**C — `cognito-identity:SetIdentityPoolRoles`** (raises `NotImplementedError`). The course's `identity_pool_demo.py` catches this and documents it. Create/Describe/List are all implemented in moto 5.x.

</details>

---

**Q8.** In an Identity Pool's trust policy, you should constrain the role assumption to your pool by:

- A. Setting the IAM role name to include the pool id
- B. Adding a `Condition.StringEquals` block on `cognito-identity.amazonaws.com:aud`
- C. Setting `MaxSessionDuration: 3600`
- D. Restricting by source IP

<details><summary>Show answer</summary>

**B — Adding a `Condition.StringEquals` block on `cognito-identity.amazonaws.com:aud`** with the pool id as the value. This is the only correct way to constrain the trust to your specific pool.

</details>

---

**Q9.** The IAM policy `${cognito-identity.amazonaws.com:sub}` resolves to:

- A. The user's email address
- B. The user's `sub` claim from their ID token
- C. The Identity ID assigned by Cognito (a stable UUID, valid for up to 365 days)
- D. The user's IAM role

<details><summary>Show answer</summary>

**C — The Identity ID assigned by Cognito.** It's a UUID that's stable for up to 365 days and is the principal you scope per-user access to. The `sub` from the ID token is not the same value.

</details>

---

**Q10.** The **guest role** (unauthenticated) should have permissions that are:

- A. Identical to the authenticated role
- B. **Strictly less** than the authenticated role (typically read-only on public assets)
- C. Admin-level (so guests can do anything)
- D. Empty (no permissions at all)

<details><summary>Show answer</summary>

**B — Strictly less** than the authenticated role. The guest role exists for public read-only content (marketing assets, public catalog). It should never have write access and should never have access to anything in your user-data bucket.

</details>
