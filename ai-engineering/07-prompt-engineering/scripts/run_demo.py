"""End-to-end demo: register prompts, promote, A/B test, pack context."""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.context import Chunk, pack_context
from src.experiments import BayesianAB, Variant
from src.registry import PromptVersion, Registry

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def main():
    reg_path = ROOT / "data" / "registry.json"
    if reg_path.exists():
        reg_path.unlink()
    reg = Registry(path=reg_path)

    # ── 1. Register two prompt versions ───────────────────────────────────────
    v1 = PromptVersion.of(
        prompt_id="ticket.summarize",
        template=(
            "Summarize this support ticket in one sentence:\n"
            "Ticket: {{ ticket }}\n"
            "Summary:"
        ),
        defaults={"ticket": ""},
        notes="initial baseline",
    )
    v2 = PromptVersion.of(
        prompt_id="ticket.summarize",
        template=(
            "You are a customer-support analyst. In ONE sentence, capture the "
            "user's intent, the affected feature, and the apparent severity.\n"
            "Ticket: {{ ticket | trim }}\n"
            "Summary:"
        ),
        defaults={"ticket": ""},
        notes="explicit role + structure",
    )
    reg.register(v1)
    reg.register(v2)
    reg.promote("ticket.summarize", v1.content_hash, "prod")
    reg.promote("ticket.summarize", v2.content_hash, "staging")

    table = Table(title="Prompt registry")
    table.add_column("prompt_id", style="cyan")
    table.add_column("env")
    table.add_column("version (content_hash)", style="bold")
    table.add_column("notes", style="dim")
    for env in ("prod", "staging"):
        v = reg.get("ticket.summarize", env)
        table.add_row("ticket.summarize", env, v.content_hash, v.notes)
    console.print(table)

    # ── 2. Render examples ────────────────────────────────────────────────────
    rendered_prod = reg.render("ticket.summarize", env="prod",
                               ticket="App crashes on Android 14 when uploading >50MB photos")
    rendered_staging = reg.render("ticket.summarize", env="staging",
                                   ticket="App crashes on Android 14 when uploading >50MB photos")
    console.print(Panel(rendered_prod, title="prod render"))
    console.print(Panel(rendered_staging, title="staging render"))

    # ── 3. A/B simulation ─────────────────────────────────────────────────────
    rng = random.Random(7)
    a = Variant("v1-prod")
    b = Variant("v2-staging")
    # Simulated truth: v2 has a slightly higher success rate (0.78 vs 0.65)
    for _ in range(300):
        a.record(rng.random() < 0.65)
        b.record(rng.random() < 0.78)
    ab = BayesianAB(a, b)
    p_b = ab.posterior_prob_b_better()
    a_lo, a_hi = ab.credible_interval(a)
    b_lo, b_hi = ab.credible_interval(b)
    decision = ab.decide(threshold=0.95)

    abt = Table(title="A/B experiment (Bayesian beta-binomial)")
    abt.add_column("variant", style="cyan")
    abt.add_column("n")
    abt.add_column("rate", style="bold")
    abt.add_column("95% CI")
    abt.add_row(a.name, str(a.n), f"{a.rate:.2%}", f"[{a_lo:.2%}, {a_hi:.2%}]")
    abt.add_row(b.name, str(b.n), f"{b.rate:.2%}", f"[{b_lo:.2%}, {b_hi:.2%}]")
    console.print(abt)
    console.print(Panel.fit(
        f"P(B > A) = [bold]{p_b:.3f}[/bold]\n"
        f"Decision: [bold]{decision.upper()}[/bold] "
        f"({'ship v2 to prod' if decision == 'ship_b' else 'keep v1' if decision == 'keep_a' else 'collect more data'})",
        title="Verdict",
    ))

    # ── 4. Promote v2 to prod (the rollback dance) ────────────────────────────
    if decision == "ship_b":
        prior = reg.env_pointers["ticket.summarize"]["prod"]
        reg.promote("ticket.summarize", v2.content_hash, "prod")
        console.print(f"Promoted v2 → prod. Prior pointer kept for rollback: [dim]{prior}[/dim]")
        # Demonstrate rollback
        reg.rollback("ticket.summarize", "prod", prior)
        console.print(f"Rolled back to [dim]{prior}[/dim] (current prod restored)")
        # Re-promote
        reg.promote("ticket.summarize", v2.content_hash, "prod")

    # ── 5. Context packing ────────────────────────────────────────────────────
    chunks = [
        Chunk("c1", "PTO accrues from day one for all full-time employees, see policy v3.", 0.92, "PTO"),
        Chunk("c2", "Open enrollment runs Nov 1–30; missing it requires a qualifying life event.", 0.88, "Benefits"),
        Chunk("c3", "EBS volumes encrypted with KMS CMK must be rotated annually per SOC 2.", 0.71, "Sec"),
        Chunk("c4", "Remote work eligible with a stipend; international moves need 90-day notice.", 0.55, "WFH"),
        Chunk("c5", "Expense reports must include receipts >=$25 and be filed within 30 days.", 0.40, "Expenses"),
        Chunk("c6", "Incident severity 1 requires page-everyone and 30-minute updates." * 6, 0.30, "Incidents"),
    ]
    pack = pack_context(chunks, budget_tokens=80, reserved_tokens=20)
    pkt = Table(title=f"Context pack — used {pack.used_tokens}/{pack.budget} tokens ({pack.utilization:.0%})")
    pkt.add_column("status", style="bold")
    pkt.add_column("chunk")
    pkt.add_column("score")
    pkt.add_column("tokens")
    pkt.add_column("note", style="dim")
    for c in pack.included:
        pkt.add_row("[green]include[/green]", c.title or c.chunk_id, f"{c.score:.2f}", str(c.token_count), "")
    for c, why in pack.dropped:
        pkt.add_row("[yellow]drop[/yellow]", c.title or c.chunk_id, f"{c.score:.2f}", str(c.token_count), why)
    console.print(pkt)


if __name__ == "__main__":
    main()
