# OpenAI FDE — Semantic Search Take-Home (real candidate report)

> **Source:** OpenAI candidate interview report, posted on an interview-prep platform, ~2 months before this writeup. The candidate made it to the onsite stage (declined to continue — took another role). The take-home was the centerpiece of the loop. The full report (4 sections: loop → take-home → live coding → onsite) is captured below.

---

## 1. What was the loop?

| Round | Length | What they tested | What they wanted |
|---|---|---|---|
| 1. Recruiter screen | 30 min | Motivation, comp, basic background | "Why FDE, why OpenAI" — clear, customer-focused |
| 2. **Take-home** | **1 week** | "Build a semantic search setup over Amazon products for ChatGPT" | The candidate who builds the same thing OpenAI builds, but can explain it in plain English |
| 3. **Live team discussion** | **60 min** | Walk through the take-home, defend decisions, adapt to new requirements | Customer-facing explanation + on-the-fly adaptation |
| 4. **AI-enabled coding screen** | 60 min | "Easy, multi-step LeetCode" with an AI assistant enabled | "Less interested in pretending tools do not exist and more interested in whether you can still reason about efficiency and write solid code" |
| 5. Onsite | Half-day | 4 interviewers + 1 hiring manager, walk through the same solution from different angles | Project discussion + cross-functional + behavioral + customer interaction |

**The loop is 4-5 rounds over ~2 weeks.** The recruiter reaches out directly (this is the OpenAI FDE norm). The take-home + live discussion is the centerpiece; the AI-enabled LeetCode is the sanity check; the onsite is the same solution walked from 4 different angles.

**The candidate's framing:** "An OpenAI recruiter reached out to me directly, and the process was pretty focused compared to a normal SWE loop. The main pieces were a one-week take home, a live team discussion of that case study, and a separate AI-enabled coding screen that was basically an easy LeetCode problem."

**The OpenAI-specific signal:** the take-home is "basically the job" — the candidate is building semantic search for ChatGPT, which is the actual FDE work. The interview is the job preview, not a proxy for it.

---

## 2. What was the take-home / case study?

**The prompt:** "Build a semantic search system over Amazon products so ChatGPT could access it."

**The time budget:** 1 week.

