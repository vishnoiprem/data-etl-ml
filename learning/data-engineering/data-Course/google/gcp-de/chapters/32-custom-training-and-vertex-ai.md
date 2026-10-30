# 8.3 — Custom Training & Vertex AI

> **Section 8 · ML on GCP & Capstone · Lecture 8.3 · 8:00**

## 🎯 What you will learn

- When you genuinely need to train your own model — and when you are wasting money
- The Vertex AI model lifecycle, stage by stage:
  - **Datasets** — the annotation workflow, the labelling UI, the programmatic labeler
  - **Notebooks** — Vertex AI Workbench managed instances and the Colab enterprise alternative
  - **Training** — `CustomJob`, `PipelineJob`, the SDK, prebuilt trainers, hyperparameter tuning, distributed training
  - **Model Registry** — versions, aliases, model gardens
  - **Endpoints** — online prediction, endpoint architecture, traffic splitting, feature importance, explainability
  - **MLOps** — the Vertex AI Pipelines SDK, model monitoring, retraining triggers
- The **container** you build for a custom training job, and why the code lives in a container at all
- **Distributed training**: what actually parallelises, and what does not
- An honest **cost analysis** using `VERTEX_AI_TRAINING_PER_NODE_HOUR = 3.67`
- The artefacts and IAM roles a production Vertex AI pipeline needs

---

## 🧠 Concept

### When to train your own model

Chapter 8.2 gave you the decision ladder. Here is the sharp version, because the most expensive mistake in ML projects is training when you did not need to.

**Train your own model when at least two of these are true:**

1. **The concept is genuinely yours** — a pre-trained model has never seen it and cannot be taught it cheaply.
2. **You need control over the objective** — a custom loss, a custom metric, a ranking objective, a fairness constraint, a cost-sensitive threshold baked into the training.
3. **You need explainability at the level of the feature** — "this document was classified as contract because of clause 14.2" rather than "the API returned 0.98".
4. **Your latency, privacy, or regulatory constraints forbid a third-party call** — on-device inference, data residency, or "the model must never see customer data outside our VPC".
5. **Your data volume and shape make the pre-trained model's bias wrong** — a model trained on English web text applied to your niche domain will be systematically off.
6. **You need to optimise the inference cost at scale** — at tens of millions of predictions a month, a small self-hosted model on Cloud Run or GKE can beat a per-unit API.

**Do not train your own model because:**

- It sounds more impressive. A pre-trained API in production beats a custom model in a notebook.
- Someone read a blog post about a bespoke architecture. The blog post did not have your data, your latency budget, or your on-call rotation.
- The pre-trained model "wasn't accurate enough" — before checking whether the problem was your features, your labels, your preprocessing, or your threshold.

**The honest framing:** every custom model you train is a system you now own. You own the training pipeline, the dependency versions, the container image, the feature parity, the monitoring, the retraining, and the 3 a.m. pager when the base image's Python version is deprecated. That cost is real and it is usually underestimated by an order of magnitude.

### The Vertex AI lifecycle

```text
   ┌─────────────┐
   │  Datasets   │  images/text/tabular + labels, versioned
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │ Notebooks   │  explore, engineer features, prototype
   └──────┬──────┘
          │
   ┌──────▼──────────────┐
   │ Training            │  CustomJob / PipelineJob / prebuilt trainer
   │  ├─ hyperparameter  │
   │  ├─ distributed     │
   │  └─ distributed     │
   └──────┬──────────────┘
          │
   ┌──────▼──────────────┐
   │ Model Registry      │  versioned models, aliases, stages
   └──────┬──────────────┘
          │
   ┌──────▼──────────────┐
   │ Endpoints           │  online prediction, traffic splitting
   └──────┬──────────────┘
          │
   ┌──────▼──────────────┐
   │ Monitoring          │  drift, skew, performance, retraining
   └─────────────────────┘
```

The important architectural point: **these are separate resources with separate permissions and separate lifecycles.** A model in the registry is not deployed. A deployed endpoint is not monitored. The gaps between them are where the incidents live.

### Stage 1: Datasets

A Vertex AI Dataset is a managed container for training data with labels and a version history.

**Managed types:**

- **Image** — for AutoML Vision. Labels are drawn on the images in the console UI, or imported from an existing annotation set.
- **Text** — for AutoML Natural Language. Labels are inline with the text, so there is no UI annotation step.
- **Video** — for video classification.
- **Tabular** — a BigQuery table reference or a CSV upload. Labels come from a column.

**The annotation workflow (image and video):**

```text
   images in GCS
        │  gcloud ai datasets import
        ▼
   Dataset (unlabelled state)
        │  human labelling in the console UI
        ▼
   Dataset (partially labelled)
        │  repeat until label coverage is sufficient
        ▼
   Dataset (version 1, 2, 3...)
```

**The console labelling UI** lets you draw bounding boxes (object detection) or assign image-level labels (classification), and supports **active learning**: Vertex selects the images it is least confident about and surfaces them first, which roughly halves the labelling effort for image classification. There is also a **labeling service** — a managed workforce that can do the annotation for you at a per-item price, integrated through the Data Labelling API.

**The programmatic labeler.** The Data Labelling API lets you push pre-existing annotations into a dataset without using the UI. This is the path when your labels already exist:

```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location="us-central1")

dataset = aiplatform.ImageDataset.create(
    display_name="packaging-defects",
    source_dataset=None,
)

# Import the images.
gcs_source = aiplatform.GcsSource(
    uris=["gs://raw-events-us-central1/images/*"]
)
import_config = aiplatform.ImportImageConfig(
    gcs_source=gcs_source,
    import_all_annotations=False,   # labels come in a later call
)
dataset.import_images(import_config=import_config)

# Push existing annotations directly.
annotation_spec = aiplatform.AnnotationSpec(
    display_name="defect_type",
    labels={
        "no_defect": "intact packaging",
        "dent": "dented or crushed packaging",
        "tear": "torn packaging",
        "label_missing": "defect present but type unclear",
    },
)
annotation_spec.save()

for image in dataset.list_images():
    image.annotation_labels = [
        aiplatform.Annotation(annotation_spec=annotation_spec, label="dent")
    ]
    image.save()
```

**The `label_missing` label is important.** If your label set has no "unclear" option, labellers will guess, and you will train on labels that are wrong with no signal that they are wrong. A dedicated "uncertain" class — or an explicit "reject" — is how you keep the noise measurable.

**The cost of labelling, again.** There is no escaping it: labelling is a human-hours budget. Before creating a dataset, compute:

```text
label_hours = n_images × seconds_per_image ÷ 3600
cost       = label_hours × loaded_hourly_rate
```

And compare that against the total value of the model. The training compute is a rounding error next to it.

### Stage 2: Notebooks

**Vertex AI Workbench** gives you a managed Jupyter server on a Compute Engine instance, preconfigured with the Vertex AI SDK and the ML libraries.

**Instance types:**

| Type | What it is | When |
|---|---|---|
| **Workbench Standard** | A VM you can SSH into, with a Jupyter web UI | Development, exploration, small-scale training |
| **Workbench Managed** | A serverless Jupyter environment, no VM to manage | Recommended default for most work |
| **Workbench GPU** | A managed instance with GPUs attached | Local model training, large notebooks |

**The Google Colab enterprise alternative.** Colab Enterprise runs on Google Cloud infrastructure, with VPC Service Controls support, BigQuery integration, and a proper identity model. It is genuinely convenient for exploratory work and for sharing notebooks with business stakeholders.

**The honest comparison.** Colab is faster to start and has no VM to clean up. Workbench has a persistent filesystem, real IAM, and can hold a 50 GB dataset on a persistent disk without re-downloading. **Rule of thumb: Colab for a two-hour exploration; Workbench for anything you will return to.** And a third option that outranks both for reproducibility: **a local notebook in a git repo, running against a BigQuery instance or a Dataflow worker.** For a data engineer, that is usually the best iteration loop, because the data is already there.

**What a notebook is for:** exploring the data, prototyping features, and running a quick training run to sanity-check the pipeline. **What a notebook is not for:** the training pipeline. Notebooks are not reproducible, not versioned in their outputs, and not schedulable. The moment the model is worth keeping, the training code moves into a versioned script or a pipeline component.

### Stage 3: Training

There are three ways to train on Vertex AI, and the choice is mostly about how much control you want.

#### The CustomJob

The lowest-level training primitive. You supply:

1. A **container image** containing your training code and its dependencies.
2. A **Python package** (the `trainer` package) that Vertex injects, which handles the framework-specific plumbing.
3. **Command-line arguments** passed to the entry point.
4. **Node configuration**: machine type, replica count, accelerator count.

