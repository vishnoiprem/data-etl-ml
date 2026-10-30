"""
iam_policy.py — a pure simulation of GCP IAM policy evaluation.

This module models the parts of GCP IAM that actually decide whether a
call succeeds:

    * **Principal types** — user, group, service account, domain.
    * **Roles** — a named bundle of permissions.
    * **Bindings** — a role granted to a principal at a resource.
    * **Conditional bindings** — a binding that only applies when a
      resource tag or IAM condition matches.
    * **The allow/deny precedence** — an explicit DENY always beats an
      ALLOW, and a grant anywhere in the hierarchy applies downwards.

The rule this module exists to teach is the one people get wrong:

    **A role granted at the project level is inherited by every bucket,
    table and dataset underneath it — which means a project-level
    ``roles/owner`` is a much bigger blast radius than it looks.**

Usage:
    from iam_policy import Policy, Binding, Principal, evaluate

    policy = Policy()
    policy.add(Principal("user", "ana@example.com"),
               Binding("roles/storage.objectViewer"))
    result = evaluate(policy, "ana@example.com", "storage.objects.get",
                      resource="projects/p/buckets/b")
    print(result.allowed)
"""
from __future__ import annotations

import dataclasses
from typing import Iterable

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

#: The primitive permissions used by the course. Real GCP has thousands;
#: these are the ones that appear in the chapters and exercises.
PERMISSIONS = frozenset(
    {
        # Storage
        "storage.buckets.create",
        "storage.buckets.delete",
        "storage.buckets.get",
        "storage.buckets.update",
        "storage.objects.create",
        "storage.objects.delete",
        "storage.objects.get",
        "storage.objects.list",
        "storage.objects.update",
        "storage.buckets.setIamPolicy",
        # BigQuery
        "bigquery.datasets.create",
        "bigquery.datasets.get",
        "bigquery.datasets.delete",
        "bigquery.tables.create",
        "bigquery.tables.get",
        "bigquery.tables.update",
        "bigquery.tables.delete",
        "bigquery.tables.getData",
        "bigquery.jobs.create",
        "bigquery.jobs.createQuery",
        "bigquery.reservations.update",
        # Pub/Sub
        "pubsub.topics.create",
        "pubsub.topics.publish",
        "pubsub.topics.attachSubscription",
        "pubsub.subscriptions.create",
        "pubsub.subscriptions.consume",
        "pubsub.subscriptions.update",
        # Compute / containers
        "compute.instances.create",
        "compute.instances.delete",
        "compute.instances.setServiceAccount",
        "container.clusters.create",
        "run.services.create",
        "run.jobs.create",
        "cloudfunctions.functions.create",
        # IAM and org
        "iam.serviceAccounts.create",
        "iam.serviceAccounts.actAs",
        "iam.serviceAccounts.get",
        "resourcemanager.projects.setIamPolicy",
        "resourcemanager.projects.getIamPolicy",
        "orgpolicy.policy.set",
        # Data and governance
        "datacatalog.entries.create",
        "datacatalog.entries.get",
        "datacatalog.tagTemplates.create",
        "sensitivedatainspection.inspect",
        "sensitivedatainspection.deidentify",
        # Machine learning
        "ml.models.create",
        "aiplatform.endpoints.predict",
        # General
        "resourcemanager.projects.get",
        "resourcemanager.projects.list",
        "serviceusage.services.enable",
    }
)

