#! number: 10
#! title: End-to-End Project
#! module: Module 5 · Capstone
#! lecture: Lecture 5.1
- Generate the sample dataset and understand exactly what it contains
- Run **every** DAG in the local runner, and cross-validate each output against the pure reference implementation
- Walk through the four real DAG files in `project/dags/` — what each task does and why it exists
- See precisely what changes when those DAGs are deployed to Composer
- Build the deployment checklist: Variables, Connections, DAG params, and how to trigger a backfill
- Prove the pipeline is idempotent, so a retry and a backfill are both safe
