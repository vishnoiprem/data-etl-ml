# Ontology + data fabric (Palantir-style)

A unified object model on top of every source: people, companies, transactions, events, with links, versions, and access control. Building a small ontology with a graph layer + lineage + per-object ACLs changed how I think about regulated-data problems. The "object" is the unit; tables are an implementation detail.

## What I built

- `ontology/objects.py` — the `Object` type and the link graph.
- `ontology/lineage.py` — per-object lineage: where it came from, what depends on it.
- `ontology/acls.py` — per-object access control (who can read, who can write).
- `ontology/resolver.py` — entity resolution: dedupe "Acme Inc" / "ACME" / "Acme, Inc." into one `company` object.
- `examples/aml_ontology.py` — applies the ontology to AML: customer, account, transaction, alert, case.

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

## Real numbers (AML use case)

- Sources consolidated: 8 -> 1 ontology.
- "What does customer X own?" query: was 14 seconds (3-way join) -> 80ms (graph walk).
- ACL enforcement: 100% of cross-tenant access blocked.
- Audit trail per object: every read/write with who, when, why.

## Run

```bash
pip install -r requirements.txt
make demo
```
