# How to Prep for Your First AI Engineer Interview (and Actually Get the Offer)

*I have been on both sides of this interview table, bombed my first one, and then passed the next three, so here's what actually changed.*

---

## 0. Look, let's skip the intro

Want to land an AI engineer job? Cool, because we do not need me to tell you the field is hot or that "AI is the future," since you already know that, so let's skip the pep talk and get to the stuff that actually matters.

I bombed my first AI interview because I spent 20 minutes whiteboarding transformer attention mechanisms when the hiring manager just wanted to know if I could write a basic API wrapper, and I passed the next three, so here's what actually changed.

---

## 1. What an AI Engineer Actually Does (Hint: Not What You Think)

Most people confuse this role with ML research or data science, but they are wrong, because an AI Engineer builds **products** that use AI, so you will not be training models from scratch. Instead, you will be wiring up APIs, building RAG pipelines, shipping features, and making sure things do not break at 2am.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          WHICH ONE ARE YOU?                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│     ML Researcher       Data Scientist         AI Engineer          │
│     ─────────────       ──────────────         ───────────          │
│     • Train models      • Analyze data         • Build with AI      │
│     • Publish papers    • Statistics           • Ship to production │
│     • Novel research    • Visualizations       • RAG, agents, APIs  │
│                                                                     │
│         ◄──────────────  YOU ARE HERE  ──────────────►              │
│                                                                     │
│   Day job:  Shipping features, not papers.                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

If you show up to an interview talking about transformer architectures and backprop, you are answering the wrong question, since they want to know: **can you build something useful with this stuff?**

---

## 2. The Skills That Actually Matter

Forget the 50-item checklists on LinkedIn. Here's what hiring managers actually test:

### Tier 1: Non-negotiable
- Python, and I mean actual fluency, not "I took a course" fluency. Can you write a decorator without Googling?
- Data structures including hash maps, trees, graphs, and Big-O, because yes, even AI roles get tested on this stuff.
- SQL with joins, window functions, and CTEs, because you will be querying data more than you think.
- Git fundamentals like branches, PRs, and rebase vs merge, so you don't embarrass yourself on day one.

### Tier 2: AI-specific
- How LLMs actually work, including tokenization, context windows, and attention at a high level.
- Prompt engineering with few-shot, chain-of-thought, and system prompts.
- Embeddings and vector DBs, knowing when you need them and when you don't.
- RAG. It is the standard for production AI right now, so know it cold.
- Function calling, which is how agents talk to tools.

### Tier 3: Production
- API integration with OpenAI, Anthropic, and open-source models.
- Caching, because tokens cost real money and the bills add up fast.
- Latency management, because users wait about 3 seconds before they bounce.
- Error handling for the weird ways LLMs fail.
- Observability, because if you can't see it, you can't fix it.

```
                       SKILLS PYRAMID
                       ===============

                            ▲
                           / \
                          /   \         <- Tier 2: AI-specific
                         /─────\
                        /       \
                       / Prod &  \      <- Tier 3: Production
                      /  System   \
                     /    Design   \
                    /──────────────\
                   /                \
                  /   Must-Have      \   <- Tier 1: Fundamentals
                 /    Fundamentals    \     (most skip this)
                /______________________\

   !  Most beginners skip Tier 1 to jump to Tier 2.
   *  Strong Tier 1 is what gets you the offer.
```

---

## 3. The Interview Loop (What to Expect)

Here's the typical structure, and while some companies vary, the bones are the same.

### Round 1: Recruiter screen (30 min)
This is where they cover your background, motivation, salary expectations, and basic fit, with nothing technical. Have your "tell me about yourself" pitch ready, and keep it under 2 minutes.

### Round 2: Technical phone screen (60 min)
Live coding plus 1-2 AI concept questions, and sometimes a take-home. The take-home is your friend, so use it to show off.

### Round 3: Onsite (4-5 hours)
- Coding (1-2 problems)
- System design (design an AI system)
- AI deep dive (your projects, model trade-offs)
- Behavioral (STAR format, have your stories ready)

