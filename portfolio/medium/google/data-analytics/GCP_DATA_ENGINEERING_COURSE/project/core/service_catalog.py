"""
service_catalog.py — the pure half of the GCP Data Engineering course project.

Every business rule the course exercises lives here, and **this module
imports nothing from Google Cloud**. That is deliberate:

    * The course premise is that you can learn the platform without a GCP
      account, credentials or a bill.
    * Rules that live inside a deployed script are nearly impossible to
      unit-test, because importing them requires a live project.
    * When the logic is pure, ``pytest`` runs in well under a second with
      no cloud SDK installed, and the same function can be called from a
      local script, from a test, or from a deployed job.

The modules in this package simulate the platform:

    ``service_catalog``  — the service inventory, regions, quotas and SLAs
    ``iam_policy``       — the IAM policy evaluation engine
    ``cost_model``       — the pricing estimator for every service
    ``pipeline_logic``   — the end-to-end pipeline the capstone builds
    ``platform_sim``     — the local runtime that ties them together

Usage:
    from service_catalog import SERVICES, get_service, regions_for
    from iam_policy import Policy, Binding, evaluate
    from cost_model import estimate

    print(get_service("bigquery").name)
    print(regions_for("dataflow"))
"""
from __future__ import annotations

import dataclasses
from typing import Iterable

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

#: The GCP regions this course covers, with their display names.
REGIONS: dict[str, str] = {
    "us-central1": "Iowa",
    "us-east1": "South Carolina",
    "us-east4": "Northern Virginia",
    "us-west1": "Oregon",
    "europe-west1": "Belgium",
    "europe-west2": "London",
    "europe-west4": "Netherlands",
    "asia-south1": "Mumbai",
    "asia-southeast1": "Singapore",
    "asia-northeast1": "Tokyo",
    "australia-southeast1": "Sydney",
    "southamerica-east1": "São Paulo",
}

#: The zones within a region. A region always has three zones; their
#: suffixes are always ``-a``, ``-b`` and ``-c``.
ZONE_SUFFIXES = ("a", "b", "c")

#: The categories used to group services in the console's product menu.
CATEGORIES = (
    "Compute",
    "Storage",
    "Databases",
    "Analytics",
    "Streaming & Messaging",
    "Integration",
    "Security & Governance",
    "AI & ML",
)

#: Broad data-engineering service categories, used by the selection matrix.
DATA_ENG_ROLE = {
    "storage": "Landing zone for raw data",
    "warehouse": "Analytical query engine",
    "batch": "Scheduled data processing",
    "streaming": "Continuous data processing",
    "orchestration": "Scheduling and dependency management",
    "transform": "Version-controlled transformation logic",
    "catalog": "Metadata and data discovery",
    "governance": "Policy, lineage and compliance",
}


@dataclasses.dataclass(frozen=True)
class RegionAvailability:
    """Which regions a service is available in, and with what caveats.

    Attributes:
        available: Regions where the service is generally available.
        preview: Regions where the service is in preview, meaning it may
            have no SLA and may change without notice.
        restricted: Regions where the service exists but is not offered to
            new customers without a support request.
    """

    available: tuple[str, ...]
    preview: tuple[str, ...] = ()
    restricted: tuple[str, ...] = ()

    def is_available(self, region: str) -> bool:
        """Return True when the service is generally available in a region.

        Args:
            region: The region code, e.g. ``"us-central1"``.

        Returns:
            True when generally available.
        """
        return region in self.available

    def status(self, region: str) -> str:
        """Classify a region's availability status.

        Args:
            region: The region code.

        Returns:
            One of ``"available"``, ``"preview"``, ``"restricted"`` or
            ``"unavailable"``.
        """
        if region in self.available:
            return "available"
        if region in self.preview:
            return "preview"
        if region in self.restricted:
            return "restricted"
        return "unavailable"


