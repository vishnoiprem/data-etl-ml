# RRK Mock Set 4: The Second RRK Round, 60 Minutes

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Format:** one timed interview simulating the **second** RRK round: a different interviewer, who has read the first interviewer's notes and goes deeper on practice, people, pre-sales and a different practical element.
**Why a fourth set:** Sets 1 to 3 leave these thin: a worked legacy-warehouse migration, BigQuery schema-evolution mechanics, Dataform, Looker and row-level security, a security incident on the write path, scoping and estimating, AWS and Microsoft positioning, and developing a strong performer.
**How to use:** 60-minute timer, answer aloud within each block, compare, score with the rubric at the end.

> **Public repo.** No employer names, customer names or real figures. Fill behavioural slots privately. Verify product facts before quoting.

| Min | Block | Type | Topic |
|---|---|---|---|
| 0-3 | 0 | Opening | Your first 30 days in the role |
| 3-12 | 1 | Behavioural | Developing a strong performer; building a diverse team |
| 12-24 | 2 | Technical | Legacy warehouse to BigQuery; schema evolution; Dataform |
| 24-39 | 3 | Practical | Beam stateful-dedup review, then live design of governed self-service analytics |
| 39-48 | 4 | Consulting | A leaked service-account key and an executive who wants it kept quiet |
| 48-55 | 5 | Practice | Scope and estimate a migration; position against AWS and Microsoft |
| 55-60 | 6 | Close | A decision you disagreed with; your questions |

---

## Block 0 (0-3 min): First 30 days

**Q:** "You've accepted. What do you do in your first 30 days?"

**Model answer**
> "Three tracks, with the deliverable for each.
>
> **Listen.** Every senior architect and engineer one-to-one, the top five account teams, two customers mid-engagement and one whose engagement went badly. I'm looking for the gap between how the practice describes itself and how customers experience it. Deliverable: a one-page view of what's working, what isn't, and what I heard that nobody expected.
>
> **Learn the numbers.** Utilisation, margin by engagement type, pipeline by probability, the bench, attrition, certification coverage. Where the practice is losing bids and why. Deliverable: the three metrics I'll run the practice on and the baseline for each.
>
> **Get hands-on.** Build something small on the platform end to end, sit in two architecture reviews as a reviewer, and book the certification. Deliverable: credibility with the people I'm asking to follow me, earned not asserted.
>
> **What I won't do in 30 days:** reorganise, announce a strategy, or change delivery methodology. Day 31 is when I bring the team a diagnosis and ask them to tear it apart."

**Follow-up:** "What if a troubled engagement lands on your desk in week one?" → "Then it's the listening track with a deadline. The 72-hour recovery routine applies, and it's the fastest way to learn how the practice actually works."

---

## Block 1 (3-12 min): Behavioural, developing people

**Q1:** "Tell me about someone you developed from a strong individual contributor into a bigger role. What did you do, specifically?"

**STAR skeleton (fill privately)**
> **S:** "[A senior engineer] was the strongest technologist on the team and the person everyone routed hard problems to. That was the problem: the team's throughput was capped by one person's calendar."
> **T:** "I wanted them leading a domain squad in a year, without losing them to a competitor first."
> **A:** "Four things. I gave them a squad with a real outcome, not a title. I made their first deliverable a design review process the whole team used, so their judgement scaled instead of their hours. I coached on the two gaps I'd seen: delegating work they could do faster themselves, and saying no to stakeholders. And I gave feedback within a day, every time, including when I was wrong about them."
> **R:** "[They lead a squad of N; the squad's outcome metric; what they shipped that I couldn't have]. **The miss:** [e.g. I waited a quarter too long to move them, because I was protecting my own delivery]."

**Q2:** "How have you built a diverse team, concretely?"
> "Concretely means process, not intent. [Fill privately with one of: a structured scorecard that replaced 'culture fit'; a rule that every shortlist had at least two candidates from under-represented groups before interviews started; sourcing from communities we hadn't used; a panel that wasn't all senior men; a metric I tracked and reported.] The result I can point to: [a hiring or retention metric that moved]. The one I'd do differently: [one honest thing]."

