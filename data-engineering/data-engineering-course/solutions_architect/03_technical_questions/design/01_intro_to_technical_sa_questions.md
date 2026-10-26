# 01 — Intro to Technical SA Questions

> **Lesson 1 of 7 — Technical Questions for SAs** · ~10 min

The 4 question types in the technical SA round, the rubric
for each, and what "passing" actually looks like. The
high-level orientation for the module.

---

## 1. The 4 question types

Technical questions in the SA loop come in 4 shapes. The
names vary by company; the structure is consistent.

| Type | Format | Duration | What it tests |
|---|---|---|---|
| **API design** | Live design, you propose an API for a 2-3 paragraph scenario | 30-45 min | Resource modeling, HTTP semantics, auth, errors, pagination |
| **Database schema** | Live design, you propose a schema for a 2-3 paragraph scenario | 30-45 min | Entity modeling, normalization, indexes, partitioning |
| **Architecture** | Live design, you propose a system architecture (mermaid diagram) for a 2-3 paragraph scenario | 45-60 min | Service choices, data flow, security, scalability, DR |
| **Tradeoff / decision** | Discussion, you defend a service choice against alternatives | 20-30 min | Tradeoff articulation, alternative consideration, "it depends" answer |

The 4 types are tested in 1-3 actual interview rounds,
depending on the company. At AWS, all 4 are covered (often
across 2 rounds). At smaller vendors, 1-2 of the 4 may be
covered in a single round.

---

## 2. The rubric (per type)

### API design rubric

| Signal | What it means |
|---|---|
| **Resource modeling** | Did the candidate identify the right resources and the right relationships? |
| **HTTP semantics** | Did the candidate use HTTP methods and status codes correctly? |
| **Auth model** | Did the candidate design a realistic auth model? |
| **Error model** | Did the candidate design a clear error model? |
| **Pagination / versioning** | Did the candidate think about pagination and API versioning? |
| **Real-world constraints** | Did the candidate center the customer's constraints, not a generic best-practice API? |

### Database schema rubric

| Signal | What it means |
|---|---|
| **Entity modeling** | Did the candidate identify the right entities and the right relationships? |
| **Normalization** | Did the candidate apply the right level of normalization (not over-normalized, not under-normalized)? |
| **Indexes** | Did the candidate identify the right indexes for the hot path queries? |
| **Partitioning** | Did the candidate think about partitioning strategy for scale? |
| **Hot path queries** | Did the candidate center the schema on the hot path queries? |
| **Real-world constraints** | Did the candidate center the customer's scale and access pattern? |

### Architecture rubric

| Signal | What it means |
|---|---|
| **Service choices** | Did the candidate choose the right services for the workload? |
| **Data flow** | Is the data flow clear and efficient? |
| **Security model** | Did the candidate think about encryption, auth, network isolation? |
| **Scalability** | Did the candidate address the scale requirement? |
| **DR** | Did the candidate think about disaster recovery? |
| **Tradeoff articulation** | Did the candidate name the tradeoffs at each major choice? |

### Tradeoff / decision rubric

| Signal | What it means |
|---|---|
| **Defensibility** | Is the choice defensible given the constraints? |
| **Alternative considered** | Did the candidate name the alternative they considered and rejected? |
| **"It depends"** | Did the candidate frame the answer as a function of the constraints, not a one-size-fits-all? |
| **Quantification** | Did the candidate use numbers (latency, cost, throughput), not adjectives? |

---

## 3. The common failure modes

### API design failure modes

- **Endpoints without resources.** Designing `/getCustomer`
  and `/createOrder` instead of `/customers/{id}` and
  `/orders`. This is the most common error.
- **Missing error model.** Designing success cases but
  not error cases. The interviewer asks "what does the
  customer see if the inventory is out of stock?" and the
  candidate has no answer.
- **Generic auth.** "We use OAuth" without specifying how
  it's scoped, what grants are used, how tokens are
  refreshed, etc.
- **No pagination.** Designing endpoints that return
  "all customers" without a pagination strategy.
- **No versioning.** Designing v1 of the API with no
  plan for v2.

### Database schema failure modes

- **Entities missing.** Missing entities the customer
  clearly needs (e.g., not modeling the order-item
  relationship in an e-commerce system).
- **Over-normalized.** Modeling every attribute as a
  separate table. The interviewer asks "how would you
  query the order history" and the candidate describes
  a 5-table JOIN.
- **Under-normalized.** Putting everything in a single
  "events" table with a JSON blob. The interviewer asks
  "how do you enforce referential integrity" and the
  candidate has no answer.
- **No indexes.** Designing tables without thinking about
  the hot path queries. The interviewer asks "how does
  this perform at 10k QPS" and the candidate has no
  answer.
- **No partitioning.** Designing tables without thinking
  about scale. The interviewer asks "what happens at
  100M rows" and the candidate has no answer.

### Architecture failure modes

- **Generic architecture.** Drawing the standard 3-tier
  architecture regardless of the scenario.
- **No service rationale.** Choosing services without
  explaining why.
- **No failure modes.** Designing the happy path only.
- **No security model.** Not thinking about encryption,
  auth, network isolation.
- **No DR.** Not thinking about backup, recovery,
  multi-region.

### Tradeoff failure modes

- **"It depends" without specifics.** Saying "it depends
  on the workload" without specifying what the workload
  needs to look like to make each answer right.
- **No alternative.** Recommending X without naming Y
  (the alternative) and explaining why X over Y.
- **No numbers.** Using adjectives ("fast," "cheap,"
  "scalable") instead of numbers.
- **Over-claiming.** Claiming X is "the best" without
  the constraint context.

---

## 4. The 4 prep modes

Same as the customer-interaction module — 4 modes, most
candidates do only 1-2.

| Prep mode | What it is | Time investment |
|---|---|---|
| **Reading** | Reading lessons like this one | 4-6 hours |
| **Worked cases** | Reading the worked cases in Lessons 03-05 | 2-3 hours |
| **Practice alone** | Designing a new system yourself | 4-8 hours |
| **Practice with friend** | Designing a new system with a friend playing the customer | 4-6 hours |

The candidate who reads all 7 lessons but doesn't design
a new system will fail the round. The behavior is built
in modes 3 and 4.

---

## 5. What "passing" looks like

A "passing" technical round has 4 characteristics:

1. **The design is defensible.** Every choice has a
   rationale, an alternative considered, and a tradeoff
   named.
2. **The design is customer-tailored.** The candidate
   centers the customer's constraints (scale, consistency,
   latency, regulatory), not a generic best-practice
   architecture.
3. **The candidate listens under pressure.** The
   "customer" introduces a new constraint mid-design; the
   candidate adapts without losing the thread.
4. **The candidate uses numbers.** Latency, throughput,
   cost, scale — concrete numbers, not adjectives.

If you hit all 4, the round is in the bag. Move on.

---

## Try it

For each of the 4 question types, answer in writing:

1. **What is the round testing?**
2. **What is my biggest failure mode for this round?**
3. **What is my prep plan for this round?**

If the answer to #2 is "I don't know yet," do the relevant
lessons (02-07) before designing a new system. If the
answer to #3 doesn't include "design a new system
yourself" and "design a new system with a friend," your
prep is incomplete.

The 4 question types are the *content* of the technical
round. The behavior (defending under pressure, using
numbers, listening) is the *quality* of the round. Both
matter.
