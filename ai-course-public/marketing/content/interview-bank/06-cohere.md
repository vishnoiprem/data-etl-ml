# 6. Cohere

> **Hero image spec:** 1400×788 px. Mood: editorial-technical (Stripe Press meets MIT Tech Review). Composition: the company name + 1 signature visual from the company's domain (hybrid retrieval / RAG stack diagram). Color: company brand color as accent (Cohere deep blue). Headline on image: "Cohere / ML Engineer / 2026".

> **TL;DR:** Cohere's loop runs 4 stages (Toronto / SF / London) and rejects ~96% of candidates — the signature question is "implement BM25 from scratch," graded on retrieval depth, not syntax. The winning candidate can name the 4-layer RAG stack (ingestion, chunking, retrieval, generation), defend the enterprise-RAG thesis over the consumer-pivot, and recite the trade-offs of hybrid vs. dense retrieval.

```
Recruiter (60%) → Phone (40%) → Onsite (30%) → Reference + offer
```

- **Role:** ML Engineer
- **Tech stack:** Python, PyTorch, JAX, CUDA, Triton, vLLM
- **Comp band:** CAD 200K-700K / USD 180K-600K total comp (L3-L6) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (Enterprise / RAG / For Work) | 1 week | ~60% advance |
| 2. **Technical phone screen** | 1-2 coding + ML fundamentals, RAG-heavy | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds, 1 day, Toronto/SF/London)** | Coding → RAG system design → ML deep-dive → behavioral | 1-2 days | ~30% advance |
| 4. **Reference checks + offer** | Comp negotiation real | 1-2 weeks | — |

The loop assumes the RAG context in every system-design round — generic ML answers lose. Most candidates under-prepare retrieval fundamentals (BM25 derivation, hybrid fusion, reranker lift).

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in NLP and RAG — most recently at [X] where I shipped a hybrid retrieval system that cut enterprise search latency by 50%. Relevant: a paper on dense retrieval for enterprise search. I'm targeting Cohere because the enterprise-RAG bet is the most differentiated enterprise-AI thesis in 2026.
**Tip:** Cohere grades enterprise-RAG depth; bring hybrid retrieval + chunking specifics.

### Q1.2: "Why Cohere?"
**Answer:** I want to work on Cohere For Work because the enterprise-RAG thesis is real — the moat isn't the model, it's the retrieval + the eval + the deployment. The 1 thing I'd test: whether Command R+ with hybrid retrieval + reranking can match GPT-4 class on a regulated-industry eval at 1/5 the cost. I disagree with the consumer-pivot thesis — stay enterprise.
**Tip:** Enterprise-RAG + Command R+ is the Cohere bet.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Implement BM25 from scratch"
**Answer:**
```python
import math
from collections import Counter, defaultdict
class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs, self.df, self.N, self.avgdl = [], defaultdict(int), 0, 0
    def fit(self, docs):
        self.docs = [d.split() for d in docs]
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(self.N, 1)
        for d in self.docs:
            for term in set(d): self.df[term] += 1
    def score(self, query, idx):
        d = self.docs[idx]; dl = len(d); tf = Counter(d)
        s = 0
        for term in query.split():
            if term not in self.df: continue
            idf = math.log((self.N - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1)
            s += idf * (tf[term] * (self.k1 + 1)) / (tf[term] + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s
```
The Cohere warmup. Name k1, b, the IDF formula.
**Tip:** BM25 + hybrid retrieval is the Cohere-canonical answer.

The phone screen is BM25 from scratch. The onsite assumes you're already in a RAG context — name the 4 layers, the bar, the trade-off at every step.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "LRU cache, thread-safe, with TTL"
**Answer:** `OrderedDict` for LRU + expiry timestamp; on `get` check TTL, evict if expired. Sharded locks for concurrency. Trade-off: sharding improves throughput but complicates the eviction policy.

### Q3.1.2: "Tokenize text with a BPE (byte-pair encoding) tokenizer"
**Answer:** BPE iteratively merges the most frequent pair of adjacent tokens. Vocabulary: starts with bytes, grows to ~50K entries. Trade-off: BPE handles OOV but can produce subword sequences that lose semantic meaning. Cohere uses a SentencePiece-style BPE for Command R+.
**Tip:** BPE is the Cohere tokenization answer.

### Round 3.2: RAG system design (60 min)

### Q3.2.1: "Design a RAG system for enterprise document search"
**Answer:** 4 components: (1) ingestion (parsers, OCR, table extraction), (2) chunking (semantic, not fixed-size), (3) retrieval (hybrid: BM25 + dense + reranker), (4) generation (Command R+ with citations). Trade-off: recall (BM25 + dense) vs. precision (reranker). For enterprise: 95% recall + 90% precision is the bar.
**Tip:** Name every component, the trade-off, the bar.

### Q3.2.2: "Design a RAG eval framework"
**Answer:** 4 layers: (1) retrieval eval (recall@K, nDCG), (2) generation eval (faithfulness, answer relevance), (3) end-to-end eval (human-rated), (4) online eval (thumbs up/down). The trade-off: cost vs. coverage. Cohere's Compass is the managed version; the candidate who can name the failure modes wins.
**Tip:** Eval is the enterprise-AI differentiator.

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "Compare dense vs. sparse vs. hybrid retrieval"
**Answer:** Sparse (BM25): keyword match, no semantic understanding, fast. Dense (embeddings): semantic, no exact match, slower. Hybrid: combine via reciprocal rank fusion. The bet: hybrid gets 80% recall; reranker is what gets to 90%+. Cohere Rerank is the production reranker.
**Tip:** Hybrid + reranker is the Cohere stack.

### Q3.3.2: "How would you fine-tune Command R+ for a customer support use case?"
**Answer:** QLoRA on customer support tickets + responses. Eval: held-out tickets, judged by GPT-4 + human review. The trade-off: full fine-tune (better quality, expensive) vs. LoRA (cheaper, slightly lower). The privacy story: on-prem training for regulated customers.
**Tip:** QLoRA + on-prem is the enterprise bet.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "A time you disagreed with a coworker"
**Answer:** A coworker wanted pure dense retrieval for our RAG system; I argued for hybrid with BM25. I built a 1K-query benchmark; hybrid beat dense by 8% on recall@10. We adopted hybrid.
**Tip:** Data, not opinion, wins.

### Q3.4.2: "Why Cohere?"
**Answer:** I want to work on Cohere For Work because the enterprise-RAG thesis is the moat. The 1 thing I'd test: whether Command R+ with hybrid retrieval + reranking can match GPT-4 class on a regulated-industry eval at 1/5 the cost. The 1 thing I disagree with: the consumer-pivot thesis — stay enterprise.
**Tip:** Enterprise + RAG is the Cohere bet.

## Stage 4: Hiring committee

The committee weighs RAG + enterprise depth + Cohere mission fit. They look for: (1) coherent enterprise narrative, (2) RAG component literacy (BM25, dense, reranker, chunking), (3) "would I trust this person with a Fortune 500 customer?" 1-2 week turnaround.

## Stage 5: Offer

Cohere comp is base + RSU + sign-on. Toronto is the primary hub (lower cost of living). The play: anchor with a competing offer (OpenAI, Anthropic). Sign-on is real for senior candidates. RSU vests 4 years.

## Tips for the Cohere loop

- **Enterprise-RAG is the bet.** Hybrid retrieval + reranker + Command R+.
- **BM25 is non-negotiable.** Be able to derive it on a whiteboard.
- **4-layer RAG stack.** Ingestion, chunking, retrieval, generation.
- **Eval is the differentiator.** 4-layer eval: retrieval, generation, e2e, online.
- **QLoRA for fine-tuning.** On-prem for regulated customers.
- **Toronto/SF/London.** Loop is on-site; travel reimbursed.
- **"Why Cohere" needs the enterprise bet.** Stay enterprise, not consumer.

## Real candidate report

> *"Cohere's loop is RAG-heavy. Every system design question assumes the RAG context. The 'why Cohere' answer needs to be about enterprise: privacy, deployment, on-prem. Generic 'I want to build AGI' answers lose. The 4-layer RAG stack — ingestion, chunking, retrieval, generation — is the canonical answer."*
> — Glassdoor candidate report, paraphrased from 2026 loops

## Sources

- [Cohere](https://cohere.com/)
- [Cohere For Work](https://cohere.com/work)
- [Cohere Rerank](https://cohere.com/rerank)
- [Cohere Compass](https://docs.cohere.com/docs/compass)
- [Levels.fyi — Cohere compensation](https://www.levels.fyi)

---

## The 1 thing to remember

At Cohere, BM25 derivation is the gate — name k1, b, and the IDF formula, then build the 4-layer RAG stack on top; enterprise-RAG thesis, not consumer-pivot, wins the loop.