# LOOP 10: 0->1 Ambiguous Product (Staff Bar - Hardest)

**Theme:** No PM, no spec — YOU define the problem
**Total Duration:** 4 hours (full day)
**Difficulty:** Hardest (this is the L6 → L7 bar)

---

## Architecture Diagram (Master)

```
┌────────────────────────────────────────────────────────────────────┐
│    "ASK META" - 0->1 DESIGN (you define the requirements)          │
└────────────────────────────────────────────────────────────────────┘

PHILOSOPHY: L6+ = DEFINE THE PROBLEM, NOT JUST SOLVE IT
────────────────────────────────────────────────────────
Bad L5 answer: "Use Qdrant and an LLM"
Good L6 answer: Define success metrics, scope, milestones, then build
Best L7 answer: Define problem + alternatives considered + risks + adoption strategy

"ASK META" - SINGLE SEARCH BOX FOR EVERYTHING
──────────────────────────────────────────────

User types: "How do I deploy a service?"
                              │
                              ▼
        ┌────────────────────────────────────┐
        │ Embed query (text-embedding-3-lg)  │
        └─────────────────┬──────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────────────┐
        │ Parallel search across 4 modalities          │
        │ ─────────────────────────────────────────────│
        │ 1. Code search (Qdrant, AST-chunked)         │
        │ 2. Docs search (Qdrant + BM25 hybrid)        │
        │ 3. People search (TAO social graph)          │
        │ 4. Meetings search (Qdrant, transcript chks) │
        └─────────────────┬────────────────────────────┘
                          │ Top 50 each
                          ▼
                ┌──────────────────────┐
                │ Dedup + merge        │
                │ Cohere rerank top 20 │
                └──────────┬───────────┘
                           │
                           ▼
        ┌────────────────────────────────────────────┐
        │ LLM with grouped answer                    │
        │ ─────────────────────────────────────────│
        │ "Here's what I found:                      │
        │                                            │
        │  📄 DOCS:                                   │
        │   - Deploy guide (wiki:123)                │
        │   - Best practices (wiki:456)              │
        │                                            │
        │  💻 CODE:                                   │
        │   - deploy.sh (repo:infra, file:42)        │
        │   - service.yaml (repo:platform, file:8)   │
        │                                            │
        │  👥 PEOPLE:                                 │
        │   - Alice (deploys 10x/week)               │
        │   - Bob (oncall for deploy service)        │
        │                                            │
        │  🎥 MEETINGS:                               │
        │   - Deploy retro (Oct 15)"                 │
        └─────────────────┬──────────────────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │ + follow-up questions│
                │ + feedback (thumbs)  │
                └──────────────────────┘
```

---

## Greet (15 min)

### Q1: Tell me about 0->1 you built with no requirements

**L6 Answer (90 sec):**

> "I built APEX-RAG from scratch at my last job. No PM, no spec, no users. Most people fail 0->1 because they code before defining success.
>
> My approach was four steps:
>
> 1. **Interview 10 users** to find top 3 pain points. Found: 'I can't find internal docs,' 'RAG hallucinates,' 'I don't know who to ask.'
>
> 2. **Define success metrics before code**: satisfaction 73% → 85%, p95 latency 1.2s → 500ms, Recall@8 0.71 → 0.85.
>
> 3. **Build eval harness first**, before the product. Even with no users, I needed to know if my retrieval was any good.
>
> 4. **MVP in 3 months, 10K by month 6, 100K by month 9**: docs only at MVP, then add modalities against the same 3 / 6 / 9-month cadence.
>
> The lesson: 0->1 isn't about coding fast. It's about defining the problem clearly enough that you know when you're done."

**L6 Keywords:** interview users, define metrics, eval harness first, MVP, iterate.

---

### Q2: What would you build if you had 6 months free?

**L6 Answer (75 sec):**

