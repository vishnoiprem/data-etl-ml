# Getting Started with Data Engineering on GCP

## Pre-requisite Skills for the course
These are the pre-requisite skills for the course.
* Working experience using SQL is required
* Programming experience is required, preferably using Python
* Data Engineering or Data Warehousing experience is highly desired
* Basic understanding of Command Line tools such as powershell
* If you are new to Data Engineering, make sure to take our Data Engineering Essentials course.

## Overview of Cloud Platforms
Let us get an overview of Cloud Platforms.
* Quick Setup
* Marketplace
* Pay-as-you-go
* Scalability

Here are the various Cloud Platforms.
* AWS
* Azure
* GCP
* Oracle
* Rackspace
* Digital Ocean

> AWS, Azure and GCP are the top 3 Cloud Platforms.

## Overview of Google Cloud Platform
Let us get an overview of Google Cloud Platform.
* GCP is one of the 3 top Cloud Platforms. Others are AWS and Azure.
* It have a big marketplace of services (both Native as well as 3rd party)
* We can manage GCP Services using CLI or SDK using all prominent programming languages such as Python, Java, etc.

## Signing up for GCP
Let us make sure we signup for GCP using valid email id. Keep in mind that you are eligible for USD 300 credit which is valid for 3 months.
* Setup Google Account using valid email id.
* Sign up for GCP using Google Account.
* Get USD 300 Credits for 3 months.
* Setup Project and Review Billing

## Setup Google Cloud SDK
Click [here](https://cloud.google.com/sdk/docs/install) to go to the instructions related to setting up gcloud CLI.

## Configure Google Cloud SDK
Once Google Cloud SDK is setup, we need to make sure it is configured properly.

Here are the commands used for your reference.
```shell
gcloud init # You need to make sure to login via browser using GCP account
gsutil list # Google Cloud SDK will take care of setting up gsutil as well
```

## Alternative — Google Cloud Shell

Installing the SDK is not always the right first move. **Cloud Shell** gives
you a browser-based terminal with `gcloud`, `kubectl`, `docker`, `git` and
`curl` already installed, authenticated through your browser session. There
is nothing to install and no key file to manage.

### When to use Cloud Shell

Use it when you want to:
* try a `gcloud` command without installing the SDK,
* run a walkthrough for a team so everyone is on identical tooling,
* work from a machine where you cannot or should not install a SDK.

Do **not** use it as a production deployment workstation. The VM is
discarded after **40 minutes of inactivity** and a session is capped at
**12 hours**, so a long-running command can be killed mid-flight. The
default weekly quota is **50 hours**. Anything repeatable belongs in a
script or a Terraform module run from CI.

### Launching Cloud Shell

In the Google Cloud console, click the **>_** icon in the top-right toolbar
(the **Activate Cloud Shell** button), or open
<https://shell.cloud.google.com>. The session initialises in a panel at the
bottom of the console.

The active project from the console is carried into the shell, and
`GOOGLE_CLOUD_PROJECT` is set to match it.

### Verifying the session

```shell
# Which account are we actually authenticated as?
gcloud auth list

# Which project is selected?
gcloud config get-value project

# Where is this VM running? (the region is assigned, not chosen)
curl metadata/computeMetadata/v1/instance/zone
```

> **The authentication trap.** Cloud Shell uses the credentials of the
> **Google account you are signed into in the browser**, not of the
> `gcloud` configuration you think you have set. If `gcloud auth list`
> shows an unexpected account, sign out of the wrong Google account in the
> browser — do not reach for `gcloud auth revoke`.

### Persistent home directory

Cloud Shell gives you **5 GB of persistent disk** mounted at `$HOME`. It is
per user, shared across projects, and survives between sessions. Anything
outside `$HOME` is lost when the VM is discarded. The home directory is
deleted after **120 days** without access.

This is where the course data lives:

```shell
git clone https://github.com/dgadiraju/data
cd data
ls -ltr
find data/retail_db
```

Because `$HOME` persists, your cloned datasets and any scripts you write
are still there tomorrow.

### Installing extra software — the persistent way

Anything you `apt-get install` outside `$HOME` disappears with the VM. Two
options fix that.

**Option 1 — install into `$HOME`** (simple, works for most tools):

```shell
pip install --user google-cloud-storage google-cloud-bigquery
```

**Option 2 — `$HOME/.customize_environment`** (the right way for system
packages):

```shell
#!/bin/sh
# $HOME/.customize_environment
apt-get update
apt-get -y install erlang
```

This script runs **once per boot**, **as root**, and its output is written
to `/var/log/customize_environment`. Because it runs in parallel with the
login prompt, your package may become available a short moment after the
prompt appears — that is normal, not a failure.

### Ephemeral mode

By default the home directory persists. **Ephemeral mode** starts faster
because nothing is restored, but everything you create is removed when the
session ends. Enable it from the **More** menu in the Cloud Shell toolbar,
or go straight to <https://shell.cloud.google.com/?ephemeral=true>.

Use ephemeral mode for throwaway exploration. Never use it for the course
data, because you would re-clone it every session.

### Files in and out

```shell
# Upload a local file into $HOME
cloudshell download <TAB>

# The cloudshell command also opens tutorials, the editor, and downloads
cloudshell --help
```

### Editor and Web Preview

The Cloud Shell toolbar has **Open Editor**, which gives you a browser IDE
against the same `$HOME` — so a file you edit there is the file your
terminal sees. **Web Preview** serves a port from your session at a public
URL, which is how you check a running app quickly:

```shell
# start something on a port, then use Web Preview on that port
python3 -m http.server 8080
```

### Cloud Shell in this course

Almost every command in the remaining chapters runs unchanged in Cloud
Shell. The two things to keep in mind:

* The course uses `gsutil`, which is already installed — no setup needed.
* For the Airflow DAGs in chapter 12, the Cloud Shell Editor is a
  convenient place to develop them, because the DAGs folder the DAG needs
  to land in is a GCS path you can reach from the shell.

```shell
# Check the SDK is present and reasonably current
gcloud --version

# Confirm the service catalogue is reachable
gcloud services list --enabled --filter="config.name:bigquery.googleapis.com"
```

## Overview of Analytics Services on GCP

GCP provides robust set of Analytics Services. Here are the most prominent and relevant ones for this course.
* Google Cloud Storage for Data Lake
* Cloud SQL for Relational Database
* Google Functions for Data Processing
* Dataproc for Big Data Cluster using Hadoop and Spark
* Databricks for Big Data Cluster using Spark
* Google Composer for Orchestration