@dataclasses.dataclass(frozen=True)
class Service:
    """One GCP service, described the way the console describes it.

    Attributes:
        id: The short service id used in APIs, e.g. ``"bigquery"``.
        name: The display name, e.g. ``"BigQuery"``.
        category: One of :data:`CATEGORIES`.
        data_role: The role it plays in a data platform, from
            :data:`DATA_ENG_ROLE`.
        summary: A one-line description.
        pricing_model: How the service is billed.
        availability: Regional availability.
        key_resources: The primary resources the service exposes.
        deep_dive: A relative link to the sibling course that covers this
            service in depth, or None when this course is the only
            coverage.
    """

    id: str
    name: str
    category: str
    data_role: str
    summary: str
    pricing_model: str
    availability: RegionAvailability
    key_resources: tuple[str, ...]
    deep_dive: str | None = None

    def is_available_in(self, region: str) -> bool:
        """Return True when the service is generally available in a region.

        Args:
            region: The region code.

        Returns:
            True when generally available.
        """
        return self.availability.is_available(region)


#: The service inventory. This is the course's spine — most chapters
#: reference services by id from this table.
SERVICES: dict[str, Service] = {
    # --- Storage ---------------------------------------------------------
    "cloud-storage": Service(
        id="cloud-storage",
        name="Cloud Storage",
        category="Storage",
        data_role="storage",
        summary="Durable object storage for raw and staged data.",
        pricing_model="Per GB stored per month, plus per-class retrieval.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Bucket", "Object", "Lifecycle Rule", "IAM Policy"),
        deep_dive=None,
    ),
    "bigquery": Service(
        id="bigquery",
        name="BigQuery",
        category="Analytics",
        data_role="warehouse",
        summary="Serverless, columnar analytical warehouse.",
        pricing_model="Per TB scanned, or flat-rate capacity by slot-hour.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
                "southamerica-east1",
            ),
            preview=(),
            restricted=(),
        ),
        key_resources=("Project", "Dataset", "Table", "View", "Materialized View"),
        deep_dive="../BigQuery/README.md",
    ),
    "biglake": Service(
        id="biglake",
        name="BigLake",
        category="Analytics",
        data_role="warehouse",
        summary="Managed open lakehouse tables in BigQuery over object storage.",
        pricing_model="Storage plus per-query metadata and compute charges.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
            ),
            preview=("southamerica-east1",),
            restricted=(),
        ),
        key_resources=("Lake", "Table", "Data Cache", "Storage Layout"),
        deep_dive=None,
    ),
    # --- Databases -------------------------------------------------------
    "cloud-sql": Service(
        id="cloud-sql",
        name="Cloud SQL",
        category="Databases",
        data_role="warehouse",
        summary="Managed relational database with PostgreSQL, MySQL or SQL Server.",
        pricing_model="Per vCPU-hour and per GB of storage, by instance tier.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Instance", "Database", "User", "Backup"),
        deep_dive=None,
    ),
    "cloud-spanner": Service(
        id="cloud-spanner",
        name="Cloud Spanner",
        category="Databases",
        data_role="warehouse",
        summary="Globally consistent, horizontally scalable relational database.",
        pricing_model="Per vCPU-hour, per node-hour, plus storage and IO.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
                "southamerica-east1",
            ),
            preview=(),
            restricted=(),
        ),
        key_resources=("Instance", "Database", "Instance Partition", "Backup"),
        deep_dive=None,
    ),
    "bigtable": Service(
        id="bigtable",
        name="Bigtable",
        category="Databases",
        data_role="warehouse",
        summary="Managed wide-column NoSQL store for large-scale key-value reads.",
        pricing_model="Per node-hour per GB provisioned, plus storage and IO.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
            ),
            preview=("southamerica-east1",),
            restricted=(),
        ),
        key_resources=("Instance", "Cluster", "Table", "Column Family"),
        deep_dive=None,
    ),
    "datastore": Service(
        id="datastore",
        name="Datastore",
        category="Databases",
        data_role="warehouse",
        summary="Managed document database for application entities.",
        pricing_model="Per entity-write and per entity-read, plus storage.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
            ),
            preview=("australia-southeast1",),
            restricted=("southamerica-east1",),
        ),
        key_resources=("Kind", "Entity", "Namespace", "Index"),
        deep_dive=None,
    ),
    "firestore": Service(
        id="firestore",
        name="Firestore",
        category="Databases",
        data_role="warehouse",
        summary="Mobile and web client database with serverless sync.",
        pricing_model="Per document read, write and delete, plus storage.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
                "southamerica-east1",
            ),
            preview=(),
            restricted=(),
        ),
        key_resources=("Collection", "Document", "Subcollection", "Index"),
        deep_dive=None,
    ),
    "memorystore": Service(
        id="memorystore",
        name="Memorystore",
        category="Databases",
        data_role="warehouse",
        summary="Managed in-memory Redis and Memcached caches.",
        pricing_model="Per node-hour by tier, plus storage.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
            ),
            preview=(),
            restricted=("southamerica-east1",),
        ),
        key_resources=("Instance", "Redis Instance", "Memcached Instance"),
        deep_dive=None,
    ),
    # --- Compute ---------------------------------------------------------
    "compute-engine": Service(
        id="compute-engine",
        name="Compute Engine",
        category="Compute",
        data_role="batch",
        summary="Virtual machines with configurable CPU, memory and disk.",
        pricing_model="Per vCPU-hour and per GB-month, plus network egress.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Instance", "Instance Group", "Disk", "Network"),
        deep_dive=None,
    ),
    "app-engine": Service(
        id="app-engine",
        name="App Engine",
        category="Compute",
        data_role="batch",
        summary="Managed PaaS for Python, Java, Go, Node.js and PHP apps.",
        pricing_model="Per instance-hour plus egress, with a free tier.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
            ),
            preview=("southamerica-east1",),
            restricted=(),
        ),
        key_resources=("Application", "Version", "Instance Class", "Service"),
        deep_dive=None,
    ),
    "kubernetes-engine": Service(
        id="kubernetes-engine",
        name="Kubernetes Engine",
        category="Compute",
        data_role="batch",
        summary="Managed Kubernetes control plane and worker nodes.",
        pricing_model="Per node-hour by machine type, plus cluster management fee.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Cluster", "Node Pool", "Pod", "Service"),
        deep_dive=None,
    ),
    "cloud-run": Service(
        id="cloud-run",
        name="Cloud Run",
        category="Compute",
        data_role="batch",
        summary="Serverless containers billed by request and CPU time.",
        pricing_model="Per request, per container CPU-second and per GB-second.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Service", "Revision", "Job", "Container"),
        deep_dive=None,
    ),
    "cloud-functions": Service(
        id="cloud-functions",
        name="Cloud Run functions",
        category="Compute",
        data_role="batch",
        summary="Event-driven serverless functions from small pieces of code.",
        pricing_model="Per invocation, per GB-second and per CPU-second.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Function", "Trigger", "Service Account", "Env Variable"),
        deep_dive=None,
    ),
    # --- Streaming -------------------------------------------------------
    "pubsub": Service(
        id="pubsub",
        name="Pub/Sub",
        category="Streaming & Messaging",
        data_role="streaming",
        summary="Managed publish/subscribe messaging for event ingestion.",
        pricing_model="Per GB of message data ingested, then per delivery.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Topic", "Subscription", "Schema", "Dead-Letter Topic"),
        deep_dive=None,
    ),
    "kafka": Service(
        id="kafka",
        name="Kafka (Confluent Cloud)",
        category="Streaming & Messaging",
        data_role="streaming",
        summary="Managed Apache Kafka for high-throughput event streaming.",
        pricing_model="Per GB ingested, per GB retained, and per cluster-hour.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
            ),
            preview=(),
            restricted=("southamerica-east1",),
        ),
        key_resources=("Cluster", "Topic", "Partition", "Consumer Group"),
        deep_dive=None,
    ),
    "datastream": Service(
        id="datastream",
        name="Datastream",
        category="Streaming & Messaging",
        data_role="streaming",
        summary="Change data capture from databases and SaaS into streaming sinks.",
        pricing_model="Per CDC row-change processed plus per-stream-hour.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
            ),
            preview=("australia-southeast1",),
            restricted=("southamerica-east1",),
        ),
        key_resources=("Stream", "Stream Job", "Connection Profile", "Event"),
        deep_dive=None,
    ),
    # --- Processing ------------------------------------------------------
    "dataproc": Service(
        id="dataproc",
        name="Dataproc",
        category="Analytics",
        data_role="batch",
        summary="Managed Apache Spark, Hadoop and Hive on GKE or Compute Engine.",
        pricing_model="Per vCPU-hour by cluster, plus managed storage.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Cluster", "Job", "Workflow Template", "Session"),
        deep_dive="../dataproc/README.md",
    ),
    "dataflow": Service(
        id="dataflow",
        name="Dataflow",
        category="Analytics",
        data_role="streaming",
        summary="Managed runner for Apache Beam batch and streaming pipelines.",
        pricing_model="Per vCPU-hour, with streaming billed per worker-hour.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Job", "Template", "Pipeline", "Worker Pool"),
        deep_dive="../Dataflow/README.md",
    ),
    "composer": Service(
        id="composer",
        name="Cloud Composer",
        category="Analytics",
        data_role="orchestration",
        summary="Managed Apache Airflow for workflow scheduling and orchestration.",
        pricing_model="Per environment-node-hour plus DB and network charges.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Environment", "DAG", "DAG Run", "Task Instance"),
        deep_dive="../composer/README.md",
    ),
    "workflows": Service(
        id="workflows",
        name="Workflows",
        category="Analytics",
        data_role="orchestration",
        summary="Serverless, event-driven orchestration of API calls and jobs.",
        pricing_model="Per workflow transition, with no idle cost.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Workflow", "Execution", "Task", "Service Account"),
        deep_dive=None,
    ),
    "dataform": Service(
        id="dataform",
        name="Dataform",
        category="Analytics",
        data_role="transform",
        summary="Transformation logic as SQL models with tests and lineage.",
        pricing_model="No separate charge — included with BigQuery.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Repository", "Workflow", "Table", "Assertion"),
        deep_dive="../dataform/README.md",
    ),
    "data-fusion": Service(
        id="data-fusion",
        name="Data Fusion",
        category="Integration",
        data_role="batch",
        summary="Visual, low-code data integration and pipeline building.",
        pricing_model="Per cluster-hour by instance class, plus data egress.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
            ),
            preview=("australia-southeast1",),
            restricted=("southamerica-east1",),
        ),
        key_resources=("Instance", "Pipeline", "Namespace", "Connector"),
        deep_dive=None,
    ),
    "dataprep": Service(
        id="dataprep",
        name="Dataprep",
        category="Integration",
        data_role="batch",
        summary="Browser-based visual data preparation and cleaning.",
        pricing_model="Per user-hour in an instance group, with a free tier.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
            ),
            preview=(),
            restricted=("southamerica-east1",),
        ),
        key_resources=("Workspace", "Flow", "Agent", "Recipe"),
        deep_dive=None,
    ),
    # --- Governance ------------------------------------------------------
    "dataplex": Service(
        id="dataplex",
        name="Dataplex",
        category="Analytics",
        data_role="catalog",
        summary="Data management and governance across lakes, warehouses and streams.",
        pricing_model="Per processed TiB, by zone and lake type.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
            ),
            preview=("australia-southeast1",),
            restricted=("southamerica-east1",),
        ),
        key_resources=("Lake", "Zone", "Asset", "Aspect Type"),
        deep_dive=None,
    ),
    "data-catalog": Service(
        id="data-catalog",
        name="Data Catalog",
        category="Analytics",
        data_role="catalog",
        summary="Unified search and metadata across the data estate.",
        pricing_model="Free for entries in BigQuery and Cloud Storage.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Entry Group", "Entry", "Tag Template", "Search"),
        deep_dive=None,
    ),
    "sensitive-data-protection": Service(
        id="sensitive-data-protection",
        name="Sensitive Data Protection",
        category="Security & Governance",
        data_role="governance",
        summary="Discovery, de-identification and inspection of sensitive data.",
        pricing_model="Per inspected byte, after a free monthly allowance.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Inspect Template", "De-identify Template", "InfoType", "Job"),
        deep_dive=None,
    ),
    "looker-studio": Service(
        id="looker-studio",
        name="Looker Studio",
        category="Analytics",
        data_role="catalog",
        summary="Browser-based business intelligence and dashboarding.",
        pricing_model="Free per user for reports, with connector and Pro costs.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Report", "Data Source", "Dashboard", "Viewer"),
        deep_dive=None,
    ),
    # --- Transfer --------------------------------------------------------
    "storage-transfer": Service(
        id="storage-transfer",
        name="Storage Transfer Service",
        category="Storage",
        data_role="storage",
        summary="Scheduled bulk transfer of object storage data.",
        pricing_model="Free; you pay the source and destination charges.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Job", "Transfer Job", "Agent", "Notification"),
        deep_dive=None,
    ),
    "bigquery-transfer": Service(
        id="bigquery-transfer",
        name="BigQuery Data Transfer Service",
        category="Analytics",
        data_role="storage",
        summary="Scheduled load of external sources into BigQuery.",
        pricing_model="Free; you pay the BigQuery query and storage charges.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Transfer Config", "Transfer Run", "Schedule"),
        deep_dive=None,
    ),
    "database-migration": Service(
        id="database-migration",
        name="Database Migration Service",
        category="Databases",
        data_role="warehouse",
        summary="Self-service, low-downtime migration to Cloud SQL.",
        pricing_model="Per connection-hour during the migration only.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Connection Profile", "Migration Job", "Source Database"),
        deep_dive=None,
    ),
    # --- AI / ML ---------------------------------------------------------
    "vertex-ai": Service(
        id="vertex-ai",
        name="Vertex AI",
        category="AI & ML",
        data_role="batch",
        summary="Managed platform for training and deploying ML models.",
        pricing_model="Per training node-hour, plus prediction request cost.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Dataset", "Model", "Endpoint", "Pipeline"),
        deep_dive=None,
    ),
    "bigquery-ml": Service(
        id="bigquery-ml",
        name="BigQuery ML",
        category="AI & ML",
        data_role="batch",
        summary="Train and serve models with SQL inside the warehouse.",
        pricing_model="Included with BigQuery compute.",
        availability=RegionAvailability(
            available=(
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "europe-west1",
                "europe-west2",
                "europe-west4",
                "asia-south1",
                "asia-southeast1",
                "asia-northeast1",
                "australia-southeast1",
            ),
            preview=(),
            restricted=(),
        ),
        key_resources=("Model", "Training Run", "Prediction Query"),
        deep_dive=None,
    ),
    "looker": Service(
        id="looker",
        name="Looker",
        category="Analytics",
        data_role="catalog",
        summary="Governed semantic layer and business-intelligence platform.",
        pricing_model="Per user per month, by edition.",
        availability=RegionAvailability(
            available=tuple(REGIONS),
            preview=(),
            restricted=(),
        ),
        key_resources=("Model", "Explore", "Dashboard", "Connection"),
        deep_dive=None,
    ),
}