> "**'Ask Meta'** — a single search box that finds code, docs, people, and meetings all at once, with grounded citations to each.
>
> Why: knowledge at Meta is fragmented. Engineers waste 30 min/day finding information across 4 systems. Total cost at Meta scale: ~$50M/year in lost productivity.
>
> The 0->1 challenge: 4 different data types, 4 different storage systems, 4 different ACL models. But one unified query interface.
>
> **3 / 6 / 9-month plan:**
> - Month 1-3 (MVP): docs only, 10 power users, validate retrieval quality
> - Month 3-6 (scale): add code → people → meetings, scale to 10K users
> - Month 6-9 (expand): scale to 100K users, measure NPS, ship to all Meta
>
> **Success metrics:** time saved per user (target: 15 min/day), search success rate, daily active users."

---

## AI-Native DE Full Stack (60 min) - AI Meeting Summarizer (you design)

### Q1 Data Model (20 min) - You define

```
┌────────────────────────────────────────────────────────────────┐
│      AI MEETING SUMMARIZER (you designed this from scratch)    │
└────────────────────────────────────────────────────────────────┘

meetings                          transcripts
┌────────────────────────┐        ┌────────────────────────────┐
│ meeting_id      PK     │◀──────▶│ meeting_id    FK           │
│ title                 │  1:1   │ segment_id    PK           │
│ host_id               │        │ speaker_id    FK           │
│ started_at            │        │ text          TEXT         │
│ ended_at              │        │ start_ts      INT (sec)    │
│ attendee_ids  ARRAY   │        │ end_ts        INT (sec)    │
│ project_tag           │        │ embedding     VECTOR       │
│ status                │        │ chunk_index   INT          │
│  'scheduled'|'active' │        └────────────────────────────┘
│  'ended'              │
└────────────────────────┘        meeting_summaries
                                  ┌────────────────────────────┐
referenced_docs                   │ summary_id     PK          │
┌────────────────────────┐        │ meeting_id     FK          │
│ meeting_id      FK     │◀──────▶│ summary_text   TEXT        │
│ doc_id                │        │ action_items   JSON        │
│ referenced_at         │        │ citations      JSON        │
│ context  TEXT         │        │   [{type, id, line}]       │
│ relevance_score       │        │ generated_by   STRING      │
└────────────────────────┘        │   'gpt-4'|'gpt-3.5'        │
                                  │ created_at     TIMESTAMP   │
meeting_search_traces             └────────────────────────────┘
┌────────────────────────┐
│ trace_id        PK     │
│ user_id               │
│ query                 │
│ meeting_id  FK NULL   │
│ doc_id      FK NULL   │
│ accessed_at           │
└────────────────────────┘
```

**SQL schema (you design from scratch):**

```sql
CREATE TABLE meetings (
  meeting_id     BIGINT PRIMARY KEY,
  title          STRING,
  host_id        BIGINT,
  started_at     TIMESTAMP,
  ended_at       TIMESTAMP,
  attendee_ids   ARRAY<BIGINT>,
  project_tag    STRING,
  status         STRING  -- 'scheduled', 'active', 'ended'
) PARTITIONED BY (DATE(started_at));

CREATE TABLE transcripts (
  meeting_id    BIGINT REFERENCES meetings(meeting_id),
  segment_id    BIGINT,
  speaker_id    BIGINT,
  text          STRING,
  start_ts      INT,    -- seconds from meeting start
  end_ts        INT,
  embedding     ARRAY<FLOAT>,
  chunk_index   INT,
  PRIMARY KEY (meeting_id, segment_id)
);

CREATE TABLE referenced_docs (
  meeting_id       BIGINT REFERENCES meetings(meeting_id),
  doc_id           BIGINT,
  referenced_at    TIMESTAMP,
  context          STRING,
  relevance_score  FLOAT,
  PRIMARY KEY (meeting_id, doc_id)
);

CREATE TABLE meeting_summaries (
  summary_id     BIGINT PRIMARY KEY,
  meeting_id     BIGINT REFERENCES meetings(meeting_id),
  summary_text   STRING,
  action_items   JSON,           -- [{owner, task, due_date}]
  citations      JSON,           -- [{type: 'transcript', segment_id}, {type: 'doc', doc_id, line}]
  generated_by   STRING,         -- 'gpt-4', 'gpt-3.5'
  created_at     TIMESTAMP
);

CREATE TABLE meeting_search_traces (
  trace_id       BIGINT PRIMARY KEY,
  user_id        BIGINT,
  query          STRING,
  meeting_id     BIGINT,
  doc_id         BIGINT,
  accessed_at    TIMESTAMP
) PARTITIONED BY (DATE(accessed_at));

CREATE TABLE eval_runs (
  run_id          BIGINT PRIMARY KEY,
  feature         STRING,           -- 'meeting_search', 'doc_search', etc.
  prompt_version  STRING,
  recall_at_8     FLOAT,
  ndcg_at_8       FLOAT,
  started_at      TIMESTAMP,
  finished_at     TIMESTAMP
) PARTITIONED BY (DATE(started_at));
```

