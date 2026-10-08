Actual questions reported for this screen:
https://www.metacareers.com/profile/interview_prep/947084298421315/1470882977345088/


Tell me about yourself — walk through last year
Tell me about a time you improved a complex process
Talk about a conflict with a PM or DS — how did you resolve?
How have you handled privacy/compliance in data projects?
How did you influence a product decision using data?
What do you do when a pipeline you own breaks at 2am?
Why Meta? Why Product Analytics org?



Situation: Retention dashboard was breaking for PMs because events were logged inconsistently.
Task: I owned logging spec + model for Instagram Story engagement.
Action: Defined 3 metrics, redesigned fact table grain, implemented Scribe -> Hive pipeline with SLA, added row count + checksum validation.
Result: Query latency down 40%, adoption by 12 PMs/DSs, used for experiment that shipped.

Have 4 stories ready:

Owned critical dataset
Fixed data quality issue
Influenced product without authority
Migration / deprecation with rollback

2. Technical Screen (1 hour) - Coding + Data Modeling + Architecture + SQL
This is the hard filter. Format from candidate reports Nov 2025 - Apr 2026:

5 min intro + 25 min SQL + 25 min Python + 5 min Q&A on CoderPad, no autocomplete. Need ∼3/5 correct in EACH half to pass. You can't compensate SQL with Python. 


30-50 min: Data Modeling + Architecture - This is where they combine:
"Design a relational database for an app / ride-sharing app" + "How would you partition fact table with 100B rows?"
They want: Clarify product question → define metrics → logging spec (what events) → star schema (fact/dim, grain, SCD) → physical (partition by ds/country, bucket, ORC) → SLA, quality, privacy, discovery (Nemo increased search success 50%). 



What product question? (e.g. why retention dropped)
Metrics (DAU, retention, watch time)
Events needed
Fact table grain, dims
Partitioning, file format, late data, idempotency
How would you migrate from old model? (row count + checksum validation)
Want me to run this as a mock with you now? I can be the interviewer:

I start Leadership: "Tell me about a time you improved a complex process"
Then jump into the 1-hour technical screen live


Meta DE Leadership Interview - Prep Sheet
Role: Data Engineer, Product Analytics - Owns data scope for major business area
Scoring: Scope / Influence / Leadership + AI Judgment
What interviewer is scoring
SCOPE: How big was your ownership? Ambiguity? Did you define success?
INFLUENCE: Did you drive accountability across XFN (PM, DS, SWE, leadership) without authority?
LEADERSHIP: Did you conceptualize major initiative, leverage team strengths, mentor diverse engineers?
You need 3-4 stories, each with this structure
For each story, fill:

Title:
Area of Ownership:
Situation (2 sentences - ambiguity + why it mattered to business):
How YOU defined success (metric, SLA, adoption):
Your Role vs Others (who did you lead/mentor/coordinate):
Tradeoffs you made (time vs quality vs scope - THIS is critical):
XFN conflict + how you prioritized:
Impact (numbers):
What you'd do differently:
Story 1: Owning Major Initiative (MUST HAVE)
Example angle for DE Product Analytics:

Rebuilt logging + fact table for core product metric (e.g. Reels watch time, Marketplace search)
Before: fragmented logs, PMs had different numbers
You: Defined single source of truth, led 2-3 engineers, drove alignment with 4 PMs + DS team
Tradeoff: Shipped V1 with daily batch to unblock PMs vs waiting for real-time (explain why)
Success definition: Adoption by X teams, query latency, data quality SLA 99.9%, metric consistency
Influence: Drove accountability - created data contract with upstream SWE, held them to it
Story 2: Leading Diverse Team + Mentoring
Junior engineers with different strengths
How you delegated, leveraged strengths, mentored
Example: One good at Spark tuning, one at SQL modeling - how you assigned
Story 3: XFN Prioritization Conflict
Two PM teams both want your team to build their dashboard/pipeline first
How you prioritized: business impact, effort, urgency framework
How you said no, communicated tradeoff
Story 4: AI Judgment (they WILL ask this now)
Meta says: "How you verify AI output, spot hallucinations, privacy risks, when AI helps vs noise"

Good answer structure:

Where you use AI: SQL generation, code boilerplate, doc search, anomaly summary
How you VERIFY: Always run query, check row count + checksum, never trust schema hallucinations, review privacy - no PII to external LLM
Risk you spotted: AI invented column that doesn't exist / leaked prod data / wrong join leading to inflated metrics
Decision: When AI helps (speed up) vs when it adds noise (critical modeling decisions you do yourself)
If your company restricts AI: "We can't use external tools due to privacy, so I reason about AI like this: I would use it for... but verify by..."
If restricted: That's completely fine per email - speak to reasoning.

Questions they will ask you (from email)
Tell me about initiative you owned end-to-end for an area of product. What was scope, tradeoffs, impact?
How do you define success for your area of ownership?
How do you lead and mentor diverse group to deliver data products?
How do you build XFN relationships and prioritize across different XFN partners?
How do you drive accountability within team + partners + leadership?
Tell me about time you conceptualized and led major initiative - from ambiguous idea to delivery
AI in your work - example, verification, risks
How to answer - 2 minute format
Use: Context (20s) -> Your definition of success (15s) -> Tradeoff + leadership (45s) -> XFN influence (20s) -> Impact numbers (20s)

Always end with: "If I did it again, I'd..."

Common fails
Too technical (spending 5 min on Spark tuning). They want leadership, not code.
"We" not "I" - they need YOUR role
No tradeoff - says you did everything perfectly = no judgment
No metric for success - "it went well" is not success definition
No XFN conflict - says everyone agreed = not senior scope
Your homework - fill now
Write 3 stories using template above. Keep each to 250 words. Practice out loud timed.


echnical Screen
What can you expect?
Meta Data Engineering teams expect that everyone has significant hands-on expertise in core skills such as SQL, Data Modeling, and basic coding. In addition, as a Senior IC, the ability to architect complex big data solutions is important. The technical portion is designed to help us understand your experience with these core skills. Please use the links in the appendix/resources section to help with preparation.




15 min Python + 15 min Data Modeling + 10 min ETL Architecture + 15 min SQL = 55 min + 5 min buffer

This is harder than the old 5+5 screen because they test all 4 in one hour. Here's how to ace each block:

1. Coding (Python) ∼15 min
What they said: Familiarity with arrays, nested lists/dicts, algorithmic thinking, walk through pseudo code, edge cases, debug executable code.

What that means: No LeetCode Hard. It's data manipulation under pressure.

You will get 1-2 of these (6-7 min each):

Level they start with: Given [{'user_id':1, 'event':'click'}, ...] return top N users by count → Must write Counter in 30 sec, handle nulls
Level they go to if you pass: Join two lists on user_id without pandas, handle unmatched → Build lookup dict O(n), not nested loops O(n²), explain inner vs left
Hard follow-up for Senior: Dedup keeping latest by timestamp + handle malformed + debug my buggy code → They will give you buggy code and ask to debug
How to win:

Always start with pseudo-code: "I'll build dict, iterate once, O(n)"
Say edge cases out loud BEFORE coding: "Empty list, missing key, null user_id, duplicate ts — in prod I'd log and filter"
Write direct solution first, then mention optimization: "This is O(n²), I'd make it linear with dict index"
Drill these cold: defaultdict, Counter, sorted(key=), set, datetime.strptime, list/dict comprehensions

2. Data Modeling ∼15 min — THIS is where offers are won/lost
What they said: Understand ambiguous business problem, core data elements, metrics + dimensions to measure success, facts/dimensions/SCD, extend model to handle new business questions.

Exact flow they use:

Interviewer: "Design data model for tracking user engagement on Instagram Reels in Thailand"

Do this in order (3 min per step):

a) Clarify business questions (2 min): "Are we measuring retention, watch time, or monetization? What decision will PM make?"

b) Metrics to measure success (2 min): "DAU, 7-day retention, avg watch time, completion rate. Success = retention +5%."

c) Dimensions + Facts (5 min):

Grain: 1 row = 1 user + 1 reel + 1 day
Fact: fct_reels_engagement (ds, user_id, reel_id, country, watch_time_sec, is_completed, device)
Dim: dim_user (user_id, country, age_bucket, SCD Type 2), dim_reel (reel_id, creator_id, category, created_at)
d) Extend to new question (5 min): They will say "Now PM wants to know: which creators drive re-engagement?"
You extend: Add fct_creator_influence or add creator_id to fact, discuss SCD for creator category changing, bridge table for multi-tag.