#: The roles used by the course, each a set of permissions.
ROLES: dict[str, frozenset[str]] = {
    "roles/owner": frozenset(PERMISSIONS),
    "roles/editor": frozenset(
        p
        for p in PERMISSIONS
        if not p.startswith(("iam.serviceAccounts.", "orgpolicy.", "resourcemanager.projects.set"))
    ),
    "roles/viewer": frozenset(
        p
        for p in PERMISSIONS
        if p.endswith((".get", ".list"))
        or p
        in {
            "storage.objects.list",
            "bigquery.tables.getData",
            "storage.buckets.get",
        }
    ),
    "roles/storage.admin": frozenset(
        {
            "storage.buckets.create",
            "storage.buckets.delete",
            "storage.buckets.get",
            "storage.buckets.update",
            "storage.objects.create",
            "storage.objects.delete",
            "storage.objects.get",
            "storage.objects.list",
            "storage.objects.update",
            "storage.buckets.setIamPolicy",
        }
    ),
    "roles/storage.objectViewer": frozenset(
        {"storage.objects.get", "storage.objects.list", "storage.buckets.get"}
    ),
    "roles/storage.objectCreator": frozenset(
        {"storage.objects.create", "storage.buckets.get"}
    ),
    "roles/bigquery.dataViewer": frozenset(
        {
            "bigquery.datasets.get",
            "bigquery.tables.get",
            "bigquery.tables.getData",
            "bigquery.jobs.createQuery",
        }
    ),
    "roles/bigquery.dataEditor": frozenset(
        {
            "bigquery.datasets.get",
            "bigquery.datasets.create",
            "bigquery.tables.get",
            "bigquery.tables.create",
            "bigquery.tables.update",
            "bigquery.tables.delete",
            "bigquery.tables.getData",
            "bigquery.jobs.create",
            "bigquery.jobs.createQuery",
        }
    ),
    "roles/bigquery.jobUser": frozenset(
        {"bigquery.jobs.create", "bigquery.jobs.createQuery", "bigquery.datasets.get"}
    ),
    "roles/pubsub.editor": frozenset(
        {
            "pubsub.topics.create",
            "pubsub.topics.publish",
            "pubsub.topics.attachSubscription",
            "pubsub.subscriptions.create",
            "pubsub.subscriptions.consume",
            "pubsub.subscriptions.update",
        }
    ),
    "roles/pubsub.subscriber": frozenset(
        {"pubsub.subscriptions.consume", "pubsub.subscriptions.update"}
    ),
    "roles/pubsub.publisher": frozenset({"pubsub.topics.publish"}),
    "roles/compute.admin": frozenset(
        {
            "compute.instances.create",
            "compute.instances.delete",
            "compute.instances.setServiceAccount",
        }
    ),
    "roles/container.admin": frozenset(
        {"container.clusters.create", "compute.instances.setServiceAccount"}
    ),
    "roles/run.admin": frozenset({"run.services.create", "run.jobs.create"}),
    "roles/cloudfunctions.admin": frozenset({"cloudfunctions.functions.create"}),
    "roles/iam.serviceAccountUser": frozenset({"iam.serviceAccounts.actAs"}),
    "roles/iam.serviceAccountAdmin": frozenset(
        {"iam.serviceAccounts.create", "iam.serviceAccounts.get", "iam.serviceAccounts.actAs"}
    ),
    "roles/resourcemanager.projectIamAdmin": frozenset(
        {"resourcemanager.projects.setIamPolicy", "resourcemanager.projects.getIamPolicy"}
    ),
    "roles/orgpolicy.policyAdmin": frozenset({"orgpolicy.policy.set"}),
    "roles/datacatalog.admin": frozenset(
        {
            "datacatalog.entries.create",
            "datacatalog.entries.get",
            "datacatalog.tagTemplates.create",
        }
    ),
    "roles/dlp.user": frozenset(
        {"sensitivedatainspection.inspect", "sensitivedatainspection.deidentify"}
    ),
    "roles/aiplatform.user": frozenset(
        {"ml.models.create", "aiplatform.endpoints.predict"}
    ),
}

