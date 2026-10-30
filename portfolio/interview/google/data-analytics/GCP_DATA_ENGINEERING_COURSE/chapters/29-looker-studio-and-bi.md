# 7.3 — Looker Studio & BI

> **Section 7 · Governance, Security & BI · Lecture 7.3 · 8:00**

## 🎯 What you will learn

- What Looker Studio actually is, and where it sits relative to BigQuery and Looker
- The three objects: **reports**, **dashboards**, and **data sources** — and how they differ
- The connector catalogue: BigQuery, Cloud Storage, Sheets, Bigtable, Cloud SQL, and the community connectors
- The data model: the data source, its fields, and the type system
- **Calculated fields** and their dependency ordering — the thing that breaks most models
- The chart types and what each is actually good for
- Exploration and filter mechanics: filters, filter scopes, and drill-down
- Sharing and permissions: viewer vs editor, and report sharing vs data-source permissions
- The performance model: the **data freshness vs query cost** tension, query inspection, and the "don't chart a table you scan on every render" rule
- Looker (the paid product) versus Looker Studio, feature by feature
- When to graduate from Looker Studio to Looker

---

## 🧠 Concept

### What Looker Studio is, precisely

Looker Studio (formerly Google Data Studio) is a **browser-based business intelligence tool**. You connect it to data, build charts, assemble them into reports and dashboards, and share them with people who should see them but should not have query access.

**The mental model:**

> **Looker Studio is a rendering layer over a query engine. It is not a data store.**

This single sentence explains almost everything about the product, including its performance characteristics and its failure modes. When someone asks "why is this dashboard slow?", the answer is almost always "because every chart in it runs its own query against a table that gets scanned from scratch." Looker Studio does not cache results by default, does not have a semantic layer, and does not materialise anything. The charts are just queries.

**Where it sits in the stack:**

```text
┌──────────────────────────────────────────────────────────┐
│  Looker Studio          reports, dashboards, charts      │  ← the BI surface
├──────────────────────────────────────────────────────────┤
│  BigQuery / Bigtable / SQL                              │  ← the query engine
├──────────────────────────────────────────────────────────┤
│  Cloud Storage / Pub/Sub / pipelines                    │  ← the data
└──────────────────────────────────────────────────────────┘
```

**When to use Looker Studio:**

- Free, browser-based reporting over BigQuery and other GCP data.
- Sharing a dashboard with people who need to *see* the data but should not have BigQuery access.
- A small team that needs a handful of operational dashboards and does not want to run a BI platform.
- Ad-hoc exploration that does not need to be a governed, certified artefact.

**When not to use it:** when the same metric appears in twenty reports and must have one definition. Looker Studio has no semantic layer, so a metric defined in one chart can drift from the same metric in another chart. That is the "Looker vs Looker Studio" decision, and it comes down to governance, not features.

### Reports, dashboards, data sources

Three objects, and confusing them causes permission bugs.

**A data source** defines *the data and how to query it*. It holds:
- A **connection** (the connector and its credentials).
- The **schema** — the fields, their types, and their descriptions.
- **Derived fields** — calculated fields, and aggregations.
- Optionally, **filters** and **parameters**.
- **Owner-level permissions** — this is the critical bit.

**A report** is a collection of **chart tiles** and other widgets, plus the layout, the styling, and the **report-level sharing settings**.

**A dashboard** is a **read-only arrangement of tiles pulled from one or more reports**. It is a presentation layer over reports; you cannot edit the charts inside a dashboard, only their layout.

**The ownership model, which is the part people get wrong:**

```text
Data source  (owned by someone, has its own permissions)
    │
    │  used by
    ▼
Report      (owned by someone, has its own permissions)
    │
    │  tiles pulled into
    ▼
Dashboard   (owned by someone, has its own permissions)
```

A dashboard shows a chart that lives in a report. **The viewer of the dashboard needs access to the report's data source, not to the report itself** — unless the report is shared with them. In practice:

- If you share a **report** with someone, they can view it and edit it (unless you set view-only).
- If you share a **dashboard** with someone, they see the tiles but cannot change the charts.
- In both cases, **the data source must also be accessible**, or the charts render empty.

**The classic failure:** you build a report, share it with your team, and they see "no data". The cause is almost always that the *data source's* permissions do not include them. The report's permissions are not enough.

### The connector catalogue

| Connector | Type | Notes and limits |
|---|---|---|
| **BigQuery** | SQL | The primary connector. Supports tables, views, custom SQL, and **parameterised queries**. |
| **Google Sheets** | SQL | Via Drive. Fine for reference data and small manually-curated inputs. The 10 million cell limit applies. |
| **Cloud Storage** | File | CSV, JSON, Parquet. A file, not a query — no aggregation server-side. |
| **Bigtable** | SQL | Limited. Bigtable is not a good Looker Studio source because it has no ad-hoc query layer. |
| **Cloud SQL** | SQL | MySQL and PostgreSQL. Works, but you are querying the database directly — put a view in front of it. |
| **MySQL** | SQL | The connector, independent of Cloud SQL. |
| **PostgreSQL** | SQL | Same. |
| **Google Analytics** | — | GA4, Universal Analytics, Google Ads. |
| **Google Ads** | — | Campaign performance. |
| **Search Console** | — | Organic search performance. |
| **YouTube Analytics** | — | Channel performance. |
| **Bigtable** | SQL | See above. |
| **Community connectors** | Various | Third-party connectors for Jira, HubSpot, Shopify, Snowflake, Salesforce, Zendesk, and more. Built and maintained outside Google. |

**The BigQuery connector is the one that matters, and it has three modes:**

1. **Table reference** — you pick a project, dataset, and table. Looker Studio generates `SELECT * FROM ...`. **This is the simplest and it is a trap**: `SELECT *` on a wide, unpartitioned table is the single most common cause of a slow dashboard.

2. **Custom SQL** — you write the query. This is where you fix the `SELECT *` problem: select the columns you need, filter with a partition predicate, and aggregate server-side so the chart receives 12 rows rather than 4.8 million.

3. **Parameterised query** — custom SQL with `?` parameters bound to report-level filters. This is the most powerful and the least used.

**On the community connectors:** they are genuinely useful, but they run against Google's infrastructure, and the credentials you supply go through a third-party service that Google does not control. **Before using one on a production data source, check what the connector's owner does with the credentials and whether the data transits infrastructure you have not vetted.** This is the same decision as the BigQuery DTS versus a Fivetran-style connector, and the answer is the same: it is a compliance decision first.

### The data model: fields and types

A data source's schema is a list of **fields**, each with:

- A **name** (the column name) and a **description** (shown as a tooltip in the chart builder).
- A **type**, which Looker Studio infers and you can override:
  - **Text / String**
  - **Number (integer or decimal)**
  - **Date** and **Date & Time**
  - **Geo** (country, region, city, postcode, lat/long, map area) — this unlocks the map charts
  - **Image URL**
  - **Hyperlink** — a URL template built from other fields
  - **Duration** (a numeric treated as seconds, formatted as a duration)
  - **JSON** — an object or array field
- An **aggregation** — `Sum`, `Average`, `Min`, `Max`, `Count`, `Count distinct`, `Median`, `Percentile`, `No aggregation`.

**The aggregation setting is where the first misunderstanding happens.** A field with a numeric type can be **aggregated** (it becomes a measure) or **non-aggregated** (it is a dimension). You configure this in the data source:

- `amount_eur` → **Sum**. It is a measure. It can be summed, averaged, plotted on an axis.
- `region` → **No aggregation**. It is a dimension. It can be broken down by, filtered on, put on an axis.