```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location="us-central1")

job = aiplatform.CustomJob(
    display_name="churn-model-v1",
    worker_pool_specs=[
        aiplatform.machine_spec.MachineSpec(
            machine_type="n1-standard-4",
            accelerator_count=0,
            accelerator_type="",
        )
    ],
    base_output_dir="gs://my-project-vertex-models/churn/v1",
)

job.run(
    source_distribution=aiplatform.python_source_distribution.TrainingDistribution(
        source_dir="src/training",
        entry_point="trainer.task",
    ),
    args=[
        "--train-table", "my-project.curated.user_features_daily",
        "--label-column", "churned_30d",
        "--epochs", "30",
        "--num-trials", "1",
    ],
)
```

**Why a container, and why the `trainer` package?** The container gives you a reproducible environment with pinned dependencies — which is the only way to guarantee that the training run today and the retraining in six months use the same library versions. The `trainer` package is a small shim Vertex provides that turns your `args` into typed objects and calls your `train()` function. You write one function:

```python
# src/training/trainer/task.py
import argparse
import os

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
import joblib


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-table", type=str, required=True)
    parser.add_argument("--label-column", type=str, required=True)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--num-trials", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def train(args):
    from google.cloud import bigquery

    client = bigquery.Client()
    sql = f"""
        SELECT * EXCEPT({args.label_column}), {args.label_column}
        FROM `{args.train_table}`
        WHERE feature_as_of < '2026-01-16'
    """
    df = client.query(sql).to_dataframe()

    X = df.drop(columns=[args.label_column])
    y = df[args.label_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=args.seed, stratify=y
    )

    model = GradientBoostingClassifier(
        n_estimators=args.epochs,
        learning_rate=0.1,
        max_depth=6,
        random_state=args.seed,
    )
    model.fit(X_train, y_train)

    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"[churn-model-v1] AUC={auc:.4f}")

    output_dir = os.environ.get("AIP_MODEL_DIR", "/tmp/model")
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(model, os.path.join(output_dir, "model.joblib"))

    with open(os.path.join(output_dir, "metrics.json"), "w") as f:
        f.write('{"auc": %.6f}\n' % auc)

    return model


if __name__ == "__main__":
    train(get_args())
```

**The environment variables Vertex injects** are the contract between your code and the platform:

| Variable | Meaning |
|---|---|
| `AIP_MODEL_DIR` | Where to write the model artefact. Vertex collects everything in this directory. |
| `AIP_CHECKPOINT_DIR` | Where to write checkpoints for a resumable job |
| `AIP_STORAGE_URI` | The root `gs://` URI for the job's outputs |
| `AIP_TRAIN_SESSION_ID` | The session identifier, useful for logging correlation |
| `AIP_INDEX_TENSOR` | The tensor index, for distributed training |

**Write the artefact to `AIP_MODEL_DIR`.** If you write it somewhere else, Vertex does not find it and the job "succeeds" with no model — a failure mode that is genuinely easy to hit.

#### Prebuilt trainers

For the four common frameworks, Vertex has a prebuilt trainer that handles the framework plumbing for you. You supply the training script; the trainer wraps it.

```python
from google.cloud import aiplatform
from kfp import dsl

@dsl.pipeline(name="churn-training")
def churn_pipeline(
    train_table: str = "my-project.curated.user_features_daily",
    label_column: str = "churned_30d",
    model_display_name: str = "churn-model-v1",
    model_dir: str = "gs://my-project-vertex-models/churn",
):
    train_job = aiplatform.CustomTrainingJob(
        display_name="churn-train",
        pipeline_root=model_dir,
        base_output_dir=model_dir,
        model_display_name=model_display_name,
        script_path="src/training/trainer.py",
        container_uri="us-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest",
        requirements=["scikit-learn==1.5.2", "pandas==2.2.3", "joblib==1.4.2"],
    )

    model = train_job.run(
        dataset=aiplatform.gapic.DatasetReference(
            project=PROJECT_ID, dataset_id="churn-dataset"
        ),
        model_display_name=model_display_name,
        replica_count=1,
        args=[
            "--train-table", train_table,
            "--label-column", label_column,
            "--epochs", "30",
            "--num-trials", "1",
        ],
    )
    return model
```

**The container images:**

| Framework | Container URI pattern | Notes |
|---|---|---|
| scikit-learn | `us-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest` | CPU only; cheap |
| XGBoost | `us-docker.pkg.dev/vertex-ai/training/xgboost-cpu.1-7:latest` | CPU and GPU variants |
| TensorFlow | `us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-15.py310:latest` | CPU and GPU variants |
| PyTorch | `us-docker.pkg.dev/vertex-ai/training/pytorch-cpu.2-5.py310:latest` | CPU and GPU variants |
| Deep Learning | `us-docker.pkg.dev/vertex-ai/training/deep-learning-cpu.2-15.py310:latest` | Prebuilt TF2 and PyTorch trainers |

**Pinning matters more than the tag suggests.** Using `latest` means your training run in six months may use a different CUDA or TensorFlow version than the one you validated. **Pin the version.** The tag `sklearn-cpu.1-0` is a family; there are dated tags below it (`sklearn-cpu.1-0.20240606T...`) that identify the exact build. Use one of those for production.

**Prebuilt trainer vs custom container — the trade-off:**

```text
Prebuilt trainer   less code, framework plumbing handled, limited control
Custom container   full control over dependencies, preprocessing, training loop
```

**Rule:** use the prebuilt trainer when your training script is a straightforward fit-and-evaluate. Use a custom container the moment you need a custom dependency, a custom preprocessing step inside the training job, a non-standard framework, or an auditable environment. My default is a **custom container with pinned dependencies** from the very first model, because the reproducibility cost of `latest` is discovered at the worst possible time.

#### Hyperparameter tuning

Vertex runs many training jobs, each with a different hyperparameter configuration, and selects the best.

```python
from google.cloud import aiplatform
from kfp import dsl

@dsl.pipeline(name="churn-training-tuned")
def churn_pipeline(
    train_table: str = "my-project.curated.user_features_daily",
    label_column: str = "churned_30d",
):
    train_job = aiplatform.CustomTrainingJob(
        display_name="churn-train-tuned",
        pipeline_root="gs://my-project-vertex-models/churn",
        model_display_name="churn-model-tuned",
        script_path="src/training/trainer.py",
        container_uri="us-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest",
        requirements=["scikit-learn==1.5.2", "pandas==2.2.3"],
    )

    model = train_job.run(
        dataset=aiplatform.gapic.DatasetReference(
            project=PROJECT_ID, dataset_id="churn-dataset"
        ),
        model_display_name="churn-model-tuned",
        replica_count=1,
        tune_metric="auc",
        tune_maximize=True,
        # The search space. Each trial picks one value from each list.
        parameter_space={
            "n_estimators": {"from": 50, "to": 500, "step": 50},
            "learning_rate": {"from": 0.01, "to": 0.3, "step": 0.01},
            "max_depth": {"from": 3, "to": 10, "step": 1},
        },
        args=[
            "--train-table", train_table,
            "--label-column", label_column,
            "--epochs", "30",
            "--num-trials", "1",
        ],
    )
    return model
```

**How the search works.** Vertex runs trials **in parallel**, each on its own node. It uses **Bayesian optimisation** informed by the results of previous trials, plus random search as a fallback for exploration. This matters: pure random search on a 5-dimensional space with a budget of 20 trials wastes most of its budget. Bayesian search typically finds a good configuration in 10-15 trials where random search needs 50.

**The cost implication is severe.** A hyperparameter tuning job with 20 trials at 4 node-hours each is **80 node-hours**. At `VERTEX_AI_TRAINING_PER_NODE_HOUR = 3.67` that is **$293.60** per tuning run. And tuning is usually part of a pipeline that runs on retraining — so it is a recurring cost, not a one-time cost.

**The number one mistake: tuning on the test set.** The `tune_metric` must be computed on a **validation** set carved out of the training data inside your training script, not on your held-out test set. If the tuning job optimises against the test set, the test set is now a validation set, and the reported score is optimistic. Your training script must therefore *split* its own data and report the tuning metric on the validation split only.

#### Distributed training

"Distributed" covers three different mechanisms on Vertex, and they are routinely confused.

**1. Distributed training (data parallel).** Replicate the model across N nodes and split the data between them. Each node computes gradients on its shard; the gradients are all-reduced (averaged) across nodes; every node updates its copy of the weights identically. This is the right mechanism when the **model fits in one node's memory but the dataset does not**.

