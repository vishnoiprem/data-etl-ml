# Case Study 2 — The Pivot (when to walk away)

> **TL;DR.** A 25-person legal-tech startup asked for a RAG chatbot over 50,000 case-law PDFs. After 2 weeks, I walked away and refunded 50% of my fee. The corpus was **not RAG-ready**: 3 PDF formats, no canonical version per case, no owner, no SLA, no eval set. Faithfulness on the messy 20K subset was 0.42 (vs 0.78 on the clean 30K); on the chaotic 5K, the chatbot returned marketing newsletters as case law. The customer was better served by walking away — the 3-month data cleanup they did instead was the right path. **The lesson:** **data readiness is the gate**; the 5-question data-readiness scorecard is the rubric. When the scorecard says "no," walk away or re-scope to a data engagement.

---

## 1. Context

### 1.1 Customer profile

| Field | Value |
|---|---|
| Company | "LexBench" (pseudonym) |
| Vertical | Legal-tech, B2B SaaS for boutique litigation firms |
| Size | 25 FTEs, $4M Series A, 8 months old |
| Product pitch | "AI-powered case-law search for boutique litigation firms" |
| Target user | 5-20-lawyer firms in SG/MY/HK |
| Founders | 1 former litigator (CEO, JD/MBA), 1 former ML engineer (CTO, ex-Google) |
| Engagement | 4-week scoping + prototype, fixed-fee $40K |

### 1.2 What they asked for

> "We have ~50,000 case-law PDFs from Singapore, Malaysia, and Hong Kong. Our customers want to ask a question and get the relevant paragraphs. We need a RAG chatbot."

The implicit ask: "ship a working demo in 4 weeks so we can show our investors and our first 3 design-partner firms."

### 1.3 What they had (the data)

A shared Dropbox with 50,000 PDFs, named according to **3 different conventions** depending on which paralegal uploaded them. **No canonical version per case.** **No metadata schema.** **No owner of the corpus.** When I asked "who decides what 'correct' means for a chatbot answer?", the answer was "we all do." When I asked "what's the SLA for the chatbot?", the answer was "fast and accurate."

### 1.4 Why this is a PE-relevant case

Most AI engagements fail not because the model is wrong, but because **the data is wrong**. Walking away is the highest-ROI decision an FDE can make — it saves the customer 3 months of building on a broken foundation, and it preserves the FDE's reputation for "I won't ship something that won't work." But walking away is also the most-avoided decision, because saying "no" to a paying customer is psychologically expensive. This case study codifies the rubric that makes the decision mechanical, not emotional.

---

## 2. Approach (the 2 weeks I stayed)

### 2.1 Week 1 — data triage

I started by **counting, not building**. The 50,000 PDFs fell into 3 categories by text-layer quality and naming consistency:

| Category | Count | % | Text-layer quality | Naming | RAG-ready? |
|---|---|---|---|---|---|
| **Clean** | ~30,000 | 60% | Native text, OCR-equivalent accuracy > 99% | `YYYY-MM-DD_CASEID.pdf` | Yes |
| **Noisy** | ~15,000 | 30% | Scanned, OCR ~70% accuracy (Tesseract) | Inconsistent: `Case 1234.pdf`, `case_1234.pdf`, `Singapore_v_xxx_2020.pdf` | No — needs OCR + dedup |
| **Chaotic** | ~5,000 | 10% | Mixed formats, some are newsletters, some are pleadings, some are duplicates with no clear "canonical" version | No convention | No — needs manual triage |

**The 70/30/10 split is the kind of insight that only an FDE sees in week 1.** A traditional software vendor would have quoted the project as "50,000 documents" and built a single pipeline; the FDE sees that **20% of the corpus is unusable as-is** and that fixing it is a 3-month data project, not an AI project.

### 2.2 Week 1 — the 5-question interview

I asked the founders 5 questions. The answers, recorded verbatim, are the data for the data-readiness scorecard:

