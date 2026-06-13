# Google Cloud Data Engineer — Interview Questions (from Josh's Experience)

> Source: "Google Data Engineer Interview Experience" by Josh, a data engineer in the Google Cloud team (ex-ZS Associates; AWS/Azure/PySpark/Hadoop background, **zero** GCP experience going in). He couldn't share exact questions due to a confidentiality agreement, so these are the **themes and question types** he described per round. Five rounds total, then hiring committee + (sometimes) team matching.

---

## HEADLINE LESSON
Josh opens by admitting he assumed he could **skip DSA** because it's a data engineering role, not SWE — and warns: *"you might be very wrong."* DSA **is** tested, just at a lower bar than SWE (LeetCode medium, not hard).

---

## ROUND 1 — Technical Screening (rapid-fire, 30–45 min)
A fast back-and-forth covering many topics in a short time:
- Rapid-fire **DSA / algorithms** questions
- **Big data / distributed systems** questions (e.g., Spark)
- **Cloud** questions
- Questions drawn from **his resume / experience**
- **Plus:** a couple of questions he had to **submit written answers to by email** after the round ended

> Format note: expect a quick-fire screen, and be ready for possible written follow-ups.

---

## ROUND 2 — Technical (Data Modeling + SQL + Python)
The recruiter told him in advance it would focus on DSA, SQL, and "data-based" questions (big data, Spark, Hadoop, Hive, cloud computing, batch/stream pipelines). What he actually got:

### Q: Data modeling question (deliberately broad)
- Given a company in some industry that wants a data model — "how will you approach this?"
- **How to answer:** ask many counter-questions — what are they selling? what's the product? what records must be captured? Example: a drug company → drug price, number sold, regions sold; a movie theater → show times, how you capture user tickets.
- Then ask: is this **OLAP or OLTP** data? Design a normalized / denormalized model accordingly. Build the tables around the scenario.

### Q: Complex SQL query — on YOUR OWN data model
- A complex query with **3–4 aggregations and joins** in a single query.
- **The catch:** you must use the data model you just designed. If you missed a pivotal field while modeling, you get caught here.
- **How to answer:** be comprehensive when designing the model so the query is writable.

### Q: A simple Python question (easy-to-medium DSA)
- A straightforward DSA problem, solvable in your preferred language.

---

## ROUND 3 — Strictly DSA (+ resume-based cloud questions)
- A couple of **pure DSA** questions, solved in the language of your choice (he used Python).
- A couple of questions on **cloud-based processing pipelines**, mostly tied to his **resume experience**.
- **Bar note:** for a big-data role the DSA bar is NOT SWE LeetCode-hard — it's around **LeetCode medium**, because they're also testing cloud + big-data knowledge + data modeling, so the coding portion is lighter than SWE.

---

## ROUND 4 — System Design (the longest round, ~1.5 hours)
### Q: Design a big-data processing pipeline using cloud components
- Broad, end-to-end design — exactly what you'd expect for a DE role.
- **Follow-ups:** justify every component — "why did you choose component A over B and C? what are its advantages?"
- Consider **open-source components** that can save cost.

### In-depth Spark questions (the genuinely new insight)
- Practical, experience-based Spark questions — *not* theory.
- Example format: "if you're facing this issue, how will you tackle it?"
- **How to answer:** you can only answer well if you've *actually faced* the issue. Explain your real approach — the steps you'd take in your Spark environment to diagnose and get the job running.
- **Prep implication:** prepare real Spark war stories (a skew / OOM / shuffle / slow-job problem you actually debugged).

### GCP reassurance (important)
- Josh used mostly **AWS/Azure** components (he had zero GCP experience) and **they were fine with it.**
- They don't expect you to know everything about GCP just because it's Google — the platforms are ~80% conceptually similar.
- Knowing GCP is "a very big plus" but not a gate.

---

## ROUND 5 — Behavioral / Googleyness
- Situational behavioral questions: "if this happens, how would you tackle it in your team?"
- They assess: **empathy, leadership skills, problem-solving, risk-taking, and communication.**

---

## AFTER THE ROUNDS
- **Hiring committee:** a group reviews your profile + all interview feedback and decides on an offer.
- **Team matching:** only if your role wasn't specific from the start (didn't apply to Josh — his role was specific). Here the tables turn: you assess the team, but must also show curiosity to join.
- Recruiter then discusses expected compensation → offer.
- **Timeline:** Google interviews typically take ~2–4 months end to end.

---

## QUICK PREP TAKEAWAYS FROM JOSH
1. **Don't skip DSA** — it's tested even for DE (medium level).
2. **Design your data model comprehensively** — you'll write SQL on top of it.
3. **Ask counter-questions** on broad/ambiguous design prompts.
4. **Prepare real Spark debugging stories** — practical, not theoretical.
5. **You don't need GCP mastery** — lean on whatever cloud you know; concepts transfer.
6. **Justify every system-design choice** (A over B over C) and mention cost-saving open-source options.
7. **Behavioral:** show empathy, leadership, problem-solving, communication.
