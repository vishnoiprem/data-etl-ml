# 7. Meta AI (FAIR)

- **Role:** Research Engineer
- **Tech stack:** Python, PyTorch, C++, Llama, FAISS, CoderPad
- **Comp band:** $250K-$1.2M+ (E4-E7)
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, level calibration | 1-2 weeks | ~50% advance |
| 2. **Technical phone screen** | 45 min CoderPad, 2 LeetCode easy/medium | 1-2 weeks | ~40% advance |
| 3. **Onsite (5 rounds in 1 day)** | 2 coding → 1 system design (E5+) → 1 Jedi behavioral → 1 AI-assisted coding | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Packet → committee vote | 1-2 weeks | ~60% advance |
| 5. **Team match + offer** | Match to FAIR / GenAI / Reality Labs | 1-3 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm a research engineer with 6 years in ML — last at [X] where I led the RLHF pipeline for a 70B model. Relevant project: [Y], a paper on memory-efficient attention we published at ICML. I'm here because Llama 4 is the open-weights bet I want to be closest to.
**Tip:** Meta grades research output; bring a paper or a shipped open-source project.

### Q1.2: "Why Meta, specifically?"
**Answer:** I want to work on FAIR because the open-weights thesis is the most important architectural bet of 2026. I want to test whether a 70B Llama 4 with MoE can match a 200B dense on reasoning benchmarks. The bet I disagree with: I think Meta is too aggressive on the open-source release cadence — quality drops before the eval gap closes.
**Tip:** FAIR / GenAI / Reality Labs — pick one and defend it.

## Stage 2: Technical phone screen (45 min)

### Q2.1: "Generate a square matrix filled with elements from 1 to n² in spiral order"
**Answer:**
```python
def spiral(n):
    m = [[0]*n for _ in range(n)]
    top, bot, left, right, num = 0, n-1, 0, n-1, 1
    while num <= n*n:
        for j in range(left, right+1): m[top][j] = num; num += 1
        top += 1
        for i in range(top, bot+1): m[i][right] = num; num += 1
        right -= 1
        for j in range(right, left-1, -1): m[bot][j] = num; num += 1
        bot -= 1
        for i in range(bot, top-1, -1): m[i][left] = num; num += 1
        left += 1
    return m
```
The Meta warmup. Talk out loud while coding; ask for hints when stuck.
**Tip:** Meta interviewers are "literally trained to give good hints." Use them.

## Stage 3: Onsite (5 rounds)

### Round 3.1: Coding

### Q3.1.1: "LRU Cache, extend to thread-safe"
**Answer:**
```python
from collections import OrderedDict
from threading import Lock
class LRUCache:
    def __init__(self, capacity):
        self.cap, self.cache, self.lock = capacity, OrderedDict(), Lock()
    def get(self, k):
        with self.lock:
            if k not in self.cache: return -1
            self.cache.move_to_end(k)
            return self.cache[k]
    def put(self, k, v):
        with self.lock:
            if k in self.cache: self.cache.move_to_end(k)
            self.cache[k] = v
            if len(self.cache) > self.cap:
                self.cache.popitem(last=False)
```

### Q3.1.2: "Lowest common ancestor of two binary tree nodes"
**Answer:** Recursive: if root is None or root is p or q, return root. Otherwise recurse left and right; if both non-null, root is LCA; else return non-null. Iterative: store parents in a hash map via BFS, then walk up from p and q.

### Round 3.2: System design

### Q3.2.1: "Design News Feed"
**Answer:** 2B DAU, must serve <200ms. Fan-out on write (precompute at post time, fast read) vs. fan-in on read (compute at read, slow read). Hybrid: fan-out on write for normal users, fan-in for celebrities (10M+ followers). Cache precomputed feed in Redis with 5-min TTL. Re-rank on read with logistic regression on user features. Meta-standard answer.
**Tip:** Hybrid fan-out / fan-in is the Meta-canonical answer.