**Getting this wrong produces the classic Looker Studio error**: "The data for this chart is too large to display, or the aggregation is invalid." It happens when you try to plot a non-aggregated numeric field on a scorecard or a pie chart, or when you mix an aggregated measure with a raw dimension in a way that produces a duplicate row per record.

**The Geo type deserves special mention.** A field typed as Geo (country, region, city) is what makes the **filled map, bubble map, and symbol map** charts work. If you use plain text for a country column, the map charts are not offered. And if a geo field contains values that do not match a recognised locality name, the chart silently drops them — a very common and very confusing failure.

### Calculated fields and dependency ordering

A **calculated field** is a new field defined by an expression over existing fields. Looker Studio computes them **in dependency order**, automatically. You do not define the order; the tool builds a dependency graph from the expressions.

**The mechanics, and the trap:**

- A calculated field can reference other **calculated fields**, not just base fields. This is powerful — you can build a layered model.
- **The field's aggregation is inherited from the fields it references**, and it is NOT always what you want. A calculated field like `amount_eur / event_count` derives from two aggregated fields, and Looker Studio decides the aggregation. You can override it in the field's configuration.
- **The type of a calculated field is inferred.** If the expression is a division, you may need to set the type explicitly, and a wrongly-typed calculated field produces an axis that is useless.

**The trap that bites in practice: a calculated field that references an aggregated field and a dimension, used in a chart that also has a breakdown.** The result is either a silent wrong number or the "invalid aggregation" error. The fix is to be explicit about which fields are measures and which are dimensions.

**The performance consequence of calculated fields:** Looker Studio pushes most calculated fields down into the generated SQL, but **some of them are computed after the query returns**. A calculated field that references a field from a *different* data source cannot be pushed down at all, and the tool materialises the whole result set locally before computing. On a large result, that is a timeout.

**A concrete, well-designed calculated field for the course pipeline:**

```text
Revenue per event = amount_eur / event_count
```

That is wrong as written, because `amount_eur` is a sum and `event_count` is a count — dividing two aggregates is valid in Looker Studio, but you must be careful about what it means. The more useful design is to define the metric in BigQuery and expose it as a view, then treat it as a base field in Looker Studio.

**That is the important architectural point:** the further left you push the logic, the better Looker Studio behaves. Define metrics in SQL (or in a Dataform model), expose views, and let Looker Studio consume them. Every calculated field you define in the BI tool is logic that lives outside your version control, outside your tests, and outside your data catalog.

### Chart types, and what each is actually good for

This is where a lot of Looker Studio usage goes wrong, so let me be opinionated.

| Chart | Actually good for | Do not use it for |
|---|---|---|
| **Scorecard** | A single number with a label, and optionally a trend. "Today's revenue: €464,848" | More than two or three tiles; a scorecard is not a table |
| **Bar chart (horizontal)** | Comparing a measure across categories, especially when the category names are long | Time series (use a line chart) |
| **Vertical bar chart (column)** | Comparing a measure across categories with short labels | More than ~15 categories — it becomes unreadable |
| **Line chart** | A measure over time. This is the time-series chart | Categorical comparison without a meaningful x-order |
| **Area chart** | A measure over time where you also want to show volume or composition | Data with gaps; areas imply continuity that may not exist |
| **Combo chart** | Two measures of different units on one chart — e.g. revenue (bars) and conversion rate (line) | Two measures of the same unit — the second axis is confusing |
| **Stacked bar / area** | Composition over time, when the total matters | More than ~5 series; the middle segments become unreadable |
| **Pie chart** | Part-to-whole with 2–4 slices, when you want the proportion to dominate the message | Anything with more than 4 slices, or comparing two pies. **Never** use a pie for more than one group |
| **Donut** | The same as a pie, with a centre total | Same as pie |
| **Scatter chart** | The relationship between two measures, and spotting outliers | Dense datasets — 10,000 points is a smear |
| **Heatmap** | A measure across two dimensions (hour of day × day of week) | Sparse data; the empty cells dominate |
| **Table** | Exact values, multiple measures, drill-down. The most under-used chart type | Very many rows — paginate |
| **Pivot table** | Cross-tabulation of a measure by two dimensions | When a chart communicates better; it is dense and hard to read |
| **Filled map** | A measure by geography | Regional comparison where the map area misleads (a huge territory with one data point) |
| **Bubble map** | A measure by point location, sized by a second measure | Large point counts; they overlap |
| **Symbol map** | Point locations with a category | Dense city-level data |
| **Geo chart (choropleth by postcode)** | Fine-grained geographic distribution | Postcodes with inconsistent formatting |
| **Timeline** | Event sequences over time | Aggregated data |
| **Filter / slider** | A control | The only way to change a chart, if the data source cannot be parameterised |

**Two opinions worth defending:**

**Use tables more than you think.** A table showing 12 rows of per-region revenue is more legible, more precise, and more useful than a bar chart of the same 12 values. People want the number. The chart is for the shape; the table is for the answer.

**Never use a pie chart for anything with more than four slices, and never use two pie charts side by side.** Comparing angles across two pies is a known perceptual failure — human angle comparison is poor, and the second pie is always judged against the first. If you must compare composition, use a stacked bar.

### Exploration and filter mechanics

This is the feature that makes Looker Studio genuinely good: **the chart explorer**.

Click into any chart in the report, and you get an exploration panel where you can:
- Change the dimension and the measure.
- Add a breakdown.
- Change the chart type.
- See the underlying rows.

It is a genuine ad-hoc analysis tool, and it is what makes Looker Studio useful for "just let me look at this one thing" without writing SQL.

**Report filters** have a **scope**, and the scope is the thing that confuses people:

| Scope | Applies to |
|---|---|
| **All data sources in the report** | Every chart in the report |
| **Single data source** | Every chart using that data source |
| **Single chart** | Only that chart |

**The default scope is "All data sources in the report"**, and that is almost always wrong. A report combining two data sources — one BigQuery table, one Sheets reference — with a filter scoped to "all data sources" tries to apply the filter to the Sheets source too, and either fails or silently does nothing useful.

**The other mechanic worth understanding: filters are applied in the generated SQL, before aggregation.** So a report-level filter on `region = 'EMEA'` reduces the rows scanned and the rows aggregated. A filter applied *after* aggregation would not. The distinction matters for the freshness-versus-cost discussion below.

**Parameters** are the better tool for a filter whose value should be driven by the report's URL or a control: a data source can define a parameter (`region` with a default of `EMEA`), a chart can use it in a custom SQL query, and a report can expose a control that sets it.

**Drill-down** works on charts with a dimension. Clicking a bar filters the other charts in the report to that bar's category — the behaviour people expect from every BI tool. This requires the filter scope to be right, so it is worth testing explicitly.

### Sharing and permissions

Three permission levels apply to a report:

| Role | Can view | Can edit the report | Can change the data source | Can share |
|---|---|---|---|---|
| **Viewer** | Yes | No | No | No |
| **Editor** | Yes | Yes | No | Yes (with permissions) |
| **Owner** | Yes | Yes | Yes | Yes |

**The distinction that matters:** in the sharing dialog, "Viewer" and "Editor" apply to the **report**, but the **data source has its own separate permission list**. A user who is a Viewer on a report still needs to be able to read the data source — either directly, or through the report's owner's service account.

**There are two fundamentally different models for how a viewer gets the data:**

**Model A — the viewer reads the data themselves.** The viewer must be granted access to the underlying BigQuery table (or the data source is shared with them). The query runs under the viewer's credentials. Their BigQuery permissions determine what they see, and BigQuery's own row-level security applies. **This is the more secure model** — you cannot accidentally expose data the viewer was not authorised to see, because the query runs as them.

**Model A — the viewer reads the data through the report.** The data source is shared with the viewer, or the report's owner has granted the viewer access to the data source. **This is the common model** and it is also the dangerous one: the viewer gets whatever the *query* returns, and if the query returns a table the viewer was never authorised to see in full, the report leaks it.

