# 5.6 — gcloud Dataflow CLI

> **Section 5 · Dataflow Templates & Deployment · Lecture 5.6 · 6:30**

## 🎯 What you will learn

- The complete `gcloud dataflow` command surface, organised
- `jobs list`, `describe`, `cancel`, `messages`, `graph`, `snapshot`
- `flex-template build` and `run`
- `templates list` and `describe`
- `regions`, and why you should stop hard-coding one
- `--format` and `--filter` — the two flags that make the CLI usable
- `jq` recipes for the extractions you actually need
- `--async`, and when it is different from `--wait=false`
- How to find the job that consumed your bucket
- Automating with a shell script
- Exit codes, and how to write a wait-loop that actually works
- `gcloud dataflow jobs` versus the older `gcloud beta dataflow`

---

## 🧠 Concept

### The command surface

```text
gcloud dataflow
├── jobs
│   ├── list
│   ├── describe
│   ├── cancel
│   ├── messages
│   │   ├── describe
│   │   └── list
│   ├── graph
│   │   ├── show
│   │   └── list
│   ├── snapshot
│   └── ...
├── flex-template
│   ├── build
│   └── run
├── templates
│   ├── list
│   └── describe
├── regions
└── operations
```

Everything in this chapter hangs off those five groups. The two flags that
turn this from a toy into a tool are `--format` and `--filter`.

### `--format`: the output control

Without `--format`, `gcloud` prints a human-readable table. That is fine
for a human and useless for a script. The options:

| Format | Output | Use |
|---|---|---|
| `--format=text` | a tab-separated table (the default) | piping to `cut`/`awk` |
| `--format=json` | pretty-printed JSON | `jq` |
| `--format=json --flatten="..."` | JSON with nested objects flattened | `jq` without `.` gymnastics |
| `--format=csv` | comma-separated | spreadsheets |
| `--format='value(field)'` | just the value of one field | scripting |
| `--format='table(field1,field2)'` | selected columns | humans |
| `--format='value(format.json)'` | a JSON value | `--format='value(format.json)'` for a whole record |
| `--format=export` | CSV with headings | bulk export |
| `--format=yaml` | YAML | config files |

The `value()` form is the workhorse:

```bash
# Just the state
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)'

# Just the job ID
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(id)'

# Just the creation time
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(createTime)'
```

The `table()` form selects columns and computes new ones:

```bash
gcloud dataflow jobs list \
  --project=YOUR_PROJECT_ID \
  --format='table(name, state, createTime, type, region)' \
  --limit=20
```

You can rename a column in the header:

```bash
--format='table(name,state,createTime,type:TYPE)'
```

And you can apply a function to a field:

```bash
--format='value(status.state)'                     # plain
--format='value(format.json)'                      # whole record as JSON
--format='table(name,createTime:date)'             # human date
```

### `--filter`: the query language

`--filter` takes a Google Cloud filter expression. It is applied
server-side, so it is fast and it does not need the whole list downloaded.

```bash
# Running jobs only
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='state=RUNNING'

# Failed jobs in the last week
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='state=FAILED AND createTime>"2026-10-21T00:00:00Z"'

# Jobs whose name starts with a prefix
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='name~"^orders-"'

# Jobs with a label
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='labels.env=prod'

# Multiple values for one field
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='(state=RUNNING OR state=FAILED) AND region=us-central1'
```

The operators that matter:

| Operator | Meaning | Example |
|---|---|---|
| `=` | equals | `state=RUNNING` |
| `:` | has substring | `name:orders` |
| `~` | regex match | `name~"^orders-[0-9]+$"` |
| `>` `<` `>=` `<=` | comparison | `createTime>"2026-10-01T00:00:00Z"` |
| `AND` `OR` `NOT` | boolean | `state=FAILED AND NOT name:debug` |
| `*` | prefix wildcard | `name=orders-*` |

**The most valuable filter on Dataflow is on the template path**, because
it is how you find the job that consumed a given bucket:

```bash
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='environment.templateLocation:gs://YOUR_BUCKET' \
  --format='table(name,state,createTime,environment.templateLocation)'
```

### `gcloud dataflow jobs list`

```bash
gcloud dataflow jobs list \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --filter='state=RUNNING' \
  --format='table(name,state,createTime,type)' \
  --limit=25 \
  --sort-by='~createTime'
```