**2. Distributed training (model parallel).** Split the *model* across nodes. Each node holds part of the layers and passes activations forward and gradients backward between nodes. This is what you need for models too large to fit on one node, and it requires a framework that supports it (Horovod, or PyTorch's native DDP).

**3. Distributed prediction (inference).** Replicate a trained model across N nodes behind one endpoint. Each replica holds the full model and serves a fraction of the traffic. This is a **serving** concern, not a training concern, and it is the one you will use most.

**The distinction matters for configuration.** In Vertex:

- Data parallel: set `replica_count > 1` on the worker pool, use `strategy="reduce_scatter"` (default) or `"allreduce"`, and use a **distributed training job** rather than a plain CustomJob.
- Model parallel: use a custom job with the framework's launcher and `worker_pool_specs` sized to the model.
- Inference: configure the endpoint with `machine_type`, `min_replica_count`, `max_replica_count`.

**The custom trainer's distributed pattern.** Vertex's `CustomTrainingJob` with `replica_count=N` runs N identical containers. Your script detects the replica set and uses the framework's launcher:

```python
# The trainer pattern for PyTorch DDP on Vertex.
import os

def main():
    # Vertex sets these for distributed jobs.
    replica_count = int(os.environ.get("REPLICA_COUNT", "1"))
    rank = int(os.environ.get("RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    print(f"replica_count={replica_count} rank={rank}/{world_size}")

    import torch
    import torch.distributed as dist

    if world_size > 1:
        dist.init_process_group(backend="nccl")
        local_rank = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(local_rank)
        device = torch.device(f"cuda:{local_rank}")
    else:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # ... build the model, shard the dataset by rank, train ...

    if world_size > 1:
        dist.destroy_process_group()
```

**The dataset sharding rule:** shard by `index % world_size == rank`, not by a contiguous slice, and use a shuffling sampler. Contiguous slices with correlated data (time-ordered rows) give each replica a non-representative shard.

**When distributed training is worth it:** only when the single-node run does not fit, or when the wall-clock saving exceeds the extra cost. **Two nodes cost twice as much as one.** If a single `n1-standard-16` finishes in 4 hours and two `n1-standard-8` nodes finish in 2 hours, the distributed version costs 2× the money to save 2 hours. For a nightly retraining job that is not a good trade. For a model you retrain 50 times a month, it might be.

### Stage 4: Model Registry

The Registry is a versioned catalogue of models with metadata, lineage, and aliases.

**Model → Model version → (Deployment) → Alias**

- A **model** is a container.
- A **model version** is an immutable artefact — a trained snapshot. It has a version ID, a URI, the framework it was trained in, the evaluation metrics, feature importances, and the lineage.
- A **deployment** is a model version attached to an endpoint.
- An **alias** is a mutable pointer to a model version. `production` is a conventional alias name.

**Aliases are the important mechanism**, because they decouple the deployment from the version number:

```text
Endpoint → alias "production" → model version 7
```

When version 8 is promoted, you move the alias. The endpoint's consumer code does not change. This is how you do a zero-downtime version change: deploy v8 alongside v7, shift traffic, verify, then retire v7.

**Model stages** (`None` → `Staging` → `Production` → `Archived`) are a workflow convention, not an enforcement mechanism. Vertex does not stop you deploying a `None` model to production. The stages are for humans.

**Model gardens** are curated collections of pre-trained and fine-tuned models — including Google's own (the same foundation models behind the pre-trained APIs) and partner models — that you can deploy directly to an endpoint. They are the bridge between Chapter 8.2 and this chapter: a garden model gives you a foundation model with a hosted endpoint, which is a middle ground between "call an API" and "write a training loop".

**What to record in the model version's metadata.** Vertex records some of this automatically; the rest is yours to attach:

```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location="us-central1")

model = aiplatform.Model(  # the uploaded model version
    model_name="churn-model",
    version="7",
)

model.version_info = aiplatform.VersionInfo(
    description="Gradient-boosted trees, 90d features, retrain 2026-01-15",
    labels={
        "framework": "scikit-learn",
        "feature_code_sha": "a3f91c7",
        "label_table": "curated.churn_labels",
        "label_as_of": "2026-01-15",
        "training_run_id": "20260115T031422Z",
    },
)

model.metrics = [
    aiplatform.Metric(
        display_name="auc", value=0.9134, step=1
    ),
    aiplatform.Metric(
        display_name="precision_at_0.35", value=0.7421, step=1
    ),
]

model.save()
```

**Why the labels matter.** When someone asks "which training data is this model?" — in an incident, in an audit, six months later — the answer should be one query, not an archaeology project.

### Stage 5: Endpoints

An **endpoint** is the serving abstraction. It is a resource with a deployment, a traffic split, scaling configuration, and access logging.

**Endpoint architecture:**

```text
                       ┌─────────────────────────┐
   prediction ────────▶│  Vertex AI Endpoint     │
   request             │  ┌───────────────────┐  │
                       │  │  Traffic split    │  │
                       │  │  90% → v7         │  │
                       │  │  10% → v8 (canary)│  │
                       │  └───────────────────┘  │
                       │      │            │     │
                       │   ┌──▼──┐      ┌──▼──┐  │
                       │   │ v7  │      │ v8  │  │
                       │   │ 2   │      │ 1   │  │
                       │   │repl.│      │repl.│  │
                       │   └─────┘      └─────┘  │
                       └─────────────────────────┘
```

**Endpoints come in two flavours:**

| Type | Use when |
|---|---|
| **Public endpoint** | Traffic arrives from outside your VPC (a browser, a mobile app). Deployed behind a Google-managed load balancer with IAM or access-token auth. |
| **Private endpoint** | Traffic arrives from inside your VPC. Keeps the traffic internal; use with a `PSC` or internal load balancer. |

**Deploying a model version to an endpoint:**

```python
aiplatform.init(project=PROJECT_ID, location="us-central1")

endpoint = aiplatform.Endpoint(
    display_name="churn-endpoint",
    project=PROJECT_ID,
    location="us-central1",
)

endpoint.deploy(
    model=model_resource,          # the model version
    machine_type="n1-standard-4",
    min_replica_count=1,
    max_replica_count=10,
    traffic_split={"10": 100},     # model version id -> traffic percentage
    sync=True,
)
```

**Traffic splitting** is the mechanism for safe rollout. You deploy the new version alongside the old, send a small percentage of traffic to it, compare, then increase.

```python
# Shift traffic from 10% to 50% on the new version.
endpoint.update_traffic_split(
    {"10": 50, "7": 50},
)
```

**The traffic split is the mechanism for a canary, and it needs a comparison.** Log predictions from both versions with the model version ID attached, and compare the score distributions, the positive rate, and — once labels arrive — the actual performance. A canary without a comparison metric is just a random traffic split.

**Scaling.** `min_replica_count` is the floor (and it is what you pay for when idle). `max_replica_count` is the ceiling. The autoscaler reacts to **concurrency** — simultaneous requests per replica — not to CPU. **Set the concurrency target deliberately**: too high and latency spikes under load because each replica is handling too many requests; too low and you pay for replicas you do not need.

**Autoscale to zero** is available for endpoints with no minimum traffic. This is the option for a spiky, mostly-idle workload: you pay nothing when nobody is calling. It is not suitable for a latency-sensitive path, because a cold start is seconds.

**Online prediction.** The request format depends on the framework; the mechanics are the same.

```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location="us-central1")
endpoint = aiplatform.Endpoint(
    endpoint_name="churn-endpoint",
    project=PROJECT_ID,
    location="us-central1",
)

# sklearn models expect a list of instances, each a dict of features.
instance = {
    "n_events": 14,
    "n_orders": 3,
    "total_spend_eur": 482.15,
    "avg_order_value_eur": 160.72,
    "refund_rate": 0.0714,
    "region": "EMEA",
    "channel": "web",
}

response = endpoint.predict(instances=[instance])
predictions = response.predictions
print(f"churn probability: {predictions[0]['scores'][0]}")
```

**Two properties of the serving path that cause outages:**

1. **The feature schema must match training exactly.** A missing feature or a renamed column produces an error at inference time — usually a 400. Validate the payload against the training schema before calling.
2. **The feature *values* must be computed the same way.** This is training/serving skew, and the endpoint will happily serve a wrong number with a 200 status. See Chapter 8.1.

**Batch prediction** is the alternative for large volumes:

```python
batch_job = aiplatform.BatchPredictionJob(
    display_name="churn-batch-2026-01-15",
    model=model_resource,
    input_instances_format="jsonl",
    output_predictions_format="jsonl",
    gcs_source_uri="gs://my-project-scoring/users-2026-01-15.jsonl",
    gcs_destination_prefix="gs://my-project-scoring/predictions-2026-01-15",
    machine_type="n1-standard-4",
)
batch_job.run()
```

Batch prediction is **much** cheaper per prediction than online serving, because there is no always-on replica and no per-request overhead. For scoring 10 million customers nightly, batch prediction is the right answer; the online endpoint would cost an order of magnitude more.

**Feature importance and explainability.** Vertex computes and exposes these for models trained in supported frameworks:

```python
# Feature importances are attached to the model version.
model = aiplatform.Model(
    model_name="churn-model", version="7", project=PROJECT_ID
)
importances = model.get_feature_importances()

# Or via the explainability API, for SHAP values per prediction.
explanation = model.explain(
    instances=[
        {"n_events": 14, "n_orders": 3, "total_spend_eur": 482.15,
         "avg_order_value_eur": 160.72, "refund_rate": 0.0714,
         "region": "EMEA", "channel": "web"}
    ],
)
```

**Feature importance tells you what the model uses globally. SHAP tells you why *this* prediction.** For an incident investigation or a customer-facing explanation, you need the per-prediction version — the global one cannot tell you why a specific customer was flagged.

**The explainability caveat:** an explanation is not a reason. SHAP decomposes a prediction into feature contributions; it does not tell you the causal mechanism. If a stakeholder asks "why was this customer flagged?", the honest answer is "these features contributed in these directions to the score", not "because they are likely to churn". Say this out loud, early, to the people who will ask.

### Stage 6: MLOps on Vertex AI

**Vertex AI Pipelines** is the orchestrator for ML workflows. It is a Kubeflow Pipelines implementation, so the SDK is `kfp`, and a pipeline is a `@dsl.pipeline`-decorated function of Python.

```python
from kfp import dsl
from kfp.dsl import Input, Output, Path


@dsl.pipeline(name="churn-training-and-eval")
def churn_pipeline(
    project_id: str = PROJECT_ID,
    region: str = "us-central1",
    train_table: str = "my-project.curated.user_features_daily",
    label_column: str = "churned_30d",
    model_display_name: str = "churn-model",
    model_dir: str = "gs://my-project-vertex-models/churn",
):
    train_op = train_model_op(
        project_id=project_id,
        region=region,
        train_table=train_table,
        label_column=label_column,
        model_display_name=model_display_name,
        model_dir=model_dir,
    )

    evaluate_op = evaluate_model_op(
        model_uri=train_op.outputs["model_uri"],
        eval_table=train_table,
        label_column=label_column,
        # Gate the promotion on a metric threshold. A pipeline that
        # always deploys is not a pipeline with a gate.
        min_auc=0.85,
    )


@dsl.component
def train_model_op(
    project_id: str,
    region: str,
    train_table: str,
    label_column: str,
    model_display_name: str,
    model_dir: str,
) -> str:
    """Trains the model and returns the model artefact URI."""
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable, "-m", "src.training.trainer",
            "--train-table", train_table,
            "--label-column", label_column,
        ],
        check=True,
    )
    return f"{model_dir}/model.joblib"
```

**The features that matter in a pipeline:**

- **Caching.** If a step's inputs are unchanged, the cached output is reused. This is what makes a retraining pipeline cheap to re-run during development.
- **Conditionals and loops.** `@dsl.condition` and `@dsl.for_loop` let you branch. Use them sparingly — a pipeline with nested conditionals is a pipeline nobody can debug.
- **Pipeline artifacts.** Every step's output is registered as an artifact with lineage. This is how you answer "which data produced this model".
- **Pipeline runs are the audit trail.** Each run has a run ID, a log, the parameters, and the artefacts.

**Model monitoring.** Vertex can watch a deployed model and alert you.

```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location="us-central1")

endpoint = aiplatform.Endpoint(
    endpoint_name="churn-endpoint",
    project=PROJECT_ID,
    location="us-central1",
)

# 1. Log predictions to BigQuery. This is the prerequisite for
#    everything else — without prediction logs, monitoring is blind.
endpoint.enable_prediction_logging(
    logging_filter=""          # empty = log everything
)

# 2. Define the skew detection: compare the live feature distribution
#    to the training distribution.
endpoint.create_skew_detection_config(
    data_source=aiplatform.DataSource(
        input_dataset_id=training_dataset_id,
        target_field="feature_timestamp",
        skew_detection_config=aiplatform.gapic.EndpointService.SkewDetectionConfig(
            data_source=aiplatform.gapic.EndpointService.DataSource(
                input_dataset_id=training_dataset_id,
                target_field="feature_timestamp",
            ),
            skew_thresholds={
                "n_events": aiplatform.gapic.EndpointService.SkewDetectionConfig
                    .Threshold(value=0.001, deviation_from_baseline=False),
                "total_spend_eur": aiplatform.gapic.EndpointService
                    .SkewDetectionConfig.Threshold(value=0.01,
                                                    deviation_from_baseline=False),
            },
        ),
    ),
)

# 3. Define the drift detection: compare the live prediction
#    distribution to the training prediction distribution.
endpoint.create_drift_detection_config(
    drift_detection_config=aiplatform.gapic.EndpointService.DriftDetectionConfig(
        drift_thresholds={
            "churn_score": aiplatform.gapic.EndpointService.DriftDetectionConfig
                .Threshold(value=0.01, deviation_from_baseline=False),
        },
    ),
)
```

**The mechanism:** Vertex computes a **TensorFlow Data Validation (TFDV) sketch** over the training data and over the live serving data, then compares them. The statistic used is the **Jensen-Shannon divergence** for categorical features and the **L-infinity distance** for numerical features, normalised against a baseline. It is not PSI, but it serves the same purpose.

**Important limits of Vertex model monitoring:**

- **Drift detection compares the live *prediction* distribution to the training *prediction* distribution.** It detects covariate shift in the model's output. It does **not** detect concept drift — that requires fresh labels.
- **Skew detection compares live *features* to training *features*.** It needs the training features to be available in a dataset, and it needs prediction logging on.
- **Both require the training data to be sketchable**, which means the training dataset must be in BigQuery or a similar source.

**The monitoring setup that is worth the effort:**

```text
1. Enable prediction logging to BigQuery, partitioned by prediction timestamp
2. Log the features alongside the prediction, not just the score
3. Enable skew detection on the top 5 features
4. Enable drift detection on the prediction score
5. Alert on:
     - skew/drift threshold exceeded
     - positive rate outside [0.5x, 2x] the baseline
     - prediction volume below a floor (the model stopped scoring)
     - endpoint error rate above 1%
6. Schedule a weekly pipeline run that evaluates the live model against
   matured labels, and compares to the baseline
```

**Retraining triggers.** Vertex Pipelines can be scheduled on a cadence, or triggered by an event. The realistic options:

| Trigger | Mechanism | Use when |
|---|---|---|
| **Scheduled** | Cloud Scheduler → API → pipeline run | Weekly/monthly retraining on a fixed rhythm |
| **Drift alert** | Monitoring alert → Pub/Sub → pipeline run | The distribution has moved enough to act |
| **Data volume** | A BigQuery scheduled query checks row counts → Pub/Sub | Enough new labelled data has arrived |
| **Manual** | A human starts the run | Approval-gated promotion |

**The right answer is usually a hybrid:** retrain on a schedule (so the model does not rot silently) *and* promote only after the evaluation gate passes (so a bad training run never reaches production). The schedule keeps the model fresh; the gate keeps it correct.

**An important nuance on drift-triggered retraining:** if the drift is caused by a genuine change in the world, retraining on the new data is correct. If the drift is caused by a broken upstream pipeline, retraining propagates the breakage into the model. **Before automating retraining on a drift signal, make sure you have an input-side guard** — a data-quality check on the feature table — that fails the pipeline when the *inputs* are broken rather than retraining on them.

### The honest cost analysis

```text
VERTEX_AI_TRAINING_PER_NODE_HOUR = 3.67
```

This is the list rate for a training node-hour on a standard machine type. A GPU node costs considerably more (typically $3-8 per node-hour depending on the accelerator). Endpoint serving is billed separately, per node-hour at a lower rate.

**Scenario A: a scikit-learn churn model, retrained monthly.**

```text
1 training job, 4 node-hours          4    × $3.67 = $14.68
1 endpoint, n1-standard-4, 1 replica  730  × ~$0.40 = ~$292.00  (approx.)
                                                   ─────────────
Monthly total                                             ≈ $306.68
```

**Scenario B: hyperparameter tuning, 20 trials.**

```text
20 trials × 4 node-hours = 80 node-hours × $3.67 = $293.60
+ one training job for the winner (4 node-hours) = $14.68
                                                   ─────────────
Tuning run total                                       $308.28
```

**Scenario C: a GPU training job for a vision model.**

```text
1 × A100 node-hour ≈ $3.67 (CPU node) + accelerator premium
Realistic: 8 node-hours × ~$8.00 (GPU-inclusive node rate) = $64.00
```

**Scenario D: what a naive pipeline actually costs per year.**

```text
Monthly retraining with 20-trial tuning:
  $308.28 × 12 = $3,699.36/year
  + endpoint ~$292 × 12 = $3,504/year
                                                 ─────────────
Total                                              ≈ $7,203/year
```

Compare with a **pre-trained API** for the same classification problem: 50,000 calls/month × $1.50/1000 = $75/month = **$900/year**. The custom model costs 8× more in cash and adds an on-call rotation.

**The correct conclusion is not "never use Vertex AI."** It is: **the cost of Vertex AI is not the training compute — it is the pipeline, the endpoint, and the retraining cadence you build around it.** A well-designed custom model beats a pre-trained API when it materially changes a business decision. A poorly-designed one costs eight times more and does the same job.

**The cost levers that actually matter:**

1. **Retrain on a schedule, not on every pipeline run.** A weekly retraining on a model that changes slowly is waste.
2. **Do not tune hyperparameters every retraining.** Tune once, record the winning configuration, and reuse it. Or tune on a schedule far less often than you retrain.
3. **Use CPU nodes for tabular models.** A scikit-learn gradient-boosting model on `n1-standard-4` costs $3.67/node-hour. A GPU would cost several times more for typically no accuracy gain on tabular data.
4. **Scale the endpoint to zero when the workload is idle.** `min_replica_count=0` on a spiky endpoint. You pay for the endpoint only when it is serving.
5. **Use batch prediction for bulk scoring.** No always-on replicas.
6. **Reduce the training dataset size.** Training on 10% of the data and measuring the AUC difference is often the highest-leverage experiment available, and it costs minutes to run.

### What a production Vertex AI pipeline needs

```text
IAM roles for the pipeline service account
  roles/aiplatform.user          Vertex AI operations
  roles/storage.objectAdmin      read training data, write artefacts
  roles/bigquery.dataViewer      read the training table
  roles/bigquery.jobUser         run the evaluation queries
  roles/iam.serviceAccountUser   act as the training service account
  roles/cloudtrace.agent         write traces (for the monitoring UI)
  roles/monitoring.metricWriter  write custom metrics
  roles/secretmanager.secretAccessor  read secrets, if the job needs any

Artefacts
  src/training/                  versioned training code
  containers/                    the container image, built and pushed
  pipelines/                     the kfp pipeline definitions
  models/                        the model manifests and metrics
  golden_set/                    the regression set for pre-trained APIs
```

**The service account should be dedicated to the pipeline and have no more than the roles above.** A Vertex AI pipeline service account with `roles/owner` is the same anti-pattern as the Vision API one in Chapter 8.2, and it is far more dangerous: it can create, delete, and invoke any model, any endpoint, and any dataset in the project.

---

## 🛠️ Hands-On

### Exercise 1 — The training script, complete and runnable

The complete trainer, including the parts people forget: the artefact location, the validation split, and the metrics file.

```python
# src/training/trainer.py
"""The training entry point for the churn model.

Vertex runs this inside the container. The contract:
  - read the training table from BigQuery
  - split train/validation INSIDE the script (the test set never
    appears here, and the tuning metric is computed on validation)
  - write the artefact to $AIP_MODEL_DIR
  - write metrics to $AIP_MODEL_DIR/metrics.json
"""
import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-table", type=str, required=True)
    parser.add_argument("--label-column", type=str, required=True)
    parser.add_argument("--as-of", type=str, default="2026-01-16")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_training_data(table, label_column, as_of):
    """Load the training matrix, with the as-of filter applied."""
    from google.cloud import bigquery

    client = bigquery.Client()
    sql = f"""
        SELECT *
        FROM `{table}`
        WHERE feature_as_of < DATE('{as_of}')
          AND {label_column} IS NOT NULL
    """
    return client.query(sql).to_dataframe()


def train(args):
    df = load_training_data(args.train_table, args.label_column, args.as_of)
    print(f"[train] rows={len(df)} columns={list(df.columns)}")

    feature_cols = [
        c for c in df.columns
        if c not in (args.label_column, "user_id", "feature_as_of")
    ]
    X = df[feature_cols]
    y = df[args.label_column].astype(int)

    # Stratify so the class balance is preserved in both splits.
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=args.seed, stratify=y
    )
    print(f"[train] train={len(X_train)} validation={len(X_val)}")

    model = GradientBoostingClassifier(
        n_estimators=args.epochs,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth,
        subsample=0.9,
        random_state=args.seed,
    )
    model.fit(X_train, y_train)

    val_scores = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, val_scores)
    pr_auc = average_precision_score(y_val, val_scores)
    print(f"[train] validation AUC={auc:.4f} PR-AUC={pr_auc:.4f}")

    importances = sorted(
        zip(feature_cols, model.feature_importances_),
        key=lambda kv: kv[1],
        reverse=True,
    )
    for name, value in importances:
        print(f"[train]   importance {name:28s} {value:.4f}")

    # THE ARTEFACT CONTRACT. Vertex collects everything in AIP_MODEL_DIR.
    output_dir = os.environ.get("AIP_MODEL_DIR", "/tmp/model")
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(model, os.path.join(output_dir, "model.joblib"))

    with open(os.path.join(output_dir, "metrics.json"), "w") as f:
        json.dump({
            "auc": float(auc),
            "pr_auc": float(pr_auc),
            "n_rows": int(len(df)),
            "feature_cols": feature_cols,
            "importances": {k: float(v) for k, v in importances},
            "as_of": args.as_of,
            "seed": args.seed,
        }, f, indent=2)

    return model


if __name__ == "__main__":
    train(get_args())
```

### Exercise 2 — The Vertex training job, end to end

```python
from google.cloud import aiplatform

PROJECT_ID = "my-project"
REGION = "us-central1"

aiplatform.init(project=PROJECT_ID, location=REGION)

job = aiplatform.CustomJob(
    display_name="churn-model-v1",
    worker_pool_specs=[
        aiplatform.machine_spec.MachineSpec(
            machine_type="n1-standard-4",
            replica_count=1,
            accelerator_count=0,
            accelerator_type="",
        )
    ],
    base_output_dir=f"gs://{PROJECT_ID}-vertex-models/churn/v1",
)

model = job.run(
    source_distribution=aiplatform.python_source_distribution.TrainingDistribution(
        source_dir="src/training",
        entry_point="trainer",
    ),
    args=[
        "--train-table", f"{PROJECT_ID}.curated.user_features_daily",
        "--label-column", "churned_30d",
        "--as-of", "2026-01-16",
        "--epochs", "100",
        "--learning-rate", "0.1",
        "--max-depth", "6",
        "--seed", "42",
    ],
    sync=True,
)

print(f"model resource name: {model.resource_name}")
```

### Exercise 3 — The cost model, with the course module

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, VERTEX_AI_TRAINING_PER_NODE_HOUR

print(f"Vertex AI training list rate: ${VERTEX_AI_TRAINING_PER_NODE_HOUR}/node-hour\n")

# A single training job: 4 node-hours on n1-standard-4.
single = estimate("vertex-ai", training_node_hours=4, monthly=False)
print("Single training job (4 node-hours):")
for line in single.lines:
    print(f"  {line.label:30s} {line.quantity:8.1f} {line.unit:14s} ${line.cost:8.2f}")
print(f"  {'TOTAL':30s} {'':8s} {'':14s} ${single.total:8.2f}")

# Hyperparameter tuning: 20 trials x 4 node-hours.
tuning = estimate("vertex-ai", training_node_hours=20 * 4, monthly=False)
print(f"\nHyperparameter tuning (20 trials x 4 node-hours = 80 node-hours):")
print(f"  TOTAL: ${tuning.total:,.2f}")

# Monthly retraining with tuning, plus an always-on endpoint.
MONTHLY_TRAIN_HOURS = 20 * 4 + 4
monthly = estimate(
    "vertex-ai",
    training_node_hours=MONTHLY_TRAIN_HOURS,
    monthly=False,
)
print(f"\nMonthly retrain + tune ({MONTHLY_TRAIN_HOURS} node-hours): ${monthly.total:,.2f}")

# Compare against a pre-trained API for the same volume.
API_PER_1000 = 1.50
MONTHLY_CALLS = 50_000
api_monthly = (MONTHLY_CALLS / 1000.0) * API_PER_1000
print(f"\nPre-trained API: {MONTHLY_CALLS:,} calls/month at ${API_PER_1000}/1000")
print(f"  API inference only: ${api_monthly:,.2f}/month")
print(f"  Vertex training only: ${monthly.total:,.2f}/month")
print(f"  Ratio: {monthly.total / api_monthly:.1f}x")
print("\n(The endpoint cost is additional to both. The point is that the")
print(" training compute is not the deciding factor — the pipeline around")
print(" it is.)")
```

### Exercise 4 — The endpoint, traffic splitting, and the canary comparison

```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location=REGION)