#: The primitive permission each role name implies at a glance. Used by
#: the "which role do I need" tables in the chapters.
ROLE_SUMMARY: dict[str, str] = {
    "roles/owner": "Full control over every resource, and the ability to grant it.",
    "roles/editor": "Read and write access to most resources, but not IAM.",
    "roles/viewer": "Read-only access to resources.",
    "roles/storage.admin": "Full control of buckets and objects.",
    "roles/storage.objectViewer": "Read objects only.",
    "roles/storage.objectCreator": "Create objects but not read them.",
    "roles/bigquery.dataViewer": "Read datasets and table data.",
    "roles/bigquery.dataEditor": "Read and write datasets and tables.",
    "roles/bigquery.jobUser": "Run queries and jobs, without seeing the data.",
    "roles/pubsub.editor": "Full control of topics and subscriptions.",
    "roles/pubsub.publisher": "Publish to topics only.",
    "roles/pubsub.subscriber": "Consume from subscriptions only.",
    "roles/compute.admin": "Manage Compute Engine instances.",
    "roles/container.admin": "Manage Kubernetes clusters.",
    "roles/run.admin": "Manage Cloud Run services and jobs.",
    "roles/cloudfunctions.admin": "Manage Cloud Run functions.",
    "roles/iam.serviceAccountUser": "Act as a service account.",
    "roles/iam.serviceAccountAdmin": "Create and manage service accounts.",
    "roles/resourcemanager.projectIamAdmin": "Set IAM policy on projects.",
    "roles/orgpolicy.policyAdmin": "Set organization policies.",
    "roles/datacatalog.admin": "Manage catalog entries and tag templates.",
    "roles/dlp.user": "Run inspect and de-identify jobs.",
    "roles/aiplatform.user": "Train models and call endpoints.",
}


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Principal:
    """An identity that can be granted a role.

    Attributes:
        kind: One of ``"user"``, ``"group"``, ``"serviceAccount"`` or
            ``"domain"``.
        name: The identity's identifier — an email, a service account
            address, or a domain.
    """

    kind: str
    name: str

    def __str__(self) -> str:
        """Render the principal in its canonical GCP form.

        Returns:
            The canonical string, e.g.
            ``"serviceAccount:svc@my-project.iam.gserviceaccount.com"``.
        """
        return f"{self.kind}:{self.name}"


@dataclasses.dataclass(frozen=True)
class Binding:
    """A role granted to a principal, optionally with a condition.

    Attributes:
        role: The role name, e.g. ``"roles/storage.objectViewer"``.
        condition: An optional condition description. A binding with a
            condition only applies when the condition is satisfied.
        denied: When True this is a DENY binding, which overrides every
            ALLOW. GCP calls this ``gcpIamDeny`` in policy overrides.
    """

    role: str
    condition: str | None = None
    denied: bool = False


@dataclasses.dataclass
class Policy:
    """An IAM policy: a set of bindings, each at a resource path.

    Attributes:
        bindings: The bindings, keyed by resource path.
    """

    bindings: dict[str, list[tuple[Principal, Binding]]] = dataclasses.field(
        default_factory=dict
    )

    def add(
        self,
        principal: Principal,
        binding: Binding,
        resource: str = "projects/p",
    ) -> None:
        """Grant a binding to a principal at a resource.

        Args:
            principal: The identity.
            binding: The role and optional condition.
            resource: The resource path the grant applies to.
        """
        self.bindings.setdefault(resource, []).append((principal, binding))

    def deny(
        self,
        principal: Principal,
        role: str,
        resource: str = "projects/p",
    ) -> None:
        """Add an explicit DENY for a principal at a resource.

        Args:
            principal: The identity.
            role: The role being denied.
            resource: The resource path.
        """
        self.add(principal, Binding(role=role, denied=True), resource)

    def grants_for(self, resource: str) -> list[tuple[Principal, Binding]]:
        """Return every binding that applies to a resource.

        GCP inheritance is downward: a grant at a project applies to
        every resource under it. This method reproduces that by walking
        the resource path from the widest scope down to the resource.

        Args:
            resource: The resource path, e.g.
                ``"projects/p/buckets/b"``.

        Returns:
            The applicable bindings.
        """
        applicable: list[tuple[Principal, Binding]] = []
        for path in ancestor_paths(resource):
            applicable.extend(self.bindings.get(path, []))
        return applicable


@dataclasses.dataclass(frozen=True)
class Decision:
    """The result of evaluating a permission request.

    Attributes:
        allowed: Whether the call is permitted.
        reason: A human-readable explanation.
        matched_roles: The roles whose permissions covered the request.
        denied_roles: The roles that explicitly denied the request.
        inherited: Whether the decisive grant came from an ancestor
            resource rather than the resource itself.
    """

    allowed: bool
    reason: str
    matched_roles: tuple[str, ...] = ()
    denied_roles: tuple[str, ...] = ()
    inherited: bool = False


