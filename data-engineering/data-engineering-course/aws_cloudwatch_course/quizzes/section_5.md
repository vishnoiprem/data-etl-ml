# Section 5 Quiz — Dashboards

> 9 questions, multi-choice, single answer.

---

**Q1.** How wide is the CloudWatch dashboard grid?

- A. 12 columns
- B. 16 columns
- C. 24 columns
- D. 32 columns

<details><summary>Show answer</summary>

**C — 24 columns.** Most widgets use multiples of 4 or 6 for clean alignment.

</details>

---

**Q2.** Where does the coordinate `(0, 0)` sit on a dashboard?

- A. Top-left
- B. Top-right
- C. Bottom-left
- D. Center

<details><summary>Show answer</summary>

**A — Top-left.** Y grows downward, X grows rightward. Widgets cannot overlap.

</details>

---

**Q3.** Is `put_dashboard` idempotent?

- A. Yes — calling it with the same body produces the same dashboard
- B. No — each call appends a widget
- C. Only if you pass `idempotencyToken`
- D. Only inside Lambda

<details><summary>Show answer</summary>

**A — Yes.** `put_dashboard` *replaces* the body. Re-running with the same body is a no-op semantically.

</details>

---

**Q4.** What is the max body size for a dashboard?

- A. 64 KB
- B. 256 KB
- C. 1 MB
- D. 10 MB

<details><summary>Show answer</summary>

**B — 256 KB.** For very large dashboards, split into multiple.

</details>

---

**Q5.** Which `view` renders a number widget?

- A. `timeSeries`
- B. `gauge`
- C. `singleValue`
- D. `bar`

<details><summary>Show answer</summary>

**C — `singleValue`.** Renders one big number, useful for hero metrics. The other views: `timeSeries` (line), `gauge` (dial), `bar` (bars), `pie` (pie).

</details>

---

**Q6.** How do you stack two metric lines into an area chart?

- A. `view: stacked`
- B. `stacked: true`
- C. `type: stacked`
- D. `area: true`

<details><summary>Show answer</summary>

**B — `stacked: true`.** A boolean flag inside the widget's `properties`. Pair with `view: timeSeries` for line; the chart renders as a stacked area.

</details>

---

**Q7.** Which widget type runs a Logs Insights query?

- A. `metric`
- B. `log`
- C. `text`
- D. `insight`

<details><summary>Show answer</summary>

**B — `log`.** Same `properties.query` as the Insights editor. Use `SOURCE '/log/group'` for a raw tail (no query).

</details>

---

**Q8.** Can a dashboard itself span multiple regions?

- A. Yes — the dashboard is global
- B. No — the dashboard is regional; only its widgets can pull cross-region
- C. Only if you use cross-account
- D. Only with `view: timeSeries`

<details><summary>Show answer</summary>

**B — No.** The dashboard is regional. You specify `region` per widget; widgets can pull from any region, but the dashboard's *storage* lives in one region.

</details>

---

**Q9.** What does the `DashboardValidationMessages` response field tell you?

- A. Authentication errors
- B. Warnings about the body (e.g. metric doesn't exist)
- C. The dashboard's full body
- D. The number of widgets

<details><summary>Show answer</summary>

**B — Warnings.** CloudWatch never rejects a `put_dashboard` for a typo; it returns a list of warnings. Always check the list is empty.

</details>
