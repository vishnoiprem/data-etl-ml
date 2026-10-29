#!/usr/bin/env python3
"""
notebook_04.py — build notebook 04, Source Configuration & the gcloud CLI.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 04.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 04 · Source Configuration & the gcloud CLI

> **Module 3 · Configuring the Source · Lecture 3.1**

In this notebook you will:

- Learn the **five objects** a Datastream setup is made of, and how they
  relate
- Walk through the `gcloud` commands that create each one
- Understand the settings that actually matter: the **read consistency
  window**, the **replication user**, and the **network path**
- Learn the `gcloud` commands for **inspecting a running stream** — which is
  what you will use when something is wrong at 3am

Everything in this notebook runs locally against **mocked API responses**,
so you can learn the shape of the commands and their output without a GCP
account. The commands are real; only the calls are stubbed.
"""),
        code("""
import json
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

sys.path.insert(0, str(COURSE_ROOT / "project"))

print("course root:", COURSE_ROOT)
"""),
        md("""
## 1. The five objects

A Datastream setup is made of five things. Confusing them is the most
common source of "I set it up but nothing happens", because the error
messages refer to them by name.

| Object | What it is | Created with |
|---|---|---|
| **Network config** | The VPC peering and IP range Datastream uses to reach the source | `gcloud datastream network-configs create` |
| **Connection profile** | *How* to reach the source database (host, port, credentials) | `gcloud datastream connection-profiles create mysql` |
| **Source config** | *What* to capture — the tables, and the read settings | `gcloud datastream source-configs create mysql` |
| **Destination config** | Where the changes go, and the **merge keys** | `gcloud datastream destination-configs create bigquery` |
| **Stream** | The thing that ties them together and actually runs | `gcloud datastream streams create` |

```text
  Stream
    ├── Source config ──────────> Connection profile ──┐
    │                                                    │  points at
    │                                                    ▼
    │                                              Source database
    │
    └── Destination config ────> Connection profile ──┐
                                                         │  points at
                                                         ▼
                                                   BigQuery
```

The **stream** is the only object that "runs". The others are
configuration. When something is broken, the stream's status tells you
*which* of the other four to look at.

## 2. A mocked API, so you can practise without a project
"""),
        code("""
class MockDatastreamClient:
    \"\"\"A stand-in for the Datastream REST API.

    It records the requests it would have made and returns realistic
    responses, so the shape of the calls — and the shape of the responses
    you have to handle — can be practised offline.
    \"\"\"

    def __init__(self):
        self.requests = []

    def create_network_config(self, name, location, ip_address, netmask):
        self.requests.append({
            "method": "networkConfig.create",
            "name": name,
            "location": location,
        })
        return {
            "name": f"projects/demo/locations/{location}/networkConfigs/{name}",
            "displayName": name,
            "state": "READY",
        }

    def create_connection_profile(self, name, location, hostname, port):
        self.requests.append({
            "method": "connectionProfile.create",
            "name": name,
            "hostname": hostname,
        })
        return {
            "name": f"projects/demo/locations/{location}/connectionProfiles/{name}",
            "displayName": name,
            "state": "READY",
        }

    def create_source_config(self, name, location, profile, tables):
        self.requests.append({
            "method": "sourceConfig.create",
            "name": name,
            "profile": profile,
            "tables": tables,
        })
        return {
            "name": f"projects/demo/locations/{location}/sourceConfigs/{name}",
            "displayName": name,
            "state": "READY",
            "sourceConnectionProfile": profile,
        }

    def create_destination_config(self, name, location, profile, merge_keys):
        self.requests.append({
            "method": "destinationConfig.create",
            "name": name,
            "mergeKeys": merge_keys,
        })
        return {
            "name": f"projects/demo/locations/{location}/destinationConfigs/{name}",
            "displayName": name,
            "state": "READY",
            "destinationConnectionProfile": profile,
        }

    def create_stream(self, name, location, source, destination):
        self.requests.append({
            "method": "stream.create",
            "name": name,
        })
        return {
            "name": f"projects/demo/locations/{location}/streams/{name}",
            "displayName": name,
            "state": "READY",
            "sourceConfig": source,
            "destinationConfig": destination,
        }


client = MockDatastreamClient()
print("mock client ready")
"""),
        code("""
# Build the whole thing, in dependency order.
location = "us-central1"

network = client.create_network_config(
    "network-config", location, ip_address="10.0.0.2", netmask="255.255.255.240"
)
profile = client.create_connection_profile(
    "mysql-connection", location, hostname="10.0.0.3", port=3306
)
source = client.create_source_config(
    "mysql-source", location, profile["name"], tables=["inventory.customers"]
)
destination = client.create_destination_config(
    "bigquery-destination", location, "projects/demo/locations/us-central1/connectionProfiles/bigquery",
    merge_keys=["customer_id"],
)
stream = client.create_stream("main-stream", location, source["name"], destination["name"])

print(json.dumps(stream, indent=2))
"""),
        md("""
## 3. The real commands

The mocked calls above map onto these `gcloud` commands. Read them as the
authoritative version:

```bash
# 1. The network config and its IP allocation
gcloud datastream network-configs create network-config \\
    --location=us-central1 \\
    --network=projects/YOUR_PROJECT_ID/global/networks/default \\
    --service-account=YOUR_PROJECT_ID-datastream@YOUR_PROJECT_ID.iam.gserviceaccount.com

gcloud datastream network-configs ip-pools create pool \\
    --location=us-central1 \\
    --network-config=network-config \\
    --ip-address=10.0.0.2 \\
    --netmask=255.255.255.240

# 2. The source connection profile
gcloud datastream connection-profiles create mysql-connection mysql \\
    --location=us-central1 \\
    --hostname=10.0.0.3 \\
    --port=3306 \\
    --username=datastream_user \\
    --password=YOUR_PASSWORD \\
    --network=network-config

# 3. The source config
gcloud datastream source-configs create mysql-source mysql \\
    --location=us-central1 \\
    --source-connection-profile=mysql-connection \\
    --table=inventory.customers \\
    --read-consistency-window=5s

# 4. The destination connection profile
gcloud datastream connection-profiles create bigquery-connection bigquery \\
    --location=us-central1 \\
    --service-account=YOUR_PROJECT_ID-datastream@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 5. The destination config — note the merge keys
gcloud datastream destination-configs create bigquery-destination bigquery \\
    --location=us-central1 \\
    --destination-connection-profile=bigquery-connection \\
    --source-table=inventory.customers \\
    --target-table=datastream.customers \\
    --merge-keys=customer_id

# 6. The stream
gcloud datastream streams create main-stream \\
    --location=us-central1 \\
    --source=mysql-source \\
    --destination=bigquery-destination \\
    --backfill-all
```

### Two flags worth understanding

`--read-consistency-window=5s` — how long Datastream waits after a
transaction commits before reading its changes, to be sure it can see all
of them. Larger is more consistent and slower. This is the main latency
knob.

`--backfill-all` — copy the **existing** contents of the table before
starting the stream. Without it, the destination table starts empty and
fills up only with changes that happen after the stream starts — which is
almost never what you want, and is a confusing first run.
"""),
        md("""
## 4. Inspecting a running stream

When a stream is not working, these are the commands that tell you why.

```bash
# The stream's state — this is the first thing to check
gcloud datastream streams describe main-stream \\
    --location=us-central1 \\
    --format=json

# The stream's detailed status, including per-object state
gcloud datastream streams describe main-stream \\
    --location=us-central1 \\
    --format="value(streamState)"
```
"""),
        code("""
# A realistic stream state, and how to read it.
STREAM_STATE = {
    "state": "READY",
    "status": {
        "code": 7,
        "message": "The stream is running.",
    },
    "sourceConfig": {"state": "READY"},
    "destinationConfig": {"state": "READY"},
}

print("stream state      :", STREAM_STATE["state"])
print("source config     :", STREAM_STATE["sourceConfig"]["state"])
print("destination config:", STREAM_STATE["destinationConfig"]["state"])
print("message           :", STREAM_STATE["status"]["message"])
"""),
        md("""
The states you will see, and what each one means:

| State | Meaning | What to do |
|---|---|---|
| `READY` | Running normally | nothing |
| `CREATING` | Being set up | wait |
| `FAILED` | Broken | read the error message — it names the object |
| `PAUSED` | Stopped by an operator | resume it |
| `MIGRATING` | Being reconfigured | wait; do not cancel |

The error message is the important part. Datastream's errors are
specific about *which* object failed and why, and they name the common
causes directly — an unreachable host, a missing replication privilege, an
invalid merge key.

"""),
        code("""
# The three failures you will hit first, and what they say.
FAILURES = {
    "unreachable source": (
        "Failed to connect to source host 10.0.0.3:3306. "
        "Check the connection profile and the network config."
    ),
    "missing replication privilege": (
        "User 'datastream_user' does not have the REPLICATION SLAVE, "
        "REPLICATION CLIENT and SELECT privileges on 'inventory.customers'."
    ),
    "invalid merge key": (
        "The merge key 'customer_id' does not exist in the source table."
    ),
}

for label, message in FAILURES.items():
    print(f"--- {label} ---")
    print(f"  {message}\\n")
"""),
        md("""
## 5. The source-side requirements

Datastream reads the source's binary log, so the source must be configured
to produce one. These are the MySQL requirements:

```sql
-- The replication user needs these privileges
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'datastream_user'@'%';

-- The binary log must be enabled
-- (in my.cnf)
-- log_bin = /var/log/mysql/mysql-bin.log
-- binlog_format = ROW
-- binlog_row_image = FULL
```

Two of these settings are worth remembering:

| Setting | Value | Why |
|---|---|---|
| `binlog_format` | `ROW` | Row-based logging. `STATEMENT` breaks CDC — a multi-row statement becomes one ambiguous event |
| `binlog_row_image` | `FULL` | Logs every column. `MINIMAL` logs only the changed and key columns — faster, but the `before` images are incomplete, which breaks backfills and audit |

`binlog_format=ROW` is not optional for CDC. `STATEMENT` format records the
SQL statement rather than the row changes, and Datastream cannot use it.

## 6. Automating it with Terraform

The `project/terraform/` directory contains the same setup as Terraform.
Read it after the CLI version — the CLI is easier to debug, and the
Terraform is what you run in production.
"""),
        code("""
# The Terraform resource names, mapped to the CLI objects.
TERRAFORM_MAP = {
    "google_datastream_network_config": "network config",
    "google_datastream_network_config_ip_allocations": "IP allocation",
    "google_datastream_mysql_connection_profile": "source connection profile",
    "google_datastream_mysql_source_config": "source config",
    "google_datastream_bigquery_connection_profile": "destination connection profile",
    "google_datastream_bigquery_destination_config": "destination config",
    "google_datastream_stream": "stream",
}

for resource, description in TERRAFORM_MAP.items():
    print(f"{resource:<52} {description}")
"""),
        md("""
## What to take away

- Five objects: **network config, connection profiles (2), source config,
  destination config, stream**. The stream is the one that runs.
- The stream's state tells you which of the others is broken.
- `--read-consistency-window` is the main latency knob.
- `--backfill-all` is almost always what you want on first run.
- The source must have `binlog_format=ROW` and `binlog_row_image=FULL`.
"""),
    ])


if __name__ == "__main__":
    from build_notebooks import NOTEBOOKS

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else NOTEBOOKS / "04-source-configuration.ipynb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
