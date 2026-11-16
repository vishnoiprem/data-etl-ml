"""D2 — which access pattern cost money.

The crux of this detector, and the reason it is the most careful one:

**CloudWatch's ``AWS/S3`` request metrics are per-bucket only.** There
is no prefix dimension. So "the scanner that hammers ``logs/``" cannot
be answered from CloudWatch, no matter how the query is written. Only
**S3 server access logs** name a prefix.

So this detector has two honest modes:

*Logs on.* It reads the log, classifies each request, and attributes
cost to prefixes. It then cross-checks the log's totals against
CloudWatch. If they differ by more than the coverage threshold, the
coverage is incomplete and the confidence is capped — the finding is
reported, but never as a complete picture.

*Logs off.* It says so. It does not pass bucket-level request counts
off as prefix-level ones, because that is the single most misleading
thing this tool could do.

The classification subtlety: ``REST.GET.BUCKET`` is a **LIST**, not a
GET. It is the console's "list objects", billed at roughly ten times
the GET rate. Classifying it as a GET understates the cost of a
scanner by an order of magnitude.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config import Thresholds
from ..models import (
    MODELLED,
    SAVINGS_BASIS_MODELLED,
    SAVINGS_BASIS_NOT_QUANTIFIED,
    UPPER_BOUND,
    Evidence,
    Finding,
    severity_for,
)
from ..pricing import classify_request

DETECTOR = "access"

#: A line of an S3 server access log.
#:
#: S3's log format is *not* Common Log Format. The fields that matter
#: here, in order, are:
#:
#:     bucket_owner bucket [time] remote_ip requester request_id operation "key" HTTP/1.1 status bytes ...
#:
#: The operation is ``REST.GET.OBJECT``-style, not ``GET`` — which is
#: exactly why the classifier in ``pricing`` exists. The key is quoted
#: and may contain spaces, so the quoted key is matched as a unit and
#: the operation is taken from the field before it.
LOG_LINE = re.compile(
    r"^\S+\s+"
    r"(?P<bucket>\S+)\s+"
    r"\[(?P<time>[^\]]+)\]\s+"
    r"\S+\s+\S+\s+\S+\s+"
    r"(?P<operation>\S+)\s+"
    r'"(?P<key>[^"]*)"\s+'
    r"\S+\s+"
    r"(?P<status>\d{3})\s+"
    r"(?P<bytes>\S+)"
)


@dataclass(slots=True)
class AccessLog:
    """A parsed access log."""

    total_requests: int = 0
    by_prefix: dict[str, dict[str, int]] = field(default_factory=dict)
    by_bucket: dict[str, int] = field(default_factory=dict)
    by_request_type: dict[str, int] = field(default_factory=dict)
    total_bytes: int = 0
    parse_errors: int = 0

    def prefix(self, bucket: str, key: str) -> str:
        """The prefix a key belongs to — its first path segment."""
        cleaned = key.lstrip("/")
        if not cleaned:
            return "(root)"
        head = cleaned.split("/", 1)[0]
        return head or "(root)"


def parse_access_log(text: str) -> AccessLog:
    """Parse an S3 server access log into per-prefix request counts."""
    log = AccessLog()

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = LOG_LINE.search(line)
        if not match:
            log.parse_errors += 1
            continue

        bucket = match.group("bucket")
        key = match.group("key")
        operation = match.group("operation")
        status = int(match.group("status"))
        raw_bytes = match.group("bytes")

        # A non-2xx response is not billed as a normal request in the
        # same way; the useful signal is the successful ones.
        if status >= 400:
            continue

        request_type = classify_request(operation, key)

        try:
            size = int(raw_bytes)
        except ValueError:
            size = 0
        log.total_bytes += size

        log.total_requests += 1
        log.by_request_type[request_type] = log.by_request_type.get(request_type, 0) + 1
        log.by_bucket[bucket] = log.by_bucket.get(bucket, 0) + 1

        prefix = log.prefix(bucket, key)
        bucket_prefixes = log.by_prefix.setdefault(bucket, {})
        bucket_prefixes[prefix] = bucket_prefixes.get(prefix, 0) + 1

    return log


def coverage_ratio(log_total: int, cloudwatch_total: float) -> float:
    """How much of the CloudWatch traffic the log actually captured.

    A ratio of 1.0 means the log saw everything CloudWatch counted. A
    ratio well below 1.0 means logging started late, was rotated away,
    or was never fully enabled — and the per-prefix picture is
    correspondingly incomplete.
    """
    if cloudwatch_total <= 0:
        return 0.0
    if log_total <= 0:
        return 0.0
    return log_total / cloudwatch_total


def detect_access_patterns(
    log: AccessLog,
    cloudwatch_requests: dict[str, float],
    thresholds: Thresholds,
    card,
    *,
    region: str = "",
    monthly_spend: float = 0.0,
) -> list[Finding]:
    """Find the access patterns that cost money.

    ``cloudwatch_requests`` maps a bucket to its CloudWatch request
    count for the period. It is the cross-check: if the log's totals do
    not agree with CloudWatch's, the log does not cover the whole
    period and the per-prefix numbers are a partial picture.
    """
    findings: list[Finding] = []

    for bucket, prefixes in log.by_prefix.items():
        cw_total = cloudwatch_requests.get(bucket, 0.0)
        log_total = sum(prefixes.values())
        coverage = coverage_ratio(log_total, cw_total)
        complete = coverage >= (1 - thresholds.max_log_coverage_gap)

        bucket_spend = monthly_spend if len(log.by_bucket) == 1 else monthly_spend * (
            log_total / max(sum(log.by_bucket.values()), 1)
        )

        # The per-prefix request cost, from the card.
        prefix_costs: list[tuple[str, float, int]] = []
        for prefix, count in prefixes.items():
            cost = card.request_cost(count, _dominant_type(log, bucket, prefix))
            prefix_costs.append((prefix, cost, count))
        prefix_costs.sort(key=lambda item: item[1], reverse=True)

        total_prefix_cost = sum(cost for _, cost, _ in prefix_costs)
        if total_prefix_cost < thresholds.min_access_usd:
            continue

        top_prefix, top_cost, top_count = prefix_costs[0]
        share = top_cost / total_prefix_cost if total_prefix_cost > 0 else 0.0

        # A prefix that is most of the traffic is the one worth naming.
        if share < 0.5:
            continue

        confidence = 1.0 if complete else thresholds.partial_log_confidence_cap

        evidence: list[Evidence] = [
            Evidence(
                metric="requests",
                value=float(top_count),
                unit="requests",
                source="access_log",
                period="",
                detail={"bucket": bucket, "prefix": top_prefix},
            ),
            Evidence(
                metric="request_cost",
                value=top_cost,
                unit="USD",
                source="rate_card",
                period="",
                detail={
                    "bucket": bucket,
                    "prefix": top_prefix,
                    "rate_card_region": card.region,
                    "analysis_region": region,
                    "basis": MODELLED,
                },
            ),
            Evidence(
                metric="log_coverage",
                value=round(coverage, 3),
                unit="ratio",
                source="access_log",
                period="",
                detail={
                    "bucket": bucket,
                    "log_requests": str(log_total),
                    "cloudwatch_requests": str(cw_total),
                },
            ),
        ]

        if not complete:
            evidence.append(
                Evidence(
                    metric="coverage_note",
                    value=1.0,
                    unit="flag",
                    source="access_log",
                    period="",
                    detail={
                        "bucket": bucket,
                        "note": (
                            "The access log accounts for only "
                            f"{coverage * 100:.0f}% of the CloudWatch request count, "
                            "so the per-prefix breakdown is incomplete."
                        ),
                    },
                )
            )

        list_share = log.by_request_type.get("LIST", 0) / max(log.total_requests, 1)
        if list_share > 0.5:
            evidence.append(
                Evidence(
                    metric="list_request_share",
                    value=round(list_share, 3),
                    unit="ratio",
                    source="access_log",
                    period="",
                    detail={
                        "bucket": bucket,
                        "note": (
                            "Most requests are LIST operations, which are billed at "
                            "about ten times the GET rate. A scanner or a chatty "
                            "listing job looks like this."
                        ),
                    },
                )
            )

        summary = (
            f"Prefix '{top_prefix}' in {bucket} took {top_count:,} requests, "
            f"about {share * 100:.0f}% of the log's traffic and roughly "
            f"${top_cost:,.2f} at the card's request rates."
        )
        if not complete:
            summary += (
                f" The log only accounts for {coverage * 100:.0f}% of the "
                f"CloudWatch request count, so this is a partial picture."
            )

        findings.append(
            Finding(
                id=f"access:{bucket}:{top_prefix}",
                detector=DETECTOR,
                title=f"{bucket}/{top_prefix} dominates the request traffic",
                severity=severity_for(top_cost, MODELLED),
                summary=summary,
                target=f"{bucket}/{top_prefix}",
                cost_impact=top_cost,
                cost_impact_basis=MODELLED,
                savings_estimate=top_cost,
                savings_basis=SAVINGS_BASIS_MODELLED,
                evidence=evidence,
                confidence=confidence,
                details={
                    "bucket": bucket,
                    "prefix": top_prefix,
                    "requests": top_count,
                    "share": share,
                    "log_coverage": coverage,
                    "coverage_complete": complete,
                    "list_request_share": list_share,
                    "bucket_monthly_spend": bucket_spend,
                },
                recommendation=(
                    "Find what is making these requests. If it is a scanner or a "
                    "listing job that does not need every object, narrowing its "
                    "prefix is usually cheaper than anything else."
                ),
            )
        )

    return findings


def _dominant_type(log: AccessLog, bucket: str, prefix: str) -> str:
    """The dominant request type for a prefix.

    The per-prefix counts do not carry the request *type*, only the
    total, so this uses the bucket's overall mix. When the bucket is
    dominated by LISTs, the prefix's cost is costed at the LIST rate.
    """
    counts = log.by_request_type
    if not counts:
        return "GET"
    return max(counts.items(), key=lambda item: item[1])[0]


def detect_logging_disabled(
    buckets: list[str],
    thresholds: Thresholds,
    card,
    *,
    region: str = "",
    monthly_spend: float = 0.0,
) -> list[Finding]:
    """Report that access logging is off, so D2 cannot name a prefix.

    This is the honest alternative to passing bucket-level request
    counts off as prefix-level ones. It says what is missing and what
    would fix it.
    """
    if monthly_spend < thresholds.min_access_usd:
        return []

    findings: list[Finding] = []
    for bucket in buckets:
        findings.append(
            Finding(
                id=f"access:{bucket}:logging-disabled",
                detector=DETECTOR,
                title=f"{bucket} has no access log, so its prefix costs are unknown",
                severity="low",
                summary=(
                    f"{bucket} has no server access logging enabled. CloudWatch "
                    f"reports its request count in total, but only an access log "
                    f"names the prefix — so the per-prefix cost of this bucket's "
                    f"requests cannot be determined."
                ),
                target=bucket,
                cost_impact=0.0,
                cost_impact_basis=UPPER_BOUND,
                confidence=1.0,
                savings_basis=SAVINGS_BASIS_NOT_QUANTIFIED,
                evidence=[
                    Evidence(
                        metric="logging_enabled",
                        value=0.0,
                        unit="boolean",
                        source="s3_api",
                        period="",
                        detail={"bucket": bucket},
                    )
                ],
                details={
                    "problem": "access_logging_disabled",
                    "note": (
                        "CloudWatch's AWS/S3 request metrics are per-bucket only. "
                        "Without an access log, no prefix can be named."
                    ),
                },
                recommendation=(
                    "Enable S3 server access logging on this bucket (and a "
                    "lifecycle rule on the log bucket). It is the only way to see "
                    "which prefix the requests are for."
                ),
            )
        )
    return findings