**The security rule:** the data returned by a Looker Studio chart must be no more than the viewer is authorised to see, regardless of how the query is authenticated. Looker Studio does not enforce this for you. If you share a report to the whole company, you must verify the query returns only aggregated, non-sensitive data.

**Sharing granularity:**

- **Share a report** → access to that report's pages.
- **Share a dashboard** → access to the dashboard layout and the tiles, read-only.
- **Share a data source** → access to the data source, which makes it available to any report that uses it, in any workspace the user can reach.
- **Share a folder** → a folder containing multiple reports and data sources, with a single permission.

**The most common sharing mistake:** sharing the data source too broadly "so people can build their own reports", which exposes the underlying table to everyone with a Google account in the domain — including people who should only ever see an aggregated dashboard. **Share the dashboard, not the data source, unless building is the point.**

### The performance model: freshness versus cost

This is the section that matters most for a working data platform, so let me build it carefully.

**The mechanics:**

1. **Each chart tile runs its own query.** A report with 12 charts runs 12 queries when it loads. They may be issued in parallel, but each one is independent.
2. **BigQuery bills per TB scanned.** A chart that selects `*` from a 4.8-million-row table scans the whole table. Twelve such charts scan it twelve times.
3. **BigQuery has a query-result cache**, but it is keyed on the exact query text, and it is subject to a cache invalidation window (historically one hour for query results, though this has changed). The practical effect: the *same* query in the same report benefits; *different* queries do not.
4. **Looker Studio's default data freshness** — there is no caching layer of its own beyond BigQuery's, and the "data freshness" setting on the data source controls BigQuery's cache behaviour and the connector's own settings.

**The tension, stated plainly:**

> **The faster your data is, the more queries run, and the more you pay.**

If you want a dashboard to reflect the last five minutes of data, you cannot aggregate it once into a summary table and serve the summary — you must query the detail, on every render, for every chart. If you want it cheap, you must aggregate into a summary table, and then the dashboard is only as fresh as your summary job's schedule.

**This is the central design decision of any Looker Studio deployment, and it has three solutions:**

**Solution 1 — Aggregate in the warehouse.** Materialise a summary table (BigQuery table, view over a partition, or a Dataform model) that is small and pre-aggregated. The chart scans a few hundred rows instead of millions.

```sql
-- The summary table the course pipeline produces.
SELECT
  region,
  event_dt,
  COUNT(*)                  AS event_count,
  ROUND(SUM(amount_eur), 2) AS revenue_eur
FROM `my-project.analytics.events`
GROUP BY region, event_dt
```

**Solution 2 — Partition pruning.** If you must query the detail, add a partition predicate so BigQuery reads only the partitions you need.

```sql
SELECT region, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
FROM `my-project.analytics.events`
WHERE event_dt = @report_date
GROUP BY region
```

A partitioned table with a date predicate reads a tiny fraction of the data. This is the single biggest performance lever you have.

**Solution 3 — Materialised views.** A BigQuery **materialised view** pre-computes the aggregation and is refreshed incrementally. BigQuery then serves the chart from the view with no scan of the base table at all. This is the best answer when the metric is stable and the base table is large.

**The rule that captures the whole thing:**

> **Never chart a table you scan on every render.**

If a dashboard's chart runs `SELECT * FROM events` on every page load, every viewer, every hour, you are paying for a full table scan per chart per viewer per refresh, and you are also making the dashboard slow enough that people stop using it. **Aggregate once, in the warehouse, and chart the aggregate.**

**Measuring it:** BigQuery's query history shows every query a Looker Studio user ran, including the ones the tool generated. Look for:
- Queries with a large `total_bytes_billed` that return few rows.
- The same table scanned repeatedly within a minute (one chart per tile).
- Queries with no partition predicate.

Looker Studio's **"Refresh data"** and the **data source's data freshness settings** control how often the tool re-runs its queries.

**One more performance trap: the "Explore" mode queries the full result set.** When a user clicks into a chart and explores, Looker Studio issues a query to fetch the underlying rows — and by default that can be the *unaggregated* result. On a large table, that query is expensive and slow. This is another reason to point Looker Studio at a summary table rather than a detail table: **the detail table is still reachable through Explore even if the chart itself is aggregated.**

### Looker Studio versus Looker

These are different products from the same vendor, and confusing them causes procurement errors.

| | **Looker Studio** | **Looker** (the paid product) |
|---|---|---|
| **Cost** | Free (Pro features and some connectors cost extra) | Per-user, per-month, by edition |
| **Hosting** | Fully managed by Google | Looker-hosted (Google-managed instance) or self-hosted |
| **Semantic layer** | **None** — each chart defines its own measures | **Yes** — a centrally-defined, version-controlled model |
| **Metric consistency** | Manual — a metric can differ between charts | Guaranteed — one definition, reused everywhere |
| **Governance** | Light | Full: content validation, scheduled delivery, permissions at the model level |
| **Data modelling** | In the data source | LookML in a Git repository |
| **Testing** | None | LookML tests, model tests |
| **Version control** | Not for the model | Git, with a review process |
| **Row-level security** | Via the database | Native, defined in the model |
| **Embedded analytics** | Limited | Yes, with an SDK |
| **Offline / scheduled delivery** | Limited (scheduled email in Pro) | Full — scheduled delivery to email, Slack, and drives |
| **BigQuery** | Yes | Yes |
| **Other databases** | Many connectors | Yes, via connections |

**The decisive difference: the semantic layer.**

In Looker Studio, "revenue" is defined in a chart. If you have twenty reports and each defines "revenue" slightly differently, you have twenty numbers called revenue. Nobody notices until a board slide disagrees with an operational dashboard, and then it is a credibility problem.

In Looker, "revenue" is defined once in LookML, version-controlled, tested, and reused by every explore, dashboard, and tile. Every report uses the same number by construction.

**That is the entire reason to pay for Looker.** It is not the charts, and it is not the SQL — it is **one definition per metric, enforced by the platform**.

### When to graduate from Looker Studio to Looker

The triggers, in the order they usually appear:

1. **Metric drift.** Two reports show different numbers for the same metric and nobody can say which is right. **This is the trigger.** Once you have this, Looker Studio will not fix it — the metrics live in the charts.
2. **Report sprawl.** More than ~30 reports, or more than ~50 people building them. At that point nobody knows what exists, and a semantic layer becomes the catalogue.
3. **Governance requirements.** Regulated organisations need row-level security defined in one place, content validation before publication, and an audit trail of who changed which metric.
4. **Embedded analytics.** Products that need to ship dashboards to their own customers. Looker Studio is not built for this.
5. **Scheduled delivery at scale.** Delivering a personalised report to ten thousand users on a schedule, per-recipient, is a Looker feature and a Looker Studio limitation.
6. **The engineer is the bottleneck.** If every new report needs an engineer to write the SQL, the cost of a BI engineer is higher than the cost of Looker.

**The counter-trigger — stay on Looker Studio when:**

- There are fewer than ~10 reports and ~20 report authors.
- The metrics are simple and mostly stable.
- Nobody is complaining about metric definitions.
- The budget is zero and the deadline is near.

**The migration path, if you graduate:**

1. **Do not port the reports.** Port the *model*. Write LookML that mirrors your existing SQL views — this is mechanical and the SQL you already have is the specification.
2. **Move the metric definitions first.** Get the Looker explores producing the same numbers as the old dashboards. Reconcile them; do not accept "close enough".
3. **Move the dashboards last**, reusing the existing reports as the visual reference.
4. **Keep Looker Studio running during the migration.** Some consumers will not move.

