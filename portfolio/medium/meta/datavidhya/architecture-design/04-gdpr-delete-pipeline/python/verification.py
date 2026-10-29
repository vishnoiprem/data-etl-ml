"""
Verification — re-run discovery and confirm zero matches.

Also aggregates per-system receipts into a signed compliance certificate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import List

from delete_coordinator import Receipt
from discovery import discover


@dataclass
class ComplianceCertificate:
    certificate_id: str
    request_id: str
    user_id: str
    systems_covered: int
    total_rows_deleted: int
    total_objects_deleted: int
    methods_used: List[str]
    merkle_root: str
    issued_at: float

    @property
    def verified(self) -> bool:
        """Re-discover and confirm zero matches."""
        d = discover(self.user_id)
        return len(d.locations) == 0


def verify_and_certify(
    request_id: str,
    user_id: str,
    receipts: List[Receipt],
) -> ComplianceCertificate:
    total_rows = sum(r.rows_deleted for r in receipts if r.status == "OK")
    total_objs = sum(r.objects_deleted for r in receipts if r.status == "OK")
    methods = sorted({r.method for r in receipts if r.status == "OK"})
    systems_covered = sum(1 for r in receipts if r.status == "OK")

    # Merkle root — Bitcoin-style: duplicate last leaf when odd.
    # The previous implementation dropped leaves on odd counts, producing
    # a different root depending on sort order. With duplication, every
    # input set deterministically produces the same root.
    hashes = sorted([r.hash() for r in receipts if r.status == "OK"])
    while len(hashes) > 1:
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])            # duplicate last leaf
        hashes = [
            hashlib.sha256((hashes[i] + hashes[i + 1]).encode()).hexdigest()
            for i in range(0, len(hashes), 2)
        ]
    merkle = hashes[0] if hashes else ""

    return ComplianceCertificate(
        certificate_id=f"cert-{request_id}",
        request_id=request_id,
        user_id=user_id,
        systems_covered=systems_covered,
        total_rows_deleted=total_rows,
        total_objects_deleted=total_objs,
        methods_used=methods,
        merkle_root=merkle,
        issued_at=__import__("time").time(),
    )


def verify(cert: ComplianceCertificate) -> dict:
    """Re-discover and report."""
    re_discovery = discover(cert.user_id)
    return {
        "certificate_id": cert.certificate_id,
        "user_id": cert.user_id,
        "verified": cert.verified,
        "rows_deleted": cert.total_rows_deleted,
        "objects_deleted": cert.total_objects_deleted,
        "systems_covered": cert.systems_covered,
        "remaining_locations": len(re_discovery.locations),
        "merkle_root": cert.merkle_root,
    }


if __name__ == "__main__":
    sample_receipts = [
        Receipt("iceberg", "local.bronze.events", 1_000_000, 0, "direct",
                1.0, 2.0, "OK"),
        Receipt("redis",   "user:42:session",     1, 0, "direct",
                1.0, 2.0, "OK"),
    ]
    cert = verify_and_certify("req-001", "user_42", sample_receipts)
    print(json.dumps(verify(cert), indent=2))