endpoint = aiplatform.Endpoint(
    display_name="churn-endpoint",
    project=PROJECT_ID,
    location=REGION,
)

# Deploy v7 and v8 together, 90/10.
endpoint.deploy(
    model=aiplatform.Model(
        model_name="churn-model", version="7", project=PROJECT_ID
    ),
    machine_type="n1-standard-4",
    min_replica_count=1,
    max_replica_count=10,
    traffic_split={"7": 90, "8": 10},
    sync=True,
)

# Promote the new version by moving the traffic, not by redeploying.
endpoint.update_traffic_split({"7": 50, "8": 50})

# The canary needs a comparison. Log the version ID with every
# prediction so the two populations can be separated.
endpoint.enable_prediction_logging(logging_filter="")


def canary_comparison(log_rows):
    """Compare two model versions from the prediction log.

    The point: a canary without a comparison metric is just a random
    traffic split. Compare the score distribution and the positive
    rate; once labels mature, compare actual performance.
    """
    from collections import defaultdict

    by_version = defaultdict(list)
    for row in log_rows:
        by_version[row["model_version_id"]].append(row)

    results = {}
    for version, rows in by_version.items():
        scores = [r["churn_score"] for r in rows]
        positives = sum(1 for s in scores if s >= 0.35)
        results[version] = {
            "n": len(scores),
            "mean_score": sum(scores) / len(scores) if scores else 0.0,
            "positive_rate": positives / len(scores) if scores else 0.0,
            "p95": sorted(scores)[int(len(scores) * 0.95)] if scores else 0.0,
        }
    return results