### Q3.2.2: "Design Messenger / WhatsApp"
**Answer:** WebSocket scaling via consistent hashing on user_id; message ordering via per-conversation sequence numbers; offline delivery via durable per-user mailbox queue; on reconnect, replay from last seen sequence number. At-least-once delivery, dedup at the client by message ID.

### Round 3.3: Jedi behavioral (45-60 min)

### Q3.3.1: "Tell me about a conflict with a teammate"
**Answer:** On Ads delivery, a senior engineer wanted a complex multi-layer caching solution; I proposed a simpler direct approach. We built benchmarks: his was 5% faster in ideal conditions but used 20% more memory and made debugging harder. I deferred to the data; we shipped his version with a memory cap and added instrumentation.
**Tip:** Specific conflict + specific disagreement + specific data that resolved it.

### Q3.3.2: "A time you failed"
**Answer:** My change introduced a subtle bug that only manifested with a specific data format — the pipeline failed silently overnight. Root cause: missing data-format tests. Fix: added a data-format test to every pipeline PR template. The lesson: silent failures need proactive testing.
**Tip:** Name the silent failure mode + the lesson.

### Q3.3.3: "A time data influenced your decision"
**Answer:** We rolled a feature out to 1% of users. Their next-day return rate was slightly lower than the control group. My analysis suggested the feature was a distraction, not an enhancement. We rolled back and redesigned with a 2% lift the next quarter.

### Round 3.4: AI-assisted coding (60 min, new 2026)

### Q3.4.1: "Add a feature to this multi-file codebase using Llama 4"
**Answer:** Prompt the tool with the feature spec, read the diff, catch the bug the tool introduced (e.g., it breaks the existing API contract), explain why you caught it. The grader watches how you prompt, when you verify, and how you catch mistakes.
**Tip:** Use the tool like a junior engineer — with supervision.

## Stage 4: Hiring committee

The committee weighs Jedi + technicals equally. They look for: (1) product sense (News Feed, Instagram, Messenger depth), (2) conflict + failure + data-influenced STAR stories, (3) AI-tool fluency with verification. Meta comp negotiation requires a competing offer; the E6+ band is wide and the top is achievable.

## Stage 5: Offer

Comp negotiation is expected — come with a competing offer from OpenAI / Anthropic / Google. E6+ comp is heavily RSU-weighted (4-year vest, 25%/year). Sign-on is real at E6+. The candidate who doesn't anchor loses the top of the band.

## Tips for the Meta loop

- **Jedi round is the offer-decider.** Prep STAR stories like coding.
- **Hints are part of the test.** Ask when stuck; don't sit silent 5 min.
- **AI-assisted coding is a thinking test.** Use the tool, catch its mistakes.
- **News Feed is canonical.** Practice the hybrid fan-out/fan-in answer.
- **Talk out loud.** Meta grader is grading thought process, not typing speed.
- **Comp negotiation expected.** Bring a competing offer.
- **Pick a team.** FAIR, GenAI, Reality Labs — defend your pick.

## Real candidate report

> *"Listen for the hints. We are literally trained to give good hints... We want to see you think. The worst thing you can do is stay silent for five minutes and then produce a perfect solution."*
> — [Meta Official Interview Prep Guide, 2026](https://www.metacareers.com/interview-prep/)

## Sources

- [JobInterviewAt — Facebook Meta Interview Questions: Complete 2026 Guide](https://jobinterviewat.com/facebook-meta-interview-questions/)
- [Meta Official Interview Prep](https://www.metacareers.com/interview-prep/)
- [r/OfferEngineering — Meta Data Engineer Interview (Mar 2026)](https://www.reddit.com/r/OfferEngineering/comments/1s2z2p1/meta_data_engineer_interview_full_loop_questions/)
- [Levels.fyi — Meta compensation](https://www.levels.fyi/companies/meta/salaries/software-engineer)
- [Glassdoor — Meta Interview Questions (2026)](https://www.glassdoor.com/Interview/Meta-Interview-Questions-E40772.htm)