| Flag | Meaning |
|---|---|
| `--project` | the project that owns the jobs |
| `--region` | limit to one region (omit for all regions) |
| `--filter` | server-side filter expression |
| `--format` | output format |
| `--limit` | maximum number of jobs to return |
| `--sort-by` | sort expression; `~` means descending |
| `--page-size` | how many per API request |

Without `--region`, the list covers **every region** the project has jobs
in. With `--sort-by='~createTime'` you get the newest first, which is
almost always what you want.

### `gcloud dataflow jobs describe`

The full record for one job. This is the richest command in the surface.

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID
```

```bash
# Just the state
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)'

# The current state, the SDK version, and the template
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(format.json)' | jq '{
            state: .status.state,
            sdk: .environment.sdkSupportStatus,
            template: .environment.templateLocation,
            region: .region,
            workers: .environment.workerMachineType
          }'

# The parameters the job was launched with
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format=json | jq -r '.parameters // "none"'
```

The `describe` record contains: `id`, `name`, `currentState`, `type`,
`createTime`, `region`, `projectId`, `environment` (SDK support status,
worker machine type, template location, experiments, Python version),
`parameters` (the `--parameters` string), `labels`, `metrics` (the live
metric values), and `steps` (the graph stages).

### `gcloud dataflow jobs cancel`

```bash
gcloud dataflow jobs cancel JOB_ID --project=YOUR_PROJECT_ID

# A batch job, with a human-readable reason
gcloud dataflow jobs cancel JOB_ID --project=YOUR_PROJECT_ID \
  --reason="Superseded by run 2026-10-28-14"

# A streaming job
gcloud dataflow jobs cancel JOB_ID --project=YOUR_PROJECT_ID
```

The job goes `CANCELLING` → drains → `CANCELLED`. It is not instantaneous.
If a worker is stuck in a long `DoFn`, the drain waits for it.

There is no `--force` in the standard surface. If a job is truly wedged,
the service's zombie-job cleanup eventually fails it.

### `gcloud dataflow jobs messages`

The job's user-facing messages — the ones Dataflow posts to the job's
message log, such as "Job exceeded the maximum number of workers" or
"Autoscaling is disabled".

```bash
# All messages
gcloud dataflow jobs messages list JOB_ID --project=YOUR_PROJECT_ID

# One message by ID
gcloud dataflow jobs messages describe MESSAGE_ID \
  --project=YOUR_PROJECT_ID --region=us-central1

# The latest message, for scripting
gcloud dataflow jobs messages list JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(messageText)' | tail -1
```

This is the wrong command for worker logs. Worker logs live in Cloud
Logging; `jobs messages` is the service's own commentary. Both are useful;
they answer different questions.

### `gcloud dataflow jobs graph`

```bash
# The graph as JSON
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format=json > graph.json

# Just the stage names
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(graph.stages[].name)'

# The number of steps per stage
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format=json \
  | jq -r '.graph.stages[] | "\(.name): \(.executionGraphSpec.stages[].spec | length) steps"'

# The graph as a picture, for a ticket
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format=json | jq '.graph' > stage.json
```

The graph JSON has three levels:

```text
graph
└── stages[]                     one per stage
    ├── name                     "s1", "s2", ...
    ├── id                       the stage ID
    ├── executionGraphSpec
    │   ├── stages[]             one per *step* within the stage
    │   │   ├── spec             the transform name (your label)
    │   │   ├── transformId      the fully-qualified transform
    │   │   └── inputs[]         upstream step names
    │   └── fusedStages[]        steps fused into this one
    └── primitiveGraphSpec       the low-level PCollection topology
```

`executionGraphSpec.stages` is where your labels live. `fusedStages` is
where fusion shows up — a step that has been fused into another appears
there, not in `stages`.

### `gcloud dataflow jobs snapshot`

A snapshot captures the graph and the job state at a moment in time. It is
useful for archiving a failed job's shape before you cancel it, and for
diffing a job's graph against a known-good one.

```bash
# Take a snapshot
gcloud dataflow jobs snapshot JOB_ID --project=YOUR_PROJECT_ID \
  --region=us-central1 --output-file=snapshot.json

# List existing snapshots
gcloud dataflow jobs snapshots list JOB_ID --project=YOUR_PROJECT_ID

