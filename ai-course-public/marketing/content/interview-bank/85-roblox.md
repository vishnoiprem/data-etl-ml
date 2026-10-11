# 85. Roblox (ML / Trust & Safety)

- **Role:** ML Engineer (Search, Discovery, Trust & Safety, Avatar/Generative AI)
- **Tech stack:** Python, C++, Lua, PyTorch, TensorFlow, Cassandra, Kafka, Spark, Kubernetes, gRPC
- **Comp band:** $220K-$550K total comp (L3-L5); L6 (Staff) $450K-$1M total comp; L7 Director $700K-$1.5M total comp (Levels.fyi 2026) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~1-2%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (an avatar being generated in a blocky 3D viewport with a safety classification overlay). Color: Roblox black + signature red. Headline: "Roblox / AI ML Engineer / 2026".

> **TL;DR:** Roblox's loop is kid-safety-first, with ML questions that test age-aware thresholds, COPPA instincts, and the cost of false positives in moderation. The winning candidate is the one who designs for a 9-year-old worst case, knows how to evaluate generative avatars, and treats discovery as more than popularity ranking.

```
┌──────────────────────────────────────────────────────────────────┐
│                       ROBLOX HIRING FUNNEL                        │
├──────────────────────────────────────────────────────────────────┤
│  Apply ──► Recruiter (45%) ──► Tech Phone (30%) ──► Onsite       │
│                                                                  │
│  Onsite ──► Coding / Design / ML / Values ──► Responsible-AI    │
│          (25%)                                  Review (55%)    │
│                                                                  │
│  Committee ──► Offer (L5 vs L6 split) ──► Pre-match team          │
└──────────────────────────────────────────────────────────────────┘
```

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, level | 30 min | ~45% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML or system design | 60 min | ~30% advance |
| 3. **Onsite (4-5 rounds)** | 1-2 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Cross-functional review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp + level + team match | 1 week | — |

Roblox has a unique ML surface: kid-safety is the existential priority (COPPA compliance, child safety), the discovery surface is "what game to play next", and they're investing heavily in generative AI for avatar / asset creation. The tech stack is unusual — Lua for game logic, C++ for engine, Python for ML services. Roblox loops are heavy on T&S and kid-safety scenarios.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** Lead with scale and T&S / safety experience. Roblox hires engineers who can think about the worst-case user (a 9-year-old).
**Tip:** Mention experience with younger or vulnerable users if you have it.

### Q1.2: "Why Roblox?"
**Answer:** "Three reasons. First, the safety problem is genuinely hard — kids are using the platform, and a model that misses a predator is a front-page story. I want that responsibility. Second, discovery ML is interesting because the content is user-generated games with wildly varying quality, so pure popularity ranking fails. Third, AI Studio and generative avatar features mean ML is being productized, not just used for ranking."
**Tip:** Reference Roblox's 2026 AI products: AI Studio, generative avatars, voice, translation.

### Q1.3: "Comp + location"
**Answer:** San Mateo HQ is primary. Some remote-US for senior. International is rare.

The recruiter screen rewards candidates who name the safety stakes upfront. The phone screen is where Roblox confirms you can reason about a kid-safety classifier — age-aware thresholds, COPPA instincts, and the cost of false positives are exactly what they're probing.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Word ladder (LeetCode 127)"
**Answer:**
```python
from collections import deque
def ladderLength(beginWord, endWord, wordList):
    wordSet = set(wordList)
    if endWord not in wordSet: return 0
    q = deque([(beginWord, 1)])
    while q:
        word, d = q.popleft()
        if word == endWord: return d
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                nw = word[:i] + c + word[i+1:]
                if nw in wordSet:
                    wordSet.remove(nw)
                    q.append((nw, d+1))
    return 0
```
**Tip:** BFS graph problems are common. Practice them.

### Q2.2: ML — "How would you detect inappropriate text chat on Roblox?"
**Answer:** "Three layers. (1) Lexical: profanity list, slur list, PII regex. (2) Classifier: fine-tuned DistilBERT on labeled chat for grooming, bullying, sexual content, scams. (3) Contextual: who is talking to whom (age, account age, prior reports), image content if shared. Threshold per category. Age-aware: stricter thresholds when a 'minor-likely' account is involved. Human review queue for ambiguous cases. False positive cost is high (legitimate kid conversation), so precision > recall."
**Tip:** Show age-awareness. COPPA is the law and they test it.

