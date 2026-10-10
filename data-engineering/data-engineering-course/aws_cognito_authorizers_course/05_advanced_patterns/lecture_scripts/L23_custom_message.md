---
lecture: L23
title: "Custom Message & Email/SMS Sender Triggers"
duration: "14:00"
section: 5
prereqs:
  - L22
---

# L23 — Custom Message & Email/SMS Sender Triggers

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 5 — Advanced Patterns
> **Duration:** 14:00

## Prereqs

- Watched **L22 — Lambda Triggers**.

## Key terms

- **`CustomMessage` trigger** — runs when Cognito is about to send a
  verification code, welcome email, MFA code, or password-reset code.
  Lets you customize the body.
- **`CustomEmailSender` trigger** — replaces Cognito's default email
  sender entirely. You send the message through your own SES config.
- **`CustomSmsSender` trigger** — same idea, for SMS. Send via
  Twilio, Pinpoint, or your own SMS provider.
- **`KMSKeyID`** — the KMS key ARN that Cognito uses to encrypt the
  one-time password before passing it to your custom sender. Without
  this, the `CustomEmailSender` / `CustomSmsSender` triggers can't
  pass the OTP securely.
- **`verificationCode`** — the one-time code your custom sender
  Lambda receives. **Must be transmitted in the body** the user
  receives.

## Lecture

In L22 we covered the 4 most-used triggers. Today we cover 3 more
that round out the production setup: `CustomMessage` (customize the
email body), `CustomEmailSender` (send email yourself), and
`CustomSmsSender` (send SMS yourself). By the end of this lecture
you'll know when each is appropriate, and how to wire them.

### The 3 custom-message triggers

| Trigger | What it does |
|---|---|
| `CustomMessage` | Customize the body of the verification / welcome / MFA / reset email |
| `CustomEmailSender` | Replace Cognito's email sender entirely (e.g. with your SES config) |
| `CustomSmsSender` | Replace Cognito's SMS sender entirely (e.g. with Twilio) |

These are all about **how the message gets to the user** — the body
and the transport. The auth flow itself is unchanged.

### `CustomMessage` — customize the body

The default Cognito verification email looks like this:

```
Your verification code is: 123456
```

It's functional but ugly. With `CustomMessage`, you can make it
look like the rest of your brand:

```python
def handler(event, context):
    code = event["request"]["code"]
    user = event["request"]["userAttributes"]

    subject, body = build_email(
        trigger_source=event["triggerSource"],
        code=code,
        user=user,
    )

    event["response"] = {
        "smsMessage": None,
        "emailMessage": body,
        "emailSubject": subject,
    }
    return event
```

`event["triggerSource"]` tells you which message it is:

| `triggerSource` | Message |
|---|---|
| `CustomMessage_AdminCreateUser` | Welcome email with temporary password |
| `CustomMessage_ResendCode` | Verification code resend |
| `CustomMessage_ForgotPassword` | Password-reset code |
| `CustomMessage_UpdateUserAttribute` | Attribute-update verification (e.g. new email) |
| `CustomMessage_VerifyUserAttribute` | Same as above |
| `CustomMessage_Authentication` | MFA code |

You can branch on the trigger source to produce different bodies
for each.

### `CustomEmailSender` — send through your own SES

Cognito's built-in email sender is fine for testing, but for
production you usually want your own SES verified domain and DKIM
signing. The `CustomEmailSender` trigger lets you do exactly that.

```python
def handler(event, context):
    # Cognito encrypts the OTP under your KMS key. We decrypt it here.
    code = event["request"]["code"]
    user = event["request"]["userAttributes"]

    # Decrypt the OTP if it was encrypted (it usually is)
    if "kmsKeyId" in event["request"]:
        code = decrypt_with_kms(code, event["request"]["kmsKeyId"])

    # Send through SES
    ses.send_templated_email(
        Source="noreply@your-app.com",
        Destination={"ToAddresses": [user["email"]]},
        Template="CognitoVerification",
        TemplateData=json.dumps({"code": code}),
    )
    return event
```

Wiring:

```python
cognito.update_user_pool(
    UserPoolId=pool_id,
    LambdaConfig={
        "CustomEmailSender": {
            "LambdaArn": "arn:aws:lambda:...:function:cognito-email-sender",
            "LambdaVersion": "V1_0",
        },
        "KMSKeyID": "arn:aws:kms:us-east-1:123456789012:key/abcd-...",
    },
)
```

Two things to set:

1. `CustomEmailSender.LambdaArn` — your Lambda
2. `KMSKeyID` — required so Cognito can encrypt the OTP

The Lambda's resource policy must allow Cognito to invoke it.

### `CustomSmsSender` — send SMS yourself

Same pattern. Most teams use this to:

- Use Twilio (cheaper than Cognito's SMS pricing in some regions)
- Send SMS in regions Cognito doesn't support
- Get delivery receipts and proper analytics

```python
def handler(event, context):
    code = decrypt_with_kms(event["request"]["code"], event["request"]["kmsKeyId"])
    phone = event["request"]["userAttributes"]["phone_number"]

    twilio.messages.create(
        body=f"Your verification code: {code}",
        from_="+15551234567",
        to=phone,
    )
    return event
```

### Cost comparison

| | Cognito built-in | Custom (Twilio / SES) |
|---|---|---|
| Email | Free in `us-east-1`, capped otherwise | SES $0.10/1000 |
| SMS | ~$0.05/SMS in the US | Twilio $0.0079/SMS (US) |
| Delivery analytics | Basic | Full |
| Custom body | Yes (CustomMessage) | Yes |
| Custom domain | No | Yes (SES verified domain + DKIM) |
| Production fit | Hobby / dev | Production |

For most production apps, **custom SMS sender + CustomMessage for
email** is the right combo. Email goes through your SES config with
the default body; SMS goes through Twilio.

### The KMS requirement

The `CustomEmailSender` and `CustomSmsSender` triggers **require a
KMS key** (`KMSKeyID` in the trigger config). The key must be in
the same region as the User Pool. Cognito encrypts the OTP under
your key before passing it to your Lambda; your Lambda decrypts it
before sending.

If you forget the KMS key, the trigger fails silently with a
`KMSAccessDeniedException` in the Lambda logs.

### Putting it together

The full "production email + SMS" setup:

```python
cognito.update_user_pool(
    UserPoolId=pool_id,
    EmailConfiguration={
        "EmailSendingAccount": "DEVELOPER",   # use SES, not Cognito
        "SourceArn": "arn:aws:ses:us-east-1:123456789012:identity/your-app.com",
        "From": "noreply@your-app.com",
        "ReplyToEmailAddress": "support@your-app.com",
    },
    LambdaConfig={
        "CustomMessage": "arn:aws:lambda:...:function:cognito-custom-message",
        "CustomEmailSender": {
            "LambdaArn": "arn:aws:lambda:...:function:cognito-email-sender",
            "LambdaVersion": "V1_0",
        },
        "CustomSmsSender": {
            "LambdaArn": "arn:aws:lambda:...:function:cognito-sms-sender",
            "LambdaVersion": "V1_0",
        },
        "KMSKeyID": "arn:aws:kms:us-east-1:123456789012:key/abcd-...",
    },
)
```

This is roughly the "minimum viable production" Cognito email/SMS
configuration. Most apps will also add `pre_token_generation`
(L22) on top.

### What's coming

L24 — SAML 2.0 federation. The biggest reason enterprises choose
Cognito over Auth0 / Okta.