**Follow-ups the interviewer will use**
1. "Name the moment you knew they were ready." → a decision they made without you that you'd have made differently, and theirs was better.
2. "What did it cost your delivery?" → a real number or a real slip.
3. "What's your leadership philosophy in one sentence?" → have one. Example: "Set the bar in writing, give people outcomes not tasks, and give feedback the same day."

---

## Block 2 (12-24 min): Technical, legacy warehouse migration

**Q:** "A bank runs a 15-year-old on-premises warehouse: about 40 TB, 3,000 tables, 1,200 ETL jobs in a proprietary tool, stored procedures everywhere, and a regulator who wants data in-country. They want to be on BigQuery in 12 months. How?"

**Model answer**
> "**Restate:** a reversible migration of a regulated warehouse in 12 months, in-country. Questions: what's driving 12 months, a licence end or a board date? How many of the 3,000 tables and 1,200 jobs are actually used? Who can authorise retiring one? That last answer sets the schedule more than any technology does.
>
> **Prepare.** Inventory first: query logs for the last 90 days give me table usage; job lineage gives me dependency order; stored-procedure complexity gives me the translation risk. Typically a large share of tables and jobs are dead or duplicate, and I want that number before I estimate anything.
>
> **Options.** A, lift and shift the whole estate with automated SQL translation: fastest, but it carries the mess and the cost model of the old platform into the new one. B, redesign everything: the right end state, won't fit 12 months. C, **waves by domain**, each a vertical slice, with automated translation where the SQL is simple and redesign where it isn't, plus a stabilisation lane for whatever can't be redesigned in time. **Recommend C.**
>
> **Mechanics on Google Cloud.** BigQuery Migration Service for assessment and batch SQL translation, with a translation-quality gate: anything below a threshold is hand-reviewed. Stored procedures become Dataform or scheduled SQL where they're transformation logic, and a service outside the warehouse where they're application logic. Data transfer by an initial bulk load and then incremental CDC until cutover. Regional datasets, CMEK, VPC Service Controls, org-policy location constraints for the regulator.
>
> **Cutover.** Dual-run per wave, including a month-end, reconciling counts, sums, checksums and KPI parity signed off by the business owner. Cutover behind a view switch so rollback is one statement. Old platform read-only for a defined period, then decommissioned as a funded deliverable.
>
> **Plan.** Months 1 to 2: inventory, landing zone, wave plan, regulator conversation started. Months 3 to 4: lighthouse domain end to end. Months 5 to 10: remaining waves, partner doing factory translation, we own architecture and quality. Months 11 to 12: decommission and hypercare.
>
> **Risks.** Translation quality on complex procedures, consumers nobody knew about, retirement with no incentive. **Measures:** reconciliation defects per wave, adopters per wave, residency violations at zero, and old-platform cost going to zero on the planned date."

**Follow-up A:** "Monthly schema changes keep breaking the new pipelines. How do you handle schema evolution on BigQuery?"
> "Classify every change as compatible or breaking, and treat them differently. Compatible: adding a nullable column, relaxing required to nullable; BigQuery allows these in place, and loads can be configured to add columns. Breaking: dropping, renaming or changing a type; BigQuery won't change a type in place, so it's a new column plus backfill plus a consumer migration, or a new table version behind the view. Mechanics: avoid schema autodetect in production because it guesses types from a sample; use an explicit schema with a contract check at ingest; write new versions of a table and repoint the view rather than mutating in place; in Dataform, assertions on the contract so a drift fails the run before it reaches consumers. The organisational half: a producer who changes a schema owns telling the consumers. That's a data contract, and it's the part that actually stops the breakage."

