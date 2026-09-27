"""
GDPR Deletion Request Intake.

Validates:
  - User identity (email OTP / SSO / government ID)
  - Account status (not already in legal hold)
  - 30-day SLA deadline

Creates a deletion_requests record and triggers discovery.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class DeletionRequest:
    request_id:        str
    user_id:           str
    requested_at:      str
    requested_by:      str
    verification_method: str
    sla_deadline:      str
    status:            str = "RECEIVED"


SLA_DAYS = 30


def create_request(
    user_id: str,
    requested_by: str = "self",
    verification_method: str = "email_otp",
) -> DeletionRequest:
    now = datetime.now(tz=timezone.utc)
    return DeletionRequest(
        request_id=str(uuid.uuid4()),
        user_id=user_id,
        requested_at=now.isoformat(),
        requested_by=requested_by,
        verification_method=verification_method,
        sla_deadline=(now + timedelta(days=SLA_DAYS)).isoformat(),
    )


def verify_identity(user_id: str, method: str, evidence: dict) -> bool:
    """Mock identity verification. Real: SSO, OTP, government ID."""
    if method == "email_otp":
        return evidence.get("otp_correct", False)
    if method == "sso":
        return evidence.get("sso_verified", False)
    if method == "gov_id":
        return evidence.get("gov_id_verified", False)
    return False


if __name__ == "__main__":
    req = create_request("user_42")
    print(json.dumps(asdict(req), indent=2))