# Delete a snapshot
gcloud dataflow jobs snapshots delete SNAPSHOT_ID \
  --project=YOUR_PROJECT_ID --region=us-central1
```

Snapshots are also the mechanism behind the job graph's "snapshot" button
in the Dataflow UI.

### `gcloud dataflow flex-template build` and `run`

```bash
gcloud dataflow flex-template build JOB_NAME \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --template-file=./orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging
```

```bash
gcloud dataflow flex-template run JOB_NAME \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --template=gs://YOUR_BUCKET/templates/orders-etl.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging \
  --service-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --parameters="input=gs://YOUR_BUCKET/orders.csv" \
  --wait=false
```

Chapter 5.2 covers both in depth. The CLI-relevant summary:

| Flag | `build` | `run` |
|---|---|---|
| `--template-file` | yes | no |
| `--template-file-gcs-path` | yes | no |
| `--template` | no | yes |
| `--parameters` | no | yes |
| `--wait` / `--wait=false` | no | yes |
| `--metadata` | yes | no |
| `--py-files` | yes | no |
| `--requirements-file-requirements` | yes | no |
| `--sdk-location` | yes | no |

### `gcloud dataflow templates list` and `describe`

```bash
# Every template in the project
gcloud dataflow templates list \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --format='table(name,createTime,description)'

# One template
gcloud dataflow templates describe orders-etl \
  --project=YOUR_PROJECT_ID --region=us-central1

# The GCS path of the template
gcloud dataflow templates describe orders-etl \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --format='value(templateFileGcsPath)'
```

A "template" in this sense is a *registered* template — one that has been
built. The registration is what makes `templates list` show it. A file in
GCS that was never `build`-ed is not a registered template, and the
`templates` commands will not find it.

The description includes the `metadata` you passed at build time, which is
where your version stamp lives:

```bash
gcloud dataflow templates describe orders-etl \
  --project=YOUR_PROJECT_ID --region=us-central1 --format=json \
  | jq '.metadata'
```

### `gcloud dataflow regions`

```bash
gcloud dataflow regions list --project=YOUR_PROJECT_ID \
  --format='table(name,locationId,displayName)'
```

| Column | Meaning |
|---|---|
| `name` | the region name you pass to `--region` |
| `locationId` | the underlying Google Cloud location (`us-central1`) |
| `displayName` | a human-readable name |

Use it rather than hard-coding `us-central1`, because the right region
depends on where your data is and where your users are — and those change.

### `--async` versus `--wait=false`

These sound similar and are not the same thing.

| | `--wait=false` | `--async` |
|---|---|---|
| Available on | `flex-template run` | every `gcloud` command, including `jobs run` |
| Effect | do not wait for the *job* to finish | do not wait for the *gcloud command* to finish |
| Return value | the job ID | an operation, usually the job ID |
| Exit code | reflects submission success | reflects submission success |

`--async` is the general `gcloud` flag. `--wait=false` is specific to
`flex-template run`. When both are available, `--async` is the more
portable choice because it works with any command, including
`gcloud dataflow jobs run` and `gcloud batch jobs submit`.

```bash
# Both of these return immediately
gcloud dataflow flex-template run orders-etl ... --wait=false
gcloud dataflow jobs run gcs://bucket/template.py --async
```

Note the difference in how the job ID comes back. With `--wait=false` on
`flex-template run`, the job ID is printed. With `--async` on `jobs run`,
gcloud prints an **operation** — and you need a second command to get the
job ID out of it:

```bash
OPERATION=$(gcloud dataflow jobs run gcs://bucket/template.py \
  --project=YOUR_PROJECT_ID --region=us-central1 --async \
  --format='value(name)')

JOB_ID=$(gcloud dataflow operations describe $OPERATION \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --format='value(response.job.id)')

echo "job: $JOB_ID"
```

That two-step is a real operational cost. It is the main reason
`flex-template run --wait=false` is the better entry point for scripts.

### Finding the job that consumed your bucket

This is the question you ask when a bucket is filling up faster than
expected, or when you need to know what wrote to a table.

```bash
# Jobs whose template lives under a bucket prefix
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='environment.templateLocation:gs://YOUR_BUCKET' \
  --format='table(name,state,createTime)' \
  --sort-by='~createTime' --limit=20

