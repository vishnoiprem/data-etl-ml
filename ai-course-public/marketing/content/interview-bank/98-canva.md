# 98. Canva (Magic Studio)

- **Role:** ML / AI Engineer (Magic Studio, Search, Templates, Generative)
- **Tech stack:** Python, Go, TypeScript, React, C++, PyTorch, TensorFlow, Kubernetes, AWS, GCP, multi-modal models (CLIP, diffusion)
- **Comp band:** AUD $180K-$400K / USD $150K-$350K (IC3-IC4); Staff (IC5) AUD $300K-$700K / USD $250K-$600K (Levels.fyi 2026)
- **Cumulative pass rate:** ~2-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, location | 30 min | ~55% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML/LLM | 60 min | ~40% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML deep-dive, 1 behavioral + values | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Loop debrief | 1-2 weeks | ~65% advance |
| 5. **Offer** | Comp + level | 1 week | — |

Canva's Magic Studio is the AI surface that competes with Adobe Firefly and Figma AI. The org spans Magic Design (text-to-template), Magic Edit (image inpainting), Magic Write (LLM-powered copy), Magic Media (text-to-image), and search/recommendations. The bar is moderate-to-high; the culture is friendly, design-led, and global (Sydney primary, with Manila, Beijing, SF, London).

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** "I built [X] for [Y]. Most recently I shipped [Z] in [ML / LLM / multi-modal]."
**Tip:** Canva is design-led. Show some design / creative-tech interest.

### Q1.2: "Why Canva?"
**Answer:** "Three reasons. First, Magic Studio is a real AI product for 220M+ users — unique distribution. Second, Canva's mission of 'empower the world to design' lines up with my interest in creative tools. Third, Canva's culture is famously kind and values-driven, and the comp is solid for Australia."
**Tip:** Reference Magic Studio features, the 2026 launches, and Canva's kind-culture values.

### Q1.3: "Location + comp"
**Answer:** Sydney primary. Manila, Beijing, SF, London are growing. Be clear on willingness to relocate to Australia if needed. Comp is in AUD; US employees are paid in USD.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Merge intervals" or "Two Sum"
**Answer:** Standard.
**Tip:** Medium LeetCode. Clean code, edge cases.

### Q2.2: ML — "How would you build text-to-template generation?"
**Answer:** "Three parts. (1) Data: a corpus of Canva templates → flattened structural representation (layouts, components, text) + textual annotations. (2) Model: fine-tuned LLM (Code Llama or similar) that takes a prompt + brand/style hints → outputs a template spec. (3) Renderer: takes the spec, retrieves assets, composes a Canva design. (4) Eval: visual quality, prompt faithfulness, brand consistency, originality. (5) Iteration: user feedback → fine-tune."
**Tip:** Mention template structure, brand/style consistency, and originality evaluation.

### Q2.3: System design — "Design Canva's template search"
**Answer:** "Index: template metadata (category, tags, dimensions, color palette) + template image embeddings (CLIP) + text embeddings of template copy. Retrieval: hybrid (BM25 + embedding ANN). Ranking: gradient-boosted on (text match, visual similarity, popularity, recency, user locale). Real-time: new templates indexed within minutes. Multi-locale: respect language and regional preferences."
**Tip:** Multi-locale is a Canva differentiator. Mention it.

## Stage 3: Onsite (4 rounds, 1-2 days)

### Round 3.1: Coding
**Q3.1.1:** "LRU cache" or "Top K frequent."
**Q3.1.2:** "Design a simple rate limiter" — token bucket.
**Q3.1.3:** "Serialize/deserialize a tree" — preorder + null.

### Round 3.2: System design
**Q3.2.1:** "Design Magic Edit (inpainting-based image editing)." User input (brush + prompt) → masked image + prompt → diffusion inpainting model (fine-tuned SD variant) → output image. Latency <5s. Eval: visual quality, prompt faithfulness, original area preserved. Cost: GPU serving, model distillation for fast inference.
**Q3.2.2:** "Design Canva's home feed (template recommendations)." Multi-stage: candidate generation (collaborative filtering + content-based) → ranking → diversity. Cold start: popularity priors. A/B test ranking changes.

### Round 3.3: ML / LLM deep-dive
**Q3.3.1:** "Walk me through a multi-modal ML system you've built."
**Q3.3.2:** "How do you evaluate a text-to-image model for design use?"
**Answer:** "Multiple axes: visual quality (FID, CLIP-score, human eval), prompt faithfulness (does the asset match the request?), style consistency (matches the user's brand / project?), originality (not a direct copy of training data), safety (no copyrighted characters, no NSFW, no offensive content). Online: pick rate, edit rate, removal rate. Reference Canva's published AI quality practices."

### Round 3.4: Behavioral + Values
**Q3.4.1:** "Tell me about a time you had to ship to a global audience." STAR.
**Q3.4.2:** "Time you made a design or product decision with limited data." STAR.
**Q3.4.3:** "How do you embody Canva's values (Be a force for good, Pursue awesome, Be a good human, Make complex simple)?" — be specific.

## Stage 4: Hiring committee
Canva's committee is a structured loop debrief. IC3 vs IC4 (Senior) is decided here. IC5 (Staff) requires cross-team influence. The bar is moderate-to-high; Canva is more forgiving than FAANG but values design thinking and culture fit heavily.

## Stage 5: Offer
Canva comp is solid for Sydney — top of the Australian market. RSU is 4-year vest. They negotiate on equity, less so on base. For US-based employees, comp is competitive with Bay Area adjusted for cost-of-living. Relocation to Sydney is well-funded. Team match is usually pre-onsite for some roles.

## Tips for the Canva loop
1. **Multi-modal ML is the differentiator** — image + text + layout.
2. **Design-aware thinking is a plus** — show you've used Canva.
3. **Coding is medium LeetCode** — clean, readable code.
4. **Reference Magic Studio features** — Magic Design, Magic Edit, Magic Media, Magic Write.
5. **Values matter** — Canva's "kind culture" is real, show it.
6. **Global / multi-locale is a differentiator** — Canva serves 220M+ users in 100+ languages.
7. **Eval rigor is tested** — have a real answer to "how do you know your model is good?"

## Real candidate report
> "I interviewed for AI Engineer on Magic Studio. The system design was on text-to-template and they pushed on the brand-consistency angle — how do you ensure a generated template matches the user's existing brand colors/fonts? Got an IC4 offer at AUD $280K base + $400K RSU/4yr, Sydney. They moved base by AUD $20K on negotiation. The loop was 4 rounds in 2 days, friendly interviewers." — Blind, 2025

## Sources
- [Canva Engineering Blog](https://www.canva.dev/blog/engineering/)
- [Canva Design Blog](https://www.canva.com/newsroom/)
- [Levels.fyi Canva](https://www.levels.fyi/companies/canva)
- [Glassdoor Canva interviews](https://www.glassdoor.com/Interview/Canva-Interview-Questions-E1108891.htm)
- [LeetCode Canva tagged](https://leetcode.com/company/canva/)