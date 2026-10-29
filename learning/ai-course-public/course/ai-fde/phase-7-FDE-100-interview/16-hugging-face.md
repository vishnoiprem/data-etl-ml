# Hugging Face — Solutions / Applied ML FDE

## Company Snapshot
- **HQ**: NYC / Paris
- **Team Size**: ~50–100 Solutions/Applied ML engineers
- **Comp**: $170K–$220K base; TC $250K–$400K
- **What they deploy**: Enterprise OSS LLM/RAG deployments (Text Generation Inference, Inference Endpoints, Spaces)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (mid LeetCode + Python/ML)
3. ML system design
4. Loop — coding 2, OSS deployment case, customer scenario

---

## ✅ SUCCESS STORIES

### ML system design
**Q:** *"Design an open-source model deployment for a customer who wants Llama-3 70B served internally with low latency."*
**A (winner):** *"Use Hugging Face Text Generation Inference (TGI) with PagedAttention + continuous batching. Quantize to AWQ 4-bit to fit on 2×A100s. Put it behind Inference Endpoints with autoscaling. Add a token streaming SSE endpoint. Add a Helm chart for the customer to self-host. Evals: text-generation-eval harness on 200 prompts."*
**Why it worked:** Used HF-native primitives (TGI, Inference Endpoints, AWQ), addressed latency, made it portable.

---

### Customer scenario
**Q:** *"Customer wants to fine-tune Llama on their data but doesn't have a GPU cluster."*
**A (winner):** *"Two paths. (1) Use HF AutoTrain + Inference Endpoints — we manage the GPUs, you pay per hour. (2) If data must never leave their VPC, deploy on their Azure/GCP using our TGI containers + a one-click Helm chart. I'd pilot with a 1B-param LoRA fine-tune to validate the loop, then scale to a 70B full fine-tune."*
**Why it worked:** Offered two paths (managed vs self-hosted), scoped MVP first.

---

## ❌ REJECTION STORIES

### ML design
**Q:** *"Build a RAG system."*
**A (loser):** Generic LangChain + OpenAI answer with no HF-specific stack.
**Why it failed:** Hugging Face wants HF-native primitives.
**What they should have said:** sentence-transformers + FAISS / HF Inference Endpoints + TGI for the LLM + RAGAS for evals.

---

### Customer scenario
**Q:** *"Customer says model is hallucinating."*
**A (loser):** *"Add RAG."*
**Why it failed:** Generic answer; didn't diagnose.
**What they should have said:** *"Pull 100 examples, categorize, root-cause (retrieval miss vs generation error vs fine-tune gap). Ship targeted fix. Measure."*

---

## 📚 Reading List
1. Hugging Face docs — TGI, Inference Endpoints, AutoTrain
2. sentence-transformers docs
3. RAGAS eval framework
4. r/MachineLearning + r/LocalLLaMA
5. levels.fyi HF Solutions