# Jobs by display name
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='name~"orders"' \
  --format='table(name,state,createTime)' \
  --sort-by='~createTime'

# Jobs with a label you set at submission
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='labels.pipeline=orders-etl' \
  --format='table(name,state,createTime)'

# Jobs launched with a particular parameter
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='parameters:"orders.csv"' \
  --format='table(name,state,createTime)'
```

The last one is the most precise and the least obvious. The `parameters`
field holds the raw `--parameters` string, so a filter on a substring of it
finds exactly the runs that used that input.

Adding labels at submission time is the most durable answer, because the
filter does not depend on the template path or the parameter formatting
staying stable:

```bash
gcloud dataflow flex-template run orders-etl \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --template=$TEMPLATE \
  --labels="pipeline=orders-etl,env=prod,owner=data-platform" \
  ...
```

### Exit codes

`gcloud` follows the standard Unix convention:

| Exit code | Meaning |
|---|---|
| `0` | success |
| `1` | a generic error — the command failed |
| `2` | a usage error — bad flag, missing argument |
| `3` | the command was interrupted (Ctrl-C) |
| `4` | an internal error in `gcloud` |
| `5` | a configuration error — usually a missing `gcloud` config or credentials |

The trap: with `flex-template run` and the **default** `--wait`, the exit
code reflects the *job's* fate. With `--wait=false`, it reflects only the
*submission*. A script that does:

```bash
gcloud dataflow flex-template run ... --wait=false
if [ $? -ne 0 ]; then echo "failed"; fi
```

will report success for a job that fails ten minutes later. The only
correct check is to poll the state.

### `gcloud dataflow jobs` versus `gcloud beta dataflow`

`gcloud beta dataflow` is the older, unstable surface. It still exists and
some scripts in the wild use it.

| | `gcloud dataflow` (GA) | `gcloud beta dataflow` |
|---|---|---|
| Stability | stable; the API is versioned | unstable; commands change without notice |
| Output format | `--format` with the full formatting engine | older, narrower format support |
| `--filter` | the full filter expression language | limited support |
| New commands | added regularly | may lag or vanish |
| Documentation | complete and current | often stale |
| Recommendation | **use this** | migrate away from it |

Migration is usually mechanical. The command names are the same or nearly
so; the differences are in the flags:

```bash
# Old
gcloud beta dataflow jobs list --project=YOUR_PROJECT_ID \
  --format="value(name)"

# New
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --format='value(name)'
```

The most common breakages when migrating:

1. **`--format="value(field)"` vs `--format=value(field)`** — both work,
   but the quoting style differs between the old and new surfaces. Quote
   the whole expression.
2. **`--status` became `--filter='state=...'`**. The old surface had
   `--status=RUNNING`; the new one uses the filter language.
3. **Output field names changed.** `currentState` is now `status.state`
   in the JSON. Check with
   `gcloud dataflow jobs list --format=json | jq '.[0] | keys'`.
4. **`gcloud beta dataflow templates` had a different lifecycle** — the
   old "classic templates" were replaced by flex templates, and the old
   commands were removed rather than deprecated.

The rule: if a script uses `gcloud beta dataflow`, migrate it. The beta
surface can change under you without notice, and it will not tell you
until the script breaks at 3am.

---

## 🛠️ Hands-On: The CLI in Practice

### Check your environment first

```bash
gcloud version
gcloud config list
gcloud auth list
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/region us-central1
```

`gcloud config set` writes to your active configuration, which is
per-configuration-set. Use `gcloud config configurations list` to see them,
and `gcloud config configurations activate` to switch.

### List the regions you can use

```bash
gcloud dataflow regions list --project=YOUR_PROJECT_ID \
  --format='table(name,locationId,displayName)'
```

### List jobs, three ways

```bash
# Everything, newest first
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --format='table(name,state,createTime,type)' \
  --sort-by='~createTime' --limit=10

# Running only, in one region
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --region=us-central1 \
  --filter='state=RUNNING' \
  --format='table(name,state,createTime)' \
  --sort-by='~createTime'

# Failed in the last week
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='state=FAILED AND createTime>"2026-10-21T00:00:00Z"' \
  --format='table(name,state,createTime)' \
  --sort-by='~createTime'
```

### Extract a single value

```bash
# The state, on one line — perfect for scripting
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)'

