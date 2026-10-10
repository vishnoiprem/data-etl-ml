# Section 10 — DataBrew (Lectures L78-L85)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles the 8 lecture scripts (L78-L85) for Section 10 — DataBrew.

---

## L78 — Section Overview (DataBrew) (1:43)

> "Section 10 is AWS Glue DataBrew — the no-code sibling of Glue Jobs. Same data sources, same Data Catalog, but the transformations are visual (point-and-click) and the output is a *recipe* (a versioned collection of steps). The 4 things we'll do: 1) create a DataBrew dataset, 2) run a data profile, 3) author a recipe, 4) create a DataBrew Job that outputs Parquet."

Note: the syllabus has the section overview at L78. The remaining 7 lectures in this section (DataBrew 101, profile, project, recipe, recipe publish, job, job run) are also covered here as the bundled script — the individual lecture files will be split before Udemy launch.

---

## L79 — DataBrew 101 (3:33)

> "DataBrew is the no-code data preparation service. The 4 entities: 1) *Dataset* — a connection to your data (S3, JDBC, Glue Catalog table). 2) *Profile job* — runs a statistical summary over the dataset. 3) *Project* — a working copy of a dataset, with a recipe applied. 4) *Recipe* — a versioned collection of transformations. 5) *Recipe job* — runs the recipe on the dataset, writes the output. The 250+ transformations are categorized: cleanup, enrichment, reshaping, filtering, etc. The most common: `FILL_NULLS`, `REMOVE_DUPLICATES`, `REMOVE_OUTLIERS`, `NORMALIZE`, `UPPER`, `LOWER`, `TRIM`, `SPLIT`, `JOIN`, `GROUP_BY`, `AGG`, `PIVOT`."

Key bullets: 4 entities; 250+ transformations; visual authoring.

---

## L80 — Create DataSource and Profile Data (3:57)

> "Create a DataBrew dataset. DataBrew → Datasets → Connect new dataset. Source: S3. Path: `s3://<source-bucket>/input/city_temperature.csv`. Format: CSV. Header row: yes. Click 'Create dataset'. Then create a Profile Job: DataBrew → Profile jobs → Create profile job. Name: `city-temperature-profile`. Dataset: the dataset you just created. Output: `s3://<target-bucket>/databrew/profile/`. IAM role: create a new DataBrew role with S3 access. Run the job. The job takes 2-3 minutes and produces a PDF profile with column types, null counts, value distributions, and outliers."

Lab: create the dataset, create + run the profile job, save the PDF.

---

## L81 — Create Project and Review Data Profile Output (4:27)

> "Create a DataBrew project. DataBrew → Projects → Create project. Name: `city-temperature-clean`. Recipe: create a new recipe (`recipe-v1`). Dataset: the dataset. The project opens in the visual editor. On the right side, you see the data profile: column types, value distributions, missing values, outliers. Note the issues: 1) `avg_temperature_uncertainty` has some nulls (about 5% of rows), 2) `avg_temperature` has a few outliers (z-score > 3), 3) `country` is mixed case (some uppercase, some lowercase). These are the 3 transformations we'll apply."

Lab: review the profile; identify the 3 issues.

---

## L82 — Create and Publish Recipe (4:33)

> "Author the recipe in the visual editor. For each row, click the column, choose a transformation, and configure. The 3 steps: 1) FILL_NULLS on `avg_temperature_uncertainty` with the column's median. 2) REMOVE_OUTLIERS on `avg_temperature` with z-score > 3. 3) UPPER on `country`. The recipe is automatically versioned. Click 'Publish' to make the recipe available to Jobs. Note: the recipe is a JSON document in S3 — you can export it for code review."

Lab: apply the 3 steps, publish the recipe, export the JSON.

---

## L83 — Create Job by Using Published Recipe (4:50)

> "Create a DataBrew Job. DataBrew → Jobs → Create job. Name: `city-temperature-clean-job`. Recipe: `recipe-v1` (the published one). Dataset: the same dataset. Output: `s3://<target-bucket>/databrew/clean/`. Output format: Parquet. IAM role: the same DataBrew role. Run the job. The job takes 2-3 minutes and writes Parquet output. Verify: `aws s3 ls s3://<target-bucket>/databrew/clean/`. You should see a `.parquet` file."

Lab: create + run the Job, verify the output.

---

## L84 — Run Job + Verify Output (already covered in L83)

> "Walk through the output. The Parquet file has the same schema as the input, with: 1) 0 nulls in `avg_temperature_uncertainty` (proves the FILL_NULLS step ran), 2) 0 outliers in `avg_temperature` (proves the REMOVE_OUTLIERS step ran), 3) all uppercase values in `country` (proves the UPPER step ran)."

---

## L85 — Recap (DataBrew) (2:00)

> "Section 10 takeaways. One: DataBrew is the no-code sibling of Glue Jobs. Two: 5 entities — Dataset, Profile, Project, Recipe, Job. Three: 250+ transformations, organized into 6 categories. Four: recipes are versioned and publishable. Five: the output is a Parquet (or CSV/JSON) file in S3. DataBrew is *not* a replacement for Glue Jobs — it's for analysts and data scientists who don't want to write PySpark. Glue Jobs are for DEs who need programmatic, version-controlled, production-grade ETL."

---

## Section 10 Quiz

5 questions, see `quizzes/section_10.md`.

---

## Section 11 — Role Plays (L86-L88, 3 lectures)

> "Section 11 is the 3 role plays. Full scripts in `11_role_plays/`. The role plays test: 1) reading error messages (RP1, trust misconfig), 2) diagnosing with metrics (RP2, streaming falling behind), 3) pitching with numbers (RP3, DQ to manager). Each role play has a scenario, 2 personas, a script, a worked answer, and a list of common mistakes."

Section 11 quiz: see `quizzes/section_11.md`.