#: Services that are part of the data-engineering core, in the order a
#: platform is usually built. The course uses this as the reference
#: architecture and the selection matrix.
CORE_PIPELINE_SERVICES = (
    "pubsub",
    "storage-transfer",
    "cloud-storage",
    "dataproc",
    "dataflow",
    "bigquery",
    "biglake",
    "dataform",
    "composer",
    "workflows",
    "dataplex",
    "data-catalog",
    "sensitive-data-protection",
)


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------


def get_service(service_id: str) -> Service:
    """Look up a service by its id.

    Args:
        service_id: The short id, e.g. ``"bigquery"``.

    Returns:
        The :class:`Service`.

    Raises:
        KeyError: If no such service exists.
    """
    try:
        return SERVICES[service_id]
    except KeyError as exc:
        raise KeyError(f"unknown service: {service_id!r}") from exc


def services_by_category(category: str) -> list[Service]:
    """Return every service in a category, in name order.

    Args:
        category: One of :data:`CATEGORIES`.

    Returns:
        The matching services.

    Raises:
        KeyError: If the category is not one of :data:`CATEGORIES`.
    """
    if category not in CATEGORIES:
        raise KeyError(f"unknown category: {category!r}")
    return sorted(
        (service for service in SERVICES.values() if service.category == category),
        key=lambda service: service.name,
    )


