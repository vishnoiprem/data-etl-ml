# Cognito Cheat Sheet (one page, 2026 edition)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Source:** AWS Cognito documentation, current as of October 2026.
> **Format:** printable one-pager. The "real" deliverable is a PDF generated from this markdown by `pandoc`.

This file is a placeholder for `downloads/cognito_cheat_sheet.pdf`. The
content below is the authoritative text the PDF is built from.

## 1. Cognito User Pool — the big numbers

| Field | Hard limit | Notes |
|---|---|---|
| App clients per user pool | 1000 | |
| Lambda triggers per user pool | 14 | pre-token-gen, post-confirm, pre-auth, custom-message, … |
| User pool domain prefix | 63 chars | Must be unique per region. |
| Custom attributes | 50 | Each has a `Name` ≤ 20 chars. |
| Schema attributes | 50 standard + 50 custom | |
| Users per pool | millions (soft) | The 50 GB per pool storage limit is the practical cap. |
| Password policy — min length | 6 – 99 | Default 8. |
| SMS MFA monthly free | 0 | Always paid; use TOTP in dev. |
| Access token TTL | 5 min – 1 day | Default 60 min. |
| ID token TTL | 5 min – 1 day | Default 60 min. |
| Refresh token TTL | 1 h – 3650 d | Default 30 d. |

## 2. Cognito Identity Pool — the big numbers

| Field | Hard limit | Notes |
|---|---|---|
| Identity pools per account | 1000 | Soft cap, raise by support ticket. |
| Roles per identity pool | 2 (authenticated + unauthenticated) | One of each. |
| Linked login providers | multiple | cognito-idp, oidc, saml, facebook, google, apple, … |
| Identity ID TTL | 365 days | Re-used across sessions. |
| Credentials TTL | 15 min – 12 h | Default 1 h. |

## 3. JWT claims (ID token)

| Claim | Meaning |
|---|---|
| `sub` | Subject (Cognito user UUID, immutable). |
| `aud` | Audience = App Client ID. |
| `iss` | Issuer = `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>`. |
| `exp` | Expiry (epoch seconds). |
| `iat` | Issued-at. |
| `auth_time` | When the user last authenticated. |
| `cognito:groups` | Groups the user belongs to. |
| `cognito:username` | The user's username in the pool. |
| `email`, `email_verified` | Populated when `email` is an alias. |
| `token_use` | `"id"` (ID token) or `"access"` (access token). |

## 4. Helpful CLI one-liners

```bash
# Create a user pool
aws cognito-idp create-user-pool --pool-name my-pool \
    --username-attributes email --auto-verified-attributes email

# List user pools
aws cognito-idp list-user-pools --max-results 60

# Create an app client (no secret — for SPA / mobile)
aws cognito-idp create-user-pool-client --user-pool-id <id> \
    --client-name web --no-generate-secret \
    --allowed-o-auth-flows "code" --allowed-o-auth-scopes openid

# Initiate auth and capture tokens
aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH \
    --client-id <id> --auth-parameters USERNAME=alice@example.com,PASSWORD=...

# Decode a JWT (no verification — dev only)
python3 -c "import jwt,sys; print(jwt.decode(sys.argv[1], options={'verify_signature': False}))" "$TOKEN"
```

## 5. Service endpoints (most important)

| Service | Endpoint shape |
|---|---|
| Cognito User Pool JWKS | `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json` |
| Cognito Hosted UI | `https://<domain-prefix>.auth.<region>.amazoncognito.com` |
| Cognito Identity | `https://cognito-identity.<region>.amazonaws.com` |
| Cognito Sync (legacy) | `https://cognito-sync.<region>.amazonaws.com` |

## 6. IAM ARNs you'll need

| Role | ARN |
|---|---|
| Cognito authenticated role | `arn:aws:iam::aws:policy/AmazonCognitoReadOnly` (read) or your custom role |
| Cognito unauthenticated role | Custom role you author |
| API Gateway invoke | `arn:aws:execute-api:<region>:<acct>:<api-id>/<stage>/<METHOD>/<path>` |