| # | Question | Their answer | Score |
|---|---|---|---|
| 1 | Is the data canonical? (one version per record, named consistently, owned by someone) | "We all own it. Different paralegals uploaded at different times." | **0/3** — no owner, no canonical version |
| 2 | Is there an SLA? (what does "good" look like, in numbers, with an owner) | "Fast and accurate. We'll figure out the numbers later." | **0/3** — no SLA, no owner |
| 3 | Is there an eval set? (can the customer measure quality today) | "We have a list of questions our customers asked in surveys." | **1/3** — questions exist, no graded answers |
| 4 | Is there a stakeholder with decision authority? (one person who can say "ship it / don't ship it") | "Both of us. We agree on most things." | **1/3** — two co-founders; no escalation path |
| 5 | Is the customer willing to pay for data work? (the cleanup is a separate engagement) | "We assumed it was part of the AI build." | **0/3** — expects data work to be free |

**Score: 2/15.** Below the engagement threshold (see §3.2). I told the founders at the end of week 1: "I can ship a working prototype on the clean 30K in week 2, but I can't recommend shipping to real customers on the full 50K without a data cleanup project first."

### 2.3 Week 2 — prototype on the clean subset

I built a prototype on the clean 30K: BM25 + a small dense index (sentence-transformers/all-MiniLM-L6-v2) + 4 RAGAS-style metrics + an eval set of 50 hand-curated questions. **On the clean 30K, the metrics were acceptable:**

| Metric | Value | Verdict |
|---|---|---|
| Faithfulness | 0.78 | OK (PF drafter baseline was 0.81) |
| Answer relevance | 0.81 | OK |
| Context precision | 0.74 | OK |
| Context recall | 0.69 | Marginal |

Then I extended the prototype to the noisy 15K:

| Metric | Value (noisy 15K) | Δ vs clean |
|---|---|---|
| Faithfulness | **0.42** | -0.36 |
| Answer relevance | 0.55 | -0.26 |
| Context precision | 0.38 | -0.36 |
| Context recall | 0.41 | -0.28 |

**Faithfulness dropped 36 percentage points.** Below any reasonable threshold for a legal product where the cost of a wrong answer is a malpractice claim.

And on the chaotic 5K, the chatbot returned **marketing newsletters as case law** on 7 of 50 test queries (14%). On 2 of those 7, the newsletter was a competitor's product announcement. The risk surface was not "the model is wrong"; it was "the data is wrong."

### 2.4 Week 2 — the pivot conversation

I called the co-founders and said:

> "I can ship the prototype on the clean 30,000. It'll work for the customers who only ask about SG 2020+ cases. For the other 20,000, you need a data cleanup project first — I estimate 3 months of paralegal time to get the corpus to RAG-ready status. I can scope that as a separate engagement at a different rate. Or, if you want to ship on the full 50K now, the chatbot will give wrong answers on 14% of queries. I'd rather refund 50% of my fee than ship that."

They asked: "Can we ship the chatbot anyway and clean up the data later?"

I said: **no.**

---

## 3. Outcome

### 3.1 Engagement economics

| Line item | Amount | Notes |
|---|---|---|
| Fee quoted | $40,000 | 4-week fixed-fee, prototype + demo |
| Fee invoiced | $20,000 | 50% delivered; 50% refunded |
| Refund amount | $20,000 | Returned in week 2 |
| FDE time invested | ~80 hours | 2 weeks × 40 hours |
| Effective hourly rate | $250/hr | 20K / 80h |

The $20K refund was the right call economically: a chatbot that returns wrong answers on 14% of queries would have generated ~3 wrong answers in the first month, costing the customer at least 1 lost design-partner firm ($50K-$100K ACV). **The refund was cheaper than the alternative by 2.5-5x.**

### 3.2 The 6-month follow-up

I checked in at month 6:

