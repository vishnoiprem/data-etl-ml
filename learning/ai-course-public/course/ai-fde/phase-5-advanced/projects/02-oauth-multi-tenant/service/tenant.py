"""
projects/02-oauth-multi-tenant/service/tenant.py — per-tenant policy file.

Each tenant gets its own YAML. The keys are: name, rate_limits, model,
budget. The drafter applies the policy on every request via the
TenantResolver.

Why a YAML, not a database
--------------------------
Same reason as Phase 4 MCP: code-reviewable, version-controlled, diffable.
A database-backed policy would lose all three.

Adding a new tenant is a 1-file change.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def load_tenant_config(
    tenant_id: str,
    config_dir: Path | None = None,
) -> dict[str, Any]:
    """Load the YAML for `tenant_id`. Falls back to the in-code defaults
    if no file exists (for the lesson; production requires a file)."""
    if config_dir is None:
        config_dir = Path(os.environ.get("TENANT_CONFIG_DIR", "tenants"))
    p = config_dir / f"{tenant_id}.yaml"
    if not p.exists():
        # Fall back to the in-code defaults in oauth.py
        from oauth import _default_tenant_config
        all_cfg = _default_tenant_config()
        if tenant_id not in all_cfg:
            raise KeyError(f"unknown tenant: {tenant_id!r}")
        return all_cfg[tenant_id]
    try:
        import yaml  # type: ignore
        return yaml.safe_load(p.read_text())
    except Exception:
        # Fall back on parse error too
        from oauth import _default_tenant_config
        return _default_tenant_config()[tenant_id]