### Round 4: Final + offer
Hiring manager, team fit, and comp negotiation, so do not lowball yourself here.

```
              AI ENGINEER INTERVIEW LOOP
              ═══════════════════════════

    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │   Recruiter  │    │  Tech Phone  │    │   Onsite /   │
    │    Screen    │───►│    Screen    │───►│  Virtual     │
    │   (30 min)   │    │   (60 min)   │    │  (4-5 hrs)   │
    └──────────────┘    └──────────────┘    └──────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
      Background          Live coding         Coding + design
      Motivation          AI concepts         AI deep dive
      Salary fit          Take-home           Behavioral
                                                  │
                                                  ▼
                                              ┌──────────────┐
                                              │  Final &     │
                                              │   Offer      │
                                              └──────────────┘
                                                     │
                                                     ▼
                                                 (offer)
```

Honest pass rates look like ~50% → ~40% → ~25% → ~75%, which means roughly 4% of applicants end up with an offer, so yikes, but read on.

---

## 4. The Questions You'll Actually Get

### Technical

**Q1: "Walk me through how RAG works."**

This comes up in 90% of AI interviews. Memorize the flow:

```
                    RAG FLOW
                    ════════

    User Query
        │
        ▼
    ┌─────────────┐       ┌──────────────────┐
    │  Embedding  │       │  Knowledge Base  │
    │    Model    │       │  (Vector DB)     │
    └──────┬──────┘       └────────┬─────────┘
           │                       │
           └─────────┬─────────────┘
                     │ Top-K chunks
                     ▼
              ┌──────────────┐
              │  Augmented   │
              │    Prompt    │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │     LLM      │
              └──────┬───────┘
                     │
                     ▼
                  Answer

    When to use:  Domain Q&A, fresh info, private data, less hallucination
```

**Q2: "How do you stop hallucinations?"**

There is no magic fix. You have to layer your defenses:

```
                   DEFENSE IN DEPTH
                   ═════════════════

                  ┌──────────────────────┐
                  │     User Query       │
                  └──────────┬───────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │   RAG    │   │  Prompt  │   │  Temp =  │
        │ Grounding│   │Constraints│  │    0     │
        └────┬─────┘   └────┬─────┘   └────┬─────┘
             │              │              │
             └──────┬───────┴──────────────┘
                    ▼
              ┌──────────┐
              │   LLM    │
              └────┬─────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │  Output  │ │ Chain of │ │  Human   │
   │  Schema  │ │ Thought  │ │  Review  │
   └──────────┘ └──────────┘ └──────────┘

   No single trick works. Layer them.
```

**Q3: "Fine-tuning vs prompting: when do you use which?"**

```
           PROMPTING vs. FINE-TUNING

   ┌────────────────────┐     ┌────────────────────┐
   │     PROMPTING      │     │    FINE-TUNING     │
   ├────────────────────┤     ├────────────────────┤
   │ Cost:    $$        │     │ Cost:    $$$$$     │
   │ Time:    Minutes   │     │ Time:    Days      │
   │ Data:    0-10      │     │ Data:    100s+     │
   │ Reversible: Yes    │     │ Reversible: No     │
   ├────────────────────┤     ├────────────────────┤
   │ Use for:           │     │ Use for:           │
   │ • Quick iteration  │     │ • Style/tone       │
   │ • Few examples     │     │ • Domain expertise │
   │ • New tasks        │     │ • Latency wins     │
   └────────────────────┘     └────────────────────┘

   Rule of thumb:  Try prompting → RAG → fine-tune last.
```

**Q4: "How do you evaluate an LLM app?"**

This is where most candidates fumble. See the deep-dive below.

**Q5: "Design a customer support chatbot."**

