"""A local model of a Composer environment.

This is the environment as a configuration object: the same fields the
`gcloud composer environments create` command takes, plus the things the
command implies. It is validated, costed, and — crucially — it can be
rendered into the exact command you would run.

No cloud access. No credentials. No network.
"""

from dataclasses import dataclass, field
from typing import Any

# --------------------------------------------------------------------------
# The reference data
# --------------------------------------------------------------------------

#: The Composer generations and the Airflow version each pins.
COMPOSER_GENERATIONS = {
    "composer-2": {
        "executor": "CeleryExecutor",
        "airflow_version": "2.9.3",
        "image_version": "composer-2.9.3-airflow-2.9.3",
        "task_startup_seconds": 1,
    },
    "composer-3": {
        "executor": "KubernetesExecutor",
        "airflow_version": "2.9.3",
        "image_version": "composer-3.0.4-airflow-2.9.3",
        "task_startup_seconds": 45,
    },
}

#: The environment sizes and their worker bands.
ENVIRONMENT_SIZES = {
    "SMALL": {"workers_min": 1, "workers_max": 2},
    "MEDIUM": {"workers_min": 3, "workers_max": 6},
    "LARGE": {"workers_min": 7, "workers_max": 15},
}

#: The IAM roles an environment's service account typically needs.
REQUIRED_ROLES = [
    "roles/composer.worker",
    "roles/bigquery.jobUser",
    "roles/storage.objectAdmin",
    "roles/cloudresourcemanager.projectViewer",
]


