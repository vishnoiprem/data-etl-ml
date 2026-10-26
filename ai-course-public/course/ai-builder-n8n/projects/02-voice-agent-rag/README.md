# Project 02 — Voice Agent with ElevenLabs + Supabase RAG

> **A phone-call agent that answers domain questions from a Supabase vector store, and hands off to a human when it doesn't know.** Twilio carries the call, ElevenLabs carries the voice, n8n carries the brain.

---

## What it does

```
Twilio voice webhook →
  Parse Twilio body (CallSid, From, SpeechResult) →
  Embed the caller's spoken question →
  Retrieve top-4 chunks from Supabase (pgvector) →
  LLM answers using ONLY those chunks (else escalate) →
  Build TwiML response (<Say> or <Say>+<Dial>) →
  Respond with application/xml →
  (parallel) Log transcript ref to ElevenLabs
```

Two properties make this a *voice* agent rather than a chatbot in a trenchcoat: the reply is capped at ~60 words (it gets spoken), and every failure path ends in `<Dial>` to a human, never in silence.

---

## Setup checklist

| Step | Where | Verify by |
|---|---|---|
| 1. Supabase project | https://supabase.com | Free tier project created |
| 2. Enable the `vector` extension | Supabase SQL editor | `create extension if not exists vector;` succeeds |
| 3. Run the DDL below | Supabase SQL editor | Table `kb_chunks` exists with `embedding vector(1536)` |
| 4. Create the match function | Supabase SQL editor | `select match_kb_chunks(...);` returns rows |
| 5. Create a Supabase credential in n8n | n8n UI (project URL + service_role key) | Test connection OK |
| 6. Sign up for ElevenLabs (free tier = 10 min/mo of voice) | https://elevenlabs.io | Agent Platform accessible |
| 7. Sign up for Twilio, get a voice-capable number | https://twilio.com | Number can receive a test call |
| 8. Point the Twilio number's voice webhook at your n8n `/webhook/voice/webhook` | Twilio console | Test call reaches n8n (check executions) |
| 9. Set `ELEVENLABS_API_KEY` as an n8n variable | n8n Settings | Resolves in the Log node |
| 10. Import `workflow.json` | n8n UI | No red nodes |

### Supabase DDL

```sql
create extension if not exists vector;

create table if not exists kb_chunks (
  id          uuid primary key default gen_random_uuid(),
  source      text        not null default 'public_kb',
  title       text,
  body        text        not null,
  embedding   vector(1536) not null,
  created_at  timestamptz default now()
);

create index if not exists kb_chunks_embedding_idx
  on kb_chunks using hnsw (embedding vector_cosine_ops);

create or replace function match_kb_chunks(
  query_embedding vector(1536),
  match_count     int      default 4,
  filter          jsonb    default '{}'::jsonb
)
returns table (id uuid, title text, body text, similarity float)
language sql stable as $$
  select
    c.id,
    c.title,
    c.body,
    1 - (c.embedding <=> query_embedding) as similarity
  from kb_chunks c
  where c.source = filter->>'source'
  order by c.embedding <=> query_embedding
  limit match_count;
$$;
```

The `vector(1536)` width matches OpenAI's `text-embedding-3-small`. If you use `text-embedding-ada-002`, also 1536 — either is fine, but the column width and the model must agree or the insert fails.

---

## Seed data

You need chunks before the agent can answer anything. Simplest path: 10–20 FAQ paragraphs, one per row, embedded with the same model the workflow uses.

```sql
insert into kb_chunks (source, title, body, embedding)
values
  ('public_kb', 'Refund policy',
   'Refunds are available within 30 days of purchase. Contact support with your order number...',
   '[...]');  -- embed the body text first
```

Better path: an n8n workflow that reads a folder of `.md` files → `OpenAI Embedding` node → `Supabase Insert` row-by-row. That second workflow is itself a Section 2 lesson; it's not included here to keep this project focused on the *query* path.

---

## The one thing people get wrong

**Twilio expects `application/xml` and nothing else.** If you respond with JSON, the call hears silence — not an error. Twilio's webhook response parser silently discards anything it doesn't recognise as TwiML.

That means the `Respond to Twilio` node's `Content-Type` header is load-bearing. If your call connects and immediately hangs up, check that header before you debug anything else.

Second most common: **the `SpeechResult` field is empty** unless you enable speech recognition on the `<Gather>` verb. An empty `SpeechResult` produces an empty embedding, which retrieves garbage, which produces a confident wrong answer. Verify `SpeechResult` is populated in the n8n execution log *before* blaming the RAG.

See `notes/twilio-webhooks.md` for the `<Gather>` configuration.

---

## Latency budget

A caller will hang up around 4–5 seconds of silence. Your budget:

| Stage | Typical | Notes |
|---|---|---|
| Twilio → n8n webhook | 100–300ms | network + form parsing |
| Embedding (OpenAI) | 80–150ms | `text-embedding-3-small` |
| Supabase vector search | 20–60ms | HNSW index; grows with table size |
| LLM answer | 600–1200ms | dominates |
| **Total** | **~1–2s** | leaves headroom |

If you exceed ~3s, the caller talks over the agent. Two fixes: drop `match_count` to 3, or cache embeddings for repeated questions.

---

## What this is NOT

- **Not a full ElevenLabs Conversational AI setup.** ElevenLabs' own agent platform can host the LLM call natively. This workflow deliberately keeps n8n in the loop so you can *see* the retrieval — that's the pedagogical point of the course section.
- **Not production telephony.** A real deployment needs call recording consent, PII retention policy, DNC handling, and a fallback when n8n is down. This workflow has none of that.
- **Not multi-turn aware.** Each webhook hit is stateless. The conversation memory is ElevenLabs' (or your caller's), not n8n's. If you put n8n in the middle of a multi-turn call, you must carry transcript history yourself.

---

**Last updated:** 2026-10-21
**License:** MIT — use freely in your own courses, prototypes, and products.