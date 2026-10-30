"""
platform_sim.py — a local runtime that simulates the GCP platform.

The simulator models a **project** with its resource hierarchy, its IAM
policy, its regions and its services, and runs a pipeline through it.
It exists so the course's labs have something to run against without a
GCP account, and so the lessons about resource placement, IAM and cost
are executable rather than hypothetical.

The hierarchy mirrors GCP exactly:

    organization
      └── folder
            └── project
                  ├── bucket        (Cloud Storage)
                  ├── dataset       (BigQuery)
                  ├── topic         (Pub/Sub)
                  └── service account

Usage:
    from platform_sim import Project, build_demo_project

    project = build_demo_project()
    result = project.run_pipeline()
    print(result.summary)
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Iterable

from cost_model import estimate
from iam_policy import Binding, Policy, Principal, evaluate, explain_principal
from pipeline_logic import (
    aggregate_events,
    build_bigquery_rows,
    dedup_key_set,
    deduplicate,
    filter_rows_for_partition,
    ingest_events,
    partition_for_event,
    publish_topic,
    reject_counts,
    render_rejects_csv,
    render_summary_csv,
)
from service_catalog import REGIONS, SERVICES, get_service


# --------------------------------------------------------------------------
# Resource model
# --------------------------------------------------------------------------


@dataclasses.dataclass
class Resource:
    """One resource in the project's hierarchy.

    Attributes:
        name: The resource's short name.
        kind: The resource type, e.g. ``"bucket"`` or ``"dataset"``.
        service: The service id that owns it.
        location: The region or multi-region it lives in.
        labels: Metadata labels, used by the governance chapters.
    """

    name: str
    kind: str
    service: str
    location: str
    labels: dict[str, str] = dataclasses.field(default_factory=dict)

    @property
    def path(self) -> str:
        """The fully-qualified resource path."""
        if self.kind in {"bucket", "dataset", "topic"}:
            return f"projects/{_PROJECT_ID}/{self.kind}s/{self.name}"
        return f"projects/{_PROJECT_ID}/{self.kind}/{self.name}"

    def location_suffix(self) -> str:
        """Return the location suffix GCP appends to a resource name.

        Buckets get their region as a suffix; BigQuery datasets get it
        in parentheses; topics use a dash.

        Returns:
            The suffix, e.g. ``"-us-central1"``.
        """
        if self.kind == "bucket":
            return f"-{self.location}"
        if self.kind == "dataset":
            return f"_{self.location}"
        if self.kind == "topic":
            return f"-{self.location}"
        return ""


#: The project id used by the simulator. Real project ids are globally
#: unique; this one is fixed so the expected outputs stay stable.
_PROJECT_ID = "gcp-de-course"


@dataclasses.dataclass
class PipelineResult:
    """The outcome of running the pipeline against a project.

    Attributes:
        accepted: The accepted, normalised events.
        rejected: The rejected events.
        summary: The per-region aggregate.
        summary_csv: The aggregate rendered as CSV.
        rejects_csv: The rejects rendered as CSV.
        published: The Pub/Sub messages the pipeline published.
        loaded_rows: The rows written to the BigQuery table.
        idempotency_keys: The deterministic identities of the loaded rows.
        cost: The estimated monthly cost of the workload.
        messages: The human-readable log of what happened.
    """

    accepted: list[dict[str, Any]]
    rejected: list[dict[str, Any]]
    summary: dict[str, dict[str, float]]
    summary_csv: str
    rejects_csv: str
    published: list[dict[str, Any]]
    loaded_rows: list[dict[str, Any]]
    idempotency_keys: set[str]
    cost: float
    messages: list[str]

    @property
    def rejected_counts(self) -> dict[str, int]:
        """The reject counts by reason code."""
        return reject_counts(self.rejected)


class Project:
    """A simulated GCP project.

    Attributes:
        project_id: The project id.
        name: The display name.
        region: The default region.
        resources: The resources in the project, keyed by name.
        policy: The project's IAM policy.
        service_accounts: The service accounts in the project.
    """

    def __init__(
        self,
        project_id: str = _PROJECT_ID,
        *,
        name: str = "GCP Data Engineering Course",
        region: str = "us-central1",
    ) -> None:
        """Create a project.

        Args:
            project_id: The project id.
            name: The display name.
            region: The default region.

        Raises:
            KeyError: If the region is not a known GCP region.
        """
        if region not in REGIONS:
            raise KeyError(f"unknown region: {region!r}")
        self.project_id = project_id
        self.name = name
        self.region = region
        self.resources: dict[str, Resource] = {}
        self.policy = Policy()
        self.service_accounts: dict[str, str] = {}

    # -- resources --------------------------------------------------------

    def add_resource(
        self,
        name: str,
        kind: str,
        service: str,
        *,
        location: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> Resource:
        """Add a resource to the project.

        Args:
            name: The resource's short name.
            kind: The resource type.
            service: The owning service id.
            location: The resource's location. Defaults to the project's
                region.
            labels: Metadata labels.

        Returns:
            The created resource.

        Raises:
            KeyError: If the service is unknown.
        """
        get_service(service)
        resource = Resource(
            name=name,
            kind=kind,
            service=service,
            location=location or self.region,
            labels=dict(labels or {}),
        )
        self.resources[name] = resource
        return resource

    def get_resource(self, name: str) -> Resource:
        """Look up a resource by name.

        Args:
            name: The resource's short name.

        Returns:
            The resource.

        Raises:
            KeyError: If no such resource exists.
        """
        try:
            return self.resources[name]
        except KeyError as exc:
            raise KeyError(f"no such resource: {name!r}") from exc

    def add_service_account(
        self, name: str, *, display_name: str | None = None
    ) -> str:
        """Create a service account and return its email address.

        Args:
            name: The service account's short name.
            display_name: An optional display name.

        Returns:
            The service account's email address.
        """
        email = f"{name}@{self.project_id}.iam.gserviceaccount.com"
        self.service_accounts[email] = display_name or name
        return email

    # -- IAM --------------------------------------------------------------

    def grant(
        self,
        principal: Principal,
        role: str,
        *,
        resource: str | None = None,
    ) -> None:
        """Grant a role to a principal.

        Args:
            principal: The identity.
            role: The role name.
            resource: The resource to grant on. Defaults to the whole
                project.
        """
        target = resource or f"projects/{self.project_id}"
        self.policy.add(principal, Binding(role=role), target)

    def deny(
        self,
        principal: Principal,
        role: str,
        *,
        resource: str | None = None,
    ) -> None:
        """Add an explicit deny for a principal.

        Args:
            principal: The identity.
            role: The role being denied.
            resource: The resource to deny on. Defaults to the whole
                project.
        """
        target = resource or f"projects/{self.project_id}"
        self.policy.deny(principal, role, target)

    def can(
        self,
        identity: str,
        permission: str,
        *,
        resource: str | None = None,
    ) -> bool:
        """Return True when an identity may perform a permission.

        Args:
            identity: The identity's identifier.
            permission: The primitive permission.
            resource: The resource path. Defaults to the project.

        Returns:
            True when permitted.
        """
        target = resource or f"projects/{self.project_id}"
        return evaluate(self.policy, identity, permission, resource=target).allowed

    def explain(self, identity: str, *, resource: str | None = None) -> list[str]:
        """Explain every binding that applies to an identity.

        Args:
            identity: The identity's identifier.
            resource: The resource path. Defaults to the project.

        Returns:
            One explanation line per applicable binding.
        """
        target = resource or f"projects/{self.project_id}"
        return explain_principal(self.policy, identity, resource=target)

    # -- the pipeline -----------------------------------------------------

    def run_pipeline(
        self,
        lines: Iterable[str],
        *,
        topic: str = "events-normalised",
        partition: str | None = None,
        idempotent: bool = True,
    ) -> PipelineResult:
        """Run the full pipeline against this project.

        The stages map onto GCP as follows:

            ingest  → Pub/Sub subscription pull
            validate→ Dataflow DoFn / Dataproc map
            publish → Pub/Sub publish
            load    → BigQuery partitioned table load

        Args:
            lines: The raw CSV lines.
            topic: The topic to publish to.
            partition: The partition to load into. Defaults to the
                partition of the first accepted event.
            idempotent: When True, deduplicate the loaded rows by their
                deterministic identity — the property that makes a retry
                safe.

        Returns:
            The :class:`PipelineResult`.
        """
        messages: list[str] = []
        raw = list(lines)

        accepted, rejected = ingest_events(raw)
        messages.append(
            f"ingest: {len(accepted)} accepted, {len(rejected)} rejected"
        )

        summary = aggregate_events(accepted)
        messages.append(
            f"aggregate: {len(summary)} regions, "
            f"{sum(int(s['event_count']) for s in summary.values())} events"
        )

        published = publish_topic(accepted, topic=topic)
        messages.append(f"publish: {len(published)} messages to {topic}")

        target_partition = partition or (
            partition_for_event(accepted[0]["event_dt"]) if accepted else "00000000"
        )
        partitioned = filter_rows_for_partition(accepted, target_partition)
        messages.append(
            f"load: partition {target_partition}, {len(partitioned)} rows"
        )

        loaded = partitioned
        if idempotent:
            loaded = deduplicate(partitioned, partition=target_partition)
            messages.append(
                f"dedup: {len(partitioned)} -> {len(loaded)} rows "
                f"({len(partitioned) - len(loaded)} duplicates removed)"
            )

        rows = build_bigquery_rows(loaded)
        keys = dedup_key_set(loaded, target_partition)

        cost = estimate(
            "bigquery",
            scanned_tb=round(len(rows) / 1_000_000, 6),
            monthly=False,
            apply_free_tier=False,
        ).total

        return PipelineResult(
            accepted=accepted,
            rejected=rejected,
            summary=summary,
            summary_csv=render_summary_csv(summary),
            rejects_csv=render_rejects_csv(rejected),
            published=published,
            loaded_rows=rows,
            idempotency_keys=keys,
            cost=cost,
            messages=messages,
        )

    def estimate_monthly_cost(
        self,
        *,
        scanned_tb: float = 1.0,
        storage_gb: float = 100.0,
        streaming_hours: float = 24.0,
    ) -> dict[str, float]:
        """Estimate the monthly cost of the platform in this project.

        Args:
            scanned_tb: The TB scanned by BigQuery each month.
            storage_gb: The GB held in Cloud Storage.
            streaming_hours: The hours the streaming pipeline runs.

        Returns:
            A dict of service -> monthly cost.
        """
        return {
            "cloud-storage": estimate(
                "cloud-storage", storage_gb=storage_gb, monthly=True
            ).total,
            "bigquery": estimate(
                "bigquery", scanned_tb=scanned_tb, monthly=True
            ).total,
            "dataflow": estimate(
                "dataflow", vcpu_hours=streaming_hours, monthly=True
            ).total,
            "composer": estimate(
                "composer", environment_nodes=1, monthly=True
            ).total,
        }


def build_demo_project() -> Project:
    """Build the project the course's labs run against.

    The project has one bucket, one dataset, one topic, one service
    account, and the IAM policy that ties them together. It is the
    executable version of the architecture in the README.

    Returns:
        The demo project.
    """
    project = Project()
    project.add_resource(
        "raw-events", "bucket", "cloud-storage", labels={"tier": "raw"}
    )
    project.add_resource(
        "curated", "dataset", "bigquery", labels={"tier": "curated"}
    )
    project.add_resource(
        "events", "topic", "pubsub", labels={"tier": "raw"}
    )

    analytics = Principal("user", "analytics@example.com")
    service_account = Principal(
        "serviceAccount", project.add_service_account("pipeline-sa")
    )

    project.grant(analytics, "roles/bigquery.dataEditor")
    project.grant(analytics, "roles/storage.objectViewer")
    project.grant(service_account, "roles/pubsub.editor")
    project.grant(service_account, "roles/storage.objectCreator")
    project.grant(service_account, "roles/bigquery.dataEditor")

    return project


def format_resource_tree(project: Project) -> str:
    """Render a project's resources as an indented tree.

    Args:
        project: The project to render.

    Returns:
        The tree, as a string.
    """
    lines = [
        f"organization: acme.example.com",
        f"└── folder: engineering",
        f"    └── project: {project.name} ({project.project_id})",
    ]
    for resource in sorted(project.resources.values(), key=lambda r: r.name):
        service = SERVICES[resource.service]
        lines.append(
            f"        ├── {resource.kind}: {resource.name}"
            f"{resource.location_suffix()}  [{service.name}]"
        )
    for email in sorted(project.service_accounts):
        lines.append(f"        └── serviceAccount: {email}")
    return "\n".join(lines)


def format_pipeline_log(result: PipelineResult) -> str:
    """Render a pipeline result as a console log.

    Args:
        result: The pipeline result.

    Returns:
        The formatted log.
    """
    lines = ["▶ Running pipeline", ""]
    for message in result.messages:
        lines.append(f"  {message}")
    lines.append("")
    lines.append(result.summary_csv.rstrip())
    return "\n".join(lines)


def format_json(value: Any) -> str:
    """Render a value as pretty-printed JSON.

    Args:
        value: The value to serialise.

    Returns:
        The JSON text.
    """
    return json.dumps(value, indent=2, sort_keys=True)