```

### Exercise 5 — The model registry, versions, and aliases

```python
def register_model_version(
    model_display_name,
    source_uri,
    labels,
    metrics,
    stage=None,
):
    """Upload a trained artefact to the registry as a new version."""
    from google.cloud import aiplatform

    aiplatform.init(project=PROJECT_ID, location=REGION)

    uploaded = aiplatform.Model.upload(
        display_name=model_display_name,
        serving_container_image_uri=(
            "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"
        ),
        artifact_uri=source_uri,
    )

    uploaded.version_info = aiplatform.VersionInfo(
        description=labels.get("description", ""),
        labels={k: v for k, v in labels.items() if k != "description"},
    )
    uploaded.metrics = [
        aiplatform.Metric(display_name=name, value=value, step=1)
        for name, value in metrics.items()
    ]
    uploaded.save()

    if stage is not None:
        uploaded.update_stage(stage)

    return uploaded


def set_alias(model, alias, version_id):
    """Point a mutable alias at a specific model version."""
    aiplatform.init(project=PROJECT_ID, location=REGION)
    model = aiplatform.Model(
        model_name=model, version=version_id, project=PROJECT_ID
    )
    model.set_alias(alias)
    print(f"alias '{alias}' -> version {version_id}")


def get_production_version(alias="production"):
    """Resolve the alias to the version currently in production."""
    aiplatform.init(project=PROJECT_ID, location=REGION)
    parent = aiplatform.Model(
        model_name="churn-model", project=PROJECT_ID
    )
    model_version = parent.get_model_version(alias)
    return model_version.version