**An intermediate option that is worth knowing:** BigQuery **semantic layer** and **Looker Studio's data source with custom SQL** can bridge the gap. If the problem is only metric consistency and you cannot justify Looker's cost, the cheap fix is to **materialise every metric as a view in BigQuery**, expose the views to Looker Studio, and never define a measure in the BI tool. That gets you one definition per metric without a semantic layer. It is not as good as Looker — there is no LookML, no testing, no RLS — but it solves the most common trigger for a fraction of the cost, and it is the right first move.

---

## 🛠️ Hands-On

### Lab 1 — Looker Studio in the service catalog

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, regions_for, REGIONS, services_by_category

for service_id in ("looker-studio", "looker"):
    service = get_service(service_id)
    print(f"{service.id}: {service.name}")
    print(f"  category     : {service.category}")
    print(f"  summary      : {service.summary}")
    print(f"  pricing      : {service.pricing_model}")
    print(f"  key resources: {', '.join(service.key_resources)}")
    available = regions_for(service_id)
    print(f"  regions      : {len(available)}/{len(REGIONS)}")
    print()

print("Both are in the Analytics category:")
for sibling in services_by_category("Analytics"):
    print(f"  {sibling.id:<24} {sibling.name}")
```

Expected output:

```text
looker-studio: Looker Studio
  category     : Analytics
  summary      : Browser-based business intelligence and dashboarding.
  pricing      : Free per user for reports, with connector and Pro costs.
  key resources: Report, Data Source, Dashboard, Viewer
  regions      : 12/12

looker: Looker
  category     : Analytics
  summary      : Governed semantic layer and business-intelligence platform.
  pricing      : Per user per month, by edition.
  key resources: Model, Explore, Dashboard, Connection
  regions      : 12/12

Both are in the Analytics category:
  biglake                  BigLake
  bigquery                 BigQuery
  bigquery-transfer        BigQuery Data Transfer Service
  composer                 Cloud Composer
  data-catalog             Data Catalog
  dataflow                 Dataflow
  dataform                 Dataform
  dataplex                 Dataplex
  dataproc                 Dataproc
  looker                   Looker
  looker-studio            Looker Studio
  workflows                Workflows
```

### Lab 2 — Model the report → dashboard → data source permission chain

```python
from dataclasses import dataclass, field


@dataclass
class Principal:
    name: str
    is_service_account: bool = False


@dataclass
class Grant:
    principal: Principal
    level: str          # OWNER | EDITOR | VIEWER | NONE
    resource: str


@dataclass
class Resource:
    name: str
    grants: list[Grant] = field(default_factory=list)

    def level_for(self, principal: Principal) -> str:
        best = "NONE"
        order = {"NONE": 0, "VIEWER": 1, "EDITOR": 2, "OWNER": 3}
        for grant in self.grants:
            if grant.principal.name == principal.name:
                if order[grant.level] > order[best]:
                    best = grant.level
        return best

    def can_view(self, principal: Principal) -> bool:
        return self.level_for(principal) in {"VIEWER", "EDITOR", "OWNER"}


alice = Principal("alice@example.com")
bob = Principal("bob@example.com")
carol = Principal("carol@example.com")
sa = Principal("looker-owner@my-project.iam.gserviceaccount.com", True)

data_source = Resource("analytics.events (BigQuery connector)")
data_source.grants = [
    Grant(sa, "OWNER", "data source"),
    Grant(alice, "VIEWER", "data source"),
]

report = Resource("Revenue dashboard report")
report.grants = [
    Grant(sa, "OWNER", "report"),
    Grant(bob, "EDITOR", "report"),
]

dashboard = Resource("Executive dashboard")
dashboard.grants = [
    Grant(sa, "OWNER", "dashboard"),
    Grant(bob, "VIEWER", "dashboard"),
    Grant(carol, "VIEWER", "dashboard"),
]

print("The permission chain")
for resource in (data_source, report, dashboard):
    print(f"  {resource.name:<40} owner: {sa.name}")
    for grant in resource.grants:
        if grant.principal is not sa:
            print(f"      {grant.level:<8} {grant.principal.name}")
print()

print("Who can actually see the data?")
print(f"{'user':<20} {'dashboard':>10} {'report':>8} {'data source':>12} {'can see?':>10}")
for user in (alice, bob, carol):
    dash_ok = dashboard.can_view(user)
    rep_ok = report.can_view(user)
    ds_ok = data_source.can_view(user)
    overall = dash_ok and rep_ok and ds_ok
    print(f"{user.name:<20} {str(dash_ok):>10} {str(rep_ok):>8} {str(ds_ok):>12} "
          f"{str(overall):>10}")
print()

print("carol can view the dashboard but sees NO DATA:")
print("  she lacks access to the report AND to the data source.")
print("  This is the 'shared the dashboard, nothing renders' bug.")
print()
print("bob is an EDITOR on the report and can therefore see the data")
print("through the report, even without a direct data-source grant.")
```

Expected output:

```text
The permission chain
  analytics.events (BigQuery connector)    owner: looker-owner@my-project.iam.gserviceaccount.com
      VIEWER   alice@example.com
  Revenue dashboard report                 owner: looker-owner@my-project.iam.gserviceaccount.com
      EDITOR   bob@example.com
  Executive dashboard                      owner: looker-owner@my-project.iam.gserviceaccount.com
      VIEWER   bob@example.com
      VIEWER   carol@example.com

Who can actually see the data?
user                  dashboard   report  data source   can see?
alice@example.com         False    False         True      False
bob@example.com            True     True        False      False
carol@example.com          True    False        False      False

carol can view the dashboard but sees NO DATA:
  she lacks access to the report AND to the data source.
  This is the 'shared the dashboard, nothing renders' bug.

bob is an EDITOR on the report and can therefore see the data
through the report, even without a direct data-source grant.
```

### Lab 3 — The `SELECT *` performance trap

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

# One chart tile, four ways.
print("One chart tile, four ways — bytes scanned per render")
print(f"{'approach':<46} {'rows to BQ':>11} {'scan (est)':>12}")
print("-" * 74)

# 1. SELECT * on the detail table (the default Looker Studio behaviour).
detail_rows = len(accepted)
detail_scan = sum(len(str(row)) for row in accepted)
print(f"{'SELECT * FROM events (no filter)':<46} {detail_rows:>11,} {detail_scan:>12,}")

# 2. SELECT the columns you need, no predicate.
column_scan = sum(len(str(row["event_id"]) + str(row["region"]) +
                       str(row["amount_eur"])) for row in accepted)
print(f"{'SELECT 3 columns FROM events':<46} {detail_rows:>11,} {column_scan:>12,}")

# 3. With a partition predicate (1 of 24 hourly windows).
partitioned = [r for r in accepted if r["event_dt"][11:13] == "00"]
part_scan = sum(len(str(row["event_id"]) + str(row["region"]) +
                     str(row["amount_eur"])) for row in partitioned)
print(f"{'SELECT 3 columns WHERE event_dt = ...':<46} {len(partitioned):>11,} {part_scan:>12,}")

# 4. Aggregated in the warehouse (the summary table).
summary = aggregate_events(accepted)
summary_rows = len(summary)
summary_scan = sum(len(str(k)) + len(str(v)) for k, v in summary.items())
print(f"{'SELECT from a pre-aggregated summary table':<46} {summary_rows:>11,} {summary_scan:>12,}")
print()

reduction = detail_scan / max(1, summary_scan)
print(f"Approach 4 scans {reduction:,.0f}x less than approach 1.")
print(f"Approach 3 scans {detail_scan / max(1, part_scan):,.0f}x less than approach 1.")
print()

# The multiplier that makes the point: a report has many charts.
CHARTS = 12
VIEWERS_PER_HOUR = 5
print(f"Now multiply: {CHARTS} chart tiles, {VIEWERS_PER_HOUR} viewers per hour")
print(f"{'approach':<46} {'per hour':>14}")
for label, scan in (("SELECT * (detail table)", detail_scan),
                    ("pre-aggregated summary", summary_scan)):
    per_hour = scan * CHARTS * VIEWERS_PER_HOUR
    print(f"{label:<46} {per_hour:>14,} bytes")
print()
print("The summary table is the only approach whose cost does not")
print("scale with the size of the detail table.")
```

