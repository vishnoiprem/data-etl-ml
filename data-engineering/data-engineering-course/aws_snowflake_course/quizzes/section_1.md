# Section 1 Quiz — Introduction

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** How many published sections is the visible Snowflake
masterclass curriculum split into (plus one "extra topics"
section)?

- A. 7
- B. 12
- C. 19 + extras
- D. 25

<details><summary>Show answer</summary>

**C — 19 published sections + 1 "extra topics" section.** The
visible curriculum is ~13h 10m of labelled content; the extra
topics section adds another ~5h of advanced material.

</details>

---

**Q2.** Snowflake is best described as a:

- A. Self-hosted Hadoop distribution
- B. Cloud-native SaaS data platform that separates compute from
  storage
- C. Pure in-memory OLTP engine
- D. On-prem appliance

<details><summary>Show answer</summary>

**B — Cloud-native SaaS data platform that separates compute from
storage.** Snowflake runs on AWS, Azure, or GCP; you do not
install or patch it.

</details>

---

**Q3.** Which of the following is **not** a deployment cloud for
Snowflake?

- A. AWS
- B. Azure
- C. GCP
- D. Oracle Cloud

<details><summary>Show answer</summary>

**D — Oracle Cloud.** Snowflake is available on AWS, Azure, and
GCP. It is not available on Oracle Cloud, IBM Cloud, or
on-prem.

</details>

---

**Q4.** The two main cost drivers in Snowflake are:

- A. CPU and RAM
- B. Storage and compute
- C. Network egress and API calls
- D. License fees and support contracts

<details><summary>Show answer</summary>

**B — Storage and compute.** Storage is billed per compressed
TB per month. Compute is billed per-second while a virtual
warehouse runs. Section 3 unpacks the pricing model in detail.

</details>

---

**Q5.** The free trial offered in L05 is:

- A. 7 days, $100 credits
- B. 14 days, $200 credits
- C. 30 days, $400 credits
- D. 60 days, $1000 credits

<details><summary>Show answer</summary>

**C — 30 days, $400 credits.** Most demos in the course run
inside the free trial without modification.

</details>

---

**Q6.** Where in the repo do the working SQL demos live?

- A. `downloads/`
- B. `code/`
- C. `scripts/`
- D. `quizzes/`

<details><summary>Show answer</summary>

**B — `code/`.** The 19 working SQL demos are named like
`s04_loading_data.sql`, one per section. They are designed to
run end-to-end in your Snowflake account.

</details>

---

**Q7.** Where in the repo do the four graded assignments live?

- A. `assignments/`
- B. `code/`
- C. `downloads/`
- D. `diagrams/`

<details><summary>Show answer</summary>

**A — `assignments/`.** The four assignments cover warehouses,
loading, performance, and data sharing.

</details>

---

**Q8.** Which of the following is **not** one of the four
recommended study strategies for this course?

- A. Watch and code in parallel
- B. Use the free trial — don't just watch
- C. Skip the quizzes to save time
- D. Build one end-to-end project alongside the course

<details><summary>Show answer</summary>

**C — Skip the quizzes.** The quizzes are the diagnostic that
tells you whether you actually understood each section. They
are not optional.

</details>

---

**Q9.** The Mermaid diagrams in the repo (architecture, data
sharing, zero-copy cloning, Snowpipe, stream+task, Cortex AI)
live in which folder?

- A. `code/`
- B. `diagrams/`
- C. `downloads/`
- D. `scripts/`

<details><summary>Show answer</summary>

**B — `diagrams/`.** All six diagrams are plain-text Mermaid
and render in GitHub, VS Code, and Obsidian.

</details>

---

**Q10.** Section 1 is best described as:

- A. A hands-on lab covering the `COPY INTO` command
- B. The conceptual foundation — course orientation, study plan,
  resource map
- C. A deep dive into zero-copy cloning
- D. The Cortex AI / ML module

<details><summary>Show answer</summary>

**B — The conceptual foundation.** Sections 2–19 all build on
the orientation, study plan, and resource map we set up here.

</details>