**The deliverables (per the candidate's report):**

- The code.
- A working app (deployed, not just a local prototype).
- A walkthrough of the choices, in plain English.

**The 4 specific case-study questions the team asked during the walkthrough:**

1. "How are you thinking about the use case for this?"
2. "Where would you make decisions to take a certain path or not?"
3. "How specific do you want to be on certain searches?"
4. (implicit) "How would you tweak the system based on what the customer actually needed?"

**The candidate's experience:** "I built the case study around semantic search for Amazon products and submitted both the code and the app. In the walkthrough, I focused on why I made certain design choices, how specific I wanted retrieval to be for different search intents, and how I would tweak the system based on what the customer actually needed. The discussion felt less like trivia and more like them checking whether I could explain the solution cleanly, understand the use case, and show that I was not just shipping slop."

**The Phase 6 prep:** This is `../take-home/01-prototype.md` (the OpenAI semantic-search pattern). The 5 deliverables match: code, tests, README, cost model, runbook. The 4 case-study questions map to the 4-step decomposition framework (clarify → decompose → design → tradeoffs).

**The candidate's #1 tip:** "I would not over-index on hard LeetCode. I would still do coding prep, but I would spend way more time practicing how to explain technical choices in plain English, especially in a customer-facing context."

---

## 3. The AI-enabled live coding screen

**The format:** 60 min, AI assistant enabled, "easy, multi-step LeetCode problem with a little pressure on efficiency."

**The 3 specific questions asked:**

1. "Solve this delivery-rate style coding problem in the live coding screen."
2. "What is the time complexity?"
3. "How efficient is your solution on memory?"

**The candidate's approach:** "I treated it like a straightforward easy LeetCode question and worked through the multi-step logic live. Since the environment was AI enabled, the real signal felt less about memorizing tricks and more about whether I could still reason through the solution. They specifically asked me to talk through time complexity and memory efficiency, so I made sure to explain the runtime and space tradeoffs instead of just getting to working code."

**The OpenAI-specific signal:** "They are less interested in pretending tools do not exist and more interested in whether you can still reason about efficiency and write solid code." This is `../practical-coding/README.md`'s "AI as a typing accelerator" pattern: the AI drafts the boilerplate, the candidate verifies + explains the complexity.

**The Phase 6 prep:** This is `../practical-coding/README.md` (the 3 sub-rounds: build / extend / debug) + `../swe-coding/README.md` (the 8 patterns: arrays / hash tables / strings / trees / graphs / DP / recursion / linked lists). The OpenAI FDE coding round is easy-medium difficulty; the signal is the explanation, not the algorithm.

---

## 4. The onsite (the round the candidate didn't reach)

**The format (per the recruiter's brief):** ~Half-day, 4 interviewers + 1 hiring manager. Mostly the same take-home solution walked through from different angles.

**The question types (per the recruiter's brief):**

- **Project discussion** — walk through the take-home from a different angle (the technical deep-dive version)
- **Cross-functional** — same solution, but from a PM/Design lens (the user-experience version)
- **Behavioral** — same solution, but framed as a customer-engagement story
- **Customer interaction** — same solution, but role-played as a customer call (the "explain it to a non-engineer" version)

**The Phase 6 prep:** The onsite is `../project-deep-dives/README.md` (the 45-min presentation format) + `../behavioral/README.md` (the 3 question types) + the on-the-fly adaptation drill from `../decomposition/README.md`.

**The candidate's #2 tip:** "I would also practice case-study style system thinking, because they really care whether you understand the use case and can adapt the solution when the customer's needs change."

---

## 5. What did they test? (the consolidated signals)

### The 7 signals (across all 4 rounds)

1. **"Whether I could explain my decisions clearly and tie them back to customer needs."** → Customer-facing communication. The FDE signal.
2. **"Whether you can adapt the solution when the customer's needs change."** → On-the-fly adaptation. The decomposition signal.
3. **"They still wanted me to speak to time complexity and memory."** → Even the AI-enabled round tested fundamentals.
4. **"They are less interested in pretending tools do not exist and more interested in whether you can still reason about efficiency and write solid code."** → AI-assisted + fundamentals. The practical-coding signal.
5. **"Whether I could build something clean, deploy it properly, explain it well, and adjust it around customer needs."** → Ship + explain + adapt. The FDE signal.
6. **"Show that I was not just shipping slop."** → Quality + customer focus. The "treat the take-home as a real engagement" signal.
7. **"How specific do you want to be on certain searches?"** → Search-relevance tradeoffs. The system-design signal.

### The 4 anti-patterns (per the candidate's report, implied)

1. **Over-indexing on hard LeetCode.** "I would not over-index on hard LeetCode." The OpenAI FDE round is easy-medium difficulty; the signal is the explanation, not the algorithm.
2. **Pretending AI tools don't exist.** They enable the AI in the coding screen. The signal is "can you use the tool AND reason about efficiency." Not "can you solve it without the tool."
3. **Abstract interview theater.** "This process felt very tied to the actual job instead of being abstract interview theater." The candidate who treats the take-home as a real engagement (with a runbook, a cost model, a customer narrative) signals FDE fitness. The candidate who treats it as a coding exercise signals SWE.
4. **Memorizing tricks.** "The real signal felt less about memorizing tricks and more about whether you could still reason through the solution." Easy-medium is the difficulty; reasoning is the signal.

---

## 6. What's the Phase 6 module that preps each round?

| Round | Phase 6 module |
|---|---|
| 1. Recruiter screen | `../interview-process.md` (the FDE loop, day-in-the-life) |
| 2. Take-home | `../take-home/01-prototype.md` (the OpenAI semantic-search pattern) |
| 3. Live team discussion | `../project-deep-dives/README.md` (the 45-min presentation) + `../decomposition/README.md` (the 4-step framework) |
| 4. AI-enabled coding screen | `../practical-coding/README.md` (the 3 sub-rounds) + `../swe-coding/README.md` (the 8 patterns) |
| 5. Onsite | `../project-deep-dives/README.md` (the 45-min presentation) + `../behavioral/README.md` (the 3 question types) + the on-the-fly adaptation drill |

**The candidate's pre-Phase-6 prep time would have been:** ~3 weeks full-time, weighted 40% on take-home (the prototype + the walkthrough) + 30% on decomposition/system-design (the case-study thinking) + 20% on practical coding (the AI-enabled screen) + 10% on behavioral (the customer-facing explanation).

---

## 7. The 5-pattern cheat sheet for OpenAI FDE prep

Based on this report + the Phase 1-5 portfolio:

1. **Build the take-home as if it were the actual job.** Runbook, cost model, eval set, customer narrative, deployed app. The candidate who treats the take-home as a prototype gets screened out; the candidate who treats it as a real engagement gets the onsite.
2. **Practice explaining technical choices in plain English.** The 4-step framework (clarify / decompose / design / tradeoffs) is the structure; the customer narrative is the content. The walkthrough is the centerpiece.
3. **Don't over-index on hard LeetCode.** Easy-medium is enough. The signal is "can you reason about efficiency AND use the AI tool well."
4. **Practice on-the-fly adaptation.** The live team discussion will throw you a curveball ("what if the customer wants to add a new product category tomorrow?"). The decomposition framework is the answer.
5. **Bring a Phase 1-5 case study as your "real customer" example.** "I've built this for PacificFreight; here's the architecture doc, the eval set, the runbook, the handoff." That's the FDE signal at OpenAI.

---

## 8. The 5 most common OpenAI FDE follow-up questions (inferred from this report)

| Question | The FDE answer |
|---|---|
| 1. "Walk me through your take-home." | "The 4-step framework: clarify (the customer is Amazon's product team, the use case is in-chat product search, the constraint is <500ms P95, the failure mode is wrong products, the timeline is 1 week). Decompose (products, embeddings, queries, results, feedback). Design (FastAPI + Postgres + OpenAI embeddings + a hybrid retriever). Tradeoffs (BM25 + dense + RRF vs dense-only; cosine vs dot product; pgvector vs Pinecone)." |
| 2. "How are you thinking about the use case for this?" | "The use case is in-chat product search: a user asks ChatGPT for a product recommendation, and the system returns the top-3 Amazon products with citations. The customer-facing metric is click-through rate; the technical metric is P95 < 500ms; the failure mode is wrong products (which loses customer trust). The architecture is a hybrid retriever because the product catalog is large + semantically rich (good for dense) but also has structured attributes (brand, price, category) that benefit from BM25." |
| 3. "How specific do you want to be on certain searches?" | "It depends on the query intent. For 'best running shoes under $100' (specific), I want narrow retrieval with brand + price filters. For 'gift for a 10-year-old' (broad), I want broad retrieval with category + age filters. The system uses query understanding to pick the retrieval mode; the eval set has 30 rows stratified by query specificity (10 specific, 10 mixed, 10 broad)." |
| 4. "What is the time complexity?" / "How efficient is your solution on memory?" | "O(n) for the dense retrieval (cosine similarity over n embeddings), O(log n) for the BM25 index, O(n) for the RRF fusion. Memory: O(n × d) where d is the embedding dimension (1536 for OpenAI's text-embedding-3-small). For 1M products, that's ~6 GB of embeddings, which fits in a single pgvector instance on a 16 GB VM. The cost ceiling is the binding constraint; I'd switch to a quantized embedding (256-d) at 10× growth." |
| 5. "What would you do if the AI tool gave you a wrong answer during the coding screen?" | "Catch it in the test. The AI is a tool; my job is to verify the output. If the test passes and I'm confident, ship it. If the test fails or I'm not confident, rewrite the relevant section by hand. The tool is not the answer; the test is the answer." |

**Memorize these 5.** They're the most common OpenAI FDE follow-ups based on this report.

---

## 9. How to use this report

1. **Read it once.** Internalize the loop + the take-home + the live coding + the onsite.
2. **Build the OpenAI take-home.** Use `../take-home/01-prototype.md` as the template. Time yourself: 1 week. Submit code + working app.
3. **Rehearse the 5 follow-up questions.** They're the most likely curveballs.
4. **Practice explaining technical choices in plain English.** The 4-step framework is the structure; the customer narrative is the content.
5. **Bring a Phase 1-5 case study as your "real customer" example.** PacificFreight is the default.
6. **For the onsite:** rehearse the same take-home from 4 angles (technical / cross-functional / behavioral / customer). The 4-angles format is `../project-deep-dives/README.md`'s 45-min presentation, broken into 4 × 10-min segments with different framings.