```

**The alias is the whole point.** Consumers reference `production`; the version number behind it changes without any consumer change. That is what makes a zero-downtime promotion possible.

### Exercise 6 — The kfp pipeline with an evaluation gate

```python
from kfp import dsl
from kfp.dsl import Input, Output, Path


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["scikit-learn==1.5.2", "pandas==2.2.3", "joblib==1.4.2"],
)
def evaluate_model_component(
    model_path: Input[Path],
    eval_table: str,
    label_column: str,
    min_auc: float,
    metrics_out: Output[Path],
) -> float:
    """Evaluate the model and FAIL the pipeline if it is not good enough.

    A pipeline that always deploys is not a pipeline with a gate. The
    gate is what stops a bad training run from reaching production.
    """
    import json
    import joblib
    import os

    import numpy as np
    import pandas as pd
    from sklearn.metrics import roc_auc_score, average_precision_score

    model = joblib.load(model_path)

    # In production: query BigQuery. Here the table is provided by the
    # caller. The evaluation set must be the TEST set, which the
    # training script never touched.
    df = pd.read_csv(eval_table)
    feature_cols = [
        c for c in df.columns
        if c not in (label_column, "user_id", "feature_as_of")
    ]
    X = df[feature_cols]
    y = df[label_column].astype(int)

    scores = model.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, scores)
    pr_auc = average_precision_score(y, scores)

    metrics = {"auc": float(auc), "pr_auc": float(pr_auc), "n": int(len(df))}
    with open(metrics_out, "w") as f:
        json.dump(metrics, f)

    if auc < min_auc:
        raise ValueError(
            f"gate failed: AUC {auc:.4f} < required {min_auc:.4f}. "
            f"Model will not be promoted."
        )
    return auc


@dsl.pipeline(name="churn-mlops")
def churn_pipeline(
    project_id: str = PROJECT_ID,
    region: str = REGION,
    train_table: str = "my-project.curated.user_features_daily",
    eval_table: str = "my-project.curated.user_features_test.csv",
    label_column: str = "churned_30d",
    model_display_name: str = "churn-model",
    model_dir: str = "gs://my-project-vertex-models/churn",
    min_auc: float = 0.85,
):
    train_op = train_model_op(
        project_id=project_id,
        region=region,
        train_table=train_table,
        label_column=label_column,
        model_display_name=model_display_name,
        model_dir=model_dir,
    )

    # The gate. If this component raises, the pipeline fails and the
    # deployment step never runs.
    evaluate_op = evaluate_model_component(
        model_path=train_op.outputs["model_artifact"],
        eval_table=eval_table,
        label_column=label_column,
        min_auc=min_auc,
    )

    deploy_op = deploy_model_op(
        model_uri=train_op.outputs["model_uri"],
        traffic_split=50,
    )


@dsl.component(base_image="python:3.11-slim")
def deploy_model_op(model_uri: str, traffic_split: int) -> str:
    """Deploy the model to the endpoint and shift traffic to it."""
    from google.cloud import aiplatform

    aiplatform.init()
    endpoint = aiplatform.Endpoint(endpoint_name="churn-endpoint")
    endpoint.deploy(
        model=aiplatform.Model(model_name="churn-model", version="candidate"),
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=10,
        traffic_split={"candidate": traffic_split},
        sync=True,
    )
    return endpoint.resource_name
```

### Exercise 7 — Build a training matrix from the course project

The data-engineering half of the ML work.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    build_bigquery_rows,
    aggregate_events,
    render_summary_csv,
)
from collections import defaultdict

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

PREDICTION_CUTOFF = "2026-01-16T00:00:00+00:00"

history = defaultdict(list)
for r in rows:
    if r["event_dt"] < PREDICTION_CUTOFF:
        history[r["user_id"]].append(r)

feature_rows = []
for user_id, events in history.items():
    orders = [e for e in events if e["event_type"] == "order"]
    refunds = [e for e in events if e["event_type"] == "refund"]
    views = [e for e in events if e["event_type"] == "page_view"]
    total = sum(o["amount_eur"] for o in orders)

    feature_rows.append({
        "user_id": user_id,
        "n_events": len(events),
        "n_orders": len(orders),
        "n_refunds": len(refunds),
        "n_page_views": len(views),
        "total_spend_eur": round(total, 2),
        "avg_order_value_eur": round(total / len(orders), 2) if orders else 0.0,
        "refund_rate": round(len(refunds) / len(events), 4),
        "order_rate": round(len(orders) / len(events), 4),
        "region": events[0]["region"],
        "channel": events[0]["channel"],
        "feature_as_of": "2026-01-16",
        "churned_30d": 1 if refunds else 0,
    })

print(f"training rows: {len(feature_rows)}")
positives = sum(r["churned_30d"] for r in feature_rows)
print(f"positives: {positives}  rate: {positives/len(feature_rows):.4f}")

# The sanity checks that belong in CI, not in a notebook.
assert len(set(r["churned_30d"] for r in feature_rows)) == 2, "single-class label"
assert all(r["feature_as_of"] == "2026-01-16" for r in feature_rows), "as-of mismatch"
assert all(r["n_events"] > 0 for r in feature_rows), "empty feature vector"

# The DDL the table needs.
print("\n--- BigQuery DDL ---")
print("""
CREATE OR REPLACE TABLE `my-project.curated.user_features_daily` (
  user_id             STRING   NOT NULL,
  n_events            INT64    NOT NULL,
  n_orders            INT64    NOT NULL,
  n_refunds           INT64    NOT NULL,
  n_page_views        INT64    NOT NULL,
  total_spend_eur     FLOAT64  NOT NULL,
  avg_order_value_eur FLOAT64  NOT NULL,
  refund_rate         FLOAT64  NOT NULL,
  order_rate          FLOAT64  NOT NULL,
  region              STRING   NOT NULL,
  channel             STRING   NOT NULL,
  feature_as_of       DATE     NOT NULL,
  churned_30d         INT64    NOT NULL
)
PARTITION BY feature_as_of
CLUSTER BY region, channel;
""")
```