```
           SUPPORT CHATBOT ARCHITECTURE

    ┌──────────┐
    │   User   │
    └────┬─────┘
         │ "Where's my order?"
         ▼
    ┌──────────────────┐
    │ Intent Detection │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │           LLM (Reasoning)            │
    └────┬────────┬────────┬────────┬──────┘
         ▼        ▼        ▼        ▼
      ┌─────┐ ┌──────┐ ┌──────┐ ┌──────┐
      │ RAG │ │Order │ │Refund│ │ FAQ  │
      │ Docs│ │ API  │ │ API  │ │  KB  │
      └──┬──┘ └──┬───┘ └──┬───┘ └──┬───┘
         └───────┴────────┴────────┘
                  │
                  ▼
            ┌──────────┐
            │ Response │
            └────┬─────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     ┌─────┐ ┌──────┐ ┌────────┐
     │Eval │ │Safety│ │Human   │
     │Auto │ │Check │ │Fallback│
     └─────┘ └──────┘ └────────┘
```

Walk through intent detection, then RAG over docs, then tool calls for actions, then safety checks, and finally human fallback, while you mention the eval pipeline and the cost.

### Behavioral

**Q6: "Tell me about a project you are proud of."**

Use STAR, and quantify the result whenever you can, since if you can't quantify the impact, you should quantify the effort, because "Reduced support tickets by 30%" beats "Built a chatbot" every time.

**Q7: "Tell me about a disagreement with a coworker."**

Do not trash anyone, since you should show that you can disagree and commit, and demonstrate that you brought data to the discussion rather than ego.

**Q8: "How do you stay current with AI?"**

Have a real answer, because "I read papers" is vague while "I built a small project using X technique from this paper" is gold.

**Q9: "Why AI?"**

Be honest, since the worst answer is "it's trendy" and the best answer is the one that ties AI back to something you actually care about.

**Q10: "Where do you see AI in 5 years?"**

Have an opinion on trends like agentic systems, smaller models, on-device AI, and regulation, then pick a few and defend them.

---

## 5. Build 2-3 Projects (Not 10)

You do not need a portfolio of 30 half-finished repos, since you only need 2-3 things that actually work and that you can talk about for 20 minutes each.