Expected output:

```text
One chart tile, four ways — bytes scanned per render
approach                                        rows to BQ   scan (est)
--------------------------------------------------------------------------
SELECT * FROM events (no filter)                     4,800    1,197,976
SELECT 3 columns FROM events                         4,800       89,299
SELECT 3 columns WHERE event_dt = ...                  203        3,781
SELECT from a pre-aggregated summary table               4          213

Approach 4 scans 5,624x less than approach 1.
Approach 3 scans 317x less than approach 1.

Now multiply: 12 chart tiles, 5 viewers per hour
approach                                             per hour
SELECT * (detail table)                            71,878,560 bytes
pre-aggregated summary                                 12,780 bytes

The summary table is the only approach whose cost does not
scale with the size of the detail table.
```

### Lab 4 — The freshness-versus-cost trade-off

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

detail_scan = sum(len(str(row)) for row in accepted)
summary_scan = len(accepted) // 100  # a 100x smaller summary

CHARTS = 12
REFRESHES_PER_HOUR = 4      # how often the dashboard is reloaded
VIEWERS = 20

print("Freshness vs cost — the same dashboard, four refresh strategies")
print(f"{'strategy':<44} {'freshness':>11} {'bytes/hour':>16}")
print("-" * 74)

# A: chart the detail table, refresh every 15 minutes.
fresh_a = "5 min"
cost_a = detail_scan * CHARTS * REFRESHES_PER_HOUR * VIEWERS
print(f"{'detail table, refresh every 15 min':<44} {fresh_a:>11} {cost_a:>16,}")

# B: chart the detail table, refresh hourly.
fresh_b = "1 hour"
cost_b = detail_scan * CHARTS * 1 * VIEWERS
print(f"{'detail table, refresh hourly':<44} {fresh_b:>11} {cost_b:>16,}")

# C: chart a summary table refreshed by a job every 5 minutes.
fresh_c = "5 min"
cost_c = summary_scan * CHARTS * REFRESHES_PER_HOUR * VIEWERS
print(f"{'summary table, job every 5 min':<44} {fresh_c:>11} {cost_c:>16,}")

# D: chart a summary table refreshed hourly.
fresh_d = "1 hour"
cost_d = summary_scan * CHARTS * 1 * VIEWERS
print(f"{'summary table, job hourly':<44} {fresh_d:>11} {cost_d:>16,}")
print()

print(f"C and A have the SAME freshness ({fresh_c}).")
print(f"C costs {cost_a / max(1, cost_c):,.0f}x less.")
print()
print("This is the whole design decision:")
print("  freshness is set by how often the SUMMARY is rebuilt,")
print("  not by how often the dashboard is opened.")
print("  A summary table refreshed every 5 minutes gives 5-minute")
print("  freshness at a fraction of the cost — the aggregation is")
print("  paid for once per refresh instead of once per viewer.")
```

Expected output:

```text
Freshness vs cost — the same dashboard, four refresh strategies
strategy                                       freshness       bytes/hour
--------------------------------------------------------------------------
detail table, refresh every 15 min                 5 min    1,150,056,960
detail table, refresh hourly                      1 hour      287,514,240
summary table, job every 5 min                     5 min           46,080
summary table, job hourly                         1 hour           11,520

C and A have the SAME freshness (5 min).
C costs 24,958x less.

This is the whole design decision:
  freshness is set by how often the SUMMARY is rebuilt,
  not by how often the dashboard is opened.
  A summary table refreshed every 5 minutes gives 5-minute
  freshness at a fraction of the cost — the aggregation is
  paid for once per refresh instead of once per viewer.
```

### Lab 5 — Filter scope and where it is applied

```python
# Where a Looker Studio filter lands in the generated SQL.
# "All data sources" is the default scope, and it is almost always wrong.

GENERATED_SQL = {
    "filter: single chart, single data source": (
        "SELECT region, SUM(amount_eur) AS revenue_eur\n"
        "FROM `my-project.analytics.events`\n"
        "WHERE region = 'EMEA'\n"
        "GROUP BY region"
    ),
    "filter: all data sources in the report": (
        "SELECT region, SUM(amount_eur) AS revenue_eur\n"
        "FROM `my-project.analytics.events`\n"
        "WHERE region = 'EMEA'          -- <-- also applied to the Sheets source\n"
        "GROUP BY region"
    ),
    "filter applied after aggregation (wrong)": (
        "SELECT region, SUM(amount_eur) AS revenue_eur\n"
        "FROM (SELECT region, amount_eur FROM `my-project.analytics.events`) AS t\n"
        "GROUP BY region\n"
        "-- the WHERE would run here, on the already-aggregated result"
    ),
}

print("Where the filter lands — and why it matters")
print()
for name, sql in GENERATED_SQL.items():
    print(f"--- {name}")
    for line in sql.strip().splitlines():
        print(f"    {line}")
    print()
print("Key properties:")
print("  - The filter is pushed INTO the query, BEFORE aggregation.")
print("    So it reduces rows SCANNED as well as rows aggregated.")
print("  - With scope 'all data sources', the filter is applied to")
print("    every source, including ones where the field does not")
print("    exist. That is where 'filter is invalid' errors come from.")
print("  - A filter applied after aggregation would still be correct")
print("    numerically for a SUM, but would not reduce the scan.")
print("    Looker Studio does not do this; BI tools that do, break")
print("    on the freshness story.")
```

Expected output:

```text
Where the filter lands — and why it matters

--- filter: single chart, single data source
    SELECT region, SUM(amount_eur) AS revenue_eur
    FROM `my-project.analytics.events`
    WHERE region = 'EMEA'
    GROUP BY region

--- filter: all data sources in the report
    SELECT region, SUM(amount_eur) AS revenue_eur
    FROM `my-project.analytics.events`
    WHERE region = 'EMEA'          -- <-- also applied to the Sheets source
    GROUP BY region

--- filter applied after aggregation (wrong)
    SELECT region, SUM(amount_eur) AS revenue_eur
    FROM (SELECT region, amount_eur FROM `my-project.analytics.events`) AS t
    GROUP BY region
    -- the WHERE would run here, on the already-aggregated result

Key properties:
  - The filter is pushed INTO the query, BEFORE aggregation.
    So it reduces rows SCANNED as well as rows aggregated.
  - With scope 'all data sources', the filter is applied to
    every source, including ones where the field does not
    exist. That is where 'filter is invalid' errors come from.
  - A filter applied after aggregation would still be correct
    numerically for a SUM, but would not reduce the scan.
    Looker Studio does not do this; BI tools that do, break
    on the freshness story.
```

### Lab 6 — The calculated-field dependency graph

```python
from dataclasses import dataclass, field


@dataclass
class CalculatedField:
    name: str
    expression: str
    dependencies: list[str] = field(default_factory=list)
    aggregation: str = "SUM"
    kind: str = "measure"          # measure | dimension


# A small model of the course pipeline's metrics.
FIELDS = [
    CalculatedField("region", "region", [], "NONE", "dimension"),
    CalculatedField("amount_eur", "amount_eur", [], "SUM", "measure"),
    CalculatedField("event_count", "COUNT(*)", [], "COUNT", "measure"),
    CalculatedField("revenue_eur", "amount_eur", ["amount_eur"], "SUM", "measure"),
    CalculatedField("avg_order_value",
                    "revenue_eur / event_count",
                    ["revenue_eur", "event_count"], "SUM", "measure"),
]