---

### Q2 Pipeline (15 min) - You design

```
┌────────────────────────────────────────────────────────────────┐
│          AI MEETING SUMMARIZER PIPELINE                        │
└────────────────────────────────────────────────────────────────┘

MEETING ENDS
   │
   ▼
┌──────────────────────┐
│ Whisper transcription│ Audio → text + speaker ID
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Speaker turn chunker │ 250 tokens per chunk
│ (your custom)        │ with speaker attribution
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Embed chunks         │ text-embedding-3-large
│ (parallel)           │ batch 100
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ NER + URL extract    │ Find references to docs:
│                      │ - "see wiki:engineering/oncall"
│                      │ - "look at config.py:42"
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Embed referenced docs│ Add to meeting context
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│ LLM summary                  │
│ ────────────────────────────│
│ Prompt:                       │
│   "Given this transcript and  │
│    referenced docs, generate  │
│    - Summary (3 sentences)    │
│    - Action items (JSON)      │
│    - Decisions made           │
│    All claims must cite       │
│    transcript segment or      │
│    doc:line."                 │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Citation validator           │
│ ────────────────────────────│
│ Extract [transcript:seg_X]   │
│ and [doc:Y:line_Z] from      │
│ output. Verify each citation │
│ exists in evidence.          │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ meeting_summaries            │
│ with citations JSON          │
└──────────────────────────────┘
```

---

### Q3 SQL (10 min) - Define Success Metrics (you design from scratch)

```sql
-- METRIC 1: Time saved per user (engagement)
SELECT
  user_id,
  COUNT(DISTINCT summary_id)              AS summaries_read,
  AVG(dwell_time_sec)                     AS avg_dwell_sec,
  SUM(dwell_time_sec) / 60.0              AS total_minutes_spent,
  -- Estimate: if user spent 5 min reading summary instead of 60 min in meeting
  COUNT(*) * 55                           AS minutes_saved
FROM meeting_search_traces t
JOIN meeting_summaries s ON t.meeting_id = s.meeting_id
WHERE accessed_at >= NOW() - INTERVAL '30' DAY
GROUP BY user_id
ORDER BY minutes_saved DESC
LIMIT 100;

-- METRIC 2: Citation accuracy (LLM-as-judge)
SELECT
  DATE_TRUNC('day', s.created_at) AS day,
  COUNT(*)                        AS total_summaries,
  AVG(citation_accuracy)          AS avg_accuracy,
  SUM(CASE WHEN has_hallucination THEN 1 ELSE 0 END) AS hallucination_count
FROM meeting_summaries s
WHERE created_at >= NOW() - INTERVAL '7' DAY
  AND has_human_review = TRUE
GROUP BY DATE_TRUNC('day', s.created_at)
ORDER BY day DESC;

-- METRIC 3: Search recall (does search find relevant meetings?)
SELECT
  prompt_version,
  AVG(recall_at_8) AS avg_recall,
  AVG(ndcg_at_8)   AS avg_ndcg,
  COUNT(*)        AS eval_count
FROM eval_runs
WHERE feature = 'meeting_search'
  AND started_at >= NOW() - INTERVAL '7' DAY
GROUP BY prompt_version
ORDER BY avg_recall DESC;
```

---

