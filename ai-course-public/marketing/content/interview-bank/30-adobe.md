# 30. Adobe (Firefly / Sensei / Document AI)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual. Color: company brand color as accent. Headline on image: "ADOBE / AI FIREFLY / 2026".

> **TL;DR:** Adobe's loop is built around **commercially-safe generative AI** — Firefly is the only indemnified model in production, and every answer should bend toward content credentials. The signature lens is **craft**: pixel-level obsession over metrics. The winning candidate names C2PA and DreamBooth without prompting.

```
Recruiter (50%) → Phone (40%) → Onsite (30%) → Tech Panel (55%) → Offer
```

- **Role:** ML Engineer / Research Engineer (Firefly, Sensei, Document AI, Acrobat AI)
- **Tech stack:** Python, PyTorch, JAX, CUDA, Diffusers, Transformers, Houdini, After Effects SDKs, Java/C++
- **Comp band:** $250K-$700K total comp (IC3-IC5) | RSUs 4-year, 1-year cliff; senior crosses $900K+
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Firefly/Doc AI/Sensei), comp | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~30% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

Adobe's loop is "craft-obsessed" by design — the panel is half engineers, half researchers, half PMs, and they all grade on output quality. If your design doesn't reach for content credentials or indemnification, you're missing the unique Adobe frame.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Adobe for AI?"
**Answer:** "Firefly is the only commercially-safe generative AI model — trained on licensed content, indemnified for enterprise. Adobe has the creator moat that no startup has — 30M+ Creative Cloud subscribers, hundreds of millions of PDFs. I want to build AI for the people who make the world's creative work."
**Tip:** Reference *Firefly*, *Sensei*, *Acrobat AI*, *Document AI* — not generic AI. Adobe's "commercially safe" angle is unique.

### Q1.2: "Tell me about a creative AI project you worked on"
**Answer:** STAR with focus on *quality* and *user craft* — Adobe creators care about pixel-level detail.
**Tip:** Adobe culture values *craft* deeply. Show you care about output quality, not just metrics.

## Stage 2: Technical phone screens (90 min)

The phone screens are where Adobe quietly checks for *craft* and *commercial safety*. If you don't mention IP-Adapter, ControlNet, or content credentials in the ML round, the interviewer will.

### Q2.1: Coding: "Merge overlapping intervals"
**Answer:** Sort by start, iterate merging if next.start ≤ curr.end.
```python
def merge(intervals):
    intervals.sort()
    out = []
    for s, e in intervals:
        if not out or s > out[-1][1]: out.append([s, e])
        else: out[-1][1] = max(out[-1][1], e)
    return out
```
**Tip:** LeetCode mediums. Some Firefly roles ask for *image-processing* questions.

### Q2.2: ML: "Design a text-to-image model fine-tuned for brand consistency"
**Answer:** (1) Base — Stable Diffusion 3 / SDXL or Firefly base; (2) LoRA fine-tuning on customer brand assets; (3) IP-Adapter for style consistency; (4) ControlNet for layout; (5) Safety classifier (NSFW, brand violations); (6) Eval — CLIP score, brand-similarity metric, human eval; (7) Serving with IP-reminder for indemnification.
**Tip:** Adobe is *the* commercially-safe AI. Reference content credentials (C2PA) and indemnification.

## Stage 3: Onsite (4 rounds)

The onsite is dense and craft-flavored. Firefly, Acrobat AI, and Sensei are all different conversations — confirm your target product with the recruiter so you can rehearse the right ML deep-dive.

### Round 3.1: Coding (60 min, 2 questions)
- Q: Implement k-means from scratch.
- Q: LRU cache with O(1) get/put.
- Optional 3rd: Tree/graph problem.

### Round 3.2: System design (60 min)
- Q: Design Firefly Services, a generative AI API for enterprises. Multi-tenant serving, custom model fine-tuning per customer, content credentials, safety filters, indemnification flow, and billing.
- Q: Design a document understanding pipeline (Acrobat AI). OCR, layout analysis, table extraction, RAG over PDF, multi-language, and citation.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you fine-tune a diffusion model for a specific brand style with limited examples? DreamBooth / LoRA, regularization set, prior preservation, and eval on brand guidelines.
- Q: How would you build a text-to-vector (SVG) model for designers? Sequence-to-sequence transformer, code-as-action tokenization, and eval on design-tool use cases (Illustrator).

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you obsessed over a 1% quality improvement. Adobe values craft.
- Q: A time you partnered with a designer or creative.
- Q: Disagreement with a PM on a launch.

## Stage 4: Hiring committee
A panel of senior engineers + researchers + PM reviews. They look for: (1) ML bar for the level, (2) creative-AI depth, (3) Adobe values (Creativity for All, Be Genuine, Be Bold, Take Action), (4) commercial-safety mindset. Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. Adobe is competitive with FAANG, sometimes above for senior+ due to AI push. Negotiation is real. Team match after loop. Adobe San Jose HQ is the main hub.

## Tips for the Adobe loop
- Reference *Firefly*, *Firefly Services*, *Sensei*, *Acrobat AI*, *Document AI* by name.
- For ML rounds, emphasize *quality* and *commercially-safe* AI.
- For system design, multi-tenant generative AI services are hot.
- For behavioral, "craft" stories score well — Adobe is creator-first.
- Reference Content Credentials (C2PA) and indemnification.
- For Firefly roles, expect diffusion model + LoRA + ControlNet depth.
- For Document AI roles, expect OCR + layout + RAG depth.

## Real candidate report
> "Loop for Firefly Services. 4 rounds in 1 day. The ML deep-dive was on LoRA fine-tuning for brand consistency with limited examples and they wanted DreamBooth specifics. The system design was multi-tenant generative AI with content credentials. Behavioral was 'craft' flavored. Offer at IC4, ~$480K total, 4 weeks." — Blind, 2025-10

## Sources
- [Adobe Careers](https://www.adobe.com/careers.html)
- [Levels.fyi Adobe salaries](https://www.levels.fyi/companies/adobe/salaries)
- [Adobe Research blog](https://research.adobe.com/)
- [Firefly docs](https://www.adobe.com/products/firefly.html)
- [r/MachineLearning Adobe thread](https://www.reddit.com/r/MachineLearning/)

---

## The 1 thing to remember

At Adobe, "commercially safe" is the differentiator — name Firefly, content credentials (C2PA), and indemnification by default, because every model Adobe ships has to defend itself in front of an enterprise legal team.
