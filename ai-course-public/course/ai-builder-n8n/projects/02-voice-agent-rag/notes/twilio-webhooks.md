# Twilio webhook notes — Project 02

The Twilio side is where 90% of the "my voice agent doesn't work" debugging happens. None of it is n8n's fault.

---

## The `<Gather>` verb is what makes SpeechResult exist

If your webhook payload has an empty `SpeechResult`, this is why. Twilio doesn't stream speech by default — you must ask for it with `<Gather>`:

```xml
<Response>
  <Gather
      input="speech dtmf"
      language="en-US"
      speechTimeout="auto"
      maxTimeout="15"
      action="https://your-n8n-host/webhook/voice/webhook"
      method="POST">
    <Say>Thanks for calling. What can I help you with?</Say>
  </Gather>
</Response>
```

Field by field:

| Attribute | Value | Why |
|---|---|---|
| `input` | `speech dtmf` | Both. `speech` alone means a caller who wants to press 1 gets nowhere. |
| `language` | `en-US` | Omit it and Twilio guesses badly on non-US callers. Match your KB. |
| `speechTimeout` | `auto` | Ends the gather on natural pause. `3` (fixed seconds) clips slow speakers. |
| `maxTimeout` | `15` | Hard ceiling. Without it, a silent caller holds the line open forever. |
| `action` | your n8n webhook URL | Where the gathered speech gets POSTed. |

The first webhook hit carries the *prompt* (`Say`) and no `SpeechResult`. The second carries the caller's answer. That's normal — you'll see two executions per turn.

---

## Form-encoded, not JSON

Twilio POSTs `application/x-www-form-urlencoded`. n8n parses that into `json.body` automatically — which is why `Parse Twilio Body` reads `$input.first().json.body ?? $input.first().json`. The fallback covers manual tests where you POST JSON directly.

Field names are **PascalCase**: `CallSid`, `From`, `To`, `CallStatus`, `SpeechResult`, `Digits`. Not `call_sid`.

---

## The response Content-Type is load-bearing

Twilio parses the response body as **TwiML (XML)**. If your `Respond to Twilio` node returns JSON — even valid JSON — Twilio reads no `<Response>`, speaks nothing, and the caller hears dead air. There is no error surfaced anywhere; Twilio just goes silent.

Set `Content-Type: application/xml` on the response node. Then verify by looking at the **raw response** tab in the n8n execution view, not the pretty-printed JSON panel.

---

## `<Say>` and special characters

Text inside `<Say>` is XML. An unescaped `&` or `<` produces malformed TwiML, and Twilio rejects the whole document. `Build TwiML Response` escapes `&`, `<`, `>` for exactly this reason.

This is not theoretical — LLM output containing "Terms & Conditions" is extremely common, and it will break your call every time that phrase appears.

---

## Call status values you'll see in `CallStatus`

| Status | Meaning | Should you respond with TwiML? |
|---|---|---|
| `ringing` | Inbound call starting | No — return empty 200 |
| `in-progress` | Connected, `<Gather>` active | Yes |
| `completed` | Caller hung up | No — call is over |
| `busy` / `no-answer` / `failed` | Carrier-level failure | No |

If your workflow tries to speak on a `completed` call, Twilio ignores it. Harmless, but it clutters your execution log — filter on `CallStatus === 'in-progress'` in `Parse Twilio Body` if the noise bothers you.

---

## `<Dial>` for escalation

```xml
<Response>
  <Say>Let me connect you with a teammate.</Say>
  <Dial>+15555550123</Dial>
</Response>
```

`<Dial>` must be the **last** verb in the document. Anything after it is ignored. `Build TwiML Response` puts `<Say>` first, `<Dial>` second — correct order.

The number goes in E.164 format (`+15555550123`), no spaces or dashes. A malformed number fails silently: the caller hears your `<Say>`, then line music forever.

---

## Test without spending minutes

Twilio's free trial gives a real number you can call, but every second counts against your ElevenLabs minutes (free tier is ~10 min/month). Before dialling:

1. **Test the n8n side first.** `curl -X POST <your-webhook> -d 'CallSid=CA_test&From=%2B15555550100&To=%2B15555550123&SpeechResult=what+is+my+refund+policy'`
2. Open the execution, confirm `SpeechResult` arrived, confirm Supabase returned chunks, confirm the TwiML in the response tab looks right.
3. *Then* call the number and trust it.

Step 1 costs nothing and catches ~all the bugs.

---

## Local development

Twilio must reach your n8n webhook over the public internet. From a laptop:

```bash
ngrok http 5678
```

Use the `https://<subdomain>.ngrok.io` URL in the Twilio console. Two gotchas:

- The ngrok URL changes on every restart unless you pay. Re-point the Twilio webhook each time.
- Set `WEBHOOK_URL=https://<subdomain>.ngrok.io` in your n8n container env, or n8n embeds the wrong URL in its own webhook responses.

---

**Last updated:** 2026-10-21