e) Physical at scale (1 min teaser for next block): "Partition by ds+country"

Fail if: You jump straight to tables without metrics. Product Analytics DEs start with product question, not schema.

3. Analytics & ETL Architecture ∼10 min — Senior IC differentiator
What they said: End-to-end ETL flow, physical models that handle big data at scale, optimize to answer analytical questions.

This is Senior IC test. They will take your model from previous block and ask:

"Now architect it. Source is MySQL social graph, several PB daily, needs to be in warehouse by 9am Bangkok for PMs. How?"

Answer script (use Meta stack names):

Ingestion: "MySQL → Scribe → Scuba (real-time) + Hive (warehouse). Daily incremental scrape. At Meta scale: exabyte-scale platform, ORC files"
Physical model: "Partition fact by ds, bucket by user_id, 256 buckets to avoid hot partitions, ORC + ZSTD, file size 256MB-1GB for Presto"
Optimization: "PM query is WHERE ds=latest AND country='TH' GROUP BY creator_id — partition pruning on ds+country gives 95% scan reduction. Bucketing gives shuffle-free join with dim_user"
Late data + Idempotency: "Store event_time, append partition, dedup job with ROW_NUMBER() OVER (PARTITION BY user_id, reel_id ORDER BY event_time DESC), make job idempotent"
Quality: "Row count + checksum vs source ensures consistency — Meta migrated 100% workload this way"
SLA + Discovery: "Airflow DAG, SLA 9am, alert if delay, register in Nemo catalog — Nemo increased search success 50%"
Say these terms: Presto, Spark, Hive, Scuba, Scribe, Daiquery, ORC, partitioning, bucketing.

4. SQL ∼15 min — Translate English to SQL
What they said: Translate English to SQL constructs, joins (inner/left/right/full/cross), correlated subqueries, aggregations, WHERE vs HAVING, NULLs, CASE.

You will get 1-2 queries on the physical schema you just designed.

Q1 — Correlated subquery (Meta signature): "Users who watched Reels in July AND were active in June"

SQL
SELECT COUNT(DISTINCT user_id) FROM fct_reels_engagement curr
WHERE ds BETWEEN '2022-07-01' AND '2022-07-31'
AND EXISTS (
  SELECT 1 FROM fct_reels_engagement prev
  WHERE prev.user_id = curr.user_id
  AND prev.ds BETWEEN '2022-06-01' AND '2022-06-30'
);

2 lines hidden
Q2 — WHERE vs HAVING + CASE + NULL:
"Average watch time per creator category, only creators with >1000 views, handling null watch_time"

SQL
SELECT 
  r.category,
  AVG(CASE WHEN f.watch_time_sec IS NULL THEN 0 ELSE f.watch_time_sec END) as avg_watch
FROM fct_reels_engagement f
JOIN dim_reel r ON f.reel_id = r.reel_id
WHERE f.ds = '2026-10-06'
GROUP BY r.category
HAVING COUNT(*) > 1000;

3 lines hidden
Key: Explain WHERE filters rows before aggregation, HAVING filters groups after. NULL handling with CASE/COALESCE.

Your 1-hour game plan
0-15 Python: Talk while you type, don't go silent. If bug, debug out loud.
15-30 Modeling: Don't write SQL yet. Spend time on metrics. Draw facts/dims on Excalidraw.
30-40 Architecture: Bring it to scale — partitioning, file format, SLA, quality, privacy. This is Senior bar.
40-55 SQL: Reference tables you just designed. Use joins correctly, mention engine choice: "This would run on Presto for ad-hoc".
One sentence to win Senior IC: After each block, say tradeoff: "I chose daily batch over real-time to unblock PMs faster, then iterated — traded latency for impact."

You have both emails now — Leadership (Scope/Influence/Leadership + AI) and Technical (4 blocks). Want me to run a full mock of the Technical 1-hour right now? I'll play the senior engineer and time each block strictly.

 
  1. “What was your highest-impact project at Makro or Lazada? How did you measure the impact?” 
  2. “Describe a disagreement with a stakeholder. What did you do?” 
  3. “Tell me about delivering under a tight deadline. What did you deprioritize?” 
  4. “How did you mentor someone while giving them ownership?” 
  5. “When multiple engineers contributed, how did you recognize their work?” 
  6. “Tell me about a failure you owned and what changed afterward.”



