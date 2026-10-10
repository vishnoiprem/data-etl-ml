# Assignment 06 — DataBrew Profile + Recipe + Job

> **Section:** 10 (DataBrew)
> **Due:** End of week 6
> **Deliverable:** A DataBrew profile (PDF or screenshot), a published recipe (JSON export), and a DataBrew Job that produces a clean Parquet output.

## Objective

Use AWS Glue DataBrew to profile the `city_temperature.csv` data, write a recipe that normalizes the data, and run a Job that outputs clean Parquet. The deliverable proves you can:
- Create a DataBrew dataset and run a data profile.
- Author a DataBrew recipe (visual or JSON) with 3+ transformations.
- Publish the recipe and create a DataBrew Job.
- Run the Job and verify the output.

## Steps

1. **Create a DataBrew dataset** pointing at `s3://<your-source-bucket>/input/city_temperature.csv`. Use the CSV file format.
2. **Run a data profile** — DataBrew's "Profile job" produces a statistical summary (column types, null counts, value distributions, outliers). Save the profile as a PDF or screenshot.
3. **Identify 3 transformations** the data needs. Common candidates from the profile:
   - `FILL_NULLS` on `avg_temperature_uncertainty` with the column's median.
   - `REMOVE_OUTLIERS` on `avg_temperature` (z-score > 3).
   - `NORMALIZE` or `UPPER` on `country` to uppercase.
4. **Author the recipe** — apply the 3 transformations in order. Version the recipe (`v1`).
5. **Publish the recipe** — `Actions → Publish` so it's available to Jobs.
6. **Create a DataBrew Job** — input: the dataset; recipe: the published recipe; output: `s3://<your-target-bucket>/databrew-output/` in Parquet format.
7. **Run the Job** — verify the output has the expected schema and no nulls in `avg_temperature_uncertainty`.
8. **Export the recipe as JSON** for the deliverable.

## Acceptance criteria

- Profile has been run and saved (PDF or screenshot).
- Recipe has 3+ transformations.
- Recipe is published (not in draft).
- DataBrew Job runs and produces Parquet output.
- The output's `avg_temperature_uncertainty` column has 0 nulls (proves the `FILL_NULLS` step ran).
- The output's `country` column is uppercase (proves the `UPPER` step ran).
- Recipe JSON export is included in the deliverable.

## Stretch (optional, 1 hour)

- Add a 4th transformation: `GROUP_BY` and `AGG` to compute the mean `avg_temperature` per `country`.
- Add a DataBrew Job schedule (every Monday at 9am) so the profile is regenerated weekly.
- Use DataBrew's "Project" feature to compare 2 versions of the recipe (e.g., `v1` with median fill vs `v2` with mean fill) and document the difference in your deliverable.