# The job ID, for chaining
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(id)'

# Every job ID, one per line
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='state=RUNNING' \
  --format='value(id)'
```

### jq recipes

These are the extractions that come up repeatedly.

```bash
# The essentials, as one JSON object
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format=json | jq '{
    id: .id,
    name: .name,
    state: .status.state,
    created: .createTime,
    region: .region,
    template: .environment.templateLocation,
    sdk: .environment.sdkSupportStatus,
    machine: .environment.workerMachineType,
    parameters: .parameters
  }'

# The metrics worth watching
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format=json | jq '.metrics | {
    cpu_seconds: .estimatedCpuSeconds,
    max_workers: .maxWorkers,
    current_workers: .currentWorkers,
    worker_health: .workerHealth,
    bundle_size: .bundleSize,
    input_bytes: .inputBytes,
    output_bytes: .outputBytes
  }'

# Every running job, as a compact table
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='state=RUNNING' --format=json \
  | jq -r '.[] | [.name, .status.state, .createTime, .region] | @tsv'

# The cost of a job, in dollars (us-central1, $0.08/vCPU-hour)
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format=json \
  | jq -r '(.metrics.estimatedCpuSeconds // 0) / 3600 * 0.08'

# Job names matching a pattern, with their IDs
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='name~"orders"' --format=json \
  | jq -r '.[] | "\(.id)\t\(.status.state)\t\(.createTime)"'

# The top 10 most expensive jobs this month
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='createTime>"2026-10-01T00:00:00Z"' --format=json \
  | jq -r 'map(select(.metrics.estimatedCpuSeconds != null))
           | sort_by(-.metrics.estimatedCpuSeconds)
           | .[:10][]
           | "\(.metrics.estimatedCpuSeconds)\t\(.name)\t\(.id)"'

# The labels on each job
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --format=json \
  | jq -r '.[] | select(.labels != null and .labels != {}) | "\(.name)\t\(.labels)"'
```

### Inspect the graph

```bash
# The stage names
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(graph.stages[].name)'

# The step labels inside each stage
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format=json \
  | jq -r '.graph.stages[]
           | .name as $s
           | (.executionGraphSpec.stages[]?.spec)
           | "\($s)\t\(.)"'

# Count the steps per stage — a proxy for how wide the pipeline is
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format=json \
  | jq -r '.graph.stages[]
           | "\(.name)\t\(.executionGraphSpec.stages | length) steps"'

# The fused steps — the ones that cost no extra I/O
gcloud dataflow jobs graph show JOB_ID --project=YOUR_PROJECT_ID \
  --format=json \
  | jq -r '.graph.stages[]
           | .executionGraphSpec.fusedStages[]?
           | "\(.primaryInput)\t\(.fusedStages)"'
```

### Find the job that touched a bucket

```bash
# By template path
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='environment.templateLocation:gs://YOUR_BUCKET' \
  --format='table(name,state,createTime)' \
  --sort-by='~createTime' --limit=10

# By parameter content
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='parameters:"orders.csv"' \
  --format='table(name,state,createTime)' \
  --sort-by='~createTime'

# By label
gcloud dataflow jobs list --project=YOUR_PROJECT_ID \
  --filter='labels.pipeline=orders-etl' \
  --format='table(name,state,createTime)'
```

### Snapshot a job's graph before you cancel it

```bash
gcloud dataflow jobs snapshot JOB_ID --project=YOUR_PROJECT_ID \
  --region=us-central1 --output-file=job-graph.json

gcloud dataflow jobs snapshots list JOB_ID --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --format='table(name,createTime,description)'
```

### The worked example: submit, poll, report

This is the complete script. It is the shape of every Dataflow automation
you will write.

```bash
#!/usr/bin/env bash
#
# submit_and_wait.sh — submit a flex template, poll for the result,
# report it, and exit with a meaningful status.
set -euo pipefail

PROJECT="${PROJECT:-YOUR_PROJECT_ID}"
REGION="${REGION:-us-central1}"
BUCKET="${BUCKET:-YOUR_BUCKET}"
DATASET="${DATASET:-YOUR_DATASET}"
JOB_NAME="${JOB_NAME:-orders-etl-$(date +%Y%m%d-%H%M%S)}"
TEMPLATE="gs://${BUCKET}/templates/orders-etl.py"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
POLL_INTERVAL="${POLL_INTERVAL:-20}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-3600}"

