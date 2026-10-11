# 94. Atlassian (ML / Rovo)

- **Role:** ML Engineer (Rovo AI, Search, Recommendations, Code AI)
- **Tech stack:** Java, Kotlin, Python, TypeScript, React, AWS, Postgres, Elasticsearch, OpenSearch, PyTorch, Transformers
- **Comp band:** $180K-$450K total comp (IC3-IC4 Senior); Staff (IC5) $350K-$800K total comp; Principal $500K-$1M total comp (Levels.fyi 2026, USD; AUD is ~20% lower) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~2-4%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (a Jira + Confluence + Bitbucket cross-product Rovo search with a permissions-aware filter). Color: Atlassian blue (#0052CC). Headline: "Atlassian / AI ML Engineer / 2026".

> **TL;DR:** Atlassian's loop is Rovo-heavy and enterprise-flavored — they care deeply about permissions-aware retrieval, agent frameworks, and eval harnesses, and they reward candidates who think "ship ML into a workflow," not "ship ML into a chat." The winning candidate has read the open playbook, speaks RAG fluently, and treats code AI evaluation as a first-class problem.

```
┌──────────────────────────────────────────────────────────────────┐
│                      ATLASSIAN HIRING FUNNEL                     │
├──────────────────────────────────────────────────────────────────┤
│  Apply ──► Recruiter (55%) ──► Tech Phone (40%) ──► Onsite       │
│                                                                  │
│  Onsite ──► Coding / Design / ML / Values ──► Loop Debrief      │
│          (35%)                                  (70%)           │
│                                                                  │
│  Committee ──► Offer (IC4 vs IC5 split) ──► Team Anywhere match │
└──────────────────────────────────────────────────────────────────┘
```

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, location | 30 min | ~55% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML/system design chat | 60 min | ~40% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1 day | ~35% advance |
| 4. **Hiring committee** | Loop debrief + cross-org calibration | 1-2 weeks | ~70% advance |
| 5. **Offer** | Comp + level + team | 1 week | — |

Atlassian's loop is well-structured but slightly less intense than FAANG — the bar is high but the loop is more predictable. Rovo (their AI assistant launched 2024) is the primary AI surface, integrating LLM capabilities into Jira, Confluence, Trello, and Bitbucket. Most ML roles focus on Rovo-related problems: search, RAG, agent design, evaluation.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML background"
**Answer:** "I built [X] for [Y]. Most recently I shipped [Z] in [domain]."
**Tip:** Atlassian is more "product engineering" than "ML research" — emphasize shipping.

### Q1.2: "Why Atlassian?"
**Answer:** "Three reasons. First, Rovo is a real product with 300K+ enterprise customers — great distribution for AI. Second, Atlassian's culture is genuinely 'open company, no bullshit' — the playbook is public. Third, I want to work on AI that helps teams ship faster, not just chat. The Jira workflow integration is a unique ML surface."
**Tip:** Reference Atlassian's open-work culture, the Rovo launch, and the 2026 AI features.

### Q1.3: "Location + remote"
**Answer:** Atlassian is "Team Anywhere" — fully remote globally. They pay in local bands. This is a real perk.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Merge K sorted lists" or "LRU cache"
**Answer:**
```python
import heapq
def mergeKLists(lists):
    heap = []
    for i, l in enumerate(lists):
        if l: heapq.heappush(heap, (l.val, i, l))
    dummy = ListNode(0); cur = dummy
    while heap:
        v, i, node = heapq.heappop(heap)
        cur.next = node; cur = cur.next
        if node.next: heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next
```
**Tip:** Medium LeetCode. Atlassian's bar is moderate — they want clean code, not clever tricks.

### Q2.2: ML — "How would you build a Rovo-style assistant for Confluence?"
**Answer:** "Three layers. (1) Indexing: ingest Confluence pages into a vector store (semantic embeddings) + BM25 keyword index. (2) Retrieval: query rewrite → hybrid retrieval (BM25 + ANN) → re-rank. (3) Generation: LLM with retrieved context, prompt-engineered to cite sources. (4) Eval: golden Q&A set, judge LLM, human eval. (5) Iteration: log user feedback, retrain ranker."
**Tip:** Show RAG fluency. Mention Rovo's strengths: integration with Jira issues, permissions-aware retrieval.

### Q2.3: System design — "Design a cross-product search (Jira + Confluence)"
**Answer:** "Federated retrieval: query → intent classifier (Jira issue? Confluence page? both?) → parallel retrieval from each product's index → merge → rank by relevance + product mix + permissions. Permissions are key — Confluence spaces and Jira projects have access controls; the ranker must respect them. Real-time indexing for newly-created pages."
**Tip:** Atlassian cares deeply about permissions. They're enterprise, so access control is non-negotiable.

## Stage 3: Onsite (4 rounds, 1 day)

### Round 3.1: Coding
**Q3.1.1:** "Word break" or "Subset sum" — DP.
**Q3.1.2:** "Design a task scheduler with rate limiting." Use token bucket + priority queue.
**Q3.1.3:** "Find the longest palindromic substring." Manacher or expand-around-center.

### Round 3.2: System design
**Q3.2.1:** "Design Rovo's agent framework." Tool calling, planning, multi-step reasoning, error recovery, eval, cost. Reference Atlassian's "Rovo Agents" launch.
**Q3.2.2:** "Design an enterprise search system." Crawling, indexing, ranking, permissions, freshness, multilingual, multi-product.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through a RAG system you've built." End-to-end: chunking, embeddings, retrieval, generation, eval.
**Q3.3.2:** "How do you evaluate a code-completion model (Bitbucket AI)?"
**Answer:** "Multiple metrics: exact-match (does the suggestion match what the user accepted?), acceptance rate, code-quality metrics (does the completed code pass tests?), latency (<300ms target), user override rate, hallucination rate (does the code reference non-existent functions?). Human eval on a sample. Online A/B test on accepted-suggestions + downstream PR throughput."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you had to ship under conflicting priorities." STAR.
**Q3.4.2:** "Time you disagreed with a teammate on architecture." STAR.
**Q3.4.3:** "How do you embody Atlassian's values (Open, Bold, Playful, Customer-first)?" — be specific.

## Stage 4: Hiring committee
Atlassian's committee is a structured loop debrief where the interviewers share notes and calibrate level. IC3 vs IC4 (Senior) vs IC5 (Staff) is decided here. The bar is high but the loop is more forgiving than FAANG. Loop typically wraps in 1-2 weeks.

## Stage 5: Offer
Atlassian comp is good but below FAANG. Remote is genuine — they pay in local bands (US, Canada, AU, EU). RSU is 4-year vest with annual refresh. Team match is pre-onsite for some roles. Negotiation is moderate — they move on equity.

## Tips for the Atlassian loop
1. **RAG fluency is table stakes** — Rovo is built on retrieval + LLM.
2. **Permissions-aware retrieval is a differentiator** — they care about enterprise access control.
3. **Coding is medium LeetCode** — focus on clean code.
4. **Reference Atlassian's open playbook** — show you've read it.
5. **Team Anywhere is a perk** — be clear on your location preference.
6. **AI features are integrated, not standalone** — show product integration thinking.
7. **Reference Rovo Agents and the 2026 AI roadmap** — shows engagement.

## Real candidate report
> "I interviewed for ML on the Rovo team. The system design was on Rovo's RAG system and they pushed hard on permissions-aware retrieval — Atlassian's customers are enterprise so access control is the #1 risk. The coding round was medium DP. The ML deep-dive was on evaluation — they asked about golden sets, LLM-as-judge, and human eval. Got IC4 offer at $280K base + $400K RSU/4yr, fully remote." — Glassdoor, 2025

## Sources
- [Atlassian Engineering Blog](https://www.atlassian.com/engineering)
- [Atlassian Work Life Blog](https://www.atlassian.com/blog/announcements/rovo)
- [Levels.fyi Atlassian](https://www.levels.fyi/companies/atlassian)
- [Glassdoor Atlassian interviews](https://www.glassdoor.com/Interview/Atlassian-Interview-Questions-E115075.htm)
- [LeetCode Atlassian tagged](https://leetcode.com/company/atlassian/)