### Q4 Coding (15 min) - Meeting Chunker + Citation Extractor

```python
from typing import List, Dict
import re


def chunk_meeting_transcript(segments: List[Dict], max_tokens: int = 250) -> List[Dict]:
    """
    Chunk by speaker turn + topic shift.
    Keeps speaker attribution so we can cite [transcript:meeting_X:seg_Y].
    """
    chunks = []
    current = {
        "speakers": [],
        "text": "",
        "start_ts": None,
        "end_ts": None,
        "segment_ids": [],   # for citation
    }

    for seg in segments:
        # Start new chunk if topic shift or size limit
        if not current["text"]:
            current["start_ts"] = seg["start_ts"]
        current["speakers"].append(seg["speaker_id"])
        current["segment_ids"].append(seg["segment_id"])
        current["text"] += f"{seg['speaker_id']}: {seg['text']}\n"
        current["end_ts"] = seg["end_ts"]

        # Approx 4 chars per token
        if len(current["text"]) > max_tokens * 4:
            chunks.append(current)
            current = {
                "speakers": [], "text": "", "start_ts": None,
                "end_ts": None, "segment_ids": [],
            }

    if current["text"]:
        chunks.append(current)

    return chunks


def extract_citations(summary: str, evidence: List[Dict]) -> List[Dict]:
    """
    Extract [type:id] or [type:id:line] citations from LLM output.
    Verify each against evidence. Return list with 'valid' flag.
    """
    citations = []
    # Match [transcript:meeting_X:seg_Y] or [doc:doc_Y:line_Z]
    pattern = r"\[(transcript|doc):([a-zA-Z0-9_-]+)(?::(\d+))?\]"

    for match in re.finditer(pattern, summary):
        kind, ref_id, line = match.groups()
        # Verify reference exists in evidence
        valid = any(
            e.get("type") == kind
            and (e.get("id") == ref_id or e.get(f"{kind}_id") == ref_id)
            for e in evidence
        )
        citations.append({
            "type": kind,
            "id": ref_id,
            "line": int(line) if line else None,
            "valid": valid,
            "context": next(
                (e.get("text", "")[:100] for e in evidence
                 if e.get("id") == ref_id or e.get(f"{kind}_id") == ref_id),
                None
            ),
        })

    return citations


def generate_meeting_summary(transcript_chunks: List[Dict], referenced_docs: List[Dict]) -> Dict:
    """
    Main function: generate summary with citations.
    """
    # Build evidence list
    evidence = []
    for chunk in transcript_chunks:
        evidence.append({
            "type": "transcript",
            "id": f"seg_{chunk['segment_ids'][0]}",
            "text": chunk["text"][:500],
        })
    for doc in referenced_docs:
        evidence.append({
            "type": "doc",
            "id": f"doc_{doc['doc_id']}",
            "text": doc.get("context", "")[:500],
        })

    # LLM prompt
    prompt = f"""You are summarizing a meeting with these transcript chunks and referenced docs.

TRANSCRIPT CHUNKS:
{chr(10).join(f"[transcript:{e['id']}] {e['text']}" for e in evidence if e['type'] == 'transcript')}

REFERENCED DOCS:
{chr(10).join(f"[doc:{e['id']}] {e['text']}" for e in evidence if e['type'] == 'doc')}

Generate:
1. Summary (3 sentences)
2. Action items (JSON: [{{"owner": "name", "task": "...", "due": "date"}}])
3. Key decisions

CRITICAL: Every claim must include a citation like [transcript:seg_123] or [doc:doc_456:42].
If not supported by evidence, write 'Not stated in meeting'."""

    import openai
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    summary_text = response.choices[0].message.content

    # Extract and verify citations
    citations = extract_citations(summary_text, evidence)
    citation_accuracy = sum(1 for c in citations if c["valid"]) / len(citations) if citations else 1.0

    return {
        "summary_text": summary_text,
        "citations": citations,
        "citation_accuracy": citation_accuracy,
        "n_citations": len(citations),
    }
```

---

## Sr Tech Design (60 min) - 0->1 "Ask Meta" (Staff Bar)

