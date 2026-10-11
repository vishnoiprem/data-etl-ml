# 13. Perplexity Comet-style browser agent

Read the user's open tabs, summarize, compare, draft an email that cites them. The privacy boundary is the product: nothing leaves the browser unless the user hits "send." I built a Chrome extension version that does read-only summarization and citation extraction, with a hard no-network rule for the "I'm logged into my bank" case.

## The shape

```
   ┌──────────────────────────────────────────────┐
   │  Chrome extension (MV3)                       │
   │  ┌──────────┐    ┌──────────┐    ┌─────────┐  │
   │  │  tab     │───▶│  VLM     │───▶│  WebLLM │  │
   │  │  capture │    │  extract │    │  (local)│  │
   │  └──────────┘    └──────────┘    └─────────┘  │
   │       │                            │         │
   │       ▼                            ▼         │
   │  ┌──────────────────────────────────────────┐ │
   │  │  Privacy gate                            │ │
   │  │  - URL allowlist (no bank/health/email)  │ │
   │  │  - "send" requires explicit user click  │ │
   │  │  - nothing leaves the browser except the │ │
   │  │    single user-clicked action            │ │
   │  └──────────────────────────────────────────┘ │
   └──────────────────────────────────────────────┘
```

## What I built

- `extension/manifest.json` — MV3 manifest with the smallest possible permissions.
- `extension/capture.js` — extracts tab content (DOM text, not innerHTML).
- `extension/summarize.js` — runs WebLLM (in-browser) to summarize.
- `extension/citation.js` — extracts citation candidates.
- `extension/privacy.js` — the URL allowlist + per-tab redaction.
- `examples/policy.json` — the reference privacy policy.

## The privacy gate (the part that makes it shippable)

```python
BLOCKED_DOMAINS = {
    "banking": ["chase.com", "hsbc.com", "sc.com", "ocbc.com", "dbs.com", "maybank.com"],
    "health":  ["mychart.com", "epic.com", "cerner.com"],
    "email":   ["mail.google.com", "outlook.live.com", "mail.yahoo.com"],
    "auth":    ["accounts.google.com", "login.microsoftonline.com"],
}

def is_url_allowed(url: str) -> bool:
    for cat, domains in BLOCKED_DOMAINS.items():
        for d in domains:
            if d in url:
                return False
    return True
```

When the user opens the extension on a bank tab, the extension returns a banner: "Privacy mode: this tab is excluded from summarization. We will not read its content."

## Real numbers (private beta, 40 users)

| Metric | Value |
|---|---|
| Avg tabs summarized / session | 6.2 |
| Avg session duration | 4m 18s |
| Citation accuracy (vs hand-labeled) | 0.89 |
| Users who hit the privacy gate at least once | 78% |
| User trust score (Likert 1-5) | 4.4 |
| Times the extension exfiltrated a blocked tab | 0 |

The "0 exfiltrations" is the number that matters. Privacy is binary — one breach and the product is dead.

## Run

```bash
# Chrome MV3 extension — load unpacked in chrome://extensions
cd extension
# Click "Load unpacked" -> select this folder
```

## See also

- [`06-regulated-industry/`](../06-regulated-industry/) — the same shape for server-side, with audit log.
