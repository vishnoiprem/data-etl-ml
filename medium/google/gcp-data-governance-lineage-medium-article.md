# Data Governance on GCP: Catalog, Lineage, and Enforcement That Actually Works

### Dataplex, policy tags, and the Lineage API — with working code, not slideware

*By a Head of AI & Data — lessons from governing multi-country retail data platforms*

---

Every data leader I know has lived this moment: an auditor, regulator, or new CDO asks *"Where does this number come from, and who can see the underlying customer data?"* — and the room goes quiet.

Governance is the difference between answering that question in five minutes and answering it in five weeks. On GCP, the tooling to answer it well has matured dramatically — but most teams still use 20% of it. In this article I'll cover the modern GCP governance stack anchored on **Dataplex**, show how **lineage** actually works (automatic vs manual), and walk through **working code** for the three enforcement layers most teams never implement: tag templates, column-level policy tags, and row access policies.

---

## The Landscape: Data Catalog vs Dataplex

First, let's clear up the naming confusion, because it trips up even senior candidates in interviews.

**Data Catalog** was GCP's original metadata management service — a fully managed catalog that automatically syncs metadata from BigQuery, GCS, Pub/Sub, and Bigtable, and lets you attach business metadata via custom tags and tag templates.

**Dataplex** is the modern, unified answer. GCP folded Data Catalog into Dataplex, making it the single governance layer covering **discovery, classification, data quality, lineage, and access management** across data lakes, warehouses, and lakehouses. It auto-discovers assets across GCS, BigQuery, and Spanner.

> "Dataplex changed governance from reactive auditing to proactive enforcement."

If you're starting today: think Dataplex first, with Data Catalog capabilities living underneath it.

## The Four Pillars of GCP Governance

```
1. Discovery & Catalog  →  Data Catalog / Dataplex
2. Access Control       →  IAM + column-level security + VPC-SC
3. Data Quality         →  Dataplex DQ / Dataflow validation
4. Lineage              →  Data Lineage API / Dataplex
```