```
┌────────────────────────────────────────────────────────────────┐
│         0->1 ASK META - YOU DEFINE THE REQUIREMENTS            │
└────────────────────────────────────────────────────────────────┘

MY REQUIREMENTS (L6+ = define the problem)
──────────────────────────────────────────

USER PROBLEM
────────────
Engineers waste 30 min/day finding info across 4 systems
(wiki, code, people, meetings). Cost-of-pain math at Meta scale:
100k engineers × 30 min/day × 220 work days = 11M hours/year wasted.
At a fully-loaded cost of $38/hour (~$80k base × 1.4 benefits × 1.05 overhead / 2080 hrs),
that is ~$50M/year in lost productivity.

SUCCESS METRICS (you define)
────────────────────────────
1. Time saved per user: 15 min/day (target)
2. Daily active users: 100k within 6 months
3. Search success rate: 80% (user finds what they need in <3 attempts)
4. Citation accuracy: 95% (LLM-as-judge)
5. NPS: 40+

NON-FUNCTIONAL REQUIREMENTS
───────────────────────────
- Latency: p95 < 500ms
- Scale: 500M potential users, 1B docs + 1B code files + 1B meetings
- ACL: private repos/people only visible to team
- Freshness: 5-min for new content
- Cost: <$0.01/query

ARCHITECTURE
────────────

1. UNIFIED INDEX (4 collections in Qdrant)
   - code_chunks (AST-parsed, 1B files)
   - doc_chunks (hybrid search, 100M docs)
   - people (TAO social graph)
   - meeting_chunks (transcript + summary, 1B meetings)

2. QUERY ROUTER
   - Embed query once
   - Parallel search across 4 collections
   - Merge top 50 each, dedup, rerank top 20

3. LLM WITH GROUPED ANSWER
   - "Here's what I found across docs, code, people, and meetings"
   - Each result has citation [type:id:line]
   - If not in evidence, return "Not found"

4. ACL LAYER
   - Filter at Qdrant payload level BEFORE LLM
   - Per-team permission, per-user history
   - Audit every access

5. FEEDBACK LOOP
   - Thumbs up/down per result
   - "Not what I wanted" → gold dataset
   - Weekly LLM-as-judge eval on 10k queries

6-PHASE ROLLOUT (you plan this, not PM)
────────────────────────────────────────
Month 1-2:  docs only, 10 power users, manual feedback
Month 3:    + code search, 100 users
Month 4:    + people search, 1000 users
Month 5:    + meetings, 10K users
Month 6:    scale to 100K, measure NPS
Month 7+:   ship to all Meta if metrics hit

METRIC GATES (no advancement without these)
──────────────────────────────────────────
Phase 1->2: WAU >= 50% of onboarded users
Phase 2->3: NPS > 30
Phase 3->4: p95 latency < 1s end-to-end
Phase 4->5: citation accuracy >= 95% on LLM-as-judge eval
Phase 5->6: zero P0 ACL incidents in prior 30 days

ADOPTION STRATEGY (L7 territory)
────────────────────────────────
- Slack bot: "ask @askmeta how do I deploy?"
- Browser extension: highlight text → right-click → ask
- IDE plugin: VSCode extension, ask without context switch
- Adoption cadence: 3 live demos/week to different teams, 1 written postmortem/week, 10 user interviews in the first 30 days

RISKS (you name them)
─────────────────────
1. ACL leak: 1 bug exposes private data
2. Hallucination: 5% bad citations erode trust
3. Cold start: new users have no personalization signal
4. Cost: at 500M scale, $0.01/query = $5M/month
5. Multi-language: code search in 20+ languages

ALTERNATIVES CONSIDERED (L7 territory)
──────────────────────────────────────
- Per-product search (existing): users hate context switching
- LLM-only with web search: no internal data, hallucination
- Elasticsearch only: no semantic, no code understanding
- Build from scratch: too slow, no infra reuse

WHY ASK META WINS: one box, four modalities, grounded citations.
```

---

## Sr Ownership (30 min)

### Q1: Time you defined problem when no one knew what to build