echo "== submitting $JOB_NAME =="

JOB_ID=$(gcloud dataflow flex-template run "$JOB_NAME" \
  --project="$PROJECT" \
  --region="$REGION" \
  --template="$TEMPLATE" \
  --temp-location="gs://${BUCKET}/dataflow/temp/${RUN_ID}" \
  --staging-location="gs://${BUCKET}/dataflow/staging/${RUN_ID}" \
  --service-account="dataflow-worker@${PROJECT}.iam.gserviceaccount.com" \
  --labels="pipeline=orders-etl,script=submit_and_wait" \
  --parameters="input=gs://${BUCKET}/orders.csv,bq-table=${PROJECT}.${DATASET}.orders_by_region" \
  --worker-machine-type=n1-standard-2 \
  --max-workers=10 \
  --min-workers=1 \
  --autoscaling_algorithm=Basic \
  --wait=false \
  --format='value(job.id)')

echo "== job id: ${JOB_ID} =="

START=$(date +%s)
STATE=""

while true; do
  STATE=$(gcloud dataflow jobs describe "$JOB_ID" \
    --project="$PROJECT" --format='value(status.state)' 2>/dev/null || echo "UNKNOWN")

  ELAPSED=$(( $(date +%s) - START ))
  echo "[$((ELAPSED / 60))m$((ELAPSED % 60))s] state=${STATE}"

  case "$STATE" in
    JOB_STATE_DONE)
      echo "== job succeeded =="
      break
      ;;
    JOB_STATE_FAILED|JOB_STATE_CANCELLED|JOB_STATE_UNKNOWN)
      echo "== job ended in state ${STATE} =="
      gcloud logging read \
        "resource.type=cloud_dataflow_job AND resource.labels.job_id=${JOB_ID} AND severity>=ERROR" \
        --project="$PROJECT" --limit=20 --sort-by="~timestamp" \
        --format='value(textPayload)' || true
      exit 1
      ;;
  esac

  if [ "$ELAPSED" -gt "$TIMEOUT_SECONDS" ]; then
    echo "== timeout after ${TIMEOUT_SECONDS}s, cancelling =="
    gcloud dataflow jobs cancel "$JOB_ID" --project="$PROJECT" || true
    exit 2
  fi

  sleep "$POLL_INTERVAL"
done

# ---- report ----
CPU=$(gcloud dataflow jobs describe "$JOB_ID" --project="$PROJECT" \
  --format=json | jq -r '.metrics.estimatedCpuSeconds // 0')
COST=$(echo "$CPU" | awk '{printf "%.4f", ($1 / 3600) * 0.08}')

echo "== report =="
echo "job_id     : ${JOB_ID}"
echo "job_name   : ${JOB_NAME}"
echo "state      : ${STATE}"
echo "cpu_seconds: ${CPU}"
echo "est_cost   : \$${COST} (us-central1, \$0.08/vCPU-hour)"

ROWS=$(bq query --project_id="$PROJECT" --use_legacy_sql=false --format=csv \
  "SELECT COUNT(*) FROM \`${PROJECT}.${DATASET}.orders_by_region\`" 2>/dev/null \
  | tail -1 || echo "n/a")
echo "rows       : ${ROWS}"
```

Run it:

```bash
chmod +x scripts/submit_and_wait.sh

PROJECT=YOUR_PROJECT_ID \
REGION=us-central1 \
BUCKET=YOUR_BUCKET \
DATASET=YOUR_DATASET \
TIMEOUT_SECONDS=1800 \
./scripts/submit_and_wait.sh
```

The exit codes mean something:

| Code | Meaning |
|---|---|
| `0` | the job reached `DONE` and the report was printed |
| `1` | the job failed, was cancelled, or the state became unknown |
| `2` | the poll loop exceeded `TIMEOUT_SECONDS` and cancelled the job |

### Verify the job from the CLI

```bash
# The output row count
bq query --project_id=YOUR_PROJECT_ID --use_legacy_sql=false --format=pretty \
  "SELECT COUNT(*) AS rows_in_table, ROUND(SUM(revenue_eur), 2) AS total_revenue
   FROM \`YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region\`"

# The checksum, to compare against the previous run
bq query --project_id=YOUR_PROJECT_ID --use_legacy_sql=false --format=pretty \
  "SELECT SUM(FARM_FINGERPRINT(
     CONCAT(region, '|', CAST(order_count AS STRING), '|',
            CAST(revenue_eur AS STRING)))) AS checksum
   FROM \`YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region\`"
```