| Milestone | Status |
|---|---|
| Data cleanup project staffed | Yes — 1 data engineer, 2 paralegals |
| Corpus status | 70% clean (was 60% on day 1) |
| RAG chatbot shipped | No — re-engaged a different AI vendor on the clean subset |
| First design-partner firm | Yes — using chatbot on SG 2020+ subset only |
| Wrong-answer rate in production | 2% (down from projected 14%) |
| Customer NPS | +42 (positive; design-partner firms find it useful) |

**The customer's outcome was better because I walked away.** The 3-month cleanup was the right path; my walking away forced the conversation that the founders were avoiding.

### 3.3 What I would have caused by staying

| Counterfactual | Cost |
|---|---|
| Wrong answers in first month | ~3 (per the 14% projection on 22 queries/mo) |
| Lost design-partner firm | 1 (probability-weighted) |
| Litigation risk from a wrong case-law citation | Tail risk; 1 event could be fatal for a Series A startup |
| Refund + reputational cost to FDE | High (would have been a "this FDE shipped a bad product" Google result) |
| **Net expected cost of staying** | **$50K-$200K** (loss of 1 design firm + tail risk) |
| **Net cost of walking away** | **$20K refund + 2 weeks of FDE time** |

The expected-value math is 2.5-10x in favor of walking away. **The hard part is not the math; the hard part is saying "no" to a paying customer.**

---

## 4. The data-readiness scorecard (the rubric)

This is the artifact that survives the engagement. The scorecard turns "should I take this engagement?" from a vibes question into a mechanical decision.

### 4.1 The 5 questions (weighted)

| # | Question | Weight | 0 points | 1 point | 3 points |
|---|---|---|---|---|---|
| 1 | Is the data canonical? | ×3 | No owner, no canonical version, mixed naming | Some canonical subset, partial naming convention | One version per record, named consistently, owned by name |
| 2 | Is there an SLA? | ×3 | "We'll figure it out" | "We have a vague target" | "P95 < 2s, faithfulness > 0.85, owned by Name" |
| 3 | Is there an eval set? | ×2 | No questions, no answers | Questions exist, no graded answers | Eval set with graded answers, runnable today |
| 4 | Is there a decision-maker? | ×2 | "We all decide" | "Two co-founders, no escalation" | One named person with authority to ship / not-ship |
| 5 | Will the customer pay for data work? | ×2 | "We assumed it's part of the AI build" | "We'll consider it" | "Yes, separate SOW, separate rate" |

**Maximum score: 45.** **Engagement threshold: 30.** Below 30, the engagement is a data engagement or it should be declined.

### 4.2 The decision tree

```
                        Start
                          │
                          ▼
                    Score the 5 questions
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
           Score ≥ 30  15 ≤ Score < 30   Score < 15
              │           │                │
              ▼           ▼                ▼
          Take the     Conditional.    Walk away.
          engagement.  Re-scope to     Or re-scope to
          Standard     a data          a 100% data
          FDE rate.    engagement      engagement
                       at a different  (cleanup, not
                       rate ($150/hr   AI).
                       for data work
                       vs $250/hr
                       for FDE).
```

### 4.3 The LexBench scorecard, re-scored

| # | Question | LexBench answer | Score |
|---|---|---|---|
| 1 | Data canonical? (×3) | 0 | 0 |
| 2 | SLA exists? (×3) | 0 | 0 |
| 3 | Eval set? (×2) | 1 | 2 |
| 4 | Decision-maker? (×2) | 1 | 2 |
| 5 | Pay for data work? (×2) | 0 | 0 |
| | **Total (max 45)** | | **4** |

Score 4 < 15 → walk away, with a referral to a data engineer for the cleanup project. **The decision is mechanical; the conversation is the hard part.**

### 4.4 What the scorecard gets wrong

The scorecard has 2 known failure modes:

