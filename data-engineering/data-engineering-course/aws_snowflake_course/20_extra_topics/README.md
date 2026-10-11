# Section 20 — Extra topics (L136–L187)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L136–L187
> **Duration:** ~5 h (the largest section in the course)

The published course's "extra topics" section is a catch-all for
the advanced material that doesn't fit the top-level curriculum
list — Tasks, Streams, Materialized Views, Data Masking, Roles
deep-dive, BI Tools, Best Practices, and Bonus lectures. The 19
visible sections (00–18) take you through the operational
foundation; section 19 closes the published list with **Data
Sampling**, and section 20 picks up everything else.

We preserve the original 7 sub-groupings from the published
curriculum so the lecture order matches what students see on the
landing page.

## Sub-groups

### 1. Tasks (L136–L143) — 8 lectures

Scheduled SQL execution inside Snowflake. The same primitive runs
the swap-and-drop pattern from section 17, the daily dev refresh
from L118, and the trigger that fans out stream consumption. We
build tasks from scratch, schedule them with `CRON`, build *trees*
of tasks, call stored procedures, handle errors, and gate execution
with `WHEN` conditions.

| L# | Title |
|---|---|
| L136 | Understanding tasks |
| L137 | Creating tasks |
| L138 | Using CRON |
| L139 | Understand tree of tasks |
| L140 | Creating trees of tasks |
| L141 | Calling a stored procedure |
| L142 | Task history & error handling |
| L143 | Tasks with condition |

### 2. Streams (L144–L154) — 11 lectures

Change-data-capture (CDC) inside Snowflake. A **stream** is an
*append-only* (or change-tracking) view of a table's mutations
between two points in time. We cover `INSERT`/`UPDATE`/`DELETE`
operation metadata, the `OFFSET` column, staleness, the *minimal
set of changes* pattern, the append-only flavor, and the
`CHANGES` clause for raw CDC queries.

| L# | Title |
|---|---|
| L144 | Understanding streams |
| L145 | INSERT operation |
| L146 | UPDATE operation |
| L147 | OFFSET in a stream |
| L148 | Staleness of a stream |
| L149 | Minimal Set of Changes |
| L150 | DELETE operation |
| L151 | Process all data changes |
| L152 | Combine streams & tasks |
| L153 | Append-only streams |
| L154 | Changes clause |

### 3. Materialized Views (L155–L160) — 6 lectures

A **materialized view** is a query whose result is precomputed and
maintained automatically. The trade-off is storage and maintenance
cost versus query latency. We cover what they are, how to use them,
how refresh works, the cost model, when to use them (and when not
to), and the limitations of the feature.

| L# | Title |
|---|---|
| L155 | Understand materialized views |
| L156 | Using materialized views |
| L157 | Refresh materialized views |
| L158 | Maintenance costs |
| L159 | When to use materialized views |
| L160 | Limitations + recap |

### 4. Data Masking (L161–L165) — 5 lectures

Column-level security. A **masking policy** is a SQL expression
that takes a value and returns either the value or a masked
version, depending on the role of the querying user. We build
policies from scratch, attach them to columns, learn how to
unset/replace, alter an existing policy, and walk through real-life
examples (PII redaction, role-based masking).

| L# | Title |
|---|---|
| L161 | Understanding data masking |
| L162 | Creating a masking policy |
| L163 | Unset & replace policy |
| L164 | Alter an existing policy |
| L165 | Real life examples |

### 5. Roles deep-dive (L166–L173) — 8 lectures

Role-based access control (RBAC) in depth. We revisit the system
roles from section 4 and dig deeper: `ACCOUNTADMIN` and its powers,
`SECURITYADMIN` for user/role grants, `SYSADMIN` for warehouses
and databases, the recommended pattern of *custom roles* layered
on top, the often-overlooked `USERADMIN`, and the `PUBLIC` role
that everyone has by default.

| L# | Title |
|---|---|
| L166 | Key concepts (RBAC) |
| L167 | Roles overview |
| L168 | ACCOUNTADMIN + practice |
| L169 | SECURITYADMIN + practice |
| L170 | SYSADMIN + practice |
| L171 | Custom roles + practice |
| L172 | USERADMIN + practice |
| L173 | PUBLIC role |

### 6. BI Tools (L174–L181) — 8 lectures

How Snowflake plugs into the BI ecosystem. **Power BI** and
**Tableau** get their own end-to-end walkthroughs; **Partner
Connect** is the in-Snowflake one-click driver installation; the
**Snowflake Marketplace** is the data-product catalog that doubles
as a free way to consume shares from real data providers.

| L# | Title |
|---|---|
| L174 | Data Visualization (Power BI/Tableau) |
| L175 | Download & install Power BI |
| L176 | Connect Power BI & Snowflake |
| L177 | Working in Power BI |
| L178 | Download & install Tableau |
| L179 | Connect Tableau & Snowflake |
| L180 | Partner Connect |
| L181 | Snowflake Marketplace |

### 7. Best Practices & Bonus (L182–L187) — 6 lectures

The closing lectures consolidate the most important production
patterns: warehouse sizing, table design, monitoring, retention
periods, and a final bonus lecture that ties together everything
covered in the course.

| L# | Title |
|---|---|
| L182 | Best practices |
| L183 | Warehouse Usage |
| L184 | Table design |
| L185 | Monitoring |
| L186 | Retention period |
| L187 | Bonus lecture |

## What comes next

After L187, the course ends. The 4 quizzes for section 20
(`section_20a.md`–`section_20d.md`) are split by sub-group so
each stays manageable in one sitting.