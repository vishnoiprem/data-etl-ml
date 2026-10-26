# LlamaIndex — FDE (Enterprise RAG)

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~20–40
- **Comp**: $170K–$230K; TC $280K–$450K
- **What they deploy**: Enterprise RAG agent deployments (LlamaIndex)
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. RAG / agent design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### RAG case
**Q:** *"Customer wants enterprise RAG over legal docs."*
**A (winner):** *"LlamaIndex + custom Data Connectors (S3, SharePoint, DMS). Sentence-window parsing, hybrid retriever, reranker, citation enforcement. LlamaParse for tables. Eval with ragas (faithfulness, relevance). Pilot: 5,000 docs, 4 weeks."*
**Why it worked:** Right LlamaIndex-native stack + ragas evals.

---

## ❌ REJECTION STORIES
### RAG scenario
**Q:** *"Documents contain tables; the model misreads them."*
**A (loser):** "Better OCR."
**What they should have said:** *"Use LlamaParse specifically for tables; structure rows into a SQL-queriable layer. Or convert tables to text with column-aligned format. Eval: per-table accuracy."*

---

## 📚 Reading List
1. LlamaIndex docs
2. RAGAS eval framework
3. LlamaParse docs
4. levels.fyi LlamaIndex