Most teams stop at pillar 2 — and only the IAM half of it. The rest of this article is about pillars 1, 2 (the parts you're missing), and 4, with code.

---

## Pillar 1 — Discovery: Tag Templates Are the Whole Game

> "If your Data Catalog has no tag templates, it's just a fancy table list."

A catalog without business metadata answers "what tables exist?" but not "which tables contain PII?", "who owns this?", or "is this gold-tier or someone's scratch table?" Tag templates fix that — a standard taxonomy applied to every asset.

Here's a working example: define a governance tag template and apply it to a BigQuery table.

```python
# tag_template.py
from google.cloud import datacatalog_v1

PROJECT = "my-project"
LOCATION = "asia-southeast1"

client = datacatalog_v1.DataCatalogClient()


def create_governance_template():
    """One-time setup: the org-wide governance taxonomy."""
    template = datacatalog_v1.TagTemplate(
        display_name="Data Governance",
        fields={
            "owner": datacatalog_v1.TagTemplateField(
                display_name="Owning team",
                type_=datacatalog_v1.FieldType(
                    primitive_type=datacatalog_v1.FieldType.PrimitiveType.STRING),
                is_required=True,
            ),
            "domain": datacatalog_v1.TagTemplateField(
                display_name="Business domain",
                type_=datacatalog_v1.FieldType(
                    primitive_type=datacatalog_v1.FieldType.PrimitiveType.STRING),
            ),
            "contains_pii": datacatalog_v1.TagTemplateField(
                display_name="Contains PII",
                type_=datacatalog_v1.FieldType(
                    primitive_type=datacatalog_v1.FieldType.PrimitiveType.BOOL),
                is_required=True,
            ),
            "sla_tier": datacatalog_v1.TagTemplateField(
                display_name="SLA tier",
                type_=datacatalog_v1.FieldType(
                    enum_type=datacatalog_v1.FieldType.EnumType(
                        allowed_values=[
                            {"display_name": "gold"},
                            {"display_name": "silver"},
                            {"display_name": "bronze"},
                        ])),
            ),
        },
    )
    return client.create_tag_template(
        parent=f"projects/{PROJECT}/locations/{LOCATION}",
        tag_template_id="data_governance",
        tag_template=template,
    )


def tag_bigquery_table(dataset: str, table: str):
    """Apply governance tags to a table — call this at ingestion time."""
    resource = (f"//bigquery.googleapis.com/projects/{PROJECT}"
                f"/datasets/{dataset}/tables/{table}")
    entry = client.lookup_entry(
        request={"linked_resource": resource})

    tag = datacatalog_v1.Tag(
        template=(f"projects/{PROJECT}/locations/{LOCATION}"
                  f"/tagTemplates/data_governance"),
        fields={
            "owner": datacatalog_v1.TagField(string_value="data-platform-team"),
            "domain": datacatalog_v1.TagField(string_value="commercial"),
            "contains_pii": datacatalog_v1.TagField(bool_value=True),
            "sla_tier": datacatalog_v1.TagField(
                enum_value=datacatalog_v1.TagField.EnumValue(display_name="gold")),
        },
    )
    client.create_tag(parent=entry.name, tag=tag)
    print(f"Tagged {dataset}.{table}")
```

The operational rule that makes this work: **tag at ingestion time, not as an afterthought.** Make tagging a required step in your pipeline framework — a table that arrives untagged fails the deployment.

---

## Pillar 2 — Access Control: The Three Layers Beyond IAM

A red flag I watch for when interviewing senior candidates: they answer the access-control question with IAM alone. Dataset-level IAM is necessary but nowhere near sufficient. The full stack:

### Layer 1: Column-Level Security with Policy Tags

> "Policy tags in BigQuery are the most underused governance feature — one tag can mask a column across every downstream query."

The model: **Taxonomy → Policy Tag → Column binding.** Tag the `customer_phone` column once, and every query, view, and dashboard downstream respects it — analysts see a masked value, the fraud-engineering group sees the real one.

```bash
# Create a taxonomy and a "PII - High" policy tag (one-time)
gcloud data-catalog taxonomies create \
  --location=asia-southeast1 \
  --display-name="Data Sensitivity" \
  --activated-policy-types=FINE_GRAINED_ACCESS_CONTROL
```

```python
# bind_policy_tag.py — attach the policy tag to a column
from google.cloud import bigquery

client = bigquery.Client()
table = client.get_table("my-project.commercial.customers")

POLICY_TAG = ("projects/my-project/locations/asia-southeast1/"
              "taxonomies/123456/policyTags/789012")  # PII - High

new_schema = []
for field in table.schema:
    if field.name in ("customer_phone", "national_id"):
        field = bigquery.SchemaField(
            name=field.name,
            field_type=field.field_type,
            mode=field.mode,
            policy_tags=bigquery.PolicyTagList([POLICY_TAG]),
        )
    new_schema.append(field)

table.schema = new_schema
client.update_table(table, ["schema"])
print("PII columns now protected by policy tag")
```

Then grant the **Fine-Grained Reader** role on the policy tag only to principals who genuinely need raw values. Everyone else gets masked output automatically — no view sprawl, no duplicated "safe" tables.

### Layer 2: Row-Level Security for Multi-Country Data

The classic retail scenario: one regional `transactions` table, but a Thai analyst must never see Cambodian customer rows. The wrong answer is duplicating tables per country. The right answer is a **row access policy**:

```sql
-- Thai analysts see only Thai rows
CREATE ROW ACCESS POLICY th_only
ON `my-project.commercial.transactions`
GRANT TO ('group:analysts-th@company.com')
FILTER USING (country_code = 'TH');

-- Regional leadership sees everything
CREATE ROW ACCESS POLICY regional_all
ON `my-project.commercial.transactions`
GRANT TO ('group:regional-leadership@company.com')
FILTER USING (TRUE);
```

One table, one pipeline, policy-enforced visibility. Scales to any number of countries by driving the filter from a mapping table instead of hardcoding.

### Layer 3: VPC Service Controls

IAM and policy tags control *who* reads data; **VPC-SC controls *where* it can go** — a perimeter that blocks exfiltration (e.g., copying a BigQuery table to an external project) even by a credentialed insider. For regulated industries this is the layer auditors ask about first.

---

## Pillar 4 — Lineage: Free Where You Can, Instrumented Where You Must

### Automatic lineage (the free part)

Every BigQuery SQL job — scheduled query, dbt model, Dataform run — **automatically emits table-level lineage** to the Data Lineage API. Dataflow pipelines emit lineage automatically too. Enable the API, and the lineage graph in the Dataplex UI populates itself for your SQL estate. You get this for free; take it.

### Manual lineage (the hard part)

Custom pipelines — PySpark on Dataproc, standalone Python ETL — emit nothing unless you instrument them. The Lineage API model has three objects: a **Process** (the job definition), a **Run** (one execution), and **LineageEvents** (the source → target links).

```python
# manual_lineage.py — instrument a custom PySpark/Python job
from datetime import datetime, timezone
from google.cloud import datacatalog_lineage_v1 as lineage

PROJECT = "my-project"
LOCATION = "asia-southeast1"
PARENT = f"projects/{PROJECT}/locations/{LOCATION}"

client = lineage.LineageClient()


def emit_lineage(job_name: str, source_table: str, target_table: str):
    # 1. The Process — the logical job
    process = client.create_process(
        parent=PARENT,
        process=lineage.Process(display_name=job_name),
    )

    # 2. The Run — this execution
    run = client.create_run(
        parent=process.name,
        run=lineage.Run(
            display_name=f"{job_name}-{datetime.now(timezone.utc):%Y%m%d%H%M}",
            state=lineage.Run.State.COMPLETED,
            start_time=datetime.now(timezone.utc),
        ),
    )

    # 3. The LineageEvent — source → target link
    client.create_lineage_event(
        parent=run.name,
        lineage_event=lineage.LineageEvent(
            links=[lineage.EventLink(
                source=lineage.EntityReference(
                    fully_qualified_name=f"bigquery:{source_table}"),
                target=lineage.EntityReference(
                    fully_qualified_name=f"bigquery:{target_table}"),
            )],
            start_time=datetime.now(timezone.utc),
        ),
    )
    print(f"Lineage recorded: {source_table} → {target_table}")


# Call at the end of your custom ETL job:
emit_lineage(
    job_name="spark-customer-enrichment",
    source_table="my-project.bronze.raw_customers",
    target_table="my-project.silver.customers_enriched",
)
```

The operational pattern that makes this sustainable: **don't ask engineers to call this manually.** Wrap your pipeline framework with lineage hooks so every job registers its source-to-target relationships automatically on completion.

> "Lineage you don't automate is lineage that won't exist in 6 months."

---

## Putting It Together: Governance Embedded, Not Bolted On

The biggest mistake I see is treating governance as a separate project — a "governance initiative" running parallel to the platform. It always loses. The pattern that works is embedding each control into the pipeline lifecycle:

```
Bronze ingestion   →  tag templates applied (owner, domain, PII flag)
Silver transform   →  lineage emitted (automatic or hooked)
Gold promotion     →  policy tags enforced, DQ checks gate the publish
Serving            →  row access policies + VPC-SC perimeter
```

A table physically cannot reach the gold layer without tags, lineage, and passing quality checks. That's governance as a property of the platform, not a committee.

---

## Azure Translation (For the Multi-Cloud Crowd)

| GCP | Azure Equivalent |
|---|---|
| Data Catalog / Dataplex | Microsoft Purview |
| Data Lineage API | Purview (Atlas) lineage |
| Policy tags | Column-level security in Synapse / Fabric |
| Row access policies | Row-level security in Synapse / Power BI |
| IAM | Azure RBAC + Unity Catalog grants |

On Databricks, **Unity Catalog** gives you the equivalent in one place — table ACLs, column masking, row filters, and lineage tracking across all Delta tables. The architecture pattern is identical regardless of cloud: **one catalog, one taxonomy, controls enforced in the pipeline.**

---

## Questions Worth Pressure-Testing Yourself On

Whether you're hiring or being hired, these separate surface knowledge from operational experience:

1. How would you handle lineage for a custom PySpark job that doesn't auto-emit?
2. What's the relationship between Data Catalog and Dataplex — and what changed when GCP unified them?
3. How do you enforce PII masking without breaking downstream ML pipelines that legitimately need raw values? (Hint: fine-grained reader grants on the policy tag for the training service account — not unmasked table copies.)
4. In a multi-country setup, how do you design row access policies without duplicating tables?

And the red flags in an answer: IAM-only access control, confusing Data Catalog with Dataplex, no story for manual lineage instrumentation, no mention of tag templates, and treating governance as one-time setup rather than something embedded in every pipeline run.

---

## The Decision Rule, In One Sentence

> **Anchor on Dataplex, take the free lineage BigQuery gives you, instrument the rest through framework hooks, and enforce access in three layers — IAM, policy tags, row policies — at the point of pipeline promotion, never as an afterthought.**

---

*If this was useful, follow for more deep dives on data platform architecture, governance engineering, and lessons from running enterprise-scale retail data systems.*
