#! number: 07
#! title: Testing DAGs
#! module: Module 2 · Reliability & Operations
#! lecture: Lecture 2.5

- Split testing into three layers: **pure logic**, **DAG structure**, **integration**
- Write structure tests against a tiny Airflow shim so they run without Airflow
- Use `pytest.mark.parametrize` to test every branch of a decision function
- Learn what **not** to test — and why testing Airflow itself is a mistake
- Assemble a CI checklist you can put in a pipeline tomorrow