def regions_for(service_id: str) -> tuple[str, ...]:
    """Return the regions where a service is generally available.

    Args:
        service_id: The short service id.

    Returns:
        The region codes.

    Raises:
        KeyError: If no such service exists.
    """
    return get_service(service_id).availability.available


def zones_in(region: str) -> tuple[str, ...]:
    """Return the three zones within a region.

    Args:
        region: The region code, e.g. ``"us-central1"``.

    Returns:
        The zone codes.

    Raises:
        KeyError: If the region is not in :data:`REGIONS`.
    """
    if region not in REGIONS:
        raise KeyError(f"unknown region: {region!r}")
    return tuple(f"{region}-{suffix}" for suffix in ZONE_SUFFIXES)


def nearest_region(region: str, service_id: str) -> str | None:
    """Find the closest region where a service is generally available.

    Real GCP has a latency-distance map between regions. This course uses
    a simplified ranking: the requested region first, then the other
    regions in declaration order. The point is the *shape* of the answer
    — a service is never truly "unavailable", it is available elsewhere
    at a latency and a data-residency cost.

    Args:
        region: The preferred region.
        service_id: The short service id.

    Returns:
        A region code, or None when the service is available nowhere.
    """
    service = get_service(service_id)
    if region in service.availability.available:
        return region
    for candidate in REGIONS:
        if candidate in service.availability.available:
            return candidate
    return None