@dataclass
class ComposerEnvironment:
    """A Cloud Composer environment, as a configuration object.

    Attributes:
        name: The environment's name.
        location: The region it runs in.
        generation: ``"composer-2"`` or ``"composer-3"``.
        size: The environment size.
        machine_type: The GCE machine type for the workers.
        dag_bucket: The GCS bucket holding the DAG files.
        log_bucket: The GCS bucket holding the task logs.
        service_account: The identity the workers run as.
        network: The VPC the web server sits in.
        subnetwork: The subnet the web server sits in.
        oauth_scope: The OAuth scope the workers request.
        python_version: The Python version in the Airflow environment.
        env_vars: The Airflow configuration, as a mapping.
        variables: The Airflow Variables to create.
        connections: The Airflow Connections to create.
        labels: The labels applied to the environment's resources.
        log_retention_days: How long task logs are kept.
        dag_retention_days: How long DAG files are kept in the bucket.
        bucket_regions: The region each bucket lives in, by bucket URI.
    """

    name: str
    location: str
    generation: str = "composer-2"
    size: str = "SMALL"
    machine_type: str = "n1-standard-2"
    dag_bucket: str = ""
    log_bucket: str = ""
    service_account: str = ""
    network: str = ""
    subnetwork: str = ""
    oauth_scope: str = "cloud-platform"
    python_version: str = "3.11"
    env_vars: dict[str, str] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)
    connections: dict[str, dict[str, str]] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    log_retention_days: int = 30
    dag_retention_days: int = 30
    bucket_regions: dict[str, str] = field(default_factory=dict)

    # -- derived properties ------------------------------------------

    @property
    def version_info(self) -> dict[str, Any]:
        """Return the version and executor for this generation.

        Returns:
            A dict with the executor, the Airflow version, the image
            version and the task startup cost.
        """
        return COMPOSER_GENERATIONS[self.generation]

    @property
    def executor(self) -> str:
        """Return the executor this environment uses.

        Returns:
            The executor's name.
        """
        return self.version_info["executor"]

    @property
    def airflow_version(self) -> str:
        """Return the pinned Airflow version.

        Returns:
            The Airflow version string.
        """
        return self.version_info["airflow_version"]

    @property
    def workers_min(self) -> int:
        """Return the minimum worker count.

        Returns:
            The minimum number of workers.
        """
        return ENVIRONMENT_SIZES[self.size]["workers_min"]

    @property
    def workers_max(self) -> int:
        """Return the maximum worker count.

        Returns:
            The maximum number of workers.
        """
        return ENVIRONMENT_SIZES[self.size]["workers_max"]

    @property
    def vcpu_per_worker(self) -> int:
        """Return the vCPUs per worker, derived from the machine type.

        Returns:
            The number of vCPUs.
        """
        return {"n1-standard-2": 2, "n1-standard-4": 4,
                "n1-standard-8": 8, "n2-standard-2": 2}[self.machine_type]

    @property
    def parallelism(self) -> int:
        """Return the recommended Airflow parallelism for this size.

        Returns:
            The parallelism setting.
        """
        return {"SMALL": 8, "MEDIUM": 32, "LARGE": 128}[self.size]

    # -- rendering ----------------------------------------------------

    def create_command(self) -> str:
        """Render the `gcloud composer environments create` command.

        Returns:
            The command, as a shell string.
        """
        parts = [
            "gcloud composer environments create", self.name,
            f"--location={self.location}",
            f"--image-version={self.version_info['image_version']}",
            f"--environment-size=ENVIRONMENT_SIZE_{self.size}",
            f"--machine-type={self.machine_type}",
            f"--dag-bucket={self.dag_bucket}",
            f"--log-bucket={self.log_bucket}",
            f"--oauth-scope={self.oauth_scope}",
            f"--python-version={self.python_version}",
        ]
        if self.service_account:
            parts.append(f"--service-account={self.service_account}")
        if self.network:
            parts.append(f"--web-server-network={self.network}")
        if self.subnetwork:
            parts.append(f"--web-server-subnetwork={self.subnetwork}")
        if self.env_vars:
            env = ",".join(f"{k}={v}" for k, v in sorted(self.env_vars.items()))
            parts.append(f"--env-vars={env}")
        if self.labels:
            labels = ",".join(f"{k}={v}" for k, v in sorted(self.labels.items()))
            parts.append(f"--labels={labels}")
        # The first element is the subcommand; the rest are flags and
        # values that contain no shell metacharacters worth quoting.
        return " \\\n  ".join(parts)

    def set_variable_commands(self) -> list[str]:
        """Render the commands that create the Airflow Variables.

        Returns:
            A list of shell commands.
        """
        return [
            f"gcloud composer environments update {self.name} "
            f"--location={self.location} "
            f"--update-airflow-variables={name}={value}"
            for name, value in sorted(self.variables.items())
        ]

    def describe(self) -> str:
        """Return a human-readable description of the environment.

        Returns:
            A multi-line description.
        """
        lines = [
            f"Composer environment: {self.name}",
            f"  location        : {self.location}",
            f"  generation      : {self.generation}",
            f"  executor        : {self.executor}",
            f"  Airflow version : {self.airflow_version}",
            f"  size            : {self.size} "
            f"({self.workers_min}-{self.workers_max} workers)",
            f"  machine type    : {self.machine_type} "
            f"({self.vcpu_per_worker} vCPU/worker)",
            f"  parallelism     : {self.parallelism}",
            f"  dag bucket      : {self.dag_bucket}",
            f"  log bucket      : {self.log_bucket}",
            f"  service account : {self.service_account or '(default)'}",
            f"  network         : {self.network or '(managed VPC)'}",
            f"  oauth scope     : {self.oauth_scope}",
            f"  python version  : {self.python_version}",
            f"  variables       : {len(self.variables)}",
            f"  connections     : {len(self.connections)}",
            f"  log retention   : {self.log_retention_days} days",
        ]
        return "\n".join(lines)

    # -- validation ---------------------------------------------------

    def validate(self) -> list[str]:
        """Check the environment for the mistakes that cost money.

        Returns:
            A list of problems; empty means the environment is valid.
        """
        problems = []

        if self.generation not in COMPOSER_GENERATIONS:
            problems.append(
                f"unknown generation {self.generation!r} "
                f"(expected one of {sorted(COMPOSER_GENERATIONS)})")
        if self.size not in ENVIRONMENT_SIZES:
            problems.append(
                f"unknown size {self.size!r} "
                f"(expected one of {sorted(ENVIRONMENT_SIZES)})")

        # The DAG bucket and the environment should be in the same region.
        if self.dag_bucket and not self.dag_bucket.startswith("gs://"):
            problems.append(f"dag_bucket must be a gs:// URI, got {self.dag_bucket!r}")
        if self.log_bucket and not self.log_bucket.startswith("gs://"):
            problems.append(f"log_bucket must be a gs:// URI, got {self.log_bucket!r}")
        if self.dag_bucket and self.log_bucket:
            if self.dag_bucket == self.log_bucket:
                problems.append(
                    "the DAG bucket and the log bucket must be different — "
                    "the log lifecycle would delete your DAG files")

        # A bucket in another region makes every DAG file read cross a
        # region boundary, and moves your data out of its residency region.
        for bucket, region in self.bucket_regions.items():
            if region != self.location:
                problems.append(
                    f"bucket {bucket!r} is in region {region!r} but the "
                    f"environment is in {self.location!r} — DAG file reads "
                    f"would cross a region boundary")

        # The web server must be in a VPC if you name a network.
        if bool(self.network) != bool(self.subnetwork):
            problems.append(
                "network and subnetwork must be set together — Composer "
                "requires both for a private web server")

        # The service account needs an email-like value.
        if self.service_account and "@" not in self.service_account:
            problems.append(
                f"service_account must be a full email address, "
                f"got {self.service_account!r}")

        # Log retention must be positive and finite.
        if self.log_retention_days <= 0:
            problems.append("log_retention_days must be positive")
        if self.log_retention_days > 365:
            problems.append(
                f"log_retention_days of {self.log_retention_days} is over a "
                f"year — check the storage cost")

        # The timezone must be explicit.
        if "AIRFLOW__CORE__DEFAULT_TIMEZONE" not in self.env_vars:
            problems.append(
                "AIRFLOW__CORE__DEFAULT_TIMEZONE is not set — set it "
                "explicitly to UTC so the scheduler and the warehouse agree")

        # A Composer 3 environment on a chatty DAG pays the pod tax.
        if self.generation == "composer-3" and self.size == "SMALL":
            problems.append(
                "Composer 3 with a SMALL environment has 1-2 workers, each "
                "paying a ~45s pod startup — check the task durations")

        return problems