**L6 STAR (90 sec):**

**S:** New team, vague mandate: "improve internal search." No PM, no spec, no success criteria.

**T:** Define the problem + success metrics in 1 week, get team aligned.

**A:**
1. **Interview 10 users:** top 3 pain points were (a) can't find docs, (b) RAG hallucinates, (c) don't know who to ask
2. **Quantified:** 30 min/day wasted per engineer, $50M/year at Meta scale; new-hire ramp is also 5% slower than benchmark (sourced from onboarding survey n=120)
3. **Defined success metrics:** satisfaction 73%→85%, p95 1.2s→500ms, Recall@8 0.71→0.85, time saved 15 min/user/day
4. **Built eval harness first** — even with no users, I needed to know if retrieval was working
5. **Ran baseline eval, proposed 3 options** to director with cost/benefit. Picked one.
6. **Shipped in 4 months**, hit all 3 metrics.

**R:** Director happy, team aligned, became team's template for all future projects.

**Lesson:** the L6+ move is not coding fast. It's defining the problem so clearly that the team knows when they're done.

---

### Q2: Time you killed a project

**L6 STAR (60 sec):**

**S:** 3 months into real-time Flink CDC for RAG freshness, cost $50k/month, 5% usage.

**T:** Kill or pivot with data, not opinion.

**A:**
1. Built cost/usage dashboard: 95% users on 24h batch, 5% on real-time
2. Showed director: 50x cost for 5% users, no business case
3. Proposed: keep Flink for premium tier (1% users), kill general rollout
4. Killed general rollout, reassigned 2 engineers to other work
5. Premium tier grew 5x in 6 months — real revenue

**R:** Saved $500k/year, freed 2 engineers, director respected data-driven kill. Lesson: killing is a feature, not a failure.

---

## Full Stack (90 min - longer for 0->1) - "Ask Meta" UI

```tsx
import { useState } from "react";

const AskMeta = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState({});
  const [followUp, setFollowUp] = useState("");

  const search = async () => {
    setLoading(true);
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    setResults(await res.json());
    setLoading(false);
  };

  const submitFeedback = async (resultId, rating) => {
    setFeedback({ ...feedback, [resultId]: rating });
    await fetch("/api/feedback", {
      method: "POST",
      body: JSON.stringify({ result_id: resultId, rating, query }),
    });
  };

  const askFollowUp = (q) => {
    setQuery(q);
    search();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-2">Ask Meta</h1>
      <p className="text-gray-600 mb-4">Search code, docs, people, and meetings in one box.</p>

      {/* Search box */}
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && search()}
          placeholder="Ask anything..."
          className="flex-1 p-3 text-lg border rounded shadow-sm focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={search}
          disabled={loading}
          className="bg-blue-500 text-white px-6 py-3 rounded font-medium disabled:bg-gray-300"
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>

      {/* Results grouped by type */}
      {results && (
        <div className="space-y-6">
          {/* DOCS */}
          {results.docs?.length > 0 && (
            <ResultGroup
              icon="📄"
              title="Docs"
              results={results.docs}
              feedback={feedback}
              onFeedback={submitFeedback}
              renderCitation={(c) => `[doc:${c.doc_id}:${c.line}]`}
            />
          )}

          {/* CODE */}
          {results.code?.length > 0 && (
            <ResultGroup
              icon="💻"
              title="Code"
              results={results.code}
              feedback={feedback}
              onFeedback={submitFeedback}
              renderCitation={(c) => `[${c.repo}:${c.file}:${c.line}]`}
            />
          )}

          {/* PEOPLE */}
          {results.people?.length > 0 && (
            <ResultGroup
              icon="👥"
              title="People"
              results={results.people}
              feedback={feedback}
              onFeedback={submitFeedback}
              renderCitation={(c) => `[user:${c.user_id}]`}
            />
          )}

          {/* MEETINGS */}
          {results.meetings?.length > 0 && (
            <ResultGroup
              icon="🎥"
              title="Meetings"
              results={results.meetings}
              feedback={feedback}
              onFeedback={submitFeedback}
              renderCitation={(c) => `[meeting:${c.meeting_id}:${c.segment_id}]`}
            />
          )}

          {/* LLM answer summary */}
          {results.summary && (
            <div className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded">
              <h3 className="font-semibold mb-2">Summary</h3>
              <p className="text-sm whitespace-pre-line">{results.summary}</p>
            </div>
          )}

          {/* Follow-up questions */}
          {results.follow_ups?.length > 0 && (
            <div className="border-t pt-4">
              <h3 className="font-semibold mb-2">Follow-up questions</h3>
              <div className="flex flex-wrap gap-2">
                {results.follow_ups.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => askFollowUp(q)}
                    className="bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded text-sm"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Not found */}
          {results.docs?.length === 0 && results.code?.length === 0
            && results.people?.length === 0 && results.meetings?.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              No results found. Try different keywords.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const ResultGroup = ({ icon, title, results, feedback, onFeedback, renderCitation }) => (
  <div>
    <h2 className="text-lg font-semibold mb-2 flex items-center gap-2">
      <span>{icon}</span> {title} ({results.length})
    </h2>
    <div className="space-y-2">
      {results.map(r => (
        <div key={r.id} className="border rounded p-3 hover:bg-gray-50">
          <div className="flex justify-between items-start mb-1">
            <h3 className="font-medium">{r.title || r.name}</h3>
            <div className="flex gap-1">
              <button
                onClick={() => onFeedback(r.id, "up")}
                className={`text-sm ${feedback[r.id] === "up" ? "text-green-600" : "text-gray-400"}`}
              >👍</button>
              <button
                onClick={() => onFeedback(r.id, "down")}
                className={`text-sm ${feedback[r.id] === "down" ? "text-red-600" : "text-gray-400"}`}
              >👎</button>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">{r.snippet || r.preview}</p>
          <code className="text-xs text-gray-400">{renderCitation(r)}</code>
        </div>
      ))}
    </div>
  </div>
);
```