def resolve_order(fields: list[CalculatedField]) -> list[str]:
    """Topologically sort the calculated fields by dependency.

    Looker Studio does this for you, automatically. Doing it
    explicitly matters because it exposes the field you forgot to
    declare a dependency on.
    """
    resolved: list[str] = []
    seen: set[str] = set()
    by_name = {f.name: f for f in fields}

    def visit(name: str, stack: tuple[str, ...] = ()) -> None:
        if name in seen:
            return
        if name in stack:
            raise ValueError(f"circular dependency: {' -> '.join(stack + (name,))}")
        for dependency in by_name[name].dependencies:
            visit(dependency, stack + (name,))
        seen.add(name)
        resolved.append(name)

    for field in fields:
        visit(field.name)
    return resolved


print("Calculated field dependency order")
for i, name in enumerate(resolve_order(FIELDS), start=1):
    f = next(x for x in FIELDS if x.name == name)
    deps = ", ".join(f.dependencies) if f.dependencies else "-"
    print(f"  {i}. {name:<18} deps: {deps:<22} agg: {f.aggregation:<7} {f.kind}")
print()

print("The trap: avg_order_value depends on revenue_eur, which is")
print("itself calculated from amount_eur. Looker Studio resolves this")
print("automatically, but the AGGREGATION it inherits is the trap.")
print("  revenue_eur/event_count with SUM aggregation is meaningless.")
print("  You must override the aggregation to AVG (or use the right")
print("  derived measure), and that override lives in the BI tool —")
print("  outside your version control and outside your tests.")
print()

# The safe alternative.
print("The safe alternative: define the metric in the warehouse.")
print()
print("  CREATE OR REPLACE VIEW analytics.revenue_by_region AS")
print("  SELECT")
print("    region,")
print("    COUNT(*)                   AS event_count,")
print("    ROUND(SUM(amount_eur), 2) AS revenue_eur,")
print("    ROUND(SUM(amount_eur) / COUNT(*), 2) AS avg_order_value")
print("  FROM analytics.events")
print("  GROUP BY region;")
print()
print("  Now Looker Studio sees four plain fields. No calculated")
print("  fields, no aggregation overrides, no drift between charts.")
```

Expected output:

```text
Calculated field dependency order
  1. region             deps: -                      agg: NONE    dimension
  2. amount_eur         deps: -                      agg: SUM     measure
  3. event_count        deps: -                      agg: COUNT   measure
  4. revenue_eur        deps: amount_eur             agg: SUM     measure
  5. avg_order_value    deps: revenue_eur, event_count agg: SUM     measure

The trap: avg_order_value depends on revenue_eur, which is
itself calculated from amount_eur. Looker Studio resolves this
automatically, but the AGGREGATION it inherits is the trap.
  revenue_eur/event_count with SUM aggregation is meaningless.
  You must override the aggregation to AVG (or use the right
  derived measure), and that override lives in the BI tool —
  outside your version control and outside your tests.

The safe alternative: define the metric in the warehouse.

  CREATE OR REPLACE VIEW analytics.revenue_by_region AS
  SELECT
    region,
    COUNT(*)                   AS event_count,
    ROUND(SUM(amount_eur), 2) AS revenue_eur,
    ROUND(SUM(amount_eur) / COUNT(*), 2) AS avg_order_value
  FROM analytics.events
  GROUP BY region;

  Now Looker Studio sees four plain fields. No calculated
  fields, no aggregation overrides, no drift between charts.
```

### Lab 7 — Chart selection against the summary

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)
summary = aggregate_events(accepted)

print("The per-region summary, and the chart that suits it")
print()
print(f"{'region':<8} {'event_count':>12} {'revenue_eur':>14}")
for region in sorted(summary):
    bucket = summary[region]
    print(f"{region:<8} {int(bucket['event_count']):>12,} {bucket['revenue_eur']:>14,.2f}")
print()

n = len(summary)
print(f"Chart selection for {n} categories:")
print(f"  {'chart':<22} {'verdict':<12} {'why'}")
print(f"  {'Bar (horizontal)':<22} {'GOOD':<12} '4 categories, labels are short but readable'")
print(f"  {'Column (vertical)':<22} {'GOOD':<12} '4 categories, fine'")
print(f"  {'Pie':<22} {'MARGINAL':<12} '4 slices is the upper limit; bar is clearer'")
print(f"  {'Line':<22} {'WRONG':<12} 'no meaningful x-order across regions'")
print(f"  {'Table':<22} {'GOOD':<12} 'people want the exact revenue number'")
print(f"  {'Heatmap':<22} {'WRONG':<12} 'needs two dimensions; only one here'")
print(f"  {'Filled map':<22} {'OPTIONAL':<12} 'works, but region area misleads'")
print()

# Now the case that breaks the pie rule.
EVENT_TYPES = ["order", "refund", "page_view", "signup"]
counts = {t: 0 for t in EVENT_TYPES}
for row in accepted:
    counts[str(row["event_type"])] = counts.get(str(row["event_type"]), 0) + 1

print(f"Event types: {len(counts)} categories")
for name, count in sorted(counts.items()):
    print(f"  {name:<12} {count:>6,}  ({count / len(accepted):>6.1%})")
print()
print(f"  {'chart':<22} {'verdict':<12} {'why'}")
print(f"  {'Pie':<22} {'BAD':<12} "
      f"{len(counts)} slices exceeds the 4-slice rule")
print(f"  {'Stacked bar':<22} {'GOOD':<12} 'composition with readable segments'")
print(f"  {'Table':<22} {'GOOD':<12} 'the exact counts, plus the percentages'")
print()
print("And for a time series, the 24 hourly windows:")
from pipeline_logic import bucket_by_window
windows = bucket_by_window(accepted)
print(f"  windows: {len(windows)}")
print(f"  {'chart':<22} {'verdict':<12} {'why'}")
print(f"  {'Line':<22} {'GOOD':<12} 'a measure over a meaningful, ordered x-axis'")
print(f"  {'Area':<22} {'GOOD':<12} 'same, when the total also matters'")
print(f"  {'Column':<22} {'OK':<12} 'acceptable, but 24 bars is a lot'")
print(f"  {'Pie':<22} {'WRONG':<12} 'a pie has no time dimension at all'")
```

Expected output:

```text
The per-region summary, and the chart that suits it

region    event_count    revenue_eur
AMER            1,238     464,848.02
APAC            1,159     421,049.85
EMEA            1,176     432,544.17
LATAM           1,227     445,554.36

Chart selection for 4 categories:
  chart                  verdict      why
  Bar (horizontal)       GOOD         '4 categories, labels are short but readable'
  Column (vertical)      GOOD         '4 categories, fine'
  Pie                    MARGINAL     '4 slices is the upper limit; bar is clearer'
  Line                   WRONG        'no meaningful x-order across regions'
  Table                  GOOD         'people want the exact revenue number'
  Heatmap                WRONG        'needs two dimensions; only one here'
  Filled map             OPTIONAL     'works, but region area misleads'

Event types: 4 categories
  order         1,215  ( 25.3%)
  page_view     1,179  ( 24.6%)
  refund        1,199  ( 25.0%)
  signup        1,207  ( 25.1%)

  chart                  verdict      why
  Pie                    BAD          4 slices exceeds the 4-slice rule
  Stacked bar            GOOD         'composition with readable segments'
  Table                  GOOD         'the exact counts, plus the percentages'

And for a time series, the 24 hourly windows:
  windows: 24
  chart                  verdict      why
  Line                   GOOD         'a measure over a meaningful, ordered x-axis'
  Area                   GOOD         'same, when the total also matters'
  Column                 OK           'acceptable, but 24 bars is a lot'
  Pie                    WRONG        'a pie has no time dimension at all'
```

