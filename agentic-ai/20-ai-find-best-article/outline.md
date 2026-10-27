# Canonical Article Outline

Every draft follows this skeleton. Drafts may vary **section order**, **organizing device**, **examples**, and **emphasis** — the functions below must all appear, but their arrangement is the draft's own choice.

Target length: **1,000–1,800 words** (body, excluding front matter, disclosure, and source list).

---

## Front matter

Title, subtitle, tags, platform, target length, disclosure statement, `rubric_score`, `hard_fail`, `distinctness_angle`. See `article-template.md`.

---

## 1. Hook — first two lines

A concrete tension, number, or challenge. No definitions. No "in today's world." The reader must have a reason to continue before any context is given.

**Must do:** put the article's most surprising evidence or most practical pain point here.

---

## 2. Thesis — within the first 150 words

One falsifiable sentence stating what the article argues. Something like: *X is the right unit of evaluation, and here is how to build it.*

**The core thesis every draft defends, in its own words:** "Best" is not a property of the artifact. It is a property of a specific job, under specific constraints, judged by someone who can detect the failures that matter. Therefore selection is a procedure you run, not a ranking you read.

---

## 3. The problem with rankings — the evidence section

Required content, in whatever order the draft chooses:

- **Leaderboards overstate differences and hide shared failure modes** (S9). Metrics miss "Reviewing Work" and "Data Structuring" entirely (S9).
- **Rankings are a single axis; capability and truthfulness are not the same axis** (S10 — larger models were *less* truthful on TruthfulQA; best model 58% vs humans 94%). Must be dated as a 2021–2022 study.
- **Static benchmarks miss operational failure** (S8): a model can pass a fixed benchmark and then "miss tool calls, hallucinate tool use, drift policy."
- **Benchmark contamination and saturation inflate results** (S13, S14).

---

## 4. Why the usual evaluation machinery also fails — the evidence section

Two sub-arguments, both mandatory:

### 4a. Automated judging has named, fixable failure modes
- LLM-as-judge hits "over 80% agreement" with human preference (S1) — good, not infallible.
- Three named biases: position, verbosity, self-enhancement (S1).
- Order swap flips rankings: "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries" (S2).
- Judges have "limited reasoning ability" (S1), may miss domain policies and required tool sequences (S8).
- Judges remain biased (S16).

### 4b. Metrics can correlate with humans for the wrong reasons
- Human-human correlation of 0.85 sets the ceiling for reference (S5).
- RAGChecker claim recall near 0.7 — but could reflect question difficulty rather than retrieval quality (S5).
- Faithfulness metrics correlate weakly as overall metrics (S5).
- METEOR — sometimes called obsolete — correlated relatively well (S5). Surprise factor.
- **High correlation does not establish validity** (S5). Evaluate at least two systems and compare outputs on the same questions.

---

## 5. The decision framework — the heart of the article

Each draft must present **at least five concrete, transferable decision rules**, and the shape of the framework must differ across drafts. Accepted shapes (drafts should not all use the same one):

- **Three-question filter** — e.g. "What job? What breaks? Who signs off?"
- **Cost–benefit lens** — spend vs. expected savings vs. switching cost
- **Persona-based lens** — different rules for the analyst, the ML engineer, the agent builder, the team lead
- **Failure-mode taxonomy** — classify candidates by how they fail, not how they score
- **Red-team lens** — what would make you drop this candidate
- **Comparative table** — candidates as rows, failure criteria as columns
- **Historical arc** — how selection changed from static benchmarks to trajectories
- **Decision tree** — a branching flow from job type to criterion
- **Scoring worksheet** — weighted criteria with a worked calculation
- **Two-speed protocol** — fast screen, slow confirm

**Each rule must be mechanical.** "Evaluate carefully" fails. "If two answers score within 5% of each other, swap the presentation order and re-judge; if the winner flips, escalate to a human" passes.

**Required rules, in substance, across the article (drafts may phrase and organize differently):**