---

## Final Day 6 Review (30 min)

### Cross-Loop Checklist (read this out loud each morning)

**L6 power phrases (must say at least 3 per round):**
- "I built X for 100M scale"
- "Cursor pagination O(1), not OFFSET O(N)"
- "Eval harness first, before code"
- "Owned without being asked"
- "Prevented recurrence with dashboard + runbook"
- "5-min rollback via feature flag"
- "Filter ACL BEFORE LLM, not after"
- "Grounded generation, not hallucination"
- "Defines the problem, not just solves it"

**Never say:**
- "I worked on a team" (say "I" 80% of the time)
- "We used Neo4j" (jumping to solution)
- "I was asked to fix" (must be "I owned without being asked")
- "Just add a cache" (no specifics)

**Always have ready:**
- 1 latency story (400 → 2500 → 420ms)
- 1 cost story ($130k → $30k)
- 1 conflict story (chunks vs embeddings)
- 1 ambiguity story (defined metrics first)
- 1 failure story (OFFSET → cursor)

### 7-Day Practice Plan

| Day | Loop | Focus |
|-----|------|-------|
| 1 | Loop 3 (Multimodal) | PDF tables, CLIP, $130k cost |
| 2 | Loop 4 (Real-time) | Flink, backpressure, 1-sec |
| 3 | Loop 5 (Eval) | Recall@8, nDCG, LLM-as-judge |
| 4 | Loop 6 (Security) | ACL, PII, GDPR |
| 5 | Loop 7+8 (Migration + Personalization) | Both compressed |
| 6 | Loop 10 (0->1) | Staff bar, you define |
| 7 | Review all 7, mock with friend | 1 round/day, recorded |

### How to record yourself

1. Open phone, hit record
2. Pick a Loop, do all 5 rounds
3. Watch playback: count "um/uh", check 2-min pitch, look for "we" vs "I"
4. Re-record, iterate

### What to do the night before the real interview

- Re-read this file
- Pick 3 stories, tell them out loud 5x each
- Sleep 8 hours

**You're ready. Good luck. The bar is high. You can hit it.**
