#!/usr/bin/env python3
"""Convert pip-audit JSON output into a SARIF 2.1.0 file for code scanning.

Why this exists
---------------
`pip-audit` 2.10.1 does NOT support `--format sarif`. Its supported output
formats are: columns, json, cyclonedx-json, cyclonedx-xml, markdown.

The pip-audit workflow used to call:

    python -m pip_audit ... --format sarif --output .audit/pip-audit.sarif

which always failed with:

    pip-audit: error: argument -f/--format: invalid OutputFormatChoice value: 'sarif'

Because that step ran under `shell: bash -e`, the non-zero exit aborted the
job and the SARIF was never uploaded to code scanning.

This script takes the `json` output that pip-audit *does* support and
translates it into a valid SARIF 2.1.0 document, so the upload step works.

Usage:
    python3 infra/scripts/pip_audit_json_to_sarif.py <input.json> <output.sarif> [manifest]

The input JSON is the raw output of:
    python -m pip_audit -r <pinned.txt> --no-deps --disable-pip --format json

The optional third argument is the repo-relative path of the requirements
manifest that was audited; it becomes the SARIF artifact location.

Exit codes:
    0 — SARIF written successfully (possibly with zero results)
    1 — usage error, unreadable input, or malformed JSON
"""

from __future__ import annotations

import json
import sys
from typing import Any

SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/"
    "Schemata/sarif-schema-2.1.0.json"
)
SARIF_VERSION = "2.1.0"
TOOL_NAME = "pip-audit"

# pip-audit advisories do not carry a severity field (it is always null), so
# we map the CVSS score onto SARIF levels. These thresholds match the ones
# used by .github/workflows/security-gate.yml.
HIGH_CVSS = 7.0
CRITICAL_CVSS = 9.0


def severity_level(score: float | None) -> str:
    """Map a CVSS score onto a SARIF result level."""
    if score is None:
        return "warning"
    if score >= CRITICAL_CVSS:
        return "error"
    if score >= HIGH_CVSS:
        return "error"
    if score >= 4.0:
        return "warning"
    return "note"


def cvss_score(vuln: dict[str, Any]) -> float | None:
    """Extract a numeric CVSS score from a pip-audit vulnerability entry."""
    cvss = vuln.get("cvss") or {}
    score = cvss.get("score")
    if isinstance(score, (int, float)):
        return float(score)
    return None


def dedupe_vulns(vulns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop duplicate advisories for the same package.

    pip-audit frequently reports the same advisory more than once (once per
    matching service record), which would otherwise produce duplicate SARIF
    results pointing at the same package.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for vuln in vulns:
        vid = vuln.get("id") or ""
        aliases = tuple(sorted(vuln.get("aliases") or []))
        key = (vid, aliases)
        if key in seen:
            continue
        seen.add(key)
        unique.append(vuln)
    return unique


def build_sarif(audit_data: dict[str, Any], manifest: str) -> dict[str, Any]:
    """Translate parsed pip-audit JSON into a SARIF 2.1.0 document."""
    results: list[dict[str, Any]] = []
    rules: dict[str, dict[str, Any]] = {}

    for dep in audit_data.get("dependencies", []):
        name = dep.get("name")
        version = dep.get("version")
        vulns = dedupe_vulns(dep.get("vulns") or [])
        if not name or not vulns:
            continue

        for vuln in vulns:
            vid = vuln.get("id") or "UNKNOWN"
            aliases = vuln.get("aliases") or []
            fix_versions = vuln.get("fix_versions") or []
            score = cvss_score(vuln)
            description = vuln.get("description") or ""

            rules[vid] = {
                "id": vid,
                "name": vid,
                "shortDescription": {"text": f"{name} {vid}"},
                "fullDescription": {"text": description.strip() or f"{name} advisory {vid}"},
                "help": {
                    "text": (
                        f"{name}=={version} is affected by {vid}"
                        + (f" ({', '.join(aliases)})" if aliases else "")
                        + (
                            f". Fixed in: {', '.join(fix_versions)}"
                            if fix_versions
                            else ". No fixed version available."
                        )
                    )
                },
                "properties": {
                    "tags": ["security", "pip-audit", "dependencies"]
                    + ([f"cvss-score:{score:g}"] if score is not None else []),
                    "security-severity": f"{score:g}" if score is not None else "0",
                },
            }

            results.append(
                {
                    "ruleId": vid,
                    "level": severity_level(score),
                    "message": {
                        "text": (
                            f"{name}=={version} is affected by {vid}"
                            + (f" ({', '.join(aliases)})" if aliases else "")
                            + (
                                f". Upgrade to {', '.join(fix_versions)}"
                                if fix_versions
                                else ". No fixed version available."
                            )
                        )
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": manifest},
                                "region": {"startLine": 1},
                            }
                        }
                    ],
                }
            )

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "informationUri": "https://pypi.org/project/pip-audit/",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def main(argv: list[str]) -> int:
    if len(argv) not in (3, 4):
        print(
            f"Usage: {argv[0]} <pip-audit-output.json> <output.sarif> [manifest]",
            file=sys.stderr,
        )
        return 1

    src, dst = argv[1], argv[2]
    # Optional third arg: the repo-relative path of the requirements manifest
    # the audit came from. Used as the SARIF artifact location so code
    # scanning points at the real source file instead of the temp JSON.
    manifest = argv[3] if len(argv) > 3 else src.rsplit("/", 1)[-1]

    try:
        with open(src, encoding="utf-8") as handle:
            audit_data = json.load(handle)
    except FileNotFoundError:
        print(f"::error::pip-audit JSON not found: {src}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"::error::Could not parse pip-audit JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(audit_data, dict):
        print("::error::pip-audit JSON must be an object", file=sys.stderr)
        return 1

    sarif = build_sarif(audit_data, manifest)

    try:
        with open(dst, "w", encoding="utf-8") as handle:
            json.dump(sarif, handle, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(f"::error::Could not write SARIF to {dst}: {exc}", file=sys.stderr)
        return 1

    count = len(sarif["runs"][0]["results"])
    print(f"Wrote {dst} with {count} result(s) from {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