---

## 🛠️ Common Errors and Fixes

### 1. The report is shared, but the viewer sees empty charts

```text
# Symptom: the viewer opens the report and every chart shows
# "No data" or a blank panel. The owner sees it working fine.
```

**Cause:** the **data source** has its own permission list, separate from the report's. The viewer has access to the report but not to the data source. This is the single most common Looker Studio permission bug.

**Fix:** share the data source with the viewers, or grant them access to the underlying BigQuery table.

```bash
# Grant read on the underlying table to the viewer group
gcloud projects add-iam-policy-binding my-project \
  --member=group:bi-viewers@example.com \
  --role=roles/bigquery.dataViewer
```

Better still, in Looker Studio: open the **data source** → **Manage data source access** → add the group. Note that sharing the data source broadly exposes the underlying table to everyone in it, so scope it or use a view.

### 2. `Invalid dimension` / "The data for this chart is too large to display, or the aggregation is invalid"

```text
Error: The data for this chart is too large to display, or the
aggregation is invalid. Check the data source's field types and
aggregations.
```

**Cause:** a field is typed or aggregated incorrectly. The usual cases: a numeric field is set to **No aggregation** but is used as a measure; a text field is set to **Sum**; or a calculated field inherits an aggregation that does not make sense for the expression.

**Fix:** in the data source's field settings, set the aggregation explicitly. Numeric measures → `Sum` or `Average`. Text and identifiers → **No aggregation**. Dimension → **No aggregation**.

```text
region       -> No aggregation   (dimension)
amount_eur   -> Sum              (measure)
event_count  -> Count            (measure)
user_id      -> No aggregation   (dimension, never Count Distinct on a huge table)
```

### 3. The map chart is empty or drops most of the rows

```text
# Symptom: the filled map renders but many regions have no colour,
# or the chart is entirely blank.
```

**Cause:** two problems, both common.

(a) The field is typed as **Text**, not **Geo**. The map charts are only offered for Geo-typed fields. Change the field type to `Country`, `Region (Geo)` or `City` in the data source.

(b) The location names do not match the recognised locality names. "United Kingdom" is recognised; "UK", "Britain" and "Great Britain" are not. "California" is recognised as a region; "CA" is not.

**Fix:** normalise the values in the warehouse, and use the canonical names Looker Studio recognises.

```sql
SELECT
  CASE
    WHEN country_code IN ('GB', 'UK') THEN 'United Kingdom'
    WHEN country_code IN ('US')        THEN 'United States'
    ELSE country_name
  END AS geo_country,
  COUNT(*) AS event_count
FROM analytics.events
GROUP BY 1
```

### 4. The dashboard is slow and the BigQuery bill is climbing

```text
# Symptom: the dashboard takes 40 seconds to load, and the BigQuery
# cost for the month is 10x what it was last month.
```

**Cause:** each chart tile runs its own query, and the data source is pointed at a wide, unpartitioned detail table with a `SELECT *`. Twelve charts × twenty viewers = 240 full table scans per refresh.

**Fix:** three steps, in order.

1. **Check the queries.** BigQuery → Query history, filtered to the dataset. Look for large `total_bytes_billed` returning few rows.
2. **Point the data source at a summary table or a view**, not the detail table. Materialise the aggregation.
3. **Add a partition predicate** if you must query the detail.

```sql
-- The view the data source should point at
CREATE OR REPLACE VIEW `my-project.analytics.revenue_by_region` AS
SELECT
  region,
  event_dt,
  COUNT(*)                   AS event_count,
  ROUND(SUM(amount_eur), 2) AS revenue_eur
FROM `my-project.analytics.events`
WHERE event_dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY region, event_dt;
```

### 5. The filter is not applied to one of the charts

```text
# Symptom: the user picks "EMEA" in the dashboard filter, and four
# charts update but the fifth still shows all four regions.
```

**Cause:** the filter's **scope**. A report filter scoped to a **single data source** does not apply to charts built on a different source. And a chart with its own filter scope overrides the report-level one entirely.

**Fix:** set the filter scope explicitly. For a report where every chart uses the same data source, scope it to that data source (not "all data sources", which is the default and causes the opposite problem).

```text
Report > layout > filter control > Scope:
  ( ) All data sources in the report
  (•) Single data source: analytics.events
  ( ) Single chart
```

### 6. `400 Bad Request` — the BigQuery data source query fails

```text
Error: Could not query the data source.
Syntax error: Unexpected keyword "SELECT" at [1:1]
```

**Cause:** in the data source's **custom SQL** mode, you pasted the `SELECT` statement into the "Table name" field, or you included a trailing semicolon. Looker Studio's custom SQL expects only the query body, with no trailing semicolon and no wrapping parentheses.

**Fix:** put the bare query in the custom SQL box, with no semicolon. If you need a parameter, use a `?` placeholder and define it in the data source's parameters.

```sql
SELECT region, SUM(amount_eur) AS revenue_eur
FROM `my-project.analytics.events`
WHERE event_dt = ?
```

### 7. Two reports show different numbers for the same metric

```text
# Symptom: the board slide says revenue was €1,832,400 and the
# operational dashboard says €1,798,215, for the same period.
```

**Cause:** metric drift. Looker Studio has no semantic layer, so "revenue" is defined independently in each report's data source — and one of them is filtering on something the other is not (a timezone boundary, a currency conversion, a join to a late-arriving dimension).

**Fix, in order of preference:**

1. **Move the metric into the warehouse.** Create a BigQuery view (or a Dataform model) that defines revenue once, and point every report at it. This solves it for free.
2. **Share the data source** across reports so the definition is literally the same object.
3. **Graduate to Looker** if the metric set is large and needs a governed model with tests.

```sql
CREATE OR REPLACE VIEW `my-project.analytics.revenue_daily` AS
SELECT
  event_dt,
  region,
  COUNT(*)                   AS event_count,
  ROUND(SUM(amount_eur), 2) AS revenue_eur
FROM `my-project.analytics.events`
GROUP BY event_dt, region;
```

### 8. The report shows stale data and the user cannot force a refresh

```text
# Symptom: the numbers are an hour old even though the pipeline runs
# every five minutes.
```

**Cause:** BigQuery's query-result cache. Looker Studio does not have its own cache layer, so it inherits BigQuery's, and BigQuery will serve a cached result for a query whose text is unchanged.

**Fix:** use a **parameterised** query so the query text changes with the filter (which busts the cache), or set the data source's **data freshness** option to query the live data. On a BigQuery connector, setting the freshness to "Live data" disables the cached-result path.

```text
Data source > Advanced options > Data freshness: Live data
```

### 9. `PERMISSION_DENIED` when adding a BigQuery data source

```text
Error: Access denied. BigQuery: User alice@example.com does not have
bigquery.tables.list permission on project my-project.
```

**Cause:** the person creating the data source lacks BigQuery permissions in the project. Looker Studio needs `bigquery.tables.list`, `bigquery.tables.get`, and `bigquery.jobs.create` to enumerate and query the tables.

**Fix:** grant the report builder a scoped role — `roles/bigquery.dataViewer` on the datasets, plus `roles/bigquery.jobUser` at the project level.

```bash
gcloud projects add-iam-policy-binding my-project \
  --member=group:bi-builders@example.com \
  --role=roles/bigquery.jobUser
```

---

## 💡 Production Notes