---

## 🛠️ Common Errors and Fixes

### `ERROR: (gcloud.dataflow.jobs.list) Invalid choice: 'status'`

```text
ERROR: (gcloud.dataflow.jobs.list) Invalid choice: 'status'
```

`--status` was the beta-surface flag. The GA surface uses `--filter`:

```bash
# Old
gcloud beta dataflow jobs list --status=RUNNING

# New
gcloud dataflow jobs list --filter='state=RUNNING'
```

### `Invalid value for field: 'status'`

The field name changed. In the JSON, the state lives at `status.state`,
not `status`:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)'
```

### `Invalid filter: state`

```text
ERROR: (gcloud.dataflow.jobs.list) Invalid filter: state
```

The field is `state` in the *list* command but the JSON key differs. Check
what the filter language accepts:

```bash
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --format=json \
  | jq '.[0] | keys'
```

### The filter matches nothing

Most likely the job is in a different project or region. `jobs list`
without `--region` covers all regions, but it still only covers the
`--project` you named.

```bash
# Confirm the project
gcloud config get-value project

# List across all regions
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --limit=50
```

### `--format='value(...)'` prints nothing

The field path is wrong, or the value is null. Inspect the record first:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format=json | jq 'keys'
```

### `jq: error (at <stdin>:1): Cannot iterate over null`

The `jq` path assumed an array but `gcloud` returned an object. `jobs list`
returns an array; `jobs describe` returns a single object. Check which one
you have:

```bash
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --format=json | jq 'type'
```

### The job list is empty but the job exists

You are in the wrong region, or you passed `--limit=1` with an
unhelpful sort. The default sort is by creation time ascending, so the
job you want may be off the end:

```bash
gcloud dataflow jobs list --project=YOUR_PROJECT_ID --region=us-central1 \
  --sort-by='~createTime' --limit=50
```

### `--wait=false` returns success for a job that fails

That is the documented behaviour: with `--wait=false` the exit code
reflects the *submission*, not the job. Poll the state:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)'
```

### `gcloud: command not found: jq`

Install `jq`, or use `--format` expressions instead:

```bash
# Without jq
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='table(name,status.state,createTime)'
```

### `gcloud beta dataflow` and `gcloud dataflow` show different jobs

They query the same API, but the beta surface may default to a different
region or project. Always pass `--project` and `--region` explicitly to
both.

### The poll loop spins forever

Your script polls a state that will never change, or the state string does
not match your `case`. Print the raw state first and check the exact
string:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(status.state)' | cat -A
```

`JOB_STATE_DONE` is not `DONE`. Always add a timeout to the loop.

---

## 💡 Production Notes

- **Use `--filter`, not client-side filtering.** `gcloud dataflow jobs
  list --limit=1000 | grep RUNNING` downloads a thousand jobs and filters
  them locally. `--filter='state=RUNNING'` asks the API for ten. The
  difference is seconds versus milliseconds, and it scales.
- **Always pass `--project` explicitly.** `gcloud config get-value project`
  gives you the default, but relying on it in a script means the script
  behaves differently on a laptop and in CI. Make it an environment
  variable with a sensible default.
- **Use `--limit` and `--sort-by='~createTime'` together.** The default
  sort is oldest-first, which means `--limit=10` gives you the ten
  *oldest* jobs. This is a genuinely confusing default.
- **Label every job.** `--labels="pipeline=orders-etl,env=prod"` turns
  "which job wrote this table?" into a one-line filter that survives
  template-path changes and parameter-format changes. It is the cheapest
  observability in the CLI.
- **Archive the graph for failed jobs.** A snapshot before you cancel a
  failed job preserves the shape that caused the failure. Without it, you
  are reconstructing from memory.
- **Put the CLI calls in a script, not in a terminal.** The commands are
  long, the flags are easy to mistype, and a mistyped `--filter` silently
  returns nothing rather than erroring. A script with `set -euo pipefail`
  and an explicit timeout is strictly better.
- **Always give the poll loop a timeout.** A job that hangs should be
  cancelled by your script, not discovered by a human three days later.
