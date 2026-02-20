"""
SCB AML Platform — Lucid Search FastAPI Application
REST API for AML analysts, compliance officers, and regulators.

Endpoints:
  GET  /search?q=Mohammed&countries=SG,HK&risk_band=HIGH
  GET  /entity/{entity_id}
  GET  /entity/{entity_id}/network
  GET  /entity/{entity_id}/transactions
  GET  /health
  GET  /stats

Run: uvicorn scb_aml_platform.lucid_search.api.app:app --host 0.0.0.0 --port 8000
     OR: python app.py
"""

import sys
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import (
    API_HOST, API_PORT, API_TITLE, API_VERSION, COUNTRIES
)
from scb_aml_platform.lucid_search.api.search_engine import LucidSearchEngine

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "Lucid Search — SCB AML High-Risk Entity Identification\n\n"
        "Covers 15 countries: SG, HK, MY, TH, IN, KR, TW, UK, US, AE, KE, NG, PK, BD, CN\n"
        "Built by: Prem Vishnoi, Big Data Consultant, Standard Chartered Bank 2016-2018"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton search engine
_engine: Optional[LucidSearchEngine] = None


def get_engine() -> LucidSearchEngine:
    global _engine
    if _engine is None:
        _engine = LucidSearchEngine()
    return _engine


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    """Health check for monitoring."""
    engine = get_engine()
    return {
        "status": "healthy",
        "backend": "elasticsearch" if engine._es else "in_memory",
        "entities_loaded": len(engine.entities),
        "version": API_VERSION,
    }


@app.get("/stats")
def stats():
    """Platform statistics."""
    engine = get_engine()
    df = engine.entities
    if df.empty:
        return {"error": "No data loaded"}

    stats_data = {
        "total_entities": len(df),
        "countries_covered": COUNTRIES,
        "high_risk_count": int((df.get("risk_band", df.get("risk_rating", "")).eq("HIGH")).sum())
            if "risk_band" in df.columns else
            int((df.get("risk_rating", "").eq("high")).sum()),
        "pep_count": int((df.get("pep_flag", "") == "Y").sum()),
        "screening_alerts": len(engine.screening),
        "relationship_edges": len(engine.relationships),
    }
    return stats_data


@app.get("/search")
def search(
    q: str = Query(..., description="Entity name to search", min_length=2),
    countries: Optional[str] = Query(None, description="Comma-separated ISO country codes, e.g. SG,HK"),
    risk_band: Optional[str] = Query(None, description="LOW | MEDIUM | HIGH | CRITICAL"),
    pep_only: bool = Query(False, description="Return PEP entities only"),
    max_results: int = Query(20, ge=1, le=100),
    mode: str = Query("all", description="fuzzy | phonetic | exact | all"),
):
    """
    Search for entities by name across all 15 countries.

    Examples:
      /search?q=Mohammed+Al-Rahman
      /search?q=Mohammed&countries=SG,HK,AE&risk_band=HIGH
      /search?q=Dragon+Trading&pep_only=false
    """
    country_list = [c.strip().upper() for c in countries.split(",")] \
        if countries else None

    engine = get_engine()
    result = engine.search(
        query=q,
        countries=country_list,
        risk_band=risk_band,
        pep_only=pep_only,
        max_results=max_results,
        search_mode=mode,
    )
    return JSONResponse(content=result)


@app.get("/entity/{entity_id}")
def get_entity(entity_id: str):
    """
    Full entity profile:
      - Entity master (name, risk score, PEP, KYC)
      - Transaction summary (volume, count, cross-border)
      - Sanctions/PEP screening results
      - Related entities network
    """
    engine = get_engine()
    profile = engine.get_entity_profile(entity_id)

    if not profile.get("entity"):
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    return JSONResponse(content=profile)


@app.get("/entity/{entity_id}/network")
def get_entity_network(entity_id: str, depth: int = Query(1, ge=1, le=3)):
    """
    Entity relationship network graph for investigation.
    Returns nodes and edges for network visualization.
    """
    engine = get_engine()
    rels = engine._get_relationships(entity_id)

    nodes = {entity_id: {"id": entity_id, "is_root": True}}
    edges = []

    for rel in rels:
        src = rel.get("entity_id", "")
        tgt = rel.get("related_entity_id", "")
        rel_type = rel.get("relationship_type", "")
        strength = rel.get("link_strength", 0.5)

        if src not in nodes:
            nodes[src] = {"id": src, "is_root": False}
        if tgt not in nodes:
            nodes[tgt] = {"id": tgt, "is_root": False}

        edges.append({
            "source": src,
            "target": tgt,
            "type": rel_type,
            "strength": strength,
        })

    return {
        "entity_id": entity_id,
        "nodes": list(nodes.values()),
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


@app.get("/entity/{entity_id}/transactions")
def get_entity_transactions(entity_id: str):
    """Aggregated transaction history for an entity."""
    engine = get_engine()
    txn = engine._get_txn_summary(entity_id)
    if not txn:
        return {"entity_id": entity_id, "transactions": {}, "message": "No transaction data"}
    return {"entity_id": entity_id, "transactions": txn}


@app.get("/screening/{entity_id}")
def get_screening_results(entity_id: str):
    """Sanctions and PEP screening results for an entity."""
    engine = get_engine()
    results = engine._get_screening(entity_id)
    return {
        "entity_id": entity_id,
        "screening_count": len(results),
        "results": results,
    }


# ─────────────────────────────────────────────
# DEMO USE CASES
# ─────────────────────────────────────────────
@app.get("/demo/use-case-1")
def demo_use_case_1():
    """
    Use Case 1: Cross-border money laundering.
    Analyst searches 'Mohammed Al-Rahman' — finds name variants across SG, HK, AE.
    """
    engine = get_engine()
    result = engine.search(
        query="Mohammed Al-Rahman",
        countries=None,
        risk_band=None,
        max_results=10,
    )
    result["use_case"] = "Cross-Border Money Laundering Detection"
    result["description"] = (
        "Analyst searches 'Mohammed Al-Rahman'. "
        "Lucid Search finds all name variants across 15 countries. "
        "Results include risk scores, PEP flag, and cross-border wire totals."
    )
    return JSONResponse(content=result)


@app.get("/demo/use-case-2")
def demo_use_case_2():
    """
    Use Case 2: Trade-based money laundering.
    RM searches 'Dragon Trading' — finds related shell companies.
    """
    engine = get_engine()
    result = engine.search(
        query="Dragon Trading",
        countries=None,
        max_results=10,
    )
    result["use_case"] = "Trade-Based Money Laundering — Pre-onboarding CDD"
    result["description"] = (
        "Relationship Manager searches 'Dragon Trading Ltd'. "
        "Finds linked entities with circular fund flows. "
        "Risk score HIGH — onboarding rejected."
    )
    return JSONResponse(content=result)


# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Lucid Search API on {API_HOST}:{API_PORT}")
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True)
