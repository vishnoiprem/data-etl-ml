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

---

## What this is NOT

- **Not Comet.** Comet is a closed product with a
  hosted model, a multi-tab UX, and a polished
  browser shell. This is the *MV3 extension +
  in-browser LLM + privacy gate* shape, built with
  primitives you can swap (WebLLM → any in-browser
  model; the privacy gate is plain JS).
- **Not a server-side agent.** Everything runs in
  the browser; nothing leaves the user's machine
  except the user-clicked "send" action. The
  server-side equivalent (with full audit log) lives
  in
  [`../06-regulated-industry/`](../06-regulated-industry/).
- **Not a privacy-by-policy system.** The URL
  allowlist is *enforced in the extension code*,
  not promised in a privacy policy. The "0
  exfiltrations" number is a property of the code,
  not a contract. The user can read the code
  and verify.
- **Not a general-purpose agent.** This is
  *read-only* summarization + citation extraction
  + user-clicked "send." It doesn't fill forms,
  click buttons, or take actions on the page.
  For that, see the Computer Use build in
  [`../17-computer-use-agent/`](../17-computer-use-agent/).

---

## Related directories

- [`../06-regulated-industry/`](../06-regulated-industry/) —
  the server-side equivalent with full audit
  log + per-tenant retention. The shape is the
  same; the privacy boundary moves from the
  browser to the server.
- [`../17-computer-use-agent/`](../17-computer-use-agent/) —
  the cousin that *does* take actions (move the
  mouse, click, type). Same planner shape, no
  privacy boundary.
- [`../12-customer-service-agent/`](../12-customer-service-agent/) —
  the cousin on the *server* side: same
  privacy-by-design (idempotency keys, audit
  log) for a payments company.
- [`../16-autonomous-loop/`](../16-autonomous-loop/) —
  the bounded-loop + budget + retry pattern; not
  directly relevant here (the extension is
  one-shot) but useful for the server-side
  agent that wraps this.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