- **Never point a Looker Studio chart at a wide, unpartitioned detail table.** Each tile runs its own query; `SELECT *` on a 4.8-million-row table, twelve times, per viewer, per refresh. Point the data source at a summary table or a narrow view with a partition predicate.

- **Move metric definitions into the warehouse.** A view per metric is free, version-controllable, testable, and visible in the catalog. A calculated field in the BI tool is none of those things.

- **Share dashboards, not data sources, unless building is the point.** Sharing a data source exposes the underlying table to everyone in it. Share the dashboard for consumption; share the data source for authoring, deliberately and separately.

- **Verify the data source's permissions before you share the report.** The report's permission list is not enough. An empty chart for one viewer is nearly always a missing data-source grant.

- **Use a single data source per report, or set the filter scope explicitly.** The default scope of "all data sources in the report" breaks as soon as a second source appears.

- **Do not use the Explore pane on a detail table.** Exploring a chart issues a fresh, unaggregated query against the underlying rows. Even if the chart itself is aggregated, Explore reaches the detail.

- **Set the data source's freshness to "Live data" when the report must be current**, and accept the cost. Otherwise understand that BigQuery's result cache can serve data that is up to an hour old and that "Live data" changes the bill.

- **Type fields correctly and you will avoid most chart errors.** Geo-typed fields unlock the map charts; numeric fields with `Sum` become measures; dimensions are `No aggregation`.

- **Use tables more than charts.** A table with 12 rows of exact values is more useful than a bar chart of the same 12 values. The chart is for the shape; the table is for the number.

- **Never use a pie chart with more than four slices, and never compare two pies.** Human angle comparison is unreliable, and the second pie is always judged against the first. Use a stacked bar.

- **Watch for metric drift across reports.** When two reports disagree, the fix is a shared view or a shared data source — not a spreadsheet reconciling the two numbers. The disagreement is a credibility incident waiting to happen.

- **If you are heading towards Looker, port the model before you port the reports.** Write LookML that mirrors your existing SQL views, reconcile the numbers exactly, and move the dashboards last. Do not rebuild dashboards first — that is the expensive, low-value way round.

- **The cheapest first step towards a semantic layer is a set of BigQuery views.** You do not need Looker to fix metric drift. You need one definition per metric, and a view is one definition.

---

## 🔑 Key Takeaways

- **Looker Studio is a rendering layer over a query engine, not a data store.** Every chart is a query, and BigQuery bills for the bytes those queries scan.
- **Three objects with three permission lists:** data source, report, dashboard. Sharing a report does not share the data source — the classic "shared it but they see no data" bug.
- **The BigQuery connector has three modes**: table reference (default, and a trap), custom SQL (where you fix the `SELECT *` problem), and parameterised query (the most powerful and least used).
- **A field's aggregation makes it a measure or a dimension.** Numeric + `Sum` is a measure; text + `No aggregation` is a dimension. Getting this wrong causes the "aggregation is invalid" error.
- **Calculated fields resolve in dependency order automatically** — but the inherited aggregation is often wrong, and the override lives outside your version control and outside your tests.
- **Push the logic left.** A metric defined in SQL is tested, versioned, and catalogued. A metric defined in a chart is none of those.
- **Chart choice is a communication decision.** Bars for categorical comparison, lines for time series, tables for exact values, stacked bars for composition, and never a pie with more than four slices.
- **Filter scope matters**: the default "all data sources in the report" is almost always wrong, and filters are pushed into the SQL *before* aggregation — which is why they reduce the scan.
- **Sharing a report is not sharing the data.** The data returned by a chart must be no more than the viewer is authorised to see, regardless of who ran the query.
- **The central tension is freshness versus cost.** The faster the data, the more queries, the more you pay. **Never chart a table you scan on every render** — aggregate once in the warehouse.
- **A summary table refreshed every five minutes gives five-minute freshness at a fraction of the cost**, because the aggregation is paid once per refresh instead of once per viewer.
- **Explore reaches the detail table**, so pointing the chart at a summary does not save you from an expensive Explore query.
- **Looker's only decisive feature is the semantic layer**: one definition per metric, enforced by the platform. That is what you are buying.
- **Graduate when metrics drift, reports sprawl, or governance bites.** The trigger is metric drift, because Looker Studio cannot fix it — the metrics live in the charts.

---

## 📚 Practice Exercises

1. **Permission chain audit.** Using the Lab 2 model, write a function `who_sees_data(dashboard, report, data_source, principals)` that returns, for each principal, whether they can see data and via which path (direct data-source grant, report grant, or dashboard grant). Then design a sharing policy for a report that must show only aggregate data, and explain why sharing the data source directly would be wrong for it.

2. **Query cost model.** Using `cost_model.estimate("bigquery", scanned_tb=...)`, model the monthly cost of a dashboard with 12 chart tiles, 20 viewers, 4 refreshes an hour, against (a) a `SELECT *` detail table of 2 TB, (b) the same table with a partition predicate reading 50 GB, (c) a 100 MB summary table. Then state the break-even number of viewers at which (c) is more than 10× cheaper than (a).

3. **Chart selection audit.** Take the course pipeline's outputs — the per-region summary, the 24 hourly windows, and the event-type counts — and specify the chart type, the dimension, the measure, and the aggregation for each of six dashboard tiles. Then justify each choice against at least two rejected alternatives.

4. **Freshness architecture.** Design a dashboard that must show revenue within five minutes of the data landing, for 50 viewers, over a 10 TB detail table. Specify the BigQuery objects (view, scheduled query, materialised view, or a summary table refreshed by Composer), the refresh interval, and the resulting monthly cost using `cost_model`. Then state the trade-off you made and what you gave up.

5. **Calculated field audit.** Write the Looker Studio calculated fields for a dashboard showing, per region: revenue, event count, average order value, and revenue per hour of the day. For each, state the referenced fields, the required aggregation override, and whether you would instead define it in SQL. Then write the BigQuery view you would actually ship and explain why.

6. **Metric drift forensics.** You have two reports showing different revenue for the same day: €464,848.02 and €461,203.17. Enumerate at least six plausible causes — timezone boundary, a currency conversion applied differently, a join to a late-arriving dimension, a filter on a different date column, a `SUM` versus a `SUM(DISTINCT ...)`, a partition boundary, a cache — and write the diagnostic query that would isolate each.

7. **Looker Studio versus Looker memo.** For a specific organisation of your choosing — say, 40 people, 25 reports, three BI metric definitions that keep disagreeing, and a regulatory requirement for row-level security — write a recommendation comparing Looker Studio, Looker, and the intermediate "views in BigQuery" option. Give the cost, the effort, and the trigger that would make you change the recommendation.

8. **Graduation plan.** Take a team that has decided to move from Looker Studio to Looker. Write the migration plan: which artefacts to build first, the reconciliation procedure that proves the numbers match, the order of the cutover, the rollback, and the specific risk in each phase. State what you would *not* port and why.

---

## 📖 Further Reading

- [Looker Studio Documentation](https://cloud.google.com/looker/docs/studio)
- [Looker Studio — Data Sources](https://cloud.google.com/looker/docs/studio/data-sources)
- [Looker Studio — Calculated Fields](https://cloud.google.com/looker/docs/studio/calculated-fields)
- [Looker Studio — Chart Reference](https://cloud.google.com/looker/docs/studio/charts)
- [Looker Studio — Sharing and Permissions](https://cloud.google.com/looker/docs/studio/sharing-and-permissions)
- [Looker Studio — BigQuery Data Source Performance](https://cloud.google.com/looker/docs/studio/bigquery-performance)
- [Looker Documentation — The Semantic Layer](https://cloud.google.com/looker/docs/what-is-looker)
- [Looker Studio vs Looker — Choosing a BI Tool](https://cloud.google.com/looker/docs/studio/choose)
