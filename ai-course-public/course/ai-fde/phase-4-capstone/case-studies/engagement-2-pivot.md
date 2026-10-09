# Case Study 2 — The pivot: when to walk away

> **TL;DR (1 page).** I was asked to build a RAG chatbot for a
> legal-tech startup's case-law corpus. After 2 weeks, I walked
> away. The corpus was not RAG-ready: 3 PDF formats, no canonical
> version per case, no owner, no SLA. I could have built a chatbot
> on top of this mess — but the customer would have been unhappy
> in 3 months. **The lesson:** data is the bottleneck. When the
> data isn't ready, the engagement is a 3-month tutorial on PDF
> parsing, not an AI engagement. Walk away.

---

## Context

**Customer:** A 25-person legal-tech startup. Two co-founders
(one former litigator, one former ML engineer). $4M Series A.
The product pitch: "AI-powered case-law search for boutique
litigation firms."

**What they asked for:** a RAG chatbot over their corpus of
~50,000 case-law PDFs from Singapore, Malaysia, and Hong Kong.
Their customers (boutique firms with 5-20 lawyers each) wanted
"ask a question, get the relevant paragraphs."

**What they had:** a shared Dropbox with 50,000 PDFs, named
according to 3 different conventions (depending on which
paralegal uploaded them). No canonical version per case.
No metadata schema. No owner of the corpus.

## Approach

**Week 1.** I started by counting. The 50,000 PDFs fell into
3 categories:
- ~30,000 in a clean format (one PDF per case, named
  `YYYY-MM-DD_CASEID.pdf`, with a clean text layer)
- ~15,000 in a noisy format (scanned PDFs, OCR was ~70%
  accurate, names were inconsistent)
- ~5,000 in a chaotic format (mixed formats, some were
  actually newsletters or marketing material, no naming
  convention)

I asked: who's the owner of the corpus? The co-founder said
"we all are." I asked: what's the SLA for the chatbot? They
said "fast and accurate." I asked: who's accountable when the
chatbot gives a wrong answer? They said "we'll figure that
out later."

**Week 2.** I built a prototype on the clean 30,000. BM25 +
a small dense index, eval set of 50 questions, 4 RAGAS-style
metrics. The eval was fine: 0.78 faithfulness, 0.81 answer
relevance. But when I extended the prototype to the noisy
15,000, faithfulness dropped to 0.42. When I tried the
chaotic 5,000, the chatbot returned marketing newsletters
as case law.

I called the co-founders and said: "I can ship the prototype
on the clean 30,000. It'll work for the customers who only
ask about Singapore 2020+ cases. For the other 20,000, you
need a data cleanup project first. I estimate 3 months of
paralegal time to get the corpus to 'RAG-ready' status."

They said: "Can we ship the chatbot anyway and clean up the
data later?"

I said no.

## Outcome

**I walked away.** The engagement ended in week 2. I
returned 50% of my fee. The co-founders were upset but not
surprised — they knew the corpus was a mess. They hired a
data engineer to clean the corpus over the next 3 months;
I checked in at month 6 and the corpus was 70% clean. They
re-engaged with a different AI vendor to build the chatbot
on the clean subset.

**The customer's outcome was better for my walking away.**
If I had shipped the chatbot on the messy corpus, the
chatbot would have given 3 wrong answers in the first month
and the customer would have lost trust. The 3-month cleanup
was the right path; my walking away forced the conversation.

## What I'd do differently

**Frame the data readiness check as a paid artifact.** I
spent 1 week on the corpus assessment and didn't charge for
it separately. The co-founders saw "1 week of free work"
and felt obligated to keep me. If I had charged $5K for the
data readiness report (a 1-pager with the 3 categories and
the recommended cleanup plan), the engagement would have
ended with a clearer contract: "the AI engagement starts
after the cleanup is done."

**Set the "data readiness" bar in the first conversation.**
The first conversation should have included: "if your
corpus isn't RAG-ready, the engagement is a data cleanup
engagement, not an AI engagement. The rate is different."
I didn't set that bar; the co-founders assumed I was
billing them for an AI engagement, not a data assessment.

**Walk away faster.** I spent 2 weeks. I should have
walked in week 1. The data readiness check is the first
week of the engagement; if it fails, the engagement is over.

## The 5-question walk-away test

Before starting an AI engagement, ask:

1. **Is the data canonical?** (one version per record, named
   consistently, owned by someone)
2. **Is there an SLA?** (what does "good" look like, in
   numbers, with an owner)
3. **Is there an eval set?** (can the customer measure
   quality, today, before the engagement starts)
4. **Is there a stakeholder who's accountable?** (one
   person, with authority to make decisions)
5. **Is the customer willing to pay for data work?** (the
   cleanup is a separate engagement, not free)

If any answer is "no" or "we'll figure that out later,"
walk away. Or re-scope the engagement to be the data
work itself.

## Closing

This case study teaches the FDE when to say no. The Pacific
Freight engagement succeeded because the customer had:
- A canonical data source (the shipments.json + the policy
  corpus)
- An SLA (P95 < 2s, thumbs-up > 70%)
- An eval set (the Phase 1 30-row set, shipped in week 1)
- A stakeholder (Mei, with authority to change CS workflows)
- A willingness to pay for data work (Daniel's time on the
  corpus cleanup was in-scope)

The legal-tech engagement failed because none of those
were in place. **The pattern that emerges:** data readiness
is the gate. When the gate is closed, walk away.