**Follow-up B:** "Where does Dataform fit versus Dataflow versus Dataproc?"
> "Dataform is SQL transformation inside BigQuery with dependencies, assertions and version control: the right tool for warehouse-style ELT and for most of those 1,200 jobs. Dataflow is for streaming and for processing that has to happen before data lands, or that SQL can't express. Dataproc is for existing Spark code the customer isn't ready to rewrite, run as ephemeral clusters or serverless, not as a permanent Hadoop replacement. My default is BigQuery-native unless there's a specific reason, because every extra engine is an operating cost the customer carries for years."

---

## Block 3 (24-39 min): Practical

### 3a. Beam code review (6 min)

"This is a stateful dedup step in a streaming Dataflow pipeline. Review it."

```python
class Dedup(beam.DoFn):
    SEEN = BagStateSpec('seen', StrUtf8Coder())

    def process(self, element, seen=beam.DoFn.StateParam(SEEN)):
        key, event = element
        if event['id'] in list(seen.read()):
            return
        seen.add(event['id'])
        event['processed_at'] = datetime.now().isoformat()
        yield json.dumps(event)
```

**Model review (order: correctness, idempotency, scale, semantics, security, maintainability)**
> "1. **Unbounded state.** Nothing ever clears `seen`. Every key's state grows forever, so this job's state size, checkpoint time and cost grow with total event history until it falls over. Fix: an event-time timer that clears the bag after a dedup horizon tied to the measured lateness, or a TTL.
> 2. **Scale.** `list(seen.read())` materialises the whole bag on every element: O(n) per event per key. It should be a set-like check; keep the bag small via the timer, or use a value state holding a compact structure.
> 3. **Correctness of the key.** Dedup state is scoped by `key`. If `key` isn't the dedup domain, say the key is `merchant` and `id` is a transaction, then the same `id` under two keys isn't deduped, and a hot key concentrates all the state and all the work on one worker.
> 4. **Non-deterministic output.** `datetime.now()` is processing time. On a retry or a replay the same input yields a different output, so downstream can't dedupe on content and backfills don't reproduce. Use event time, or the window's timestamp, and keep processing time only as metadata.
> 5. **Semantics.** Deduping on `id` alone keeps the first version seen; a later update to the same `id` is dropped. If updates exist, dedup on `(id, version)` or keep the latest.
> 6. **Failure handling.** A missing `id` key raises and fails the bundle, which retries the whole bundle. No dead-letter path.
> 7. **Maintainability.** Emits a JSON string, so the schema is lost for the next step. Emit a typed row. No tests for duplicate, late, missing-field cases.
>
> **Sentence to say:** 'This dedups correctly for the first hour and then becomes the pipeline's own outage. Fix the state horizon first, then determinism, then the key.'"

**Follow-up:** "The engineer says state is cheap and they'll add the timer later." → "State is cheap; a job that can't checkpoint in time isn't. And 'later' in streaming means after the incident. The timer is ten lines; I'd block the merge on it."

### 3b. Live design (9 min)

**Q:** "A retail group wants self-service analytics for 2,000 business users across five countries, with one definition of revenue, and country managers only seeing their own country's data. Design it."

