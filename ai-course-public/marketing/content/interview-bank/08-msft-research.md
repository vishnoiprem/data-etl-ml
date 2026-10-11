# 8. Microsoft Research

- **Role:** Research Engineer / Applied Scientist
- **Tech stack:** Python, PyTorch, .NET, TypeScript, Azure ML, C#/C++
- **Comp band:** $250K-$1.1M+ (L62-L64)
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, level calibration | 1-2 weeks | ~50% advance |
| 2. **Technical phone screen** | 1-2 coding problems + ML fundamentals | 1-2 weeks | ~40% advance |
| 3. **Onsite (4-5 rounds in 1-2 days)** | 2 coding → 1 system design (Azure) → 1 ML theory → 1 behavioral ("As Appropriate") | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Packet → committee vote | 1-2 weeks | ~60% advance |
| 5. **Team match + offer** | Match to MSR / Copilot / Bing / Azure AI | 1-2 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an applied scientist with 5 years in NLP — most recently at [X] where I shipped a Copilot-style code-completion feature for an enterprise IDE. Relevant: a paper on retrieval-augmented generation that beat the SOTA on [benchmark]. I'm targeting MSR because the data + AI convergence in Azure AI Foundry is the bet I want to test.
**Tip:** MSR is research-heavy; bring a paper or a shipped research artifact.

### Q1.2: "Why Microsoft Research?"
**Answer:** I want to work on the small-models-on-Azure thesis — the bet that a 7B model with strong RAG beats a 200B model with weak retrieval on enterprise tasks. The 1 thing I'd test: whether Phi-4 with hybrid retrieval can match GPT-4 class on the MMLU-Pro enterprise subset.
**Tip:** Specific MSR bet + specific test.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Merge two sorted linked lists"
**Answer:**
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next

def merge(a, b):
    dummy = ListNode(0); tail = dummy
    while a and b:
        if a.val <= b.val: tail.next, a = a, a.next
        else: tail.next, b = b, b.next
        tail = tail.next
    tail.next = a or b
    return dummy.next
```
The Microsoft warmup. Walk through edge cases (one empty, equal values).
**Tip:** Microsoft's loop is conversational — talk out loud, ask for hints.

### Q2.2: "Implement a thread-safe bounded blocking queue"
**Answer:**
```python
from collections import deque
from threading import Condition
class BoundedQueue:
    def __init__(self, cap): self.q, self.cap, self.cv = deque(), cap, Condition()
    def put(self, x):
        with self.cv:
            while len(self.q) >= self.cap: self.cv.wait()
            self.q.append(x); self.cv.notify_all()
    def get(self):
        with self.cv:
            while not self.q: self.cv.wait()
            x = self.q.popleft(); self.cv.notify_all(); return x
