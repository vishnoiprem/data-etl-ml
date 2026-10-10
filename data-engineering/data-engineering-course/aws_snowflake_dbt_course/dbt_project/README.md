# dbt_project/

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

The shared runnable dbt project that grows lecture-by-lecture across
the 19 sections of "dbt + Snowflake Analytics Engineering Cert Prep".

## Layout

```
dbt_project/
├── dbt_project.yml                ← project config (materializations, vars, selectors)
├── profiles.yml                   ← Snowflake profile (`mock` target for tests)
├── packages.yml                   ← codegen, dbt_utils, audit_helper
├── selectors.yml                  ← named selector presets (state:modified+, etc.)
├── models/
│   ├── staging/
│   │   ├── _sources.yml
│   │   ├── stg_ethereum__transactions.sql
│   │   └── stg_ethereum__blocks.sql
│   └── marts/
│       ├── transactions.sql       ← enriched transactions (incremental merge)
│       ├── activity.sql           ← daily activity (incremental merge)
│       ├── stablecoin_activity.sql
│       ├── fraud_score.py         ← Python dbt model
│       ├── dag_demo.sql
│       ├── _grants.yml
│       ├── _contracts.yml
│       ├── _versions.yml
│       ├── _access.yml
│       └── _microbatch_config.yml
├── macros/
│   ├── log_macro.sql
│   ├── dry_refactor.sql
│   └── debug_helper.sql
├── seeds/
│   └── static_categories.csv
├── snapshots/
│   └── transactions_snapshot.sql
└── tests/
    ├── generic/
    │   ├── test_positive_value.sql
    │   └── test_accepted_recent.sql
    └── unit/
        └── test_fraud_score_unit.yml
```

## Usage

```bash
# From the course root:
cd aws_snowflake_dbt_course

# Parse-only smoke test (no Snowflake account needed)
dbt parse --project-dir dbt_project --profiles-dir dbt_project \
          --target mock --no-version-check

# Install packages
dbt deps --project-dir dbt_project

# To run against a real Snowflake account, edit profiles.yml with:
#   account, user, private_key_path, database, warehouse
# Then:
dbt run --project-dir dbt_project --target dev
dbt test --project-dir dbt_project
dbt build --project-dir dbt_project --select state:modified+
```
