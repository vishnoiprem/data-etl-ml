# Per-node gotchas — Project 01

A focused list. Skim this when something breaks before you re-import the workflow.

---

## Trigger — `Every 4 Hours`

- `n8n-nodes-base.scheduleTrigger` v1.2 stores the rule as an object literal, not a string. If you copy-paste from elsewhere, parse JSON before pasting.
- n8n Cloud free tier limits trigger frequency to once per 5 minutes. 4-hour cadence fits; minute-cadence does not.

---

## Code — `Load Tickers`

- Hard-coded to a 5-ticker portfolio. Swap this for a `Google Sheets Read` node pointing at a `Config` tab once you're past happy-path.
- The `jsCode` node uses **plain `items`** (n8n's wrapped type). Don't import from your own packages — there's no `requirements.txt` here.

---

## HTTP — `Fetch MarketStack EOD`

- Free tier = 100 req/day. The workflow schedules 6 runs/day × 5 tickers = 30 req/day. Fits comfortably.
- MarketStack returns `{ data: [...], pagination: {...} }`. The bars come **most-recent-first**. The Code node assumes `$json.data[0]` is the latest — confirm against the API response before relying on it.
- The `access_key` is read from an n8n **Variable**, not the credential store. Reason: variables are simple to rotate and don't require re-issuing an OAuth-style refresh.
- If your account is on the *paid* tier, also pass `date_from`/`date_to` to bound `limit`.

---

## Code — `Compute Signals`

- Assumes at least 50 daily bars; throws otherwise. Bump `limit` to 100 if you track long-history tickers.
- `annualised_vol` is **annualised daily realised vol**, not implied vol. Different number from what Bloomberg shows. Don't expect them to agree.
- If you add risk-free rate, subtract it from the mean return before annualising. The current code does the standard deviation; the mean is unused.

---

## Agent — `LLM Rebalance Decision`

- This is the **only** node where the workflow is fragile to model choice. GPT-4o-mini and Claude Haiku both follow the JSON-only instruction; Llama-3-70b via OpenRouter frequently wraps the JSON in a markdown code fence. If you must use Llama, attach a `Structured Output Parser` sub-node and parse `{output: {decisions: [...]}}` rather than the raw top-level object. The validation Code node already handles both shapes — it was deliberately written that way.
- The prompt's "RULES (hard constraints)" block is **load-bearing**. An LLM told to "summarise" without rules will produce a paragraph. The chain expects JSON.
- Temperature 0.4 (default) is fine. Below 0.2, the model starts returning the same allocation every run even when signals diverge — overconfident.

---

## Code — `Validate & Normalise`

- **The single most important node.** If the LLM returns prose, an empty decisions array, or a number outside [2, 40], this node throws. The append-to-Sheets step never runs. The previous day's `Allocations` row remains intact because we don't update — only append.
- The renormalisation step rounds to 2 decimals. You can sometimes get `99.99` or `100.01` from rounding arithmetic; `drift_after_norm` exposes this. Anything under 0.05 is normal floating-point drift.
- Do not remove the `MAX` cap without also updating the prompt. The prompt rules and the validation rules must agree.

---

## Sheets — `Write to Google Sheets`

- `sheetName: 'Allocations'` — column letters are case-sensitive. If you renamed the tab, the node writes to a *new* tab it silently creates.
- The Credentials tab in n8n must have **both** Sheets and Drive scopes — see project README's "single most failure-prone step".
- For a high-traffic variant, replace with `upsert` keyed on `as_of+symbol`. Today this just appends — duplicates appear across days, which is the audit trail.

---

## Code — `Summarise Run`

- Handy for Slack notifications; pair with a downstream Slack node. Not included in this skeleton because notification targets are user-specific.

---

**Last updated:** 2026-10-21