**Model answer**
> "**Outcome:** 2,000 people making decisions on numbers they trust and are allowed to see, without a central team in the loop. **NFRs to confirm:** concurrency at peak, acceptable dashboard latency, residency per country, how often definitions change, and who arbitrates when two countries define margin differently. That last one is a governance question and it decides whether this project succeeds.
>
> **Draw it.** Sources into BigQuery, raw then curated, per-country datasets in regional locations where residency requires it, and a group-level curated layer where it doesn't. On top, one semantic layer in Looker: LookML holds the single definition of revenue, margin and the other governed metrics, with a named business owner per metric and a change process. Row-level security enforced in BigQuery with row-access policies keyed on country, mapped to identity groups, so the rule holds whichever tool queries the table, not only in Looker. Column-level security via policy tags for personal data. Dataplex for the catalogue, lineage and quality scans, so a user can see where a number came from and whether it's fresh. BI Engine or materialised views for the hot dashboards.
>
> **Failure path.** The one that kills self-service is two numbers for the same metric. Prevention: metrics defined once in LookML, certified content marked, uncertified content allowed but labelled, and freshness and quality status shown on the dashboard itself.
>
> **Security.** Access through groups, never individuals; row and column policies in the warehouse; audit logs on who saw what; VPC Service Controls around the datasets; service accounts for the BI tool with no standing human access to raw.
>
> **Cost.** Partitioning and clustering on the curated layer, `maximum_bytes_billed` on ad-hoc, BI Engine for repeated aggregates, and showback per country so the cost is visible to the people generating it.
>
> **Operating model.** A platform team owns standards, the semantic layer and security. Each country has a data steward who owns their definitions within the group framework. Adoption measured as weekly active users of certified content, and the number of 'which number is right' tickets, which should fall to near zero.
>
> **Trade-offs.** I rejected one global dataset for everything: residency and blast radius. I rejected per-country Looker instances: five definitions of revenue by month three. I rejected enforcing row security only in the BI tool: the first analyst with SQL access bypasses it."

**Follow-up:** "A country manager insists their revenue definition is right and the group's is wrong." → "Then it's a decision for the metric owner and the CFO, not for me and not for the dashboard. I give them both definitions side by side with the difference quantified, and the group definition stays certified until the owner changes it. What I won't do is publish both as 'revenue'."

---

## Block 4 (39-48 min): Consulting, a security incident

**Q:** "On a live engagement, a service-account key with write access to the customer's BigQuery datasets is found in a public code repository. Nobody knows yet if it was used. The customer's programme director asks you to fix it quietly and not involve their security or compliance teams because it would delay go-live. What do you do?"

**Model answer**
> "**First hour, regardless of the conversation:** rotate and disable the key, and check the audit logs for any use of it: what was read, written or exported, from which IPs, since when. Containment isn't a decision; it's the job.
>
> **Then the programme director.** I'd say it plainly: I can't agree to keep this from the customer's security team, and I'd explain why in their terms, not mine. If that key was used, this is potentially a notifiable incident under the local data-protection law and under the regulator's technology-risk rules, with deadlines measured in hours and days. A go-live delayed by a week is recoverable. A regulator finding that a breach was known and concealed isn't, for them or for us. I'd also say that our own policy requires me to report it, so this isn't a choice I'm making against them.
>
> **How I keep trust.** I don't go around them; I go with them. I offer to join the call to their CISO, bring the audit-log evidence, and present the containment already done. I frame it as 'here's what happened, here's what we've done, here's what we don't yet know'. Most leaders say no to an escalation they imagine and yes to one they can see.
>
> **Root cause and prevention.** Why was there a long-lived key at all? The fix is structural: Workload Identity Federation or short-lived credentials, no keys in repos enforced by secret scanning in CI, least-privilege service accounts per pipeline, VPC Service Controls so a leaked credential can't exfiltrate outside the perimeter, and the write path owned by one identity with an audit trail.
>
> **Impact on the engagement.** I'd re-plan go-live openly with the sponsor, with the incident as the reason. And I'd ask whose code repository it was. If it was ours, I say so first.
>
> **Measure:** time to contain, confirmation of use or non-use from logs, notification made within the window if required, and zero long-lived keys at the end of the remediation."

**Follow-up:** "The programme director says they'll escalate to your leadership that you're being difficult." → "I'd say that's fine, and I'd call my leadership first so they hear it from me with the facts. Being escalated for reporting a security incident is a conversation I'm comfortable having."

---

## Block 5 (48-55 min): Practice, scoping and positioning

**Q1:** "An account team asks you to estimate the migration from Block 2 for a proposal due in two weeks. How do you scope and estimate it, and how confident is the number?"

