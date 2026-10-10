# 63. Jasper

- **Role:** AI Engineer (Marketing LLM applications)
- **Tech stack:** Python, PyTorch, OpenAI/Anthropic APIs, LangChain, Postgres, Snowflake, AWS
- **Comp band:** $170K-$350K base + equity (post-IPO, Austin/SF)
- **Cumulative pass rate:** ~4-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, marketing AI interest | 30 min | ~60% |
| 2. Take-home + technical screen | Build a small marketing gen app | 1 week | ~40% |
| 3. Onsite (3 rounds) | Coding, system design, product ML | 3-4 hrs | ~35% |
| 4. Hiring manager | Vision, leadership | 45 min | ~70% |
| 5. Offer | Comp, equity refresh | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Jasper after the post-IPO reset?"
**Answer:** "Jasper pivoted to enterprise marketing OS in 2024 and is the only company shipping end-to-end campaign generation — copy, image, brand voice — at that scale. I want to be there."
**Tip:** Show you read the Q3 2025 earnings call; they value informed candidates.

### Q1.2: "How do you stay current in a fast-moving field?"
**Answer:** "I read 3 papers a week on arXiv, follow the Jasper engineering blog, and replicate one new technique a month — last month I built a LoRA pipeline for brand-voice fine-tuning."
**Tip:** Name specific things you've built or read.

## Stage 2: Take-home + screen

### Q2.1: Build a brand-voice fine-tuner.
**Answer:** Use Hugging Face PEFT + LoRA on Llama-3 8B with a brand corpus, expose a Gradio UI to generate with the adapter, evaluate on a held-out brand-voice test set with BERTScore + a custom tone classifier.
**Tip:** Quality > scope. They review code style and prompt engineering.

### Q2.2: Live coding — palindrome check.
**Answer:**
```python
def is_pal(s):
    l, r = 0, len(s) - 1
    while l < r:
        while l < r and not s[l].isalnum(): l += 1
        while l < r and not s[r].isalnum(): r -= 1
        if s[l].lower() != s[r].lower(): return False
        l += 1; r -= 1
    return True
```
**Tip:** Talk through edge cases; they want to see communication.

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Top-K frequent words in a stream.
**Answer:** Counter + heap of size K, O(n log k).

### Round 3.2: System design
**Q:** Design a campaign generation platform for 100K marketers.
**Answer:** Prompt templating service, async generation queue, brand-voice adapter registry, A/B testing layer, content moderation guardrails, usage-based billing integration.

### Round 3.3: Product ML
**Q:** How would you measure if AI-generated copy outperforms human copy?
**Answer:** A/B test on click-through + conversion; pre-register hypotheses; segment by industry; combine with qualitative brand surveys. Acknowledge novelty effects.

### Round 3.4: Behavioral
**Q:** Tell me about a product you shipped from zero.
**Answer:** STAR: owned a 0-to-1 feature, navigated ambiguity, hit a metric.

## Stage 4: Hiring manager
Cultural fit + product judgment. They look for marketers' empathy and strong opinions on taste.

## Stage 5: Offer
Post-IPO RSUs vest 25% year 1, then quarterly. They have a hiring bar that dropped ~10% after 2024 reset.

## Tips for the Jasper loop
- Read the Jasper engineering blog and recent earnings.
- Practice a 4-hour take-home that ships with a Gradio demo.
- Be ready to defend "what is good marketing copy" — they want taste.
- Show you can ship end-to-end (data → model → UI → metrics).
- Know their competitors: Writer, Copy.ai, Mutiny, 6sense.

## Real candidate report
> "Take-home was to build a brand-voice fine-tuner in 4 hours. Onsite was 3 rounds, all about product thinking and coding. Whole process was 9 days. Got an offer that was below the Levels median but the equity made it interesting." — Glassdoor, ML Engineer, 2025

## Sources
- [Jasper careers](https://www.jasper.ai/careers)
- [Jasper engineering blog](https://www.jasper.ai/blog/category/engineering)
- [Levels.fyi — Jasper](https://www.levels.fyi/companies/jasper)
- [Glassdoor — Jasper interviews](https://www.glassdoor.com/Interview/Jasper-Interview-Questions.htm)
- [Reddit r/cscareerquestions — Jasper thread](https://reddit.com/r/cscareerquestions)