def services_available_in(region: str) -> list[Service]:
    """Return every service generally available in a region.

    Args:
        region: The region code.

    Returns:
        The matching services, in name order.
    """
    return sorted(
        (
            service
            for service in SERVICES.values()
            if service.is_available_in(region)
        ),
        key=lambda service: service.name,
    )


def services_with_deep_dive() -> list[Service]:
    """Return the services this course links out to.

    Returns:
        The services with a ``deep_dive`` link, in name order.
    """
    return sorted(
        (service for service in SERVICES.values() if service.deep_dive),
        key=lambda service: service.name,
    )


def data_role_index() -> dict[str, list[str]]:
    """Group service ids by the role they play in a data platform.

    Returns:
        A dict of role -> list of service ids, sorted within each role.
    """
    index: dict[str, list[str]] = {}
    for service in SERVICES.values():
        index.setdefault(service.data_role, []).append(service.id)
    return {role: sorted(ids) for role, ids in sorted(index.items())}


def summary_table() -> list[dict[str, object]]:
    """Build a tabular view of the service inventory.

    The course's tables are generated from this function rather than
    hand-written, so a change to the inventory stays consistent across
    every chapter and notebook.

    Returns:
        A list of row dicts, sorted by category then name.
    """
    rows: list[dict[str, object]] = []
    for service in SERVICES.values():
        rows.append(
            {
                "id": service.id,
                "name": service.name,
                "category": service.category,
                "role": service.data_role,
                "regions": len(service.availability.available),
                "pricing": service.pricing_model,
                "deep_dive": service.deep_dive or "",
            }
        )
    return sorted(rows, key=lambda row: (str(row["category"]), str(row["name"])))


