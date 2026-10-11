# 58. Casetext (acquired by Thomson Reuters — now CoCounsel)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (e.g., a CoCounsel document analysis card with a contract clause underlined and the Thomson Reuters red palette). Color: Thomson Reuters red (#E60028 on white). Headline: "Casetext (CoCounsel) / AI Legal Engineer / 2026".

> **TL;DR:** Casetext is now CoCounsel inside Thomson Reuters with the 2013 legal-AI pedigree and a 2022 LLM pivot; the loop is recruiter → 60 min coding+LLM phone → 4-round onsite → Thomson Reuters process committee → offer, and the signature round is "design a legal Q&A system with citations" plus the hallucination-prevention question. The winning candidate has shipped a RAG system, can name LegalBench, and treats hallucination prevention as a first-class engineering problem (not a research paper).

```
Recruiter (50%) → Phone (40%) → Onsite (30%) → Committee (60%) → Offer
```

- **Role:** AI Engineer (Legal AI / Document Analysis)
- **Tech stack:** Python, TypeScript, React, Kubernetes, OpenAI/Anthropic APIs, Postgres, Elasticsearch, vector DBs, fine-tuning
- **Comp band:** $180K-$380K total comp (Senior AI Engineer) | RSUs/equity 4-year vest (TR RSU)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + LLM | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, LLM, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Panel review (TR process) | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1-2 weeks | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Casetext/CoCounsel?"
**Answer:** Three reasons. (1) Casetext has been at legal AI since 2013, and the 2022 LLM pivot to CoCounsel put them ahead of the curve. Being inside Thomson Reuters now means distribution no startup can match. (2) The team is ex-LexisNexis, ex-Westlaw, plus AI researchers. (3) CoCounsel was the first real AI legal assistant shipped at scale in 2023.
**Tip:** Show you've used CoCounsel or read about its features. Casetext values legal domain curiosity.

### Q1.2: "Tell me about an LLM app you built for a non-technical user"
**Answer:** Walk through one project where you partnered with a non-engineering user (lawyer, doctor, marketer) and shipped something they actually use. Mention iteration, since first versions are usually wrong.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a simple document classifier (e.g., contract vs brief)"
**Answer:**
```python
import re
def classify_legal_doc(text):
    if re.search(r'\b(plaintiff|defendant|motion to|complaint)\b', text, re.I):
        return "brief"
    if re.search(r'\b(party|consideration|whereas|herein)\b', text, re.I):
        return "contract"
    return "other"
```
**Tip:** Real classifiers use transformer-based zero-shot or fine-tuned BERT. Mention `facebook/bart-large-mnli` for zero-shot.

### Q2.2: LLM — "How would you build a legal document summarization feature?"
**Answer:** Three pillars: (1) **chunking** with structural awareness (sections, paragraphs), (2) **extractive summarization** (TF-IDF, TextRank) for key sentences, (3) **abstractive summarization** (LLM) with grounding + citations. Mention ROUGE/BERTScore for eval.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a sliding window chunker.
- **Q3.1.2:** Build a small LRU cache.
- **Q3.1.3:** Implement a TF-IDF ranker.

### Round 3.2: System design
- **Q3.2.1:** "Design CoCounsel's document analysis pipeline." Discuss: ingest (PDF, DOCX, OCR), parse (sections, headers, footers), chunk, embed, store in vector DB, retrieve, summarize with LLM, present results.
- **Q3.2.2:** "Design a legal Q&A system with citations." Talk: retrieval (BM25 + vector + reranker), grounded generation, citation verification, audit trail.

### Round 3.3: LLM / legal deep-dive
- **Q3.3.1:** "How do you handle hallucinations in legal AI?" Discuss: grounding, citations, post-hoc verification, confidence scores, human review for high-stakes answers.
- **Q3.3.2:** "How do you measure legal AI quality?" Talk: domain benchmarks (LegalBench, Bar Exam), human expert review, citation accuracy, faithfulness, coverage.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a time you worked with a domain expert."
- **Q3.4.2:** "Why legal AI?"

## Stage 4: Hiring committee
Now part of Thomson Reuters, the loop is more structured. The committee looks for: LLM/RAG depth, legal domain curiosity, and a real passion for "AI for experts" products. Red flags: never having built a RAG system, no interest in the legal domain. The TR process is slower (8-day offer in the real-candidate report) but the bar is also more uniform — the committee optimizes for shipping reliability and legal-domain humility, not research depth.

## Stage 5: Offer
Base is at the high end ($200K-$300K+ for senior), equity is now TR RSU (4-year vest, 1-year cliff). TR benefits are excellent. Negotiation: title, sign-on.

## Tips for the Casetext loop
1. **Brute-force RAG fundamentals** — chunking, retrieval, reranking, grounding, citations.
2. **Read about LegalBench** — the standard legal AI benchmark.
3. **Have a legal AI project to discuss** — even a side project (RAG over SEC filings, a summarizer, etc.).
4. **Practice the "design a legal Q&A system" round** — almost always asked.
5. **Be ready to discuss hallucination prevention** — this is the #1 concern in legal AI.
6. **Show domain curiosity** — read a few legal AI papers or the CoCounsel product page.
7. **Have opinions on CoCounsel vs Harvey vs LexisNexis Protege** — they'll ask.

## Real candidate report
> "Phone screen was document classifier coding + LLM design. Onsite had 4 rounds including a tough RAG round where they asked me to design a citation-aware system end-to-end. The behavioral round was a 'tell me about a time you worked with a non-technical user' — I used my previous job where I built a tool for lawyers. Offer: $220K + TR RSU, 8 days." — Levels.fyi, 2025

## Sources
- [Casetext/CoCounsel careers](https://www.thomsonreuters.com/en/careers.html)
- [CoCounsel product](https://www.thomsonreuters.com/en/products/cocounsel.html)
- [Thomson Reuters AI blog](https://www.thomsonreuters.com/en/ai.html)
- [LegalBench benchmark](https://huggingface.co/spaces/open-llm-leaderboard/legalbench)
- [CoCounsel Glassdoor](https://www.glassdoor.com/Interview/Thomson-Reuters-Interview-Questions-E9983.htm)

---

## The 1 thing to remember

Build a citation-aware RAG system before the onsite — Casetext/CoCounsel's #1 concern is hallucination prevention in legal AI, and the candidate who walks grounding, citation verification, and LegalBench numbers in the same answer wins the Thomson Reuters committee, while "I just use GPT-4" gets softly filtered out.
