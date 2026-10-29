# Ontology + data fabric (Palantir-style)

> **A unified object model on top of every source: people,
> companies, transactions, events, with links, versions, and
> access control.** Building a small ontology with a graph
> layer + lineage + per-object ACLs changed how I think about
> regulated-data problems. The "object" is the unit; tables
> are an implementation detail.

The pattern in this project is what Palantir calls the
"ontology" and what every modern data platform eventually
grows into: a single unified view of the world's objects,
where the objects have identity, links, version history,
and access control — and the underlying tables are an
implementation detail no human has to think about.

The same pattern is what makes a customer's question
"show me every account that touched this sanctions-list
entity, and who at our bank approved the relationship"
answerable in 80ms instead of 14 seconds.

---

## What I built

- `ontology/objects.py` — the `Object` type and the link graph.
- `ontology/lineage.py` — per-object lineage: where it came
  from, what depends on it.
- `ontology/acls.py` — per-object access control (who can
  read, who can write).
- `ontology/resolver.py` — entity resolution: dedupe
  "Acme Inc" / "ACME" / "Acme, Inc." into one `company`
  object.
- `examples/aml_ontology.py` — applies the ontology to
  AML: customer, account, transaction, alert, case.

The split is by concern. `objects.py` is the data model.
`resolver.py` is the entity-resolution layer. `acls.py` is
the access layer. `lineage.py` is the observability layer.
The `examples/aml_ontology.py` is the worked example
showing all four together.

---

## The shape

```
   Sources:        Core Banking  ·  KYC  ·  Sanctions  ·  CRM
                       │           │         │           │
                       └───────────┴────┬────┴───────────┘
                                          │
                                          ▼
                              Entity Resolver (dedupe)
                                          │
                                          ▼
                            Ontology (objects + links)
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                       lineage          ACLs           types
                  (where from?)    (who can read?)   (schema)
```

The **entity resolver** is the magic layer. Without it,
"Acme Inc" in core banking, "ACME" in CRM, and "Acme, Inc."
in KYC are three different objects, and you can't answer
"is this sanctions hit the same Acme as the customer in
core banking?" With it, they're one object with three
source records, and the answer is a graph walk.

---

## The five object types in the AML ontology

The `aml_ontology.py` example defines:

- **Customer** — a person or company. Source: KYC, CRM,
  core banking. Has links to accounts, sanctions hits,
  alerts.
- **Account** — a bank account. Source: core banking. Has
  links to customer, transactions, alerts.
- **Transaction** — a money movement. Source: core banking.
  Has links to source account, destination account, alerts.
- **Alert** — a triggered rule. Source: AML rules engine.
  Has links to transaction, customer, case.
- **Case** — an analyst's investigation. Source: case
  management system. Has links to alerts, customer,
  decisions.

Every object has the same five fields: `id`, `type`,
`version`, `created_at`, `updated_at`. Per-type schemas
extend this. Per-object ACLs ride alongside.

---

## Real numbers (AML use case)

- Sources consolidated: **8 → 1 ontology**.
- "What does customer X own?" query: was 14s (3-way join)
  → **80ms (graph walk)**.
- ACL enforcement: **100%** of cross-tenant access blocked.
- Audit trail per object: every read/write with who, when,
  why.

The 14s → 80ms is the number that gets the customer's
attention. It's also the number that exposes every bad
schema decision you've made; a graph walk is fast only if
the graph is well-modeled.

---

## How to run it

```bash
pip install -r requirements.txt
make demo
```

The `make demo` target:

1. Spins up a local graph DB (Neo4j in Docker, or an
   in-memory emulator for CI).
2. Creates the AML ontology.
3. Loads 1,000 synthetic customers, 5,000 accounts,
   50,000 transactions, 200 alerts, 50 cases.
4. Runs the entity resolver (dedupes 8% of customers).
5. Runs a few sample queries to show the ontology in
   action: "show me every alert for customer X and the
   cases they escalated to."
6. Prints the query latency and the ACL check log.

---

## What this is NOT

- **Not a replacement for a data warehouse.** The
  ontology is the read model. The warehouse is still
  where the data lives. The pattern is "warehouse
  + ontology on top," not "ontology instead of warehouse."
- **Not a knowledge graph for ML.** ML on knowledge
  graphs (link prediction, entity classification) is a
  real field; this project is the
  regulated-data-platform angle, not the ML angle. For
  the ML angle, see
  [`../../ai-engineering/16-graph-rag/`](../../ai-engineering/16-graph-rag/).
- **Not a customer-facing product.** The Palantir
  product wraps this pattern in a deep application
  layer (AIP, Foundry, etc.). This project is the
  data-layer reference, not the product.

---

## Related directories

- [`../scb_aml_platform/`](../scb_aml_platform/) — the
  production-shaped AML build that consumes the
  patterns in this project. The 15-country, MAS 7-year
  retention cousin.
- [`../event-sourced-audit/`](../event-sourced-audit/) —
  the append-only audit log that records every
  read/write on every object. The ontology's
  observability layer.
- [`../multi-tenant-isolation/`](../multi-tenant-isolation/) —
  the per-tenant access control that the ontology's
  ACL layer is built on top of.
- [`../`](../) — the parent `data-engineering/`
  directory. 18 projects; this one is the
  "unified-object view of the world's data" half.