def region_status_matrix(service_ids: Iterable[str] | None = None) -> list[dict[str, object]]:
    """Build a region-by-service availability matrix.

    Args:
        service_ids: The service ids to include. Defaults to every service.

    Returns:
        A list of row dicts — one per service — with a per-region status.
    """
    ids = list(service_ids) if service_ids is not None else list(SERVICES)
    rows: list[dict[str, object]] = []
    for service_id in ids:
        service = get_service(service_id)
        row: dict[str, object] = {"id": service.id, "name": service.name}
        for region in REGIONS:
            row[region] = service.availability.status(region)
        rows.append(row)
    return rows


def format_service_table(service_ids: Iterable[str] | None = None) -> str:
    """Render the service inventory as a Markdown table.

    Args:
        service_ids: The service ids to include. Defaults to every service.

    Returns:
        The Markdown table.
    """
    ids = list(service_ids) if service_ids is not None else list(SERVICES)
    lines = [
        "| Service | Category | Role | Regions | Pricing |",
        "|---|---|---|---|---|",
    ]
    for row in summary_table():
        if row["id"] not in ids:
            continue
        lines.append(
            f"| {row['name']} | {row['category']} | {row['role']} | "
            f"{row['regions']} | {row['pricing']} |"
        )
    return "\n".join(lines)


def format_region_matrix(service_ids: Iterable[str] | None = None) -> str:
    """Render the region availability matrix as a Markdown table.

    Args:
        service_ids: The service ids to include. Defaults to every service.

    Returns:
        The Markdown table.
    """
    rows = region_status_matrix(service_ids)
    header = "| Service | " + " | ".join(REGIONS) + " |"
    divider = "|---" * (len(REGIONS) + 1) + "|"
    symbols = {"available": "✅", "preview": "🟡", "restricted": "🟠", "unavailable": "—"}
    lines = [header, divider]
    for row in rows:
        cells = " | ".join(symbols[str(row[region])] for region in REGIONS)
        lines.append(f"| {row['name']} | {cells} |")
    return "\n".join(lines)
