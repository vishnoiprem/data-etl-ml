# AI Builder in n8n — Course Scaffold & Capstones

> **Build low-code AI Agents & Voice Agents in n8n.** Three sections, three capstones, no Node.js required. ~3 weeks.
>
> **What this directory is:** the *project skeletons* from the 88-lecture course — the workflow JSON, the setup notes, and the wiring — without the full per-lecture narrative. Use it as a working starting point; refer to the video for the per-lecture walkthrough.

---

## What you build

| Section | Project | Stack | What it does |
|---|---|---|---|
| 1 — n8n + LLM agents | **01 — Financial agent** | n8n + OpenRouter + MarketStack + Google Sheets | A scheduled agent that polls MarketStack prices, decides buy/sell/hold using an LLM, and writes allocations back to a Google Sheets portfolio |
| 2 — Voice agents | **02 — Voice agent + RAG** | n8n + ElevenLabs + Twilio + Supabase Vector | A phone-call voice agent that pulls answers from a Supabase-hosted knowledge base and triggers business actions |
| 3 — Multi-agent orchestration | **03 — GTM multi-agent** | n8n + MCP + FireCrawl + Hunter.io + Google Calendar | A lead-to-meeting system where scrape, enrich, qualify, and book agents each own one node cluster and hand off via shared state |

Each project is **self-contained**: it has its own `workflow.json` (n8n-importable), a `README.md` with the setup checklist, and a `notes/` folder for node-specific quirks.

---

## File layout

```
ai-builder-n8n/
├── README.md                  ← you are here
└── projects/
    ├── 01-financial-agent/
    │   ├── README.md
    │   ├── workflow.json      ← importable into n8n
    │   └── notes/
    │       └── nodes.md
    ├── 02-voice-agent-rag/
    │   ├── README.md
    │   ├── workflow.json
    │   └── notes/
    │       └── twilio-webhooks.md
    └── 03-gtm-multi-agent/
        ├── README.md
        ├── workflow.json
        ├── mcp-server.json    ← MCP server definition (n8n-hosted)
        └── notes/
            └── orchestration.md
```

---

## How to use this

1. **Pick a project.** Don't try all three at once — each uses a different vendor sandbox (ElevenLabs phone numbers, Twilio credentials, Hunter.io API).
2. **Follow that project's `README.md`** — it lists exactly which external accounts to create, which API keys to paste, and what the workflow expects.
3. **Import `workflow.json` into an n8n instance** (n8n Cloud free tier or a local Docker — see `01-financial-agent/README.md` for the local-Docker recipe).
4. **Wire credentials in n8n's Credentials panel** — workflow JSON never contains plaintext secrets by design.
5. **Test with a manual trigger first**, then switch the trigger to a webhook / schedule / cron.

---

## What this directory is NOT

- **Not a transcript.** Lecture footage carries the *why* and the *demo*. The `workflow.json` carries the *what*. Use them together.
- **Not production-grade on first import.** Every workflow here has been authored to demo the pattern, not to ship. Before you run any of these against real customers, walk through `notes/` for that project — the gotchas section is where real bugs hide.
- **Not vendor-neutral.** The elevenlabs/Twilio/Supabase choices are the course's. Swap any of them out, but expect to redo the `nodes.md` for the new vendor.
- **Not a complete rewrite of any course it shares concepts with.** This course and `../ai-fde/` (Phase 1–4, the PacificFreight drafter) and `../agentic-ai/` overlap heavily. They live side by side; pick by stack, not by depth.

---

## Source / provenance

The course outline for this directory is a published 88-lecture, 14-hour, 3-week video course titled *"AI Builder: Create Agents, Voice Agents & Automations in n8n"* (5 sections × 5 days). **The instructor/creator is not recorded in the source material I was given** — fill it in here if you know it.

The project skeletons here are **reverse-engineered from the lecture titles alone**, plus public n8n node documentation and the public APIs named in the lectures. No lecture footage, transcript, or course material was available while writing these files.

**Practical consequence:** treat every node name, credential scope, and payload shape here as a *strong first draft*, not ground truth. n8n in particular renames nodes and credential types between minor versions. Import, then reconcile against your installed version and against the video.

---

## What survives the loop

The three workflow JSONs are the artifacts. The setup notes (`nodes.md`, `twilio-webhooks.md`, `orchestration.md`) are the *knowledge*. The most-failure-prone step in every project is **credentials** — the `workflow.json` can be perfect and still fail at runtime because an OAuth scope was missing. That's why credentials are deliberately *not* in the JSON.

---

**Last updated:** 2026-10-21
**License:** MIT — use freely in your own courses, prototypes, and products.
