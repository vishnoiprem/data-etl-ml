# 97. Figma (ML / Design AI)

- **Role:** ML Engineer / AI Engineer (Figma AI, Search, Recommendations, Design Generation)
- **Tech stack:** TypeScript, C++, Rust, Python, React, WebGL, Postgres, Redis, Kubernetes, PyTorch, Hugging Face, multi-modal models
- **Comp band:** $200K-$500K (L3-L4 Senior); L5 (Staff) $400K-$900K; L6 Principal $600K-$1.3M (Levels.fyi 2026)
- **Cumulative pass rate:** ~1-2.5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, level | 30 min | ~50% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML/LLM | 60 min | ~35% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML/LLM deep-dive, 1 behavioral | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Loop debrief + cross-org | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp + level | 1 week | — |

Figma's AI org focuses on three areas: (1) Figma AI (generate, edit, summarize), (2) search and recommendations (templates, plugins, files), (3) design generation (text-to-UI, image-to-design). The unique surface is multi-modal — code, image, layout, text — and the design domain. Figma's bar is high but the culture is "ship fast, learn fast."

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** "I built [X] for [Y]. Most recently I shipped [Z] in [LLM / multi-modal / search]."
**Tip:** Be specific about multi-modal work if you have it.

### Q1.2: "Why Figma?"
**Answer:** "Three reasons. First, Figma AI is genuinely useful — the Figma Make and AI design generation launches in 2025-26 are real ML products. Second, the design surface is uniquely multi-modal — text, image, layout, vector — and the ML is hard. Third, Figma's culture of 'build what you wish existed' plus small team ownership is a great fit for me."
**Tip:** Reference Figma Make, AI features, design generation, and the 2026 launches.

### Q1.3: "Location + comp"
**Answer:** SF and NYC primary. Some remote. Comp is competitive Bay Area.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Two Sum" or "LRU cache"
**Answer:** Standard.
**Tip:** Medium LeetCode. Clean, fast code.

### Q2.2: LLM — "How would you build text-to-UI generation?"
**Answer:** "Three parts. (1) Data: a corpus of design files → flattened JSON (frames, layers, styles) + textual annotations (component names, accessibility labels). (2) Model: fine-tuned LLM (Code Llama or similar) that takes a text prompt and outputs JSON describing the layout. (3) Rendering: Figma plugin reads the JSON and instantiates frames. (4) Eval: visual similarity to human designs, faithfulness to the prompt, renderability, diversity. (5) Iteration: user feedback → fine-tune."
**Tip:** Text-to-UI is Figma's frontier. Be specific about the data pipeline.

### Q2.3: System design — "Design Figma's template/file search"
**Answer:** "Index: file metadata + design embeddings (image of the file, text from layers, component names). Retrieval: hybrid (BM25 + image embedding ANN). Ranking: gradient-boosted on (text match, visual similarity, recency, file size, popularity). Permissions: respect team / organization access. Real-time: new files indexed within minutes."
**Tip:** Multi-modal search is a differentiator. Show image + text retrieval.

## Stage 3: Onsite (4 rounds, 1-2 days)

### Round 3.1: Coding
**Q3.1.1:** "Merge intervals" or "Top K frequent."
**Q3.1.2:** "Design a real-time collaborative cursor system" — WebSocket, OT or CRDT.
**Q3.1.3:** "Parse a simple layout DSL" — recursive descent, then render.

### Round 3.2: System design
**Q3.2.1:** "Design Figma Make (AI design generation)." Prompt understanding, layout generation, asset retrieval, multi-step editing, renderability checks, eval.
**Q3.2.2:** "Design a plugin recommendation system." Plugin metadata, user-plugin interaction, collaborative filtering + content-based, ranking, A/B testing.

### Round 3.3: ML / LLM deep-dive
**Q3.3.1:** "Walk me through a multi-modal ML system you've built."
**Q3.3.2:** "How do you evaluate a text-to-image model for design assets?"
**Answer:** "Multiple axes: visual quality (FID, CLIP-score, human eval), prompt faithfulness (does the asset match the request?), style consistency (matches the user's brand / project?), originality (not a direct copy of training data), safety (no copyrighted characters, no NSFW). Online: pick rate, edit rate, removal rate. Reference Figma's published AI quality metrics."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you shipped a feature in 1-2 weeks." STAR — Figma values velocity.
**Q3.4.2:** "Time you had to design for edge cases (mobile, low-bandwidth)." STAR.
**Q3.4.3:** "What's your favorite Figma feature and how would you improve it?" — be specific.

## Stage 4: Hiring committee
Figma's committee is a structured loop debrief. L4 (Senior) requires independent ML feature ownership. L5 (Staff) requires cross-team influence on the platform. L6 (Principal) is rare. Committee is fast — usually 1 week.

## Stage 5: Offer
Figma comp is competitive with Bay Area. RSU is 4-year vest. They negotiate on equity. Relocation is well-funded. Team match is usually pre-onsite for some roles. The recent IPO affected equity comp structure but base remains strong.

## Tips for the Figma loop
1. **Multi-modal ML is the differentiator** — image + text + layout + code.
2. **Design-aware thinking is a plus** — if you've used Figma, show it.
3. **Coding is medium LeetCode** — focus on clean code, real-time / WebGL is a plus.
4. **Velocity matters** — Figma ships fast, show you can too.
5. **Reference 2026 Figma AI features** — Figma Make, AI design generation, image editing.
6. **Eval rigor is tested** — have a real answer to "how do you know your model is good?"
7. **Latency matters** — Figma is real-time, ML features can't lag.

## Real candidate report
> "I interviewed for AI Engineer on Figma Make. The system design was on text-to-UI generation and they wanted me to walk through the data pipeline (design files → JSON) and the renderability checks. The ML deep-dive was on multi-modal model evaluation. Got L4 offer at $340K base + $600K RSU/4yr. They moved base by $25K on negotiation." — Blind, 2025

## Sources
- [Figma Engineering Blog](https://www.figma.com/blog/engineering/)
- [Figma AI Documentation](https://help.figma.com/hc/en-us/sections/14506167395095-Figma-AI)
- [Levels.fyi Figma](https://www.levels.fyi/companies/figma)
- [Glassdoor Figma interviews](https://www.glassdoor.com/Interview/Figma-Interview-Questions-E2865493.htm)
- [LeetCode Figma tagged](https://leetcode.com/company/figma/)