# --------------------------------------------------------------------------
# A well-formed environment
# --------------------------------------------------------------------------
ENV = ComposerEnvironment(
    name="composer-prod",
    location="europe-west1",
    generation="composer-2",
    size="MEDIUM",
    machine_type="n1-standard-2",
    dag_bucket="gs://YOUR_PROJECT_ID-dags",
    log_bucket="gs://YOUR_PROJECT_ID-logs",
    service_account="composer-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com",
    network="YOUR_VPC_NETWORK",
    subnetwork="YOUR_VPC_SUBNET",
    oauth_scope="cloud-platform",
    python_version="3.11",
    env_vars={
        "AIRFLOW__CORE__DEFAULT_TIMEZONE": "UTC",
        "AIRFLOW__CORE__PARALLELISM": "32",
        "AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG": "16",
        "AIRFLOW__WEBSERVER__EXPOSE_CONFIG": "True",
    },
    variables={
        "gcp_project_id": "YOUR_PROJECT_ID",
        "source_bucket": "YOUR_PROJECT_ID-source",
        "target_bucket": "YOUR_PROJECT_ID-target",
        "bq_dataset": "analytics",
        "bq_table": "orders_enriched",
        "full_load_threshold": "1000000",
    },
    connections={
        "google_cloud_default": {
            "conn_type": "google_cloud_platform",
            "extra": '{"project_id": "YOUR_PROJECT_ID"}',
        },
        "http_orders_api": {
            "conn_type": "http",
            "host": "api.example.com",
            "login": "svc_account",
            "password": "<stored in Secret Manager, not here>",
        },
    },
    labels={"team": "data-platform", "env": "prod"},
    log_retention_days=30,
    dag_retention_days=30,
    bucket_regions={
        "gs://YOUR_PROJECT_ID-dags": "europe-west1",
        "gs://YOUR_PROJECT_ID-logs": "europe-west1",
    },
)

print(ENV.describe())
print()

problems = ENV.validate()
print("Validation:", problems or "no problems")
print()

print("=" * 78)
print("The command you would run (run in a terminal, not executed here)")
print("=" * 78)
print(ENV.create_command())
print()

print("=" * 78)
print("Setting the Variables after creation")
print("=" * 78)
for command in ENV.set_variable_commands():
    print(command)
