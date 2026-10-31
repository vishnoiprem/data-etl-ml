# PatSnap Interview Quick-Reference Card (Last-Minute Review)

## 🎯 30-Second Elevator Pitch
"I'm an Engineering Lead with X years building data platforms, search systems, and AI/ML products at scale. I've led teams of Y engineers, owned technical roadmaps for data-intensive products, and stay hands-on with Python/Java/Go. I'm excited about PatSnap's mission to transform IP/R&D innovation through AI-native intelligence — my background in [search/relevance | data platforms | AI productionization] directly maps to your Data, Search & AI charter."

---

## 🔑 Must-Know PatSnap Facts
| Fact | Detail |
|------|--------|
| **Founded** | 2007, Singapore |
| **Core Product** | AI-native innovation intelligence platform |
| **Customers** | 18,000+ enterprises, 1/3 of top R&D spenders |
| **Domain** | Patents, scientific literature, IP analytics, competitive intelligence |
| **AI Angle** | Domain-specific AI agents for IP/R&D workflows |
| **Role Scope** | Data ingestion → Search/Retrieval → AI Agents → Production |

---

## 🧠 Technical Keywords to Sprinkle
- **Search**: Hybrid search (BM25 + vector), reranking, Learning to Rank, query understanding
- **Data**: Data contracts, schema evolution, Iceberg/Delta Lake, lineage, quality metrics
- **AI/ML**: RAG, agent orchestration, evaluation (RAGAS), guardrails, LLM Ops, fine-tuning
- **Architecture**: Event-driven, CQRS, multi-tenant, observability (OTel, Prometheus), cost optimization
- **Leadership**: Roadmap ownership, build vs buy, technical debt budget, hiring bar, career ladders

---

## ⭐ Top 5 STAR Stories to Have Ready

| # | Situation | Task | Action | Result | Competency |
|---|-----------|------|--------|--------|------------|
| 1 | Search relevance was poor | Improve NDCG@10 | Hybrid search + reranker + A/B framework | +35% relevance, +20% conversion | Data & Search |
| 2 | Data quality incidents weekly | Build trust in data | Data contracts + Great Expectations + alerting | 90% fewer incidents | Data Engineering |
| 3 | No AI production path | Productionize LLMs | MLOps platform + evaluation + guardrails | 5 models in prod, 60% cost reduction | AI Production |
| 4 | Team of 3 → 15 in 18 months | Scale engineering | Structured hiring + career framework + mentorship | 95% retention, 3 promotions | Leadership |
| 5 | Conflicting Product/Sales asks | Prioritize roadmap | RICE scoring + quarterly planning + stakeholder sync | 40% faster delivery | Product Collaboration |

---

## 🎤 Round-by-Round Cheat Sheet

### Round 1: Recruiter Screen (30 min)
- **Focus**: Background fit, motivation, logistics
- **Key Questions**: "Why PatSnap?", "Why this role?", "Notice period?", "Salary expectations?"
- **Your Ask**: Team structure, interview process, timeline

### Round 2: Technical Screen - Coding/Data (60 min)
- **Focus**: Python/Java coding, data structures, algorithms
- **Prep**: LeetCode Medium (arrays, hash maps, heaps, tries)
- **PatSnap Twist**: Patent/search-related problems (inverted index, prefix search, deduplication)

### Round 3: System Design (60 min)
- **Focus**: Large-scale data/search/AI architecture
- **Likely Problems**: 
  1. Patent search platform (100M docs, hybrid search)
  2. AI agent platform for IP workflows
  3. Multi-source data ingestion pipeline
- **Framework**: Requirements → API → Data Model → Architecture → Deep Dive → Scale/Bottlenecks

### Round 4: Technical Deep-Dive (60 min)
- **Focus**: Your actual experience - search, data, or AI
- **Be Ready to Draw**: Your current/previous system architecture
- **Questions**: "Walk me through your search stack", "How did you evaluate RAG?", "Biggest data quality win?"

