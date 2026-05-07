"""CLI: run all sample requests through the secure pipeline + verify audit chain."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.audit import AuditLog
from src.authz import Principal, Resource
from src.pipeline import PipelineRequest, run_pipeline

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def main():
    log_path = ROOT / "data" / "audit.log"
    if log_path.exists():
        log_path.unlink()
    audit = AuditLog(log_path)

    requests = [json.loads(l) for l in (ROOT / "sample_data" / "requests.jsonl").read_text().splitlines() if l]
    console.rule(f"[bold cyan]Secure Pipeline — {len(requests)} requests[/bold cyan]")

    table = Table(title="Per-request outcomes")
    table.add_column("ID")
    table.add_column("Kind")
    table.add_column("Principal")
    table.add_column("Allowed", style="bold")
    table.add_column("Blocked at")
    table.add_column("Findings", style="dim")

    for r in requests:
        req = PipelineRequest(
            principal=Principal(**r["principal"]),
            resource=Resource(**r["resource"]),
            action=r["action"],
            user_text=r["user_text"],
        )
        resp = run_pipeline(req, audit)
        allowed = "[green]yes[/green]" if resp.allowed else "[red]no[/red]"
        blocked_at = resp.blocked_at or "-"
        findings = []
        if resp.findings.get("injection", {}).get("reasons"):
            findings.append(f"injection: {','.join(resp.findings['injection']['reasons'])}")
        if resp.findings.get("input_pii"):
            findings.append(f"input_pii: {len(resp.findings['input_pii'])} hits")
        if resp.findings.get("output_pii"):
            findings.append(f"output_pii: {len(resp.findings['output_pii'])} hits")
        if resp.findings.get("authz"):
            findings.append(f"authz: {','.join(resp.findings['authz'])[:40]}")
        table.add_row(r["id"], r["kind"], req.principal.user_id, allowed, blocked_at,
                      "; ".join(findings)[:80])

    console.print(table)

    # Verify audit chain
    ok, broken = audit.verify()
    console.print(Panel.fit(
        f"Total entries: [bold]{len(audit.entries)}[/bold]\n"
        f"Hash chain verified: {'[green]yes[/green]' if ok else f'[red]NO (broken at seq {broken})[/red]'}\n"
        f"Log file: {log_path}",
        title="Audit log",
    ))

    # Demonstrate tamper detection
    console.print("\n[bold]Tamper-detection check:[/bold]")
    if audit.entries:
        original_outcome = audit.entries[2].outcome
        audit.entries[2].outcome = "TAMPERED"
        ok2, broken2 = audit.verify()
        console.print(
            f"  Modified entry seq=3 outcome → chain verifies? "
            f"{'[green]yes[/green]' if ok2 else f'[red]no, broken at seq {broken2}[/red]'}"
        )
        audit.entries[2].outcome = original_outcome   # restore for cleanliness


if __name__ == "__main__":
    main()