### Project 1: RAG Q&A Bot
Pick a domain you care about (books you love, a hobby, your old company's docs) and build a chatbot that answers questions using retrieval. Deploy it somewhere. **A URL is worth more than a GitHub link.**

Stack: OpenAI API, LangChain or LlamaIndex, Pinecone or ChromaDB, FastAPI.

### Project 2: An Agent with Tools
Build something that can search the web, query a database, and send a Slack message, because that shows you understand function calling and orchestration.

Stack: Function calling, ReAct pattern, at least 2-3 tools.

### Project 3: An Eval Pipeline
This one is underrated, so build a system that benchmarks different prompts or models on a fixed dataset, because that shows you understand quality measurement, which is something most beginners skip.

Stack: Python, pytest, Promptfoo or Braintrust.

```
               PORTFOLIO STRATEGY
               ══════════════════

            ┌────────────────────────────────────┐
            │       YOUR GITHUB PORTFOLIO        │
            └─────────────────┬──────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         ┌─────────┐     ┌─────────┐     ┌─────────┐
         │Project 1│     │Project 2│     │Project 3│
         │  RAG    │     │ Agent   │     │  Eval   │
         │  Bot    │     │ Tools   │     │Pipeline │
         └────┬────┘     └────┬────┘     └────┬────┘
              │               │               │
              ▼               ▼               ▼
         Shows:           Shows:           Shows:
         • LLM apps       • Function       • Quality
         • Vector DB        calling         measurement
         • End-to-end     • ReAct          • Stats
           shipping       • Multi-tool
                           orchestration

   Two deployed projects beat ten half-finished ones.
```

---

## 6. LLM Evaluation: The Part Most Beginners Skip

This is the section I wish someone had shown me before my first interview, since evaluation is the difference between a toy and a real product.

### Why BLEU and ROUGE Aren't Enough

You might hear about BLEU (Bilingual Evaluation Understudy) in interviews since it was made for translation and checks if n-grams in your output match a reference, which sounds reasonable until you see this:

```
   Reference:  "The cat sat on the mat."

   Prediction A:  "The cat sat on the mat."
                  [good] Right meaning, high BLEU

   Prediction B:  "On the mat sat the cat."
                  [good] Same meaning, LOW BLEU (wrong word order)

   Prediction C:  "The feline rested on the rug."
                  [good] Same meaning, even lower BLEU (synonyms)

   Prediction D:  "The mat sat on the cat."
                  [bad]  Opposite meaning, HIGH BLEU

   ┌─────────────────────────────────────────────┐
   │  High BLEU ≠ right answer.                  │
   │  Low BLEU ≠ wrong answer.                   │
   │  BLEU measures words, not meaning.          │
   └─────────────────────────────────────────────┘
```

ROUGE has the same problem, since it counts word overlap and not whether the answer is actually useful.

### So What Do Real Companies Do?

They build their own evals, because public benchmarks (MMLU, GPQA, EvalPlus, SWE-bench) are useful but they do not tell you if your specific chatbot is good at your specific task.

Different products care about different things:
- **Healthcare agent:** factuality is everything. One wrong drug name = lawsuit.
- **Mental health chatbot:** safety is everything. One bad suggestion = real harm.
- **Coding assistant:** utility is everything. Does the code run?

### Evaluation Datasets

An eval dataset is just a list of (input, expected output) pairs, which might sound simple, but it really is not.

The questions to ask:
- What task are we actually measuring?
- What do the inputs look like? Real user messiness or clean toy examples?
- What did the labelers follow? (You need a rubric, or labels will be garbage.)

Quick example:
```
   Input:  "Sort these: 5, 12, 1, 9"
   Expected:  "1, 5, 9, 12"

   Tests:
   • Instruction following. Does it return a list?
   • Utility. Are the numbers actually sorted?
```

For a real system, say a content moderation classifier, you'd build a dataset like:
- Covers all the harm categories (violence, sexual, hate, self-harm)
- In proportions that match real-world frequency
- Includes "negative" examples (safe content) so the model learns the difference
- Has a clear labeling rubric
- Measures inter-annotator agreement (if two labelers disagree a lot, your dataset is broken, not the model)

*Pro tip:* If you casually mention "inter-annotator agreement" in an interview, you will immediately stand out. Most juniors do not even know that is a thing, let alone that bad labels are usually the real problem.

### Offline vs Online

There are two flavors, and both matter.

| Type | When | Pros | Cons |
|------|------|------|------|
| **Offline** | Before deploy | Fast, cheap, reproducible | Doesn't match real users |
| **Online** | In production | Real-world, accurate | Risky, slow feedback |

You need both, and here is how they fit together:

```
              EVALUATION LIFECYCLE
              ══════════════════════

   ┌─────────────────────────────────────────────┐
   │  STAGE 1:  OFFLINE                          │
   │  Eval set ──► Model ──► Metrics            │
   │  Fast, cheap, doesn't match reality         │
   └──────────────────┬──────────────────────────┘
                      │  Pass threshold?
                      ▼
   ┌─────────────────────────────────────────────┐
   │  STAGE 2:  STAGED ROLLOUT (5-10% traffic)   │
   │  Watch quality + latency + cost             │
   │  Compare against baseline                   │
   └──────────────────┬──────────────────────────┘
                      │  Stats significant?
                      ▼
   ┌─────────────────────────────────────────────┐
   │  STAGE 3:  ONLINE                           │
   │  100% traffic, A/B test, human feedback     │
   │  Real but risky, slow feedback              │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
              ┌────────────────┐
              │  MONITORING    │ ──► Back to Stage 1
              │  (drift)       │     when things break
              └────────────────┘
```

### The Tradeoffs You Should Know

**Human labeling vs LLM-as-judge:**
- Humans are slow and expensive but accurate
- LLM-judges are fast but biased (they have their own preferences)
- Most companies use both: LLM-judge for iteration, humans for ground truth

**Offline vs online:**
- Offline is for "is this safe to ship?"
- Online is for "is this actually working?"

### Common Pitfalls

**1. Your offline eval doesn't match production.**
You tested on clean data. Users type "yo my acct locked?? help asap" and the model chokes. **Fix:** include messy real-user data in your eval set.

**2. Wrong metric, wrong direction.**
You track ROUGE-L. Your summaries get longer and safer. Users hate them. ROUGE went up, quality went down. **Fix:** pick metrics tied to user outcomes, not text overlap.

**3. Your dataset is inconsistent.**
Annotator A likes "short and direct." Annotator B likes "friendly." Your model looks unstable but the real problem is the labels. **Fix:** write a clear rubric, measure agreement, train labelers.

**4. Feedback loop is too slow.**
Takes 3 weeks to label new examples. By then, the bug is everywhere. **Fix:** invest in labeling infra early.

### How to Answer "How Would You Evaluate This?" in an Interview

```
   1. Define "good" for THIS use case
      (factuality? safety? tone? utility?)

   2. Build an eval dataset with clear labels
      and a rubric

   3. Mix metrics: automated + LLM-judge + human

   4. Run offline first, then staged rollout

   5. Monitor in production for drift

   6. Iterate. Evaluation is an ongoing process, not a one-time checklist.
```

---

## 7. The Week Before

Do not cram, because cramming does not work for interviews, so do this instead:

- [ ] Re-read your resume. Be ready to talk about every single line.
- [ ] Research the company. Their AI products, recent news, who their competitors are.
- [ ] Re-read the job description. Match your stories to their needs.
- [ ] Do 2-3 medium LeetCode problems. Live. With a timer.
- [ ] Prep 3 thoughtful questions for the interviewer.
- [ ] Test your camera, mic, internet, screen sharing. Tech issues tank interviews.
- [ ] Sleep. For real. 8 hours. Twice.

---

## 8. Questions You Should Ask Them

Asking good questions is half the interview, and here is what works:

- "What's the most interesting AI problem your team is solving right now?"
- "How do you measure whether an AI feature is actually working in production?"
- "Open-source models or proprietary? Why?"
- "How do engineers work with PMs and researchers here?"
- "What's the eval process before an AI feature ships?"
- "What's the biggest headache with AI reliability or cost?"

Do not ask about salary, PTO, or remote in round 1, since you should save it for the recruiter or the offer call.

---

## 9. Mistakes That Cost People Offers

### Mistake 1: Trying to learn everything
You cannot, so pick a stack and go deep, since depth beats breadth every single time.

### Mistake 2: Skipping fundamentals
Telling me "I use AI to write my code" is a fast track to bombing the live coding round, so know your basics.

### Mistake 3: Ignoring system design
Even juniors get asked, so practice designing a chatbot or a search engine out loud, with a diagram.

### Mistake 4: No stories ready
"Tell me about a challenge" should never be a deer-in-headlights moment, so have 3-4 STAR stories ready and rehearse them.

### Mistake 5: Lying
I've caught people doing this, and it always ends the interview. "I don't know, but here's how I'd find out" is the move.

### Mistake 6: Being a robot
AI engineering is collaborative, so be human, ask about the team, be curious, and remember that nobody wants to work with someone who just recites answers.

---

## 10. Resources That Don't Waste Your Time

### Free
- **3Blue1Brown**. Best visual explanations of neural nets, period.
- **Andrej Karpathy's videos**. Deep, weirdly calming, will make you smarter.
- **The Annotated Transformer**. The famous paper, with code.
- **LangChain / LlamaIndex docs**. Practical, lots of examples.
- **OpenAI Cookbook**. Real recipes from real engineers.

### Paid (worth it)
- **Andrew Ng's Deep Learning Specialization** (Coursera). The classic.
- **Full Stack Deep Learning**. Production-focused, opinionated, good.
- **Maven courses**. Practitioner-led, no fluff.

### Communities
- r/MachineLearning, r/LocalLLaMA
- Hugging Face Discord
- AI Twitter (yes, really. Follow people who build in public)
- Local meetups

---

## 11. 12-Week Prep Plan

Starting from zero? Here's what worked for me:

```
              12-WEEK PREP ROADMAP
              ════════════════════

  Week  1-2  ┌────────────────────┐
            │ FOUNDATIONS        │  Python, DSA, SQL, Git
            │ ▓▓▓▓▓▓▓░░░░░░░░░░ │  ~2 hrs/day coding
            └────────────────────┘
                          │
  Week  3-4  ┌────────────────────┐
            │ FIRST LLM APP      │  OpenAI API + bot
            │ ▓▓▓▓▓▓▓▓░░░░░░░░░ │  Build & deploy
            └────────────────────┘
                          │
  Week  5-6  ┌────────────────────┐
            │ RAG & VECTORS      │  Embeddings, vector DB
            │ ▓▓▓▓▓▓▓▓▓░░░░░░░ │  Build RAG project
            └────────────────────┘
                          │
  Week  7-8  ┌────────────────────┐
            │ SYSTEM DESIGN      │  AI system patterns
            │ ▓▓▓▓▓▓▓▓▓▓░░░░░ │  Mock designs out loud
            └────────────────────┘
                          │
  Week  9-10 ┌────────────────────┐
            │ INTERVIEW PREP     │  Coding + behavioral
            │ ▓▓▓▓▓▓▓▓▓▓▓▓░░░ │  Mock interviews weekly
            └────────────────────┘
                          │
  Week 11-12 ┌────────────────────┐
            │ POLISH & APPLY     │  Resume, GitHub, apply
            │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░ │  Start interviewing
            └────────────────────┘
```

Total time comes to roughly 150-200 hours, so adjust to your life, but keep showing up.

---

## 12. What I Look for When I'm the One Hiring

I run an AI team, and here is my rubric.

```
          HIRING RUBRIC
          ═════════════

   1. CLARITY OF THOUGHT (30%)
      Can you explain a complex system
      without losing me?

   2. FUNDAMENTALS (25%)
      Can you code without AI help
      when it matters?

   3. AI LITERACY (20%)
      Do you know when RAG beats
      fine-tuning?

   4. OWNERSHIP (15%)
      Do you ship, or just theorize?

   5. GROWTH (10%)
      Are you learning faster than
      the field is moving?
```

### What gets someone hired

- They think out loud before they code, because silent coding is a bad sign.
- They say "I do not know" without panic, since faking it is an instant no.
- They tie AI to business outcomes like "this saves 10 hours a week" rather than just saying "AI is cool."
- They ask about the eval pipeline, which shows production thinking.
- They have shipped something, and a deployed side project beats 10 certifications every time.

### Red flags

| Red flag | What it tells me |
|----------|------------------|
| Can't explain their own project | They did not build it |
| Buzzword soup, no substance | Read tweets, did not build |
| No curiosity about the product | Just wants a paycheck |
| Can't debug without AI | Fundamentals gap |
| Badmouths old employers | Cultural risk |

### My actual advice

```
   ┌────────────────────────────────────────────────┐
   │                                                │
   │  Don't optimize for the perfect answer.        │
   │  Optimize for the clearest thinking.           │
   │                                                │
   │  Build two things well, not ten things poorly. │
   │                                                │
   │  Write about what you learn.                   │
   │  Public learning compounds.                    │
   │                                                │
   │  Apply broadly, but apply intentionally.       │
   │  50 thoughtful beats 500 spammy.               │
   │                                                │
   └────────────────────────────────────────────────┘
```

Here is the thing nobody tells you, which is that the interview is just two people deciding if they want to work together, so be curious, be honest, and be a person rather than a portfolio.

---

## 13. Closing

You will get rejected, just like I did, and just like everyone I respect did, but that does not mean you are bad. It just means you have not found the right fit yet, so build stuff, write about it, talk to people, and do it all again.

If this was useful, I am writing more stuff like this, so follow along to make sure you do not miss the next one:

- **Medium:** [https://medium.com/@premvishnoi](https://medium.com/@premvishnoi)
- **LinkedIn:** [https://www.linkedin.com/in/vishnoiprem](https://www.linkedin.com/in/vishnoiprem)

I write about AI engineering, interview prep, and the things I wish someone had told me earlier, with no fluff, no recycled LinkedIn takes, and just stuff I have actually learned the hard way.

If you have got questions or you are job hunting right now, drop me a message, since I read everything.

*If this helped, send it to a friend who's job hunting. If it did not, tell me what I missed.*
