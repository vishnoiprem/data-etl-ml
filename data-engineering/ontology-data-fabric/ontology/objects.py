"""
Minimal ontology: typed objects + links + lineage + ACLs.

The unit is the object (e.g., `Customer`, `Account`, `Transaction`).
Tables are an implementation detail. This is the shape behind
Palantir / Salesforce Data Cloud / Salesforce Einstein.
"""
from __future__ import annotations
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Object:
    id: str
    type: str            # "Customer" | "Account" | "Transaction" | ...
    props: dict          # type-specific properties
    created_at: float
    source: str          # where this object came from
    version: int = 1


@dataclass
class Link:
    src: str
    dst: str
    kind: str            # "owns" | "transacted_with" | "employs" | ...
    ts: float


class Ontology:
    def __init__(self):
        self.objects: dict[str, Object] = {}
        self.out_edges: dict[str, list[Link]] = defaultdict(list)
        self.in_edges: dict[str, list[Link]] = defaultdict(list)

    def upsert(self, type: str, props: dict, source: str, obj_id: Optional[str] = None) -> Object:
        if obj_id and obj_id in self.objects:
            o = self.objects[obj_id]
            o.props.update(props)
            o.version += 1
            return o
        oid = obj_id or f"{type.lower()}-{uuid.uuid4().hex[:8]}"
        o = Object(id=oid, type=type, props=props, created_at=time.time(), source=source)
        self.objects[oid] = o
        return o

    def link(self, src: str, dst: str, kind: str):
        l = Link(src=src, dst=dst, kind=kind, ts=time.time())
        self.out_edges[src].append(l)
        self.in_edges[dst].append(l)

    def walk(self, start: str, kind: str, depth: int = 1) -> list[str]:
        """BFS up to `depth` following outgoing links of `kind`."""
        seen = {start}
        frontier = [start]
        for _ in range(depth):
            next_frontier = []
            for n in frontier:
                for l in self.out_edges[n]:
                    if l.kind == kind and l.dst not in seen:
                        seen.add(l.dst)
                        next_frontier.append(l.dst)
            frontier = next_frontier
        return sorted(seen - {start})


if __name__ == "__main__":
    ont = Ontology()
    cust = ont.upsert("Customer", {"name": "Acme Inc"}, source="kyc.csv")
    sub1 = ont.upsert("Account", {"iban": "..."}, source="core_banking")
    sub2 = ont.upsert("Account", {"iban": "..."}, source="core_banking")
    ont.link(cust.id, sub1.id, "owns")
    ont.link(cust.id, sub2.id, "owns")
    print(f"customer {cust.id} owns: {ont.walk(cust.id, 'owns')}")
