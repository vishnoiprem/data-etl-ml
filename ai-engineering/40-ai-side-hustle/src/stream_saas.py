"""
stream_saas.py — Micro-SaaS scaffolder (Stream 2).

Pipeline:
  1. Generate 3 SaaS ideas for a target niche.
  2. Pick the best by expected first-month revenue (price × assumed
     conversion × assumed traffic).
  3. Generate the landing page copy.
  4. Scaffold a minimal MVP repo (FastAPI + SQLite) under
     `output/saas/<idea_name>/`.
  5. Record a conservative "first month" revenue projection.

This doesn't actually build a real product (that's a 6-month job
for the human), but it does the *idea → copy → repo skeleton*
loop in 30 seconds, so you can pitch/test 10 ideas in an hour.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledger import Ledger
from publisher import write_file
from router import LLMRouter


SAAS_SYSTEM = """You are a SaaS copywriter. Write landing pages that:
- Lead with the outcome, not the feature
- Use plain language (8th-grade reading level)
- Have exactly 3 pricing tiers
- End with one CTA above the fold

Tone: confident, specific, no hype words. Output as markdown."""


@dataclass
class SaaSIdea:
    name: str
    one_liner: str
    mvp_weeks: int
    tam_usd: int
    price_usd: int
    moat: str

    @property
    def expected_month1_usd(self) -> float:
        """Conservative: 10 paying customers in month 1 if we launch fast."""
        return 10 * self.price_usd


def discover_ideas(niche: str, router: LLMRouter, n: int = 3) -> list[SaaSIdea]:
    prompt = (
        f"Niche: {niche}\n\n"
        f"Generate {n} small SaaS ideas targeting this niche. Each one must be "
        f"buildable in 1-2 weeks by a solo developer, have a clear moat, and "
        f"target a specific buyer (not 'everyone')."
    )
    data = router.json(
        prompt,
        schema_hint='{"ideas": [{"name": str, "one_liner": str, "mvp_weeks": int, '
                    '"tam_usd": int, "price_usd": int, "moat": str}]}',
    )
    return [
        SaaSIdea(
            name=i["name"],
            one_liner=i.get("one_liner", ""),
            mvp_weeks=int(i.get("mvp_weeks", 2)),
            tam_usd=int(i.get("tam_usd", 0)),
            price_usd=int(i.get("price_usd", 19)),
            moat=i.get("moat", "first-mover"),
        )
        for i in data.get("ideas", [])
    ]


def write_landing_copy(idea: SaaSIdea, router: LLMRouter) -> str:
    prompt = (
        f"Idea: {idea.name}\n"
        f"One-liner: {idea.one_liner}\n"
        f"Price: ${idea.price_usd}/mo\n\n"
        f"Write the full landing page copy in markdown."
    )
    return router.complete(prompt, system=SAAS_SYSTEM, max_tokens=1200)


def scaffold_mvp(idea: SaaSIdea, output_dir: Path) -> dict[str, str]:
    """Write a minimal FastAPI + SQLite MVP skeleton.

    The scaffold is intentionally tiny: 1 endpoint, 1 table, 1 Dockerfile.
    Real product work happens later; this is enough to deploy and test
    pricing/signup flow.
    """
    root = output_dir / "saas" / _slug(idea.name)
    root.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {}

    files["README.md"] = f"# {idea.name}\n\n{idea.one_liner}\n\n## Run\n\n```\npip install -r requirements.txt\nuvicorn app:app --reload\n```\n"

    files["requirements.txt"] = "fastapi==0.115.0\nuvicorn[standard]==0.32.0\n"

    files["app.py"] = (
        "from fastapi import FastAPI\n"
        "from pydantic import BaseModel\n\n"
        "app = FastAPI(title=\"" + idea.name + "\")\n\n"
        "@app.get('/')\n"
        "def root():\n"
        "    return {'name': '" + idea.name + "', 'tagline': \"" + idea.one_liner.replace('"', '\\"') + "\"}\n\n"
        "class Signup(BaseModel):\n"
        "    email: str\n\n"
        "@app.post('/signup')\n"
        "def signup(s: Signup):\n"
        "    # TODO: charge via Stripe, persist to DB\n"
        "    return {'ok': True, 'email': s.email}\n"
    )

    files["Dockerfile"] = (
        "FROM python:3.12-slim\n"
        "WORKDIR /app\n"
        "COPY requirements.txt .\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n"
        "COPY . .\n"
        "EXPOSE 8000\n"
        'CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]\n'
    )

    files["pricing.md"] = (
        f"# {idea.name} — Pricing\n\n"
        f"- **Free**: 1 project, 100 events/mo\n"
        f"- **Pro (${idea.price_usd}/mo)**: unlimited projects, 10k events/mo\n"
        f"- **Team ($99/mo)**: 5 seats, SSO, priority support\n"
    )

    for name, body in files.items():
        write_file(root, name, body)

    return {k: str(root / k) for k in files}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "saas"


def run(niche: str, router: LLMRouter, ledger: Ledger,
        output_dir: Path, top: int = 1, record_projected: bool = True) -> dict:
    try:
        ideas = discover_ideas(niche, router, n=3)
    except Exception as e:
        print(f"  [saas] discover_ideas failed: {e}")
        return {"stream": "saas", "niche": niche, "ideas": 0, "built": [],
                "error": str(e)}
    # Pick the top by expected month-1 revenue
    ideas.sort(key=lambda i: i.expected_month1_usd, reverse=True)
    chosen = ideas[:top]

    built: list[dict] = []
    for idea in chosen:
        try:
            copy = write_landing_copy(idea, router)
            write_file(output_dir / "saas" / _slug(idea.name), "landing.md", copy)
            paths = scaffold_mvp(idea, output_dir)
        except Exception as e:
            print(f"  [saas] build failed for {idea.name}: {e}")
            continue
        if record_projected:
            ledger.record(
                stream="saas",
                amount_usd=round(idea.expected_month1_usd, 2),
                units=10,  # assumed 10 paying customers in month 1
                source=str(output_dir / "saas" / _slug(idea.name)),
                note=f"projected month-1 — {idea.name} @ ${idea.price_usd}/mo",
            )
        built.append({
            "name": idea.name,
            "expected_month1_usd": round(idea.expected_month1_usd, 2),
            "files": list(paths.keys()),
        })

    return {
        "stream": "saas",
        "niche": niche,
        "ideas": len(ideas),
        "built": built,
    }
