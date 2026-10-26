# Assignment 4 — Slim CI Pipeline

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Estimated time:** 4-5 hours
> **Sections tested:** 17, 18

## Goal

Build a Slim CI pipeline in GitHub Actions that runs `dbt build` on
every PR using `state:modified+` + the `--defer` flag.

## Steps

1. **Create `.github/workflows/dbt_ci.yml`**:
   - Trigger on `pull_request`
   - Steps: checkout → setup Python → `dbt deps` → download prod
     manifest → `dbt parse` → `dbt list --select state:modified+` →
     `dbt build --select state:modified+ --defer --state ./prod_manifest/`

2. **Configure a Snowflake service account** for CI:
   - Create user `DBT_CI` with `TRANSFORMING` warehouse access
   - Add the public key to the user
   - Store the private key as a GitHub secret `DBT_SNOWFLAKE_PK`

3. **Open a test PR** with a trivial change to one model.
   Verify the workflow:
   - Only the modified model + downstream run
   - Unmodified models use prod tables via `--defer`
   - The full pipeline takes <2 minutes

4. **Add a comment bot** that posts the `dbt run` summary on the PR.

## Bonus

- Add a `merge` deploy job that runs `dbt build` against prod on PR merge.
- Add a cleanup job that drops dev schemas older than 7 days.

## Acceptance criteria

- [ ] `.github/workflows/dbt_ci.yml` exists
- [ ] A test PR triggers the workflow and completes in <2 minutes
- [ ] The workflow uses `state:modified+` (not the full DAG)
- [ ] The `merge` deploy job works on the default branch
