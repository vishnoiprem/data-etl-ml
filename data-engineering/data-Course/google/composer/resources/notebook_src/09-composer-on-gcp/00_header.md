#! number: 09
#! title: Composer on GCP
#! module: Module 4 · Cloud Composer
#! lecture: Lecture 4.1
- Explain what Cloud Composer **is**: managed Apache Airflow running on GKE
- Walk the architecture: Cloud SQL metadata DB, GCS for DAGs, GKE workers, Cloud Storage for logs
- Provision an environment with **`gcloud composer environments create`** — every command in a fenced `bash` block, marked *run in a terminal, not executed here*
- Size an environment and **compute the cost** in a pandas DataFrame with a monthly projection
- Compare **Composer 2 (Celery) vs Composer 3 (KubernetesExecutor)** and the Airflow version each pins
- Tour the **Composer UI** — DAGs, Graph, Calendar, Logs, Admin panes, Config
- Set up **IAM**: the environment's service account and the permissions it needs
- Plan **cleanup and cost control** — deleting an environment, what survives, bucket retention, budget alerts
- **Simulate the environment locally** with a Python dataclass and render the cost table — fully executable