Note the partitioning on `feature_as_of` and the clustering on `region, channel`. The training job reads the table on every retrain, so both reduce the bytes scanned — which is the difference between a $3.67 training run and an expensive one.

### Exercise 8 — The monitoring configuration and the drift alert

```python
def configure_monitoring(endpoint_name, training_dataset_id, threshold=0.01):
    """Set up skew, drift, and prediction logging on an endpoint."""
    from google.cloud import aiplatform

    aiplatform.init(project=PROJECT_ID, location=REGION)
    endpoint = aiplatform.Endpoint(
        endpoint_name=endpoint_name, project=PROJECT_ID, location=REGION
    )

    # 1. Prediction logging is the prerequisite for everything else.
    endpoint.enable_prediction_logging(logging_filter="")

    # 2. Skew detection: live feature values vs the training baseline.
    endpoint.create_skew_detection_config(
        data_source=aiplatform.DataSource(
            input_dataset_id=training_dataset_id,
            target_field="feature_as_of",
        )
    )

    # 3. Drift detection: live prediction distribution vs baseline.
    endpoint.create_drift_detection_config(
        drift_detection_config=aiplatform.gapic.EndpointService
            .DriftDetectionConfig(
                drift_thresholds={
                    "churn_score": aiplatform.gapic.EndpointService
                        .DriftDetectionConfig.Threshold(
                            value=threshold, deviation_from_baseline=False
                        ),
                },
            )
    )
    return endpoint


def build_alert_payload(feature, statistic, threshold, value):
    """The Pub/Sub message format for a Vertex monitoring alert."""
    import json
    return json.dumps({
        "alert_type": "vertex_model_monitoring",
        "feature": feature,
        "statistic": statistic,
        "threshold": threshold,
        "value": value,
        "severity": "high" if value > threshold * 2 else "medium",
        "action": "investigate_feature_pipeline",
    })
```

---

## 🛠️ Common Errors and Fixes

### 1. `google.api_core.exceptions.InvalidArgument: Both labels and ... ` — conflicting label operations

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: Both labels and import_all_annotations are specified
```

**Cause.** You passed `import_all_annotations=True` to `import_images()` *and* are separately pushing annotations with the Data Labelling API. The two are mutually exclusive.

**Fix.** Pick one path:

```python
# Path A: import the images with their existing annotations.
import_config = aiplatform.ImportImageConfig(
    gcs_source=gcs_source,
    import_all_annotations=True,      # annotations come with the import
)

# Path B: import images without annotations, then push them.
import_config = aiplatform.ImportImageConfig(
    gcs_source=gcs_source,
    import_all_annotations=False,     # annotations are pushed separately
)
```

### 2. `ValueError: Invalid feature` — the training and serving feature sets differ

**Symptom.** Training succeeds. The endpoint returns:

```text
google.api_core.exceptions.InvalidArgument: Invalid feature
```

**Cause.** The inference payload does not contain every feature the model was trained on, or contains one it does not know about. This happens when the feature list is maintained in two places — the training script and the serving code — and they drift.

**Fix.** Make the feature list a single artefact that both read. Write it to GCS at training time and load it at serving time:

```python
import json
import os

# At the end of training, alongside the model.
# `feature_cols` is the ordered list of feature names the model was
# trained on — the SAME list the training loop used, not a
# reconstruction of it.
feature_schema = {
    "features": [
        {"name": name, "dtype": "FLOAT64"}
        for name in feature_cols
    ],
    "order": feature_cols,
}
output_dir = os.environ.get("AIP_MODEL_DIR", "/tmp/model")
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, "feature_schema.json"), "w") as f:
    json.dump(feature_schema, f)
```

Then at serving time, validate before calling:

```python
def validate_payload(payload, schema):
    expected = set(schema["order"])
    received = set(payload.keys())
    missing = expected - received
    extra = received - expected
    if missing or extra:
        raise ValueError(
            f"feature mismatch: missing={sorted(missing)} extra={sorted(extra)}"
        )
    return payload
```

### 3. The training job "succeeds" but there is no model

**Symptom.** `job.run()` returns successfully. `model.resource_name` points at a version with no artefacts.

**Cause.** The artefact was written somewhere other than `$AIP_MODEL_DIR`. Vertex collects exactly what is in that directory.

**Fix.**

```python
import os

import joblib

# `model` is the fitted estimator. Vertex collects exactly what is in
# this directory — a file written anywhere else is invisible to it.
output_dir = os.environ.get("AIP_MODEL_DIR", "/tmp/model")
os.makedirs(output_dir, exist_ok=True)
joblib.dump(model, os.path.join(output_dir, "model.joblib"))
```

And assert it after training:

```python
import os

output_dir = os.environ.get("AIP_MODEL_DIR", "/tmp/model")
assert os.path.exists(os.path.join(output_dir, "model.joblib")), (
    f"model artefact not written to AIP_MODEL_DIR={output_dir}"
)
```

### 4. `403 Permission denied on resource projects/.../locations/.../endpoints/...`

**Symptom.**

```text
google.api_core.exceptions.Forbidden: Permission 'aiplatform.endpoints.predict' denied on resource
```

**Cause.** The calling identity lacks `roles/aiplatform.endpointUser` or `roles/aiplatform.user`.

**Fix.** Grant the narrow role for prediction and nothing more:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:scoring-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.endpointUser"
```

**Note:** `roles/aiplatform.user` is broad — it includes the ability to create and delete endpoints. If the caller only predicts, `roles/aiplatform.endpointUser` is the correct choice.

### 5. The hyperparameter tuning job tunes against the test set

**Symptom.** The tuning job reports an AUC of 0.97. The held-out test set scores 0.81.

**Cause.** The `tune_metric` was computed on the test split inside the training script, so 20 trials selected the configuration that happened to fit the test set best. The test set is now a validation set and its score is meaningless.

**Fix.** The training script must split its input into train and validation, and report the tuning metric on validation only. The test set lives in a different table entirely and is never read by the training job:

```python
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# Inside the training script — validation, not test.
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=args.seed, stratify=y
)
model.fit(X_train, y_train)
auc = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
print(f"[tune-metric] auc={auc}")   # this is what the tuner optimises
```

### 6. `ValueError: No such model version` when deploying

**Symptom.**

```text
google.api_core.exceptions.NotFound: No such model version
```

**Cause.** You referenced a version that does not exist, or referenced the *parent model* rather than a version. Deploying requires a **model version**, not a model.

**Fix.**

```python
# Wrong — a model parent, not a version.
aiplatform.Model(model_name="churn-model", project=PROJECT_ID)

# Right — a specific version.
aiplatform.Model(model_name="churn-model", version="7", project=PROJECT_ID)
```

And if the version genuinely does not exist, check the upload:

```python
parent = aiplatform.Model(model_name="churn-model", project=PROJECT_ID)
print([v.version for v in parent.list_versions()])
```

---

## 💡 Production Notes

- **Pin the container image by digest, not by tag.** `latest` changes. A pinned digest means the training run today and the retraining in eight months use byte-identical dependencies. Record the digest in the model version's labels.

- **Use a dedicated service account for the pipeline with only the roles it needs.** `roles/aiplatform.user`, `roles/storage.objectAdmin` on the model bucket, `roles/bigquery.dataViewer` on the training dataset, `roles/bigquery.jobUser`, and `roles/cloudtrace.agent`. A pipeline service account with `roles/owner` can delete every model in the project.

- **Keep the training data versioned and immutable.** The model version's labels should record the feature SQL SHA, the label table, and the label as-of date. "Which training data produced this model" must be one query, not an archaeology project.

- **Enable prediction logging at deploy time, not later.** Retrofitting logging onto a running endpoint means losing the historical data you need to establish a drift baseline — and the baseline is the thing monitoring compares against. Log the features alongside the score, not just the score.