def ancestor_paths(resource: str) -> list[str]:
    """Return a resource's ancestry, most specific first.

    GCP resource paths are sequences of ``type/name`` pairs, and the
    inheritance hierarchy steps in *pairs*, not in single segments. For
    ``"projects/p/buckets/b/objects/o"`` the ancestry is:

        * ``projects/p/buckets/b/objects/o``
        * ``projects/p/buckets/b``
        * ``projects/p``

    Note what is **not** in that list: ``projects/p/buckets/b/objects``
    and ``projects/p/buckets``. Those are not real GCP scopes — there
    is no such thing as an IAM binding on "the objects collection of a
    bucket" — and treating them as scopes makes a policy look like it
    inherits grants it does not.

    Args:
        resource: The resource path.

    Returns:
        The ancestor paths, most specific first.
    """
    parts = [part for part in resource.split("/") if part]
    # A GCP path is a sequence of type/name pairs. An odd number of
    # segments is malformed; fall back to the flat interpretation.
    if len(parts) % 2 != 0:
        return ["/".join(parts[:index]) for index in range(len(parts), 0, -1)]

    paths: list[str] = []
    for pairs in range(len(parts) // 2, 0, -1):
        paths.append("/".join(parts[: pairs * 2]))
    return paths


def role_permissions(role: str) -> frozenset[str]:
    """Return the permissions a role grants.

    Args:
        role: The role name.

    Returns:
        The permission set. An unknown role grants nothing.

    Raises:
        KeyError: If the role is not in :data:`ROLES`.
    """
    if role not in ROLES:
        raise KeyError(f"unknown role: {role!r}")
    return ROLES[role]


def evaluate(
    policy: Policy,
    identity: str,
    permission: str,
    *,
    resource: str = "projects/p",
    attributes: dict[str, str] | None = None,
) -> Decision:
    """Evaluate whether an identity may perform a permission.

    The precedence rules implemented here are the real ones:

    1. An explicit **DENY** anywhere wins over any ALLOW.
    2. Otherwise, an **ALLOW** from any applicable binding wins.
    3. A binding with a **condition** only applies when the condition
       matches the supplied attributes.
    4. If nothing matches, the call is denied.

    Args:
        policy: The policy to evaluate.
        identity: The identity's identifier, e.g. ``"ana@example.com"``.
        permission: The primitive permission being requested.
        resource: The resource the call targets. Defaults to the
            project-level scope, which is where most grants live.
        attributes: Resource attributes used to evaluate conditions.

    Returns:
        A :class:`Decision`.
    """
    attributes = attributes or {}
    applicable = policy.grants_for(resource)
    exact = resource in policy.bindings

    matched: list[str] = []
    denied: list[str] = []
    for principal, binding in applicable:
        if not _identity_matches(principal, identity):
            continue
        if binding.condition and not _condition_matches(binding.condition, attributes):
            continue
        if binding.denied:
            denied.append(binding.role)
            continue
        try:
            permissions = role_permissions(binding.role)
        except KeyError:
            continue
        if permission in permissions:
            matched.append(binding.role)

    if denied:
        return Decision(
            allowed=False,
            reason=(
                f"explicit DENY on {', '.join(sorted(set(denied)))} overrides "
                f"the ALLOW on {', '.join(sorted(set(matched))) or 'no role'}"
            ),
            matched_roles=tuple(sorted(set(matched))),
            denied_roles=tuple(sorted(set(denied))),
            inherited=not exact,
        )

    if matched:
        source = "granted at" if exact else "inherited from an ancestor of"
        return Decision(
            allowed=True,
            reason=f"{permission} is {source} the resource via {', '.join(sorted(set(matched)))}",
            matched_roles=tuple(sorted(set(matched))),
            inherited=not exact,
        )

    return Decision(
        allowed=False,
        reason=f"no binding grants {permission} on this resource",
    )


def _identity_matches(principal: Principal, identity: str) -> bool:
    """Return True when a principal matches an identity string.

    A ``domain`` principal matches any identity in that domain. A
    ``group`` matches its member list, which this module does not model,
    so group principals only match an identity whose name is the group's
    own address.

    Args:
        principal: The principal in the binding.
        identity: The identity being evaluated.

    Returns:
        True when the binding applies to the identity.
    """
    if principal.kind == "domain":
        domain = principal.name.lstrip("@")
        return identity.endswith("@" + domain) or identity == domain
    if principal.kind == "group":
        return identity == principal.name
    return identity == principal.name


def _condition_matches(condition: str, attributes: dict[str, str]) -> bool:
    """Evaluate a condition against resource attributes.

    The course uses a deliberately simple condition syntax — a
    comma-separated list of ``attribute == value`` pairs — rather than
    CEL, so the chapters can show the *shape* of a conditional binding
    without needing the full expression language.

    Args:
        condition: The condition expression.
        attributes: The resource attributes.

    Returns:
        True when every clause in the condition holds.
    """
    for clause in condition.split(","):
        clause = clause.strip()
        if not clause:
            continue
        if "==" not in clause:
            # A condition with no comparison we understand fails closed.
            return False
        key, _, expected = clause.partition("==")
        key = key.strip()
        expected = expected.strip()
        actual = attributes.get(key)
        if actual is None:
            return False
        if actual != expected:
            return False
    return True


def effective_permissions(
    policy: Policy,
    identity: str,
    *,
    resource: str = "projects/p",
    attributes: dict[str, str] | None = None,
) -> list[str]:
    """Return every permission an identity holds on a resource.

    Args:
        policy: The policy to evaluate.
        identity: The identity's identifier.
        resource: The resource path.
        attributes: Resource attributes for condition evaluation.

    Returns:
        The sorted permission list.
    """
    granted: set[str] = set()
    for principal, binding in policy.grants_for(resource):
        if not _identity_matches(principal, identity):
            continue
        if binding.condition and not _condition_matches(binding.condition, attributes or {}):
            continue
        if binding.denied:
            granted -= role_permissions(binding.role)
            continue
        granted |= role_permissions(binding.role)
    return sorted(granted)


def explain_principal(
    policy: Policy,
    identity: str,
    *,
    resource: str = "projects/p",
) -> list[str]:
    """Explain every binding that applies to an identity, in order.

    This is the "why can I do this?" tool. It reports the resource each
    grant came from, so an inherited project-level grant is visibly
    distinct from a resource-level one.

    Args:
        policy: The policy to explain.
        identity: The identity's identifier.
        resource: The resource path.

    Returns:
        One explanation line per applicable binding.
    """
    lines: list[str] = []
    for path in ancestor_paths(resource):
        for principal, binding in policy.bindings.get(path, []):
            if not _identity_matches(principal, identity):
                continue
            kind = "DENY " if binding.denied else "ALLOW"
            scope = "exact" if path == resource else "inherited"
            condition = f" [if {binding.condition}]" if binding.condition else ""
            lines.append(
                f"{kind} {binding.role} on {path} ({scope}) for {principal}{condition}"
            )
    return lines


def blast_radius(
    policy: Policy,
    identity: str,
    resources: Iterable[str],
) -> dict[str, bool]:
    """Compute which resources an identity can reach.

    This is the tool for the question the course keeps asking: *if this
    identity is compromised, what can it touch?*

    Args:
        policy: The policy to evaluate.
        identity: The identity's identifier.
        resources: The resource paths to test.

    Returns:
        A dict of resource -> whether the identity holds any permission
        on it.
    """
    result: dict[str, bool] = {}
    for resource in resources:
        permissions = effective_permissions(policy, identity, resource=resource)
        result[resource] = bool(permissions)
    return result


def find_over_privileged(
    policy: Policy,
    identity: str,
    *,
    resource: str = "projects/p",
) -> list[str]:
    """Return the roles granted to an identity that they do not need.

    The check is deliberately simple: a role that contributes **no**
    permission the identity was not already getting from a narrower role
    is redundant. A role that contributes many permissions is *not*
    flagged by this function — that judgement needs a purpose, which is
    the point the chapter makes.

    Args:
        policy: The policy to evaluate.
        identity: The identity's identifier.
        resource: The resource path.

    Returns:
        The redundant role names.
    """
    applied: list[str] = []
    for principal, binding in policy.grants_for(resource):
        if not _identity_matches(principal, identity):
            continue
        if binding.denied or binding.condition:
            continue
        if binding.role not in applied:
            applied.append(binding.role)

    if len(applied) < 2:
        return []

    redundant: list[str] = []
    for index, role in enumerate(applied):
        others = [
            role_permissions(other)
            for position, other in enumerate(applied)
            if position != index
        ]
        combined: set[str] = set()
        for permissions in others:
            combined |= permissions
        if role_permissions(role) <= combined:
            redundant.append(role)
    return redundant
