# Avilx — JD Inbox

> **Paste job descriptions + email addresses here. I'll read this file, generate a tailored cover letter for each, and fire the email.**
>
> **Format:** One block per lead. Copy-paste this template and fill it in. Then say **"send from jd-inbox"** and I'll process + send all of them.

---

## Template — copy this for each lead

```yaml
---
company: <Company Name>
role: <Role Title>
to_email: <recruiter@example.com>
rate: <$X-Y/hr or $X-Y/year or "not listed">
resume: <PREM_2026.pdf | Prem_Resume_2026.pdf>
---

## Job description

<paste the full JD here, or a few paragraphs of the most relevant parts>


## Why I want this

<optional: 1-2 lines on what hooks you about this role>


## Notes for Prem

<optional: anything I should know — specific stack emphasis, name to mention, salary ask, etc.>
```

---

## Examples (already filled in, as a reference)

### Example 1 — recruiter-pitch

```yaml
---
company: Stripe
role: Staff Engineer, Risk Platform
to_email: jane@stripe.com
rate: $250-300K
resume: PREM_2026.pdf
---

## Job description

You'll be a Staff Engineer on our Risk Platform team, building the systems that detect and prevent payment fraud at global scale. We process billions of dollars in payments across 100+ countries and need engineers who can reason about distributed systems, real-time ML, and large-scale data pipelines. The team owns the entire risk decisioning stack — from feature engineering and model serving to the policy engine that decides approve/decline in <100ms.

Requirements:
- 8+ years building production backend systems
- Strong distributed systems fundamentals (consensus, partitioning, replication)
- Experience with ML serving and feature pipelines
- Python, Go, or Rust
- Bonus: payments, fraud, or risk domain experience

## Why I want this

Real-time risk decisioning is the kind of problem I love — combining low-latency engineering with applied ML at scale.

## Notes for Prem

Lead with the banking CDC lakehouse case study — same sub-100ms SLA discipline. Mention the SEA fintech cross-cloud work.
```

---

## Quick-paste minimal version (if you don't want to write a JD)

```yaml
---
company: <Company>
role: <Role>
to_email: <recruiter@company.com>
---

<paste whatever you have — even a 1-line LinkedIn DM or job post snippet>
```

If the JD is too thin, I'll use my best inference from the role title + company + your hook notes.

---

## Status (auto-updated by auto.py after each send)

- `2026-10-10 18:09` — Sticker Mule → help@stickermule.com ✅
- `2026-10-10 18:17` — LiveKit → recruiting@livekit.io ✅
- `2026-10-10 18:27` — Menrva Group / APAC Bank → adam.davies@menrvagroup.com ✅
- `2026-10-10 18:35` — SingleStore → pkhaitan@singlestore.com (queued)
- `2026-10-10 18:35` — FunnelStory → preetam@funnelstory.ai (queued)
- `2026-10-10 18:35` — Buoyant → scott.deakin@buoyant.io (queued)
- `2026-10-10 18:35` — ICEYE → wb@iceye.com (queued)
- `2026-10-10 18:35` — Quantum Minds → jobs@quantumminds.com (queued)

---

## What I'll do when you say "send from jd-inbox"

1. **Parse** every YAML block in this file (below the examples)
2. **For each one**, generate a tailored Avilx cover letter (3-4 short paragraphs) using:
   - The pasted JD (if any) — pull 1-2 specific must-haves
   - Your "Why I want this" — drives the personal hook
   - Your "Notes for Prem" — overrides any defaults
   - Standard Avilx positioning: global delivery, Databricks Champion, 7+ clouds, senior-only
3. **Update** `leads.json` with the new lead (email, status=pending, generated cover letter)
4. **Fire** all pending emails via `python3 auto.py --email`
5. **Append** the status to this file
6. **Show you** what was sent (subject + recipient + first 100 chars of each letter)

If the file is empty / has no new blocks, I'll just say "no new JDs to process" and stop.
