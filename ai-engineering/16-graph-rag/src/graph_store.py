"""Knowledge graph store — NetworkX in-memory, SQLite-mirrored for persistence.

The class boundary is the seam where Neptune / Neo4j would later plug in.
See ARCHITECTURE.md ADR-001.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import networkx as nx


@dataclass
class Triple:
    head: str
    head_type: str
    rel: str
    tail: str
    tail_type: str

    @classmethod
    def from_dict(cls, d: dict) -> "Triple":
        return cls(
            head=d["head"].strip(),
            head_type=d.get("head_type", "Thing"),
            rel=d["rel"].strip().upper().replace(" ", "_"),
            tail=d["tail"].strip(),
            tail_type=d.get("tail_type", "Thing"),
        )


class GraphStore:
    """Directed, labelled multigraph. Persisted to SQLite.

    Schema in SQLite:
        nodes(id PRIMARY KEY, type, props_json)
        edges(src, dst, rel, props_json)  -- composite key
    """

    def __init__(self) -> None:
        self._g: nx.MultiDiGraph = nx.MultiDiGraph()

    # ---- mutation ------------------------------------------------------

    def add_node(self, node_id: str, type: str = "Thing", props: dict | None = None) -> None:
        if not self._g.has_node(node_id):
            self._g.add_node(node_id, type=type, props=props or {})

    def add_edge(self, src: str, dst: str, rel: str, src_type: str = "Thing", dst_type: str = "Thing") -> None:
        self.add_node(src, type=src_type)
        self.add_node(dst, type=dst_type)
        self._g.add_edge(src, dst, key=rel, rel=rel)

    def add_triple(self, t: Triple) -> None:
        self.add_edge(t.head, t.tail, t.rel, src_type=t.head_type, dst_type=t.tail_type)

    def add_triples(self, triples: Iterable[Triple]) -> None:
        for t in triples:
            self.add_triple(t)

    # ---- query ---------------------------------------------------------

    def has_node(self, node_id: str) -> bool:
        return self._g.has_node(node_id)

    def neighbors(self, node_id: str, depth: int = 1) -> list[tuple[str, str, str]]:
        """Return (src, rel, dst) edges within `depth` hops of `node_id`, BFS."""
        if not self._g.has_node(node_id):
            return []
        seen_edges: set[tuple[str, str, str]] = set()
        frontier = {node_id}
        visited: set[str] = {node_id}
        out: list[tuple[str, str, str]] = []
        for _ in range(depth):
            next_frontier: set[str] = set()
            for n in frontier:
                for _, dst, k, data in self._g.out_edges(n, keys=True, data=True):
                    rel = data.get("rel", k)
                    edge = (n, rel, dst)
                    if edge not in seen_edges:
                        seen_edges.add(edge)
                        out.append(edge)
                    if dst not in visited:
                        visited.add(dst)
                        next_frontier.add(dst)
                for src, _, k, data in self._g.in_edges(n, keys=True, data=True):
                    rel = data.get("rel", k)
                    edge = (src, rel, n)
                    if edge not in seen_edges:
                        seen_edges.add(edge)
                        out.append(edge)
                    if src not in visited:
                        visited.add(src)
                        next_frontier.add(src)
            frontier = next_frontier
            if not frontier:
                break
        return out

    def subgraph_edges(self, seed_ids: list[str], depth: int = 1) -> list[tuple[str, str, str]]:
        seen: set[tuple[str, str, str]] = set()
        for seed in seed_ids:
            for edge in self.neighbors(seed, depth=depth):
                seen.add(edge)
        return list(seen)

    def nodes(self) -> list[str]:
        return list(self._g.nodes)

    def edges(self) -> list[tuple[str, str, str]]:
        return [(u, d.get("rel", k), v) for u, v, k, d in self._g.edges(keys=True, data=True)]

    def __len__(self) -> int:
        return self._g.number_of_nodes()

    # ---- entity linking (cheap) ---------------------------------------

    def link_query(self, query: str) -> list[str]:
        """Return seed node IDs whose label appears in `query` (case-insensitive).

        Cheap-but-effective entity linker for the demo.  In production this is
        a real NER step (Comprehend, GLiNER, etc.).
        """
        q = query.lower()
        seeds: list[str] = []
        for node in self._g.nodes:
            label = node.lower()
            if label and label in q:
                seeds.append(node)
        return seeds

    # ---- persist -------------------------------------------------------

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()
        con = sqlite3.connect(str(path))
        try:
            con.executescript(
                """
                CREATE TABLE nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    props_json TEXT
                );
                CREATE TABLE edges (
                    src TEXT,
                    dst TEXT,
                    rel TEXT,
                    props_json TEXT,
                    PRIMARY KEY (src, dst, rel)
                );
                """
            )
            for n, data in self._g.nodes(data=True):
                con.execute(
                    "INSERT OR REPLACE INTO nodes(id, type, props_json) VALUES (?, ?, ?)",
                    (n, data.get("type", "Thing"), json.dumps(data.get("props", {}))),
                )
            for u, v, k, data in self._g.edges(keys=True, data=True):
                con.execute(
                    "INSERT OR REPLACE INTO edges(src, dst, rel, props_json) VALUES (?, ?, ?, ?)",
                    (u, v, data.get("rel", k), json.dumps({})),
                )
            con.commit()
        finally:
            con.close()

    def load(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(path)
        con = sqlite3.connect(str(path))
        try:
            self._g = nx.MultiDiGraph()
            for row in con.execute("SELECT id, type, props_json FROM nodes"):
                node_id, ntype, props_json = row
                props = json.loads(props_json) if props_json else {}
                self._g.add_node(node_id, type=ntype, props=props)
            for row in con.execute("SELECT src, dst, rel FROM edges"):
                src, dst, rel = row
                if self._g.has_node(src) and self._g.has_node(dst):
                    self._g.add_edge(src, dst, key=rel, rel=rel)
        finally:
            con.close()