- **Migrate off `gcloud beta dataflow` now.** The beta surface can change
  without notice and will not warn you. The migration is mechanical and
  the GA surface has better filter and format support.
- **`gcloud` config is per-configuration-set.** A CI job that assumes the
  default configuration may use the wrong project. Set everything
  explicitly, or use `CLOUDSDK_CONFIG` to point at a dedicated config
  directory.
- **Rate limits are real.** `gcloud` makes an API call per command, and
  listing jobs in a loop is a common way to hit the quota. Cache the job
  list once and query it locally rather than re-listing per iteration.

---

## 🔑 Key Takeaways

- The command surface is `jobs`, `flex-template`, `templates`, `regions`
  and `operations`. Everything else is a subcommand.
- `--format` turns the CLI into a scripting tool: `value(field)` for one
  value, `table(...)` for humans, `json` for `jq`.
- `--filter` is applied **server-side** and is the filter language, not
  the old `--status` flag. `state=RUNNING`, `name~"regex"`,
  `parameters:"substring"`, `labels.key=value` all work.
- `jobs messages` is the service's commentary; **worker logs are in Cloud
  Logging** via `gcloud logging read`.
- `jobs graph show --format=json` gives you stages, steps and
  `fusedStages` — the fusion view.
- `--async` is the general "do not wait" flag; `--wait=false` is the
  flex-template-specific one. `--async` on `jobs run` returns an
  *operation*, which costs a second command to get the job ID.
- **Exit codes with `--wait=false` reflect the submission, not the job.**
  Polling is the only correct check.
- `gcloud beta dataflow` is unstable and should be migrated away from.
- The canonical automation is **submit → poll with a timeout → report →
  exit meaningfully**.

---

## 📚 Practice Exercises

1. **Build a job inventory.** Write a script that lists every job in a
   project across all regions and emits a TSV with: job ID, name, state,
   type, create time, region, template path, and estimated cost in
   dollars. Sort by cost descending. Use `--filter` for the state
   filtering, not `grep`.

2. **A `jq` toolkit.** Write five `jq` expressions against
   `gcloud dataflow jobs list --format=json` that answer: (a) which jobs
   are still running, (b) which failed in the last 24 hours, (c) the total
   estimated cost of the last 7 days, (d) the job with the largest
   `estimatedCpuSeconds`, (e) the average job duration. Test each one.

3. **Find the culprit.** A bucket's storage is growing. Write a single
   command that finds the five most recent jobs that referenced that
   bucket, whether via template path or via a parameter. Then write a
   second command that finds the job that wrote to a specific BigQuery
   table. Explain why the second is harder.

4. **A robust wait-loop.** Write a shell function that takes a job ID and
   a timeout, polls every 15 seconds, prints the elapsed time and the
   state, exits 0 on `JOB_STATE_DONE`, exits 1 on `FAILED`/`CANCELLED`,
   and exits 2 on timeout after cancelling the job. Handle the case where
   `gcloud` itself fails transiently (retry the describe up to three
   times).

5. **Migrate a beta script.** Take a script that uses
   `gcloud beta dataflow jobs list --status=...` and
   `--format="value(name)"` and migrate it to the GA surface. Document
   every change and explain what would break if you left it.

6. **Audit the graph.** Write a script that takes a job ID and prints: the
   number of stages, the number of steps per stage, the number of fused
   steps, and a list of your transform labels that appear in more than one
   stage (which indicates a stage boundary you might be able to remove).
   Run it on a real job and interpret the result.

---

## 📖 Further Reading

- Google Cloud Dataflow: gcloud reference — https://cloud.google.com/dataflow/docs/guides/using-dataflow-with-gcloud
- Google Cloud SDK: formatting output — https://cloud.google.com/sdk/gcloud/reference/topic/formats
- Google Cloud SDK: filter expressions — https://cloud.google.com/sdk/gcloud/reference/topic/filters
- Google Cloud SDK: `gcloud topic filters` — https://cloud.google.com/sdk/gcloud/reference/topic/filters
- Google Cloud SDK: exit codes — https://cloud.google.com/sdk/gcloud/reference/topic/exit-codes
- Google Cloud Dataflow: monitoring and operations — https://cloud.google.com/dataflow/docs/guides/monitoring