```

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding

### Q3.1.1: "Reverse a linked list in groups of k"
**Answer:** Recursive: reverse the first k, then recurse on the rest; base case < k → return head unchanged. Iterative: walk through in groups of k, reverse each, stitch.

### Q3.1.2: "Longest substring without repeating characters"
**Answer:** Sliding window with a hash set; expand right, contract left when duplicate. O(n).

### Round 3.2: System design (Azure-infra)

### Q3.2.1: "Design a RAG system for enterprise document search"
**Answer:** Azure AI Search for hybrid retrieval (BM25 + vector + semantic re-ranker), semantic chunker (not fixed-size), text-embedding-3-large or domain model, retrieve top-50, re-rank to top-5, feed to LLM with system prompt + retrieved chunks + citation requirement. Trade-off: recall vs. precision. Hybrid gets 80% recall; re-ranker gets to 90%+ precision.
**Tip:** Name every component, the trade-off, the threshold.

### Q3.2.2: "Design a Copilot feature for M365"
**Answer:** Frontend: M365 add-in. Backend: Azure AI Search for retrieval + Semantic Kernel for orchestration + prompt caching for cost. Latency budget: <200ms p99 for the chat path, <2s for the rewrite path. Eval: offline rubric (GPT-4 judge) + online A/B + red-team + human queue. Trade-off: latency vs. quality.

### Round 3.3: ML theory

### Q3.3.1: "Derive scaled dot-product attention on a whiteboard"
**Answer:** Attention(Q,K,V) = softmax(QKᵀ/√d) V. The √d scales the logits to keep gradients stable. For multi-head: split Q,K,V into h heads, run attention in parallel, concatenate, project.
**Tip:** Derivation, not recitation.

### Q3.3.2: "Compare GPT-4 class vs. open-weights for a Copilot feature"
**Answer:** 3 options: GPT-4 class (highest quality, $0.03/1K, privacy concerns), open-weights (cheaper, lower quality), fine-tuned domain (best for specific task, 2-4 weeks training). Right pick: GPT-4 for MVP; migrate to fine-tuned open-weights at 10K DAU.
**Tip:** 3 options, named trade-offs, migration path.

### Round 3.4: Behavioral ("As Appropriate")

### Q3.4.1: "A time you shipped under a tight deadline with limited resources"
**Answer:** We had 2 weeks to ship a Copilot feature for an enterprise customer. I cut the eval suite to 100 hand-picked queries (vs. 5K), kept the offline rubric, deferred the red-team to v2. We shipped on time; quality passed the bar; red-team shipped 3 weeks later.

### Q3.4.2: "A time you disagreed with your manager"
**Answer:** My manager wanted to use GPT-4 class for everything; I argued for hybrid (open-weights for the latency-sensitive path, GPT-4 for the quality-sensitive path). I built a benchmark; the hybrid was 40% cheaper at <1% quality loss. We adopted hybrid for the latency path.
**Tip:** Microsoft's framework: Adaptable, Self-aware, Customer-obsessed, Drive for Results.

### Q3.4.3: "Why Microsoft?"
**Answer:** I believe deeply in the Copilot-for-M365 thesis — if every Office user is 10% more productive, that's a $10B/year revenue story. I'd test whether semantic-kernel orchestration hits <200ms p99 at 10K QPS — that's the threshold where Copilot feels native vs. bolted-on.

## Stage 4: Hiring committee

The MSR committee weighs research output + Azure-system-design fluency. They look for: (1) coherent research narrative, (2) Azure-first system design (AI Search, Semantic Kernel, prompt caching), (3) "As Appropriate" behavioral fit. MSR comp is band-driven; L63 vs. L64 is the call that matters.

## Stage 5: Offer

Microsoft comp negotiates — base + RSU + sign-on + bonus. The play: come with a competing offer (Google, Meta). RSUs vest 4 years, 25%/year, 1-year cliff. The candidate who anchors with a top-of-band Google offer gets the top of MSR's band.

## Tips for the MSR loop

- **Conversational, not a test.** Talk out loud, ask for hints.
- **Azure-first, not generic.** AI Search + Semantic Kernel + prompt caching.
- **RAG end-to-end.** Name every component, the trade-off, the threshold.
- **GPT-4 vs. open-weights.** 3 options, named trade-offs, migration path.
- **"As Appropriate" is the framework.** Adapt, self-aware, customer, drive.
- **4-layer eval rubric.** Offline + online A/B + red-team + human queue.
- **Comp negotiation works.** Bring a competing offer.

## Real candidate report

> *"I actually failed interviews at Meta, Google, Roblox, Snapchat, and TikTok before this. Microsoft was literally the last company on my interview list. The interview felt more like a conversation than a test. The interviewer walked me through their thought process on each problem."*
> — [r/leetcode — I cracked a Microsoft L63 (Senior) role (Nov 2025)](https://www.reddit.com/r/leetcode/comments/1osm7o9/i_cracked_a_microsoft_l63_senior_role_and_wanted/)

## Sources

- [DataInterview — Microsoft AI Engineer Guide (2026)](https://www.datainterview.com/blog/microsoft-ai-engineer-interview)
- [Hello Interview — Microsoft L63-64 Interview Guides & Questions (2026)](https://www.hellointerview.com/guides/microsoft/senior)
- [r/leetcode — I cracked a Microsoft L63 (Senior) role (Nov 2025)](https://www.reddit.com/r/leetcode/comments/1osm7o9/i_cracked_a_microsoft_l63_senior_role_and_wanted/)
- [Levels.fyi — Microsoft compensation](https://www.levels.fyi/companies/microsoft/salaries/software-engineer)
- [Glassdoor — Microsoft Interview Questions (2026)](https://www.glassdoor.com/Interview/Microsoft-Interview-Questions-E1651.htm)