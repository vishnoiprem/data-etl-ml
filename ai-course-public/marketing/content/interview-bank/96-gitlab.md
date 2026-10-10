# 96. GitLab (Duo)

- **Role:** AI Engineer (GitLab Duo, Code Suggestions, Chat)
- **Tech stack:** Ruby, Go, Python, TypeScript, Vue, Postgres, Redis, Gitaly, Kubernetes, PyTorch, Hugging Face, Anthropic / Vertex AI / self-hosted models
- **Comp band:** $150K-$400K (IC3-IC4 Senior); Staff (IC5) $300K-$650K; Principal $400K-$900K (Levels.fyi 2026; comp varies by country)
- **Cumulative pass rate:** ~2-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, location, async-fit check | 30 min | ~55% advance |
| 2. **Take-home or async exercise** | Code or system design writing task | 1 week | ~50% advance |
| 3. **Technical phone screen** | 1 coding + 1 ML/LLM | 60 min | ~35% advance |
| 4. **Onsite (3-4 rounds)** | 1 coding, 1 system design, 1 ML/LLM deep-dive, 1 behavioral | 1-2 days | ~30% advance |
| 5. **Hiring committee** | Async loop debrief (written) | 1-2 weeks | ~65% advance |
| 6. **Offer** | Comp + level | 1 week | — |

GitLab is a fully-remote, async-first company. The interview loop itself reflects this — expect a take-home or async written exercise, written panel debriefs, and interviewers who respect "I'm in a different timezone." The Duo team (their AI assistant, including Code Suggestions, Chat, MR reviews) is the primary AI surface. Bar is moderate-to-high but more forgiving than GitHub/Microsoft.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** "I built [X] for [Y], working on [LLM / ML / backend]. Most recently I shipped [Z]."
**Tip:** GitLab values async written communication. Speak in structured, clear sentences.

### Q1.2: "Why GitLab?"
**Answer:** "Three reasons. First, async-first means I can do my best work without meetings — and the loop itself is async-friendly. Second, Duo is a real product, but the bar is to ship to enterprise customers with strict security and self-hosted requirements. Third, GitLab's open handbook and culture are uniquely transparent — I want to work somewhere that documents how it works."
**Tip:** Reference GitLab's handbook, the async culture, the self-hosted AI offering (a real differentiator for enterprise/government customers).

### Q1.3: "Location + remote + comp band"
**Answer:** GitLab is global remote. They pay in country-specific bands. Be clear on location. Comp is good but varies by country (US is highest).

## Stage 2: Take-home (1 week)

GitLab's take-home is typically a written exercise: design a system, or write a small LLM-based application, or analyze a tradeoff. Submit a markdown doc or PR.

**Tip:** Take your time. They want clarity, structure, and depth. Show your work.

## Stage 3: Technical phone screen (60 min)

### Q3.1: Coding — "String to integer (atoi)" or "LRU cache"
**Answer:** Standard.
**Tip:** Medium LeetCode. Clean code, edge cases.

### Q3.2: LLM — "How would you build a self-hosted code suggestion system?"
**Answer:** "Three challenges. (1) Latency: on-prem, low-budget GPU (e.g., 1-2 A100s), so use a small fine-tuned model (Code Llama 7B or StarCoder) with vLLM/TGI for fast serving. (2) Quality: continuous fine-tuning on user's own code (with permission). (3) Privacy: no external API calls. Eval: HumanEval + user-specific golden set + online acceptance rate."
**Tip:** Self-hosted is GitLab's differentiator. Show you understand on-prem tradeoffs.

### Q3.3: System design — "Design Duo Chat (multi-turn coding assistant)"
**Answer:** "WebSocket / streaming UI → backend: conversation memory (per user, per repo), RAG over repo + GitLab issues + MRs, LLM with retrieved context. Permissions: respect repo access. Eval: golden test set + human eval + online feedback. Cost: prompt caching, model selection per task. Reference GitLab's open-source Duo Chat for the architecture."
**Tip:** Mention prompt caching and model selection — both are real production concerns.

## Stage 4: Onsite (3-4 rounds, 1-2 days, often async)

### Round 4.1: Coding
**Q4.1.1:** "Top K frequent elements" or "Merge intervals."
**Q4.1.2:** "Design a rate limiter for API calls." Token bucket, Redis-backed.
**Q4.1.3:** "Implement a simple queue with at-least-once delivery."

### Round 4.2: System design
**Q4.2.1:** "Design GitLab Duo's MR review AI." Diff parsing, change understanding, comment generation, issue categorization. Eval on precision + developer feedback.
**Q4.2.2:** "Design a self-hosted LLM serving platform." Multi-tenant, GPU scheduling, model caching, cost attribution, observability.

### Round 4.3: LLM / ML deep-dive
**Q4.3.1:** "Walk me through a RAG system you've built."
**Q4.3.2:** "How do you evaluate a code suggestion model in production?"
**Answer:** "Online: acceptance rate, time-to-accept, code-churn after acceptance, developer NPS. Offline: HumanEval, MBPP, internal golden set per language, LLM-as-judge on quality. Counterfactual: what would the developer have written without the suggestion? Continuous A/B testing of model versions. Reference GitLab's published Duo metrics."

### Round 4.4: Behavioral (often written)
**Q4.4.1:** "Time you had to ship to enterprise with security constraints." STAR.
**Q4.4.2:** "Time you worked async across timezones." STAR.
**Q4.4.3:** "What would you change about GitLab's product?" — be specific.

## Stage 5: Hiring committee
GitLab uses async written panel debriefs. Each interviewer writes up their notes in a shared doc, then the committee calibrates level and decision. IC3 vs IC4 (Senior) is decided here. IC5 (Staff) requires cross-team influence. Loop typically wraps in 1-2 weeks.

## Stage 6: Offer
GitLab comp is solid for remote work but varies by country. US band is competitive with Bay Area adjusted for cost-of-living. RSU is 4-year vest. They negotiate on equity, less so on base. Team match is post-offer within 30 days.

## Tips for the GitLab loop
1. **Async communication is a skill being tested** — clear, structured writing.
2. **Self-hosted LLM fluency is a differentiator** — on-prem tradeoffs, model selection.
3. **Enterprise / security awareness** — GitLab's customers are security-conscious.
4. **Coding is medium LeetCode** — clean code, not clever tricks.
5. **Read the GitLab handbook** — they expect you to have skimmed it.
6. **Reference 2026 Duo features** — MR review, code suggestions, security scanning AI.
7. **Show you can ship async** — your work speaks, not your meetings.

## Real candidate report
> "Loop was async-first — I had a take-home (design a Duo Chat system in writing), then 3 panel interviews over 2 days via video. The system design was on self-hosted LLM serving, which is GitLab's differentiator. They asked me to walk through GPU scheduling, model caching, and cost attribution. Got IC4 offer at $260K base + $400K RSU/4yr, fully remote US. They moved base by $20K on negotiation." — Blind, 2025

## Sources
- [GitLab Engineering Blog](https://about.gitlab.com/blog/categories/engineering/)
- [GitLab Handbook (the famous open handbook)](https://about.gitlab.com/handbook/)
- [GitLab Duo Documentation](https://docs.gitlab.com/ee/user/duo/)
- [Levels.fyi GitLab](https://www.levels.fyi/companies/gitlab)
- [Glassdoor GitLab interviews](https://www.glassdoor.com/Interview/GitLab-Interview-Questions-E891556.htm)