**Model answer**
> "**Scope first, then estimate; never the other way around.** In two weeks I can't inventory 3,000 tables, so the proposal is a **two-phase offer:** a fixed-price discovery and architecture phase of 4 to 6 weeks that produces the inventory, the wave plan and a firm estimate, then delivery priced from that inventory, time-and-materials or capped per wave.
>
> **The estimate for the proposal is a range, bottom-up by wave.** Drivers: number of live tables and jobs after retirement, translation complexity distribution from the assessment tool, number of consumers to migrate, reconciliation effort per domain, and the dual-run infrastructure cost. I'd apply the practice's actuals from similar engagements for productivity rates, and contingency sized to the unknowns, higher on the stored-procedure estate.
>
> **Delivery model.** We own architecture, the lighthouse, quality gates and cutover. A partner does the factory translation under our standards. That protects margin and gives the customer the right people on the risky parts.
>
> **Assumptions and exclusions in writing:** retirement authority exists, source access in week one, a named business owner per domain, no scope added mid-wave without a change request.
>
> **Confidence:** the discovery price is firm. The delivery number is plus or minus 30% until the inventory exists, and I'd say exactly that to the customer rather than hide it in contingency. Customers trust a range with a method more than a point with none."

**Q2:** "They're also considering AWS and Microsoft. How do you position, and when would you not bid?"
> "**Honestly, by workload.** Where the customer's estate is already deep on one of them, the switching cost is real and I'd say so. **AWS:** strong breadth and a mature ecosystem; the data stack is more assembled from parts, so the customer carries more integration and operations. **Microsoft:** strong where the enterprise lives in Microsoft 365 and Power BI; the unified analytics platform is compelling for that audience, and it's newer, so I'd be candid about maturity in large, regulated migrations. **Where we're strongest:** serverless analytics with no cluster sizing, AI and generative AI tightly integrated with the data without moving it, streaming at scale, a governed semantic layer, and open formats that reduce lock-in. I tell the customer where we're weaker, because they'll find out anyway and trust is the asset.
>
> **When I wouldn't bid:** no executive sponsor for a business outcome, a residency or regulatory requirement we can't meet, a timeline that only works if nothing goes wrong, or a margin that only works if the partner delivers for free. A clean no-bid costs a quarter; a bad win costs a year."

**Follow-up:** "How do you make the practice repeatable, so it scales beyond you?" → "Assets: a migration accelerator with reconciliation and translation gates baked in, reference architectures with the governance already drawn, and a discovery playbook. Enablement: certification targets and architecture reviews that teach. Partner leverage: partners do volume under our quality gates. The measure is the share of an engagement delivered from reusable assets, rising quarter on quarter."

---

## Block 6 (55-60 min): Close

**Q:** "Briefly, a decision you disagreed with, and what you did."
> "[Fill privately.] Structure: the decision, why I disagreed, how I argued it with evidence and a recommendation rather than a veto, the outcome, and that once decided I committed fully and said so to my team. If I turned out to be wrong, say that; it scores higher than being right."

**Your questions (pick two)**
1. "What did the practice learn from its hardest engagement in the last year?"
2. "How does the practice decide which opportunities not to bid?"
3. "What would you want the person in this role to have changed by this time next year?"

---

## Scoring (0 to 2 per line, 8 per block, 48 total for blocks 0 to 5)

| Line | 0 | 1 | 2 |
|---|---|---|---|
| Structure | Jumped to a solution | Some clarifying | Restated, clarified, stated assumptions, then options |
| Judgement | Component list or "it depends" | Options, weak pick | 2 to 3 options, trade-offs, a clear recommendation |
| Evidence and numbers | Vague | Some figures | Defensible numbers with baseline, method and your role |
| Enterprise scope | Single project | Mentions operations | Ownership, adoption, rollback, decommission, cost |

**Targets:** 36 or more of 48 is ready. 27 to 35: repeat the weakest two blocks. Under 27: restudy `ROUND_1_RRK_TOPIC_DEEP_DIVE.md` first.

**Hard fails for this round specifically:** agreeing to keep the incident quiet in any form; a point estimate with no range or method; positioning that only lists competitor weaknesses; a people story with no named mechanism and no cost to you.