- **Do not tune hyperparameters on every retraining.** Tune once, record the winning configuration, and reuse it. Tuning at $293.60 per run on a monthly cadence is $3,524/year spent rediscovering the same answer.

- **Set the endpoint's concurrency target deliberately.** Autoscales reacts to concurrency per replica, not CPU. Too high and p99 latency spikes under load; too low and you pay for replicas you do not need.

- **Scale to zero for spiky workloads.** `min_replica_count=0` costs nothing when idle. Do not use it for a latency-sensitive path — cold starts are seconds.

- **Use batch prediction for bulk scoring.** It costs a fraction of online serving and removes the always-on replica. Scoring 10 million customers nightly should never touch an online endpoint.

- **Do not automate retraining on a drift signal without an input-side guard.** If the drift is caused by a broken upstream pipeline, retraining propagates the breakage into the model. Gate on feature-table data-quality checks first.

- **Say "contribution", not "cause", when explaining a prediction.** SHAP decomposes a score into feature contributions. It does not establish a causal mechanism, and a customer-facing explanation that implies causation is a liability.

---

## 🔑 Key Takeaways

- **Train your own model when at least two of these hold:** the concept is genuinely yours, you need control over the objective, you need feature-level explainability, privacy/residency forbids a third-party call, the data shape breaks the pre-trained model's bias, or inference cost matters at scale.
- **Every custom model is a system you now own** — training pipeline, dependencies, image, feature parity, monitoring, retraining, and the pager.
- **Vertex AI's lifecycle is Datasets → Notebooks → Training → Registry → Endpoints → Monitoring**, and each stage is a separate resource with its own permissions. The gaps between them are where incidents live.
- **Datasets** are versioned containers for labelled data. The **console UI** supports active learning; the **Data Labelling API** pushes existing annotations without the UI.
- **Always include an "uncertain" label.** Without one, labellers guess, and the noise is invisible.
- **Labelling is the real budget.** 20,000 images at 20 seconds each is 111 human-hours — often 30× the training compute cost.
- **Notebooks are for exploration, not for the training pipeline.** They are not reproducible and not schedulable. Colab for two hours; Workbench for anything you return to.
- **`CustomJob` + a container + the `trainer` package** is the lowest-level training primitive. The `trainer` package turns args into typed objects and calls your `train()` function.
- **The `trainer` package is the contract.** Write the artefact to `$AIP_MODEL_DIR` or the job succeeds with no model — a genuinely easy mistake.
- **Pin container versions.** `latest` means your retraining in six months runs on a different CUDA build than you validated. Use a dated tag or a digest.
- **Prebuilt trainers** cover scikit-learn, XGBoost, TensorFlow, PyTorch, and deep learning. They save plumbing code but not control.
- **Hyperparameter tuning runs trials in parallel with Bayesian optimisation.** 20 trials × 4 node-hours = 80 node-hours = **$293.60** at $3.67/node-hour. That is a *recurring* cost if it is in the retraining pipeline.
- **Never tune against the test set.** The `tune_metric` must be computed on a validation split inside the training script. The test set lives in another table.
- **"Distributed" means three different things:** data parallel (split the data), model parallel (split the model), and distributed inference (replicate for serving). Only the third is one you will use often.
- **Distributed training must pay for itself.** Two nodes cost twice as much. For a nightly job, a single bigger node is often cheaper.
- **Shard by `index % world_size`, not by contiguous slices** — contiguous slices give each replica a non-representative shard of time-ordered data.
- **The Registry separates models, versions, deployments, and aliases.** **Aliases are the important mechanism**: consumers reference `production`, and promoting a version is an alias move, not a redeploy.
- **Model stages are a human convention, not an enforcement mechanism.** Vertex will not stop you deploying a `None` model.
- **Endpoints come in public and private flavours.** Deploy with `traffic_split` to run a canary — but **a canary without a comparison metric is just a random traffic split.**
- **Autoscaling reacts to concurrency, not CPU.** Set the concurrency target deliberately.
- **Batch prediction costs a fraction of online serving** for bulk scoring. Never score ten million customers through an online endpoint.
- **Feature importance is global; SHAP is per-prediction.** For an incident or a customer explanation, you need the per-prediction version.
- **An explanation is not a reason.** Say "contributed", not "caused".
- **Prediction logging is the prerequisite for all monitoring.** Without it, skew and drift detection are blind.
- **Vertex's drift detection compares live predictions to training predictions.** It catches covariate shift. It does **not** catch concept drift — that needs matured labels.
- **The right retraining design is a hybrid:** retrain on a schedule so the model does not rot, and gate promotion on an evaluation threshold so a bad run never reaches production.
- **Do not automate retraining on drift without an input-side guard.** A broken upstream pipeline plus drift-triggered retraining equals a model trained on garbage.
- **The cost of Vertex AI is not the training compute — it is the pipeline, the endpoint, and the retraining cadence around it.** A 20-trial monthly tuning plus an endpoint can exceed $7,000/year against $900/year for a pre-trained API at 50,000 calls/month.

---

## 📚 Practice Exercises

1. **Cost comparison, fully specified.** Using `cost_model.estimate("vertex-ai", training_node_hours=...)` and `VERTEX_AI_TRAINING_PER_NODE_HOUR`, build a five-year TCO for a churn model: monthly retraining (4 node-hours), quarterly hyperparameter tuning (20 trials × 4 node-hours), an always-on endpoint (1 replica), and monthly drift monitoring. Compare it against a pre-trained API at 50,000, 500,000, and 5,000,000 calls/month. State the break-even call volume and the conditions under which the answer changes.

2. **Training-data versioning.** Design the manifest for a Vertex training run: every field you would record, where it would live (BigQuery table, GCS JSON, Model Registry labels), and the query that answers "which training data produced model version 7?" Then implement `build_manifest()` and `verify_manifest()` that detects a mismatch between the recorded feature SQL SHA and the current file.

3. **The as-of training table.** Using `project/core/pipeline_logic.py` and `sample_data/events.csv`, build a training table with a label column, an as-of filter, and at least six features. Write the BigQuery DDL with partitioning and clustering, and the SQL that would produce the leaky version. Then write the test that detects the leak, and explain which metric each version reports.

4. **Training/serving parity harness.** Write `feature_contract.py` with a `build_features(row)` function used by both the training script and the serving code, a `validate_payload()` that checks the payload against the saved schema, and a parity test that runs 1,000 rows through both paths and asserts identical outputs. Then describe how you would deploy the schema so a drift in one path is caught in CI rather than in production.

5. **The canary comparison.** Write `compare_versions(log_rows, version_a, version_b)` that computes, for each version: the score distribution (mean, p50, p95), the positive rate at the operating threshold, the missing-feature rate, and — once labels are available — precision, recall, and calibration error. Then define the promotion criteria: what must be true on which metric before you move the alias from v7 to v8.

6. **Pipeline with a real gate.** Build a `kfp` pipeline with four components — train, evaluate, gate, deploy — where the gate raises if AUC is below a threshold or if the positive rate on the test set deviates by more than 20% from the training positive rate. Explain why the second check matters, and what it catches that the AUC check does not.

7. **Monitoring architecture.** Specify the full monitoring setup for the churn endpoint: the prediction log table schema and partitioning, the skew detection configuration for five features, the drift detection threshold, the Pub/Sub alert topic, the alerting policy, and the weekly evaluation job against matured labels. Include the SQL that computes the calibration error by score bucket.

8. **Migration decision.** You have a production churn model on Vertex AI that costs $8,400/year. A pre-trained API would cost $1,200/year but scores 0.03 lower AUC. Write the recommendation memo: what would have to be true about the business cost of a missed churn (the €180 saved value from Chapter 8.1) for the custom model to be worth it? Include the break-even false-negative rate.

---

## 📖 Further Reading

- [Vertex AI — Documentation](https://cloud.google.com/vertex-ai/docs)
- [Vertex AI — Custom Training Jobs](https://cloud.google.com/vertex-ai/docs/training/custom-training-methods)
- [Vertex AI — Create a Custom Job](https://cloud.google.com/vertex-ai/docs/training/create-custom-job)
- [Vertex AI — Hyperparameter Tuning Overview](https://cloud.google.com/vertex-ai/docs/training/hyperparameter-tuning-overview)
- [Vertex AI — Model Registry](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/model-registry/introduction)
- [Vertex AI — Deploy a Model to an Endpoint](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/predictions/deploy-model-api)
- [Vertex AI — Model Monitoring: Model Drift Overview](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/model-monitoring/overview)
- [Vertex AI — Model Explainability (SHAP)](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/ml-use)
- [Vertex AI Pipelines — Kubeflow Pipelines SDK](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/pipelines/introduction)