### Q2.3: System design — "Design a game discovery feed for Roblox"
**Answer:** "Two-sided: 'continue playing' (recent games) + 'discover new' (recommendations). New game retrieval: collaborative filtering on user-game matrix, content-based on game tags + embeddings (CLIP for thumbnails), popularity priors. Ranking: gradient-boosted on (user-game features, game recency, session quality, age-appropriateness). Diversity and surprise budget — don't show 5 simulators in a row. Cold start: tag-based + popularity, with exploration bonus."

## Stage 3: Onsite (4-5 rounds, 1-2 days)

### Round 3.1: Coding
**Q3.1.1:** "LRU cache" or "LFU cache" (real Roblox question).
**Q3.1.2:** "Implement a thread-safe connection pool."
**Q3.1.3:** "Top K most frequent URLs in a stream." Count-min sketch + heap.

### Round 3.2: System design
**Q3.2.1:** "Design voice chat moderation." Real-time audio transcription, classifier on transcript + acoustic features, human review queue, fast takedown. Edge cases: kids disguising voices.
**Q3.2.2:** "Design Roblox's game economy ML." Virtual currency, item pricing, fraud detection, item recommendation.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through a real ML system you shipped." End-to-end, with safety/quality metrics.
**Q3.3.2:** "How do you evaluate a generative avatar model for kids?"
**Answer:** "Multimodal eval: image quality (FID, CLIP-score, human eval), age-appropriateness (classifier + human review), safety (NSFW classifier, no PII, no identifiable features), diversity (representation across ethnicities, body types, abilities), bias testing across demographic groups."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you balanced business metrics with user safety." STAR.
**Q3.4.2:** "How do you handle pressure to ship fast when safety is at stake?" — Roblox cares deeply.
**Q3.4.3:** "What would you do if you found your model was biased against a demographic?" — be specific.

The onsite is 4-5 rounds across 1-2 days, and the ML deep-dive round is always a kid-safety system. Expect "what's the cost of a false positive?" three different ways — and prepare a real answer for each. The behavioral round probes whether you'll ship under pressure when safety is on the line.

## Stage 4: Hiring committee
Roblox's committee includes a senior leader outside the team. They explicitly test for "responsible AI" and "kid-safety instincts." Senior (L5) requires independent project leadership; L6 (Staff) requires cross-team influence. They move slowly on offers — typically 1-2 weeks for committee.

## Stage 5: Offer
Roblox is competitive with Bay Area. Base is solid, RSU is 4-year vest with 1-year cliff. They are willing to negotiate base aggressively for senior candidates. Team match is pre-onsite for some roles.

## Tips for the Roblox loop
1. **Kid-safety is a first-class concern** — show COPPA awareness, age-tiered systems.
2. **False positive cost is real** — banning a kid's legitimate chat is bad; show you've thought about it.
3. **Generative AI is a hot area** — know how to evaluate text-to-image, avatar generation.
4. **C++ and Lua are differentiators** — even partial knowledge is a plus.
5. **Coding is moderate-hard** — graph BFS, heaps, concurrency.
6. **Reference the 2026 AI Studio and avatar generation features** — shows you've kept up.
7. **Diversity of users is huge** — global, multilingual, all ages, all genders. Mention this.

## Real candidate report
> "Loop was 4 rounds + a hiring manager chat. The ML deep-dive was on a kid-safety classifier and they kept asking 'what's the cost of a false positive?' I had to walk through real scenarios where banning a teenager's slang would alienate them. They want engineers who think in tradeoffs, not in pure metrics. Got an L5 offer at $380K base + $800K RSU/4yr. They moved base by $30K on negotiation." — Blind, 2025

## Sources
- [Roblox Engineering Blog](https://blog.roblox.com/technology/)
- [Roblox Trust & Safety](https://corp.roblox.com/safety/)
- [Levels.fyi Roblox](https://www.levels.fyi/companies/roblox)
- [Glassdoor Roblox interviews](https://www.glassdoor.com/Interview/Roblox-Interview-Questions-E425581.htm)
- [LeetCode Roblox tagged](https://leetcode.com/company/roblox/)

---

## The 1 thing to remember

Roblox is designing for a 9-year-old worst case — the L5+ candidate is the one who names that user before the interviewer does and designs age-aware thresholds instead of one-size-fits-all.