### Round 5: Leadership & Behavioral (60 min)
- **Focus**: Management philosophy, conflict, hiring, strategy
- **Use STAR**: Every answer needs Situation, Task, Action, Result
- **Key Themes**: Technical roadmap, team building, trade-offs, influence without authority

### Round 6: Cross-Functional / Product (45-60 min)
- **Focus**: Product sense, stakeholder management, ambiguity
- **Scenarios**: "Sales promises feature X", "Product wants AI feature with no data", "Customer POC failing"

### Round 7: Senior Leadership / CTO (45 min)
- **Focus**: Strategic thinking, 3-year vision, culture fit
- **Questions**: "How would you approach PatSnap's AI strategy?", "Build vs buy for vector DB?", "How do you measure engineering success?"

---

## 📝 Questions You MUST Ask (Per Interviewer)

| Interviewer | Top 2 Questions |
|-------------|-----------------|
| **Engineering Manager** | 1. "What's the #1 technical challenge the team faces today?" 2. "How do you balance platform investment vs feature delivery?" |
| **Senior Engineer** | 1. "What's the current search/data stack?" 2. "What's the worst technical debt you'd fix?" |
| **Product Manager** | 1. "How do customer requests flow into the roadmap?" 2. "What's a recent AI feature that surprised you?" |
| **CTO/VP Engineering** | 1. "What's the 3-year vision for AI at PatSnap?" 2. "How does engineering influence company strategy?" |
| **Peer Lead** | 1. "How does on-call work?" 2. "What's the deployment/release process?" |

---

## ⚡ Rapid-Fire Technical Refreshers

### Search Relevance Metrics
```
NDCG@k = DCG@k / IDCG@k
DCG = Σ (rel_i / log2(i+1))
MAP = Mean Average Precision
MRR = Mean Reciprocal Rank
```

### Vector Search Basics
- **HNSW**: Hierarchical Navigable Small World - graph-based ANN, fast, memory-heavy
- **IVF**: Inverted File - cluster centroids, faster build, lower recall
- **PQ**: Product Quantization - compression for large-scale

### RAG Evaluation (RAGAS)
- **Faithfulness**: Answer grounded in context?
- **Answer Relevancy**: Answers the question?
- **Context Precision**: Retrieved chunks relevant?
- **Context Recall**: All needed info retrieved?

### Data Quality Dimensions
1. **Completeness** - Missing values?
2. **Accuracy** - Correct values?
3. **Consistency** - Same across systems?
4. **Timeliness** - Fresh enough?
5. **Validity** - Conforms to schema?
6. **Uniqueness** - No duplicates?

---

## 🚨 Red Flags to Avoid Saying
- ❌ "I'm not hands-on anymore" → ✅ "I code review weekly, wrote [X] last quarter"
- ❌ "We just used Elasticsearch" → ✅ "We tuned BM25, added learning-to-rank, built hybrid search"
- ❌ "AI is just prompting" → ✅ "We built evaluation pipelines, guardrails, cost tracking"
- ❌ "Product gives us requirements" → ✅ "We co-discover, prototype, validate with customers"
- ❌ "I hire senior only" → ✅ "I build balanced teams: senior/mid/junior with growth paths"

---

## ✅ Final 24-Hour Checklist
- [ ] Read this card 3x
- [ ] Practice 5 STAR stories aloud (timer: 2 min each)
- [ ] Review system design framework (draw 2 architectures from memory)
- [ ] Research 2 interviewers on LinkedIn
- [ ] Prepare 3 questions per interviewer
- [ ] Test camera/mic/lighting
- [ ] Print/save PatSnap website, blog, recent news
- [ ] Sleep 7+ hours
- [ ] Wear confident professional attire
- [ ] Have water, notebook, pen ready

---

## 💪 Mindset Anchors
1. **You've done this work** — you're not interviewing for a stretch role
2. **They need you** — 18K customers, AI-native transformation, they're hiring for a reason
3. **Conversation, not interrogation** — they want a peer they'd enjoy working with
4. **PatSnap context** — always tie answers to patents, IP, innovation intelligence
5. **Stay curious** — ask thoughtful questions; it signals seniority

---

*Print this. Read it morning of. Crush it.* 🚀