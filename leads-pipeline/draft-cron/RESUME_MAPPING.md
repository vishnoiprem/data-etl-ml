# Resume Mapping

> **Two resumes on your machine, two angles.**

## Files

| File | Pages | Use for |
|---|---|---|
| `PREM_2026.pdf` | 4 | **Principal / architect / staff / lead / director roles** |
| `Prem_Resume_2026.pdf` | 2 | **Senior / mid roles / stop-gap contracts** |

## Currently mapped in `leads.json`

### 4-page PREM_2026.pdf (principal track)
- LiveKit (Product Engineer, $90-140/hr → $120-180/hr principal)
- A.Team (AI Engineer / Architect, $90-170/hr)
- Tailscale (Analytics Engineer, principal positioning)
- Dremio (SWE Query Execution, principal positioning)
- Reef Tech (Sr Python Backend, principal positioning)
- Sticker Mule (AI Agent Engineer, principal positioning)

### 2-page Prem_Resume_2026.pdf (senior track — stop-gap)
- Lemon.io (Sr React Full-stack, $40-70/hr → $80-100/hr senior)
- Proxify AB (Sr Backend Python, $45-65/hr → $80-100/hr senior)
- Typeform (Full Stack Developer, $50-80/hr → $80-100/hr senior)
- Toggl (Senior Full Stack, $40-55/hr → $80-100/hr senior)

## Why two angles

Most leads in the firehoses (RemoteOK, WWR, etc.) post at **$40-90/hr** for "engineer" roles. Your **principal rate is $120-180/hr** — 2-3x what those platforms pay for individual contributors.

Two strategies:
1. **Push principal roles** — apply to architect/staff/lead/director postings and skip mid-level
2. **Take mid-level as stop-gap** — accept senior rates while you find a principal seat

The leads.json is split 6 principal / 4 senior to cover both strategies.

## When to use which

- **Apply to principal first** (LiveKit, A.Team, Tailscale, Dremio, Reef, Sticker Mule) — these match your actual level
- **Apply to senior as backup** (Lemon.io, Proxify, Typeform, Toggl) — if no principal hits in 2-3 weeks, take a senior contract to keep cash flowing

## How to change resume per lead

Edit `leads.json` and change `resume_file`:
```json
"resume_file": "PREM_2026.pdf"           // 4-page, principal track
"resume_file": "Prem_Resume_2026.pdf"    // 2-page, senior track
```

## Add more resumes

Drop more PDFs in `Resume/` and add them to `leads.json`:
```json
"resume_file": "PREM_Databricks_Champion.pdf"  // future specialized resume
```
