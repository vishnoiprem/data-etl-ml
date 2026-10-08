"""Unit tests for the in-memory graph store."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph_store import GraphStore, Triple


def test_add_node_and_edge() -> None:
    g = GraphStore()
    g.add_node("AcmeCorp", type="Organization")
    g.add_edge("AcmeCorp", "PTO", "OFFERS")
    assert g.has_node("AcmeCorp")
    assert g.has_node("PTO")
    edges = g.edges()
    assert ("AcmeCorp", "OFFERS", "PTO") in edges


def test_add_triple() -> None:
    g = GraphStore()
    g.add_triple(Triple("New Hire", "Persona", "ACCRUES", "PTO", "Policy"))
    g.add_triple(Triple("PTO", "Policy", "GRANTS", "20 days", "Quantity"))
    g.add_triple(Triple("New Hire", "Persona", "READS", "Expense Policy", "Document"))
    assert g.has_node("New Hire")
    edges = g.subgraph_edges(["New Hire"], depth=2)
    rels = {r for _, r, _ in edges}
    assert "ACCRUES" in rels
    assert "READS" in rels


def test_neighbors_two_hop() -> None:
    g = GraphStore()
    # Path: A -[R1]-> B -[R2]-> C
    g.add_edge("A", "B", "R1")
    g.add_edge("B", "C", "R2")
    edges = g.subgraph_edges(["A"], depth=2)
    pairs = {(s, t) for s, _, t in edges}
    assert ("A", "B") in pairs
    assert ("B", "C") in pairs
    # Depth 1 should NOT see C
    edges_d1 = g.subgraph_edges(["A"], depth=1)
    pairs_d1 = {(s, t) for s, _, t in edges_d1}
    assert ("B", "C") not in pairs_d1


def test_link_query_finds_seeds() -> None:
    g = GraphStore()
    g.add_edge("AcmeCorp", "PTO", "OFFERS")
    g.add_edge("AcmeCorp", "PagerDuty", "USES")
    seeds = g.link_query("Does AcmeCorp use PagerDuty for on-call?")
    assert "AcmeCorp" in seeds
    assert "PagerDuty" in seeds


def test_persist_round_trip(tmp_path) -> None:
    g = GraphStore()
    g.add_edge("A", "B", "R1")
    g.add_edge("B", "C", "R2")
    path = tmp_path / "g.sqlite"
    g.save(path)
    g2 = GraphStore()
    g2.load(path)
    assert g2.has_node("A")
    edges = g2.edges()
    assert ("A", "R1", "B") in edges
    assert ("B", "R2", "C") in edges