1. **Write the job down first.** Name the input, the output, the failure that would cost you most, and the person who signs off. (S14: define a theory of change with stakeholders — goals, inputs, outputs, outcomes.)
2. **Use your own data.** Static benchmarks don't reflect your deployment. (S8, S9, S13.)
3. **Separate retrieval from generation.** If you use RAG, score the retrieval stage and the generation stage independently. (S5, S4, S13.)
4. **Control for position.** Put the evidence where the model will actually attend to it. (S3.)
5. **Swap order, control length, change judge.** Defend any close ranking. (S1, S2.)
6. **Check the claim against the source, not just the link.** A live, on-topic link does not mean the source supports the claim. (S15, S16.)
7. **Read the trace.** Answer text can look fine while the process violated your rules. (S8, S12.)
8. **Enforce what you cannot afford to get wrong outside the model.** Deterministic guards, not prompts. (S12.)
9. **Escalate on a trigger.** When the metric says "close," when the domain is regulated, when the tool count exceeds roughly 100. (S5, S6, S8.)
10. **Re-check on a schedule.** Rankings decay; so do citations and web pages. (S16, S14.)

---

## 6. Worked examples — at least two, spanning different roles

Examples must be concrete and drawn from the sources, e.g.:

- **RAG system selection** — two systems, same questions, per S5's method.
- **Tool registry at scale** — 20 tools versus 120 tools, per S6's ~100-candidate finding.
- **Agent purchase** — a static-benchmark winner that fails trace inspection, per S8.
- **Long-context document work** — position effects per S3, plus the 36.2% strict pass@1 humility anchor per S12.
- **Coding-agent selection** — repository, language, test strength, contamination exposure, latency, cost, per S13.
- **Citation audit** — link works but claim unsupported, per S16.
- **Research-tool comparison** — fact-check rate, not link rate, per S16.

**Do not** fabricate a personal trial. Use `[AUTHOR EXPERIENCE: ...]` if a first-person note is needed.

---

## 7. Limitations — must be explicit

Say plainly:
- **No published, validated algorithm exists** for picking the best tool or paper. Every framework here is a synthesis, not a finding.
- **Every number is setup-specific.** 43.13%, 36.2%, 76.8%, 58% — none are constants. Cite each with its context.
- **Several sources are preprints** (S5, S6, S7, S8, S9, S12, S13, S14, S15, S16), not peer-reviewed. Name the peer-reviewed ones (S1 NeurIPS 2023, S3 TACL 2023, S4 AAAI 2024, S10 ACL 2022, S11 ICLR 2023).
- **LLM-judge agreement figures are from 2023-era models** (S1, S2); S8 and S16 (2026) update the picture.
- **What this framework cannot settle:** whether a specific paper is worth reading on a subjective basis. It can settle whether you read it at all.

---

## 8. Actionable next steps

Three to five concrete things a reader can do this week. Each with a time estimate or a trigger. Examples:
- Build a 30-question task set from your last three closed tickets.
- Re-run your last two candidates with swapped presentation order.
- Pull the tool-call trace for your last agent run.
- Audit ten citations from your last article for claim support.
- Set a calendar reminder to re-check your shortlist in 90 days.

---

## 9. Source list

6–10 sources, each with URL, mapped to the claim it supports. Must match inline citations exactly.

---

## 10. AI-assistance disclosure

One to three sentences. Specific about what AI did and what a human must still do.

> This article was drafted with AI assistance and edited by a human. The evidence and URLs were checked against primary sources, but **the author remains responsible for every claim**. `[AUTHOR EXPERIENCE: ...]` markers indicate places where the author's firsthand account must be inserted before publication.

---

## 11. Closing question

Last line. A question the reader can actually answer about their own situation — not "what do you think?"

---

## Content checklist before a draft is considered done

- [ ] Hook in the first two lines; no throat-clearing.
- [ ] Thesis stated as a falsifiable sentence within 150 words.
- [ ] S3, S5, S8, S9, S10, S13, S14, S15, S16, S1, S2, S4, S6, S7, S11, S12 represented as appropriate — **minimum 6 distinct sources**.
- [ ] At least 5 mechanical decision rules.
- [ ] At least 2 worked examples in different contexts.
- [ ] Limitations section states: no validated algorithm; numbers are setup-specific; preprint/peer-reviewed split.
- [ ] 3–5 concrete next steps.
- [ ] Source list matches inline citations exactly; no orphans either way.
- [ ] AI-assistance disclosure present.
- [ ] Closing question is specific and answerable.
- [ ] At least one `[AUTHOR EXPERIENCE: ...]` placeholder where a personal note genuinely helps (must survive into `article.md`).
- [ ] Zero banned phrases (`rubric.md` list).
- [ ] Zero invented first-person claims.
- [ ] Word count in 1,000–1,800.