1. **The "1-point" trap.** A customer with questions but no graded answers scores 2 on question 3. This is below the threshold (30) but might mask latent readiness. Mitigation: ask for 1 graded answer; if the customer can't produce one, the answer is "no" not "1."

2. **The "we'll pay for data work" answer.** Some customers will say "yes" in week 1 and renegotiate in week 4. Mitigation: include a separate SOW for the data work, with a separate rate, signed before the AI engagement starts. If they won't sign, the answer is "no."

---

## 5. What I'd do differently

### 5.1 Frame the data-readiness check as a paid artifact

I spent 1 week on the corpus assessment and didn't charge for it separately. The co-founders saw "1 week of free work" and felt obligated to keep me. **If I had charged $5K for the data-readiness report** (a 1-pager with the 3 categories, the 70/30/10 split, and the recommended cleanup plan), the engagement would have ended with a clearer contract: "the AI engagement starts after the cleanup is done, at which point the data-readiness score is recomputed."

**This is the single most important fix.** It converts a sunk-cost-loss-aversion trap ("we already paid for 1 week, might as well continue") into a clean phase boundary.

### 5.2 Set the scorecard bar in the first conversation

The first conversation should include: **"if your data-readiness score is below 30, the engagement is a data engagement, not an AI engagement. The rate is different."** I didn't set that bar; the co-founders assumed I was billing them for an AI engagement, not a data assessment. Setting the bar in advance turns the conversation from "you're walking away on us" into "the scorecard said the engagement isn't ready; here's the data engagement that is."

### 5.3 Walk away faster (week 1, not week 2)

I spent 2 weeks. I should have walked in week 1. **The data-readiness check is the first week of the engagement; if it fails, the engagement is over.** A week-1 walkaway costs 1 week of FDE time. A week-2 walkaway costs 2 weeks and a prototype that the customer might be tempted to ship anyway.

### 5.4 The asymmetric advice I'd give a junior FDE

**You will be tempted to stay.** The customer will say "we'll clean up the data after the prototype." The investor demo is in 6 weeks. The founders are smart. The prototype will be impressive. **Stay anyway, and the 14%-wrong-answer rate will be your fault, not theirs.** Walking away is the high-status move: it signals that you have a rubric, that your rubric says "no," and that you will not ship something that will fail.

---

## 6. The pattern (generalized)

The data-readiness scorecard is the second of the FDE's three artifacts. The eval set is the spec; the runbook is the contract; **the scorecard is the gate**.

```
  ┌──────────────────────────────────────────────────────────┐
  │  THE 3 FDE ARTIFACTS                                     │
  │                                                          │
  │  1. The eval set (what "good" means)                     │
  │  2. The runbook (what to do when it goes wrong)          │
  │  3. The data-readiness scorecard (whether to engage)     │
  │                                                          │
  │  All three are required to call an FDE engagement done.  │
  │  The eval set survives the engagement.                   │
  │  The runbook survives the FDE's exit.                    │
  │  The scorecard survives the customer's next vendor.      │
  └──────────────────────────────────────────────────────────┘
```

A junior FDE has only the eval set. A senior FDE has the eval set and the runbook. **A principal FDE has all three — and the courage to walk away when the third one says "no."**

---

## 7. References

- **The scorecard source**: derived from "AI Readiness Assessment" templates published by McKinsey (2023) and BCG (2024), adapted for FDE engagements where the deliverable is a working service, not a strategy deck.
- **The LexBench engagement**: 6-month follow-up data is from a personal communication with the LexBench CTO in month 6.
- **PacificFreight comparison**: see [`engagement-1-pf-drafter.md`](./engagement-1-pf-drafter.md) for a scorecard 5/5 engagement.
- **The pivot case study template**: modeled on the public postmortems at statuspage.io and the Google SRE book ch. 17 (eliminating toil) and ch. 28 (postmortem culture).
- **RAGAS metric validation**: Es et al., arXiv:2309.15217 (Sep 2023), used to justify the deterministic 4-metric eval set.
