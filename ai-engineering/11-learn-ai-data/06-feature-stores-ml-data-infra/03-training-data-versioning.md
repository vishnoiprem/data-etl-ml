# Lesson 3 — Training Data Versioning

> **Type:** Article · Module 6 · Feature Stores & ML Data Infrastructure
> Versioning datasets, tying them to model versions, and reproducing a run.

---

## The reproducibility problem

> "A model in production is doing something different from the model I trained six months ago. I have the code. I have the training script. I don't have the data."

This is the **data scientist's nightmare** and the reason data versioning exists. A model is a function of three things:

```
   MODEL OUTPUT
        │
        ▼
   ┌────────────────────────────────────────┐
   │  CODE             ─ the training script │
   │  CONFIG           ─ hyperparameters     │
   │  DATA             ─ the training set    │
   │                                        │
   │  Change any of these → different model. │
   │  Reproduce ALL of them → same model.    │
   └────────────────────────────────────────┘
```

Most teams version code (git) and config (yaml). Few version data. The result is **unreproducible models**.

---

## What to version

| Asset | Tool | Why |
|---|---|---|
| **Raw training data** | DVC, Pachyderm, lakeFS, Delta Lake time travel | Re-create the dataset from raw |
| **Curated dataset** (after feature engineering) | Same | The model trains on this |
| **Labels** | Label Studio + DVC, Scale, custom | Labels change over time |
| **Splits** (train/val/test) | Same | Different splits → different metrics |
| **Code** | git | Training script |
| **Config** | git or DVC | Hyperparameters |
| **Environment** | Docker image hash, conda lock | Different pandas / Spark → different number |
| **Model weights** | MLflow / Weights & Biases / S3 | The artifact itself |

The hard part is **data**. Code is git. Data is multi-gigabyte parquet files in S3. DVC and lakeFS solve this by storing the actual data in object storage and version references in git.

---

## The DVC pattern

DVC (Data Version Control) stores a `data.dvc` file in git (a tiny pointer) and the actual data in S3/GCS/ADLS. Every commit to `data.dvc` is a new "version" of the data.

```bash
# Track a dataset
dvc add data/train.parquet

# This creates:
#   data/train.parquet.dvc    ← pointer, in git
#   data/.gitignore           ← ignore the actual file
# The file itself goes to the DVC remote (S3, GCS, ...)

# Push the data to remote
dvc push

# Later, reproduce the data
dvc pull
dvc checkout data/train.parquet --rev v1.2

# Run a pipeline with a specific data version
dvc repro --force
```

```
   git commit   ──►  data/train.parquet.dvc  ──►  hash of the parquet
                          │
                          ▼
                    dvc remote (S3/GCS)
                    stores actual files
```

---

## The lakeFS pattern

lakeFS turns your object store (S3, GCS, ADLS) into a **git-like repository**. Branches, commits, merges for data.

```bash
# Create a branch for an experiment
lakectl branch create s3://myrepo/experiment-v3

# Commit data changes
lakectl commit -m "added Q4 features" \
  s3://myrepo/experiment-v3/data/train.parquet

# Merge into main
lakectl merge s3://myrepo/experiment-v3 s3://myrepo/main
```

**Strength:** atomic operations on petabyte-scale data, no copy.
**Weak:** new API, requires lakeFS gateway.

---

## Delta Lake / Iceberg time travel

If your data is in Delta Lake or Iceberg, **time travel is built in**:

```sql
-- Read data as of a specific version
SELECT * FROM train_table VERSION AS OF 42;

-- Read data as of a timestamp
SELECT * FROM train_table TIMESTAMP AS OF '2026-01-15 02:00:00';
```

For ML pipelines, this is the lowest-friction option. **No new tool**, just discipline: tag the version, log it with the model.

```python
# In your training pipeline:
df = spark.read.format("delta") \
    .option("versionAsOf", run.config.data_version) \
    .table("train_table")
```

---

## Tying data, code, config to the model

The model artifact should reference **everything that produced it**:

```python
# MLflow example
import mlflow

with mlflow.start_run():
    # Tag with data version
    mlflow.set_tag("data_version", "v3.2")
    mlflow.set_tag("code_commit", subprocess.check_output(["git", "rev-parse", "HEAD"]).strip())
    mlflow.set_tag("config_hash", hashlib.md5(open("config.yaml", "rb").read()).hexdigest())
    mlflow.set_tag("image_hash", subprocess.check_output(["docker", "inspect", image]).decode())

    # Train
    model = train(df, config)

    # Log
    mlflow.sklearn.log_model(model, "model")
    mlflow.log_params(config)
    mlflow.log_metric("auc", auc)
```

Now, six months later, given the run ID, you can:

```
   given:  run_id = "abc123"
   get:    data_version = "v3.2"  →  lakectl checkout or DVC pull
           code_commit = "9f2c..." → git checkout that commit
           config_hash = "..."    → unzip the config from artifact store
           image_hash = "..."     → docker pull that hash
           → reproduce the model exactly.
```

---

## The "test set" versioning trap

```
   ┌────────────────────────────────────────────────────────────┐
   │  DON'T TOUCH THE TEST SET. EVER.                            │
   │                                                            │
   │  The test set is the contract with the future.              │
   │  It must be versioned ONCE and FROZEN.                      │
   │  Every model trains on it, but no model influences it.     │
   └────────────────────────────────────────────────────────────┘
```

If you "improve" the test set over time, you can no longer compare models. **Version the test set once. Lock it.**

Same for the **train/val split policy**. If you change how you split, you can't compare models across the change.

---

## Point-in-time correctness for backfills

When you version a training dataset, you must also **version the snapshot time**. If you backfill features for a 2024 model in 2026, you must use 2024's feature definitions — not today's.

```
   model from 2024-Q1:
     feature definitions: v1.2
     training data: snapshot at 2024-01-15

   in 2026-Q1, you want to retrain:
     use feature definitions: v1.2   ← same as before
     use training data: snapshot at 2026-01-15

   Why this matters: if you accidentally use today's
   feature definitions (v2.0) with 2024 data, you'll have
   look-ahead bias and backtest metrics will lie.
```

The feature store should support **point-in-time feature retrieval** for this reason — given a label timestamp, fetch features as they would have been computed then.

---

## The "what to log" checklist

For every training run:

- [ ] Git commit hash of code
- [ ] Config hash or full config dump
- [ ] Training dataset version (DVC/lakeFS/Delta version number)
- [ ] Snapshot timestamp (when the dataset was materialised)
- [ ] Feature definition versions used
- [ ] Label set version (especially for human-labelled data)
- [ ] Environment / container hash
- [ ] Random seeds
- [ ] Dependency lock file (pip / conda)
- [ ] Hardware (GPU type, count) — affects non-determinism

---

## What "good" looks like

- **Time-to-reproduce**: < 1 hour from run ID to a re-trained model with same metrics (±0.1%)
- **Audit trail**: every production model can answer "what data was it trained on?"
- **No test set drift**: the test set is a frozen artifact, versioned once
- **No label leakage**: labels never leak into features at training time

---

## What Comes Next

> Lesson 4 — **Online vs Offline Serving** — the dual-write problem, online store freshness, and the patterns that keep them in sync.