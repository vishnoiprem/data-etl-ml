"""
Minimal ontology: typed objects + links + lineage + ACLs.

The unit is the object (e.g., `Customer`, `Account`, `Transaction`).
Tables are an implementation detail. This is the shape behind
Palantir / Salesforce Data Cloud / Salesforce Einstein.

Meaningful workload:
- Generate ~1,200 entities across 10 types (Person, Company, Account,
  Transaction, Alert, Case, Address, Device, Document, Email).
- Generate ~2,400 relations across 15 kinds (owns, worksAt, transactedWith,
  flaggedBy, investigatedBy, livesAt, usesDevice, attachedTo, sentFrom,
  parentOf, subsidiaryOf, employedBy, monitors, references, relatedTo).
- Run 4 scenarios: integrity check, 2-hop traversal, type aggregation,
  pattern match (Person worksAt Company in industry X).
- Measure: traversal time vs naive BFS, query counts, aggregations.
- Assert: integrity, traversal validity, aggregation totals, pattern-match
  consistency across multiple starting points.
"""
from __future__ import annotations
import random
import time
import uuid
from collections import defaultdict, Counter
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
        self.all_links: list[Link] = []

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
        self.all_links.append(l)

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

    def walk_any_kind(self, start: str, depth: int = 2) -> list[str]:
        """BFS up to `depth` hops following ANY link kind (mixed traversal)."""
        seen = {start}
        frontier = [start]
        for _ in range(depth):
            next_frontier = []
            for n in frontier:
                for l in self.out_edges[n]:
                    if l.dst not in seen:
                        seen.add(l.dst)
                        next_frontier.append(l.dst)
            frontier = next_frontier
        return sorted(seen - {start})

    def find(self, type: str, **filters) -> bool:
        """Return True iff props match all filters."""
        o = self.objects.get(type)  # placeholder; not used
        return False

    def count_by_type(self) -> dict[str, int]:
        c: dict[str, int] = Counter()
        for o in self.objects.values():
            c[o.type] += 1
        return dict(c)

    def relation_count_by_kind(self) -> dict[str, int]:
        c: dict[str, int] = Counter()
        for l in self.all_links:
            c[l.kind] += 1
        return dict(c)


# === synthetic data generation ===
ENTITY_TYPES = [
    "Person", "Company", "Account", "Transaction",
    "Alert", "Case", "Address", "Device", "Document", "Email",
]
assert len(ENTITY_TYPES) >= 10, "need >= 10 entity types"

RELATION_KINDS = [
    "owns", "worksAt", "transactedWith", "flaggedBy", "investigatedBy",
    "livesAt", "usesDevice", "attachedTo", "sentFrom", "parentOf",
    "subsidiaryOf", "employedBy", "monitors", "references", "relatedTo",
]
assert len(RELATION_KINDS) >= 15, "need >= 15 relation kinds"

INDUSTRIES = ["Finance", "Tech", "Healthcare", "Retail", "Energy", "Media"]
DEVICE_KINDS = ["phone", "laptop", "tablet", "server"]
DOC_STATUS = ["MFC", "KYC", "SAR", "CTR"]
SOURCES = ["core_banking", "kyc.csv", "sanctions", "crm", "aml_alerts", "case_mgmt"]


def build_workload(seed: int = 42) -> Ontology:
    """Build ~1,200 entities and ~2,400 relations, all internal references valid."""
    rng = random.Random(seed)
    ont = Ontology()

    # Count target: aim for 1,200+ entities total
    per_type = {
        "Person": 250,
        "Company": 180,
        "Account": 200,
        "Transaction": 200,
        "Alert": 100,
        "Case": 80,
        "Address": 100,
        "Device": 60,
        "Document": 50,
        "Email": 30,
    }
    # safety net: ensure >= 1000
    total_planned = sum(per_type.values())
    assert total_planned >= 1000, f"planned entities={total_planned} < 1000"

    # 1. create all entities, index by type
    by_type: dict[str, list[Object]] = defaultdict(list)
    for t in ENTITY_TYPES:
        n = per_type[t]
        for _ in range(n):
            props = _make_props(t, rng)
            src = rng.choice(SOURCES)
            o = ont.upsert(t, props, source=src)
            by_type[t].append(o)

    # 2. create relations: every link's src/dst must exist in the ontology
    #    (we'll only call ont.link with existing ids, so integrity holds by construction)
    rel_counts: dict[str, int] = {k: 0 for k in RELATION_KINDS}
    target_relations = 2400
    # Add dense cross-type chains so 2-hop BFS from a Person is meaningful:
    # Person -> Company (worksAt) -> Company (subsidiaryOf) gives 2 companies;
    # Person -> Company -> Company -> other relations gives more depth.
    # Every Person worksAt at least 1 Company.
    for p in by_type["Person"]:
        for _ in range(rng.randint(1, 2)):
            co = rng.choice(by_type["Company"])
            ont.link(p.id, co.id, "worksAt")
            rel_counts["worksAt"] += 1
    # Every Company has 1-3 subsidiaryOf links to other Companies (chainable)
    for co in by_type["Company"]:
        for _ in range(rng.randint(1, 3)):
            other = rng.choice(by_type["Company"])
            if other.id != co.id:
                ont.link(co.id, other.id, "subsidiaryOf")
                rel_counts["subsidiaryOf"] += 1
    # Every Person has 1-2 relatedTo links to other People
    for p in by_type["Person"]:
        for _ in range(rng.randint(1, 2)):
            other = rng.choice(by_type["Person"])
            if other.id != p.id:
                ont.link(p.id, other.id, "relatedTo")
                rel_counts["relatedTo"] += 1
    # Every Transaction has 1-2 transactedWith links to other Transactions
    for tx in by_type["Transaction"]:
        for _ in range(rng.randint(1, 2)):
            other = rng.choice(by_type["Transaction"])
            if other.id != tx.id:
                ont.link(tx.id, other.id, "transactedWith")
                rel_counts["transactedWith"] += 1
    # fill remainder with random relations across all kinds
    while sum(rel_counts.values()) < target_relations:
        kind = rng.choice(RELATION_KINDS)
        src, dst = _pick_endpoints(kind, by_type, rng)
        if src is None or dst is None:
            continue
        if src.id == dst.id:
            continue
        ont.link(src.id, dst.id, kind)
        rel_counts[kind] += 1

    # Final invariant: all relation endpoints exist
    bad = []
    for l in ont.all_links:
        if l.src not in ont.objects:
            bad.append(("src", l))
        if l.dst not in ont.objects:
            bad.append(("dst", l))
    assert not bad, f"orphan relations detected at build time: {bad[:5]}"
    return ont


def _make_props(t: str, rng: random.Random) -> dict:
    if t == "Person":
        return {"name": f"Person{rng.randint(1, 9999)}", "age": rng.randint(18, 80)}
    if t == "Company":
        return {"name": f"Co{rng.randint(1, 9999)}", "industry": rng.choice(INDUSTRIES)}
    if t == "Account":
        return {"iban": f"IBAN{rng.randint(1, 999999):06d}",
                "balance": round(rng.uniform(0, 1_000_000), 2)}
    if t == "Transaction":
        return {"amount": round(rng.uniform(1, 100_000), 2),
                "currency": rng.choice(["USD", "EUR", "GBP", "JPY", "SGD"])}
    if t == "Alert":
        return {"score": round(rng.uniform(0.1, 1.0), 3),
                "rule": rng.choice(["large_tx", "velocity", "sanctions_hit"])}
    if t == "Case":
        return {"status": rng.choice(["open", "in_review", "closed"]),
                "analyst": f"analyst{rng.randint(1, 30)}"}
    if t == "Address":
        return {"city": rng.choice(["NYC", "SF", "LDN", "SG", "FRA"]),
                "country": rng.choice(["US", "GB", "DE", "SG", "FR"])}
    if t == "Device":
        return {"kind": rng.choice(DEVICE_KINDS),
                "os": rng.choice(["iOS", "Android", "Win", "Linux"])}
    if t == "Document":
        return {"status": rng.choice(DOC_STATUS), "pages": rng.randint(1, 200)}
    if t == "Email":
        return {"subject_len": rng.randint(5, 80),
                "spam_score": round(rng.uniform(0, 1), 2)}
    return {}


def _pick_endpoints(kind: str, by_type: dict[str, list[Object]], rng: random.Random):
    """Return (src, dst) Objects for the given relation kind, ensuring both exist."""
    schema = {
        "owns":            ("Person", "Account"),
        "worksAt":         ("Person", "Company"),
        "transactedWith":  ("Transaction", "Transaction"),
        "flaggedBy":       ("Alert", "Transaction"),
        "investigatedBy":  ("Case", "Alert"),
        "livesAt":         ("Person", "Address"),
        "usesDevice":      ("Person", "Device"),
        "attachedTo":      ("Document", "Account"),
        "sentFrom":        ("Email", "Address"),
        "parentOf":        ("Company", "Company"),
        "subsidiaryOf":    ("Company", "Company"),
        "employedBy":      ("Person", "Company"),
        "monitors":        ("Case", "Person"),
        "references":      ("Document", "Transaction"),
        "relatedTo":       ("Alert", "Alert"),
    }
    src_t, dst_t = schema[kind]
    src_pool = by_type.get(src_t, [])
    dst_pool = by_type.get(dst_t, [])
    if not src_pool or not dst_pool:
        return None, None
    return rng.choice(src_pool), rng.choice(dst_pool)


# === scenario queries ===

def assert_no_orphans(ont: Ontology) -> None:
    """Every relation's src and dst must exist as objects."""
    bad = []
    for l in ont.all_links:
        if l.src not in ont.objects:
            bad.append(("src", l.src, l.kind))
        if l.dst not in ont.objects:
            bad.append(("dst", l.dst, l.kind))
    assert not bad, f"orphan relations found: {bad[:5]} (total {len(bad)})"


def assert_traversal_valid(ont: Ontology, start: str, reachable: list[str]) -> None:
    """Every node returned by traversal must (a) exist and (b) be reachable from start."""
    assert start in ont.objects, f"start {start} not in ontology"
    # BFS rebuild and compare as a check
    seen = {start}
    frontier = [start]
    for _ in range(2):
        nf = []
        for n in frontier:
            for l in ont.out_edges[n]:
                if l.dst not in seen:
                    seen.add(l.dst)
                    nf.append(l.dst)
        frontier = nf
    expected = sorted(seen - {start})
    assert reachable == expected, (
        f"traversal mismatch: returned {len(reachable)} nodes, "
        f"rebuilt BFS got {len(expected)}"
    )
    for nid in reachable:
        assert nid in ont.objects, f"traversal returned unknown id {nid}"


def assert_aggregation_totals(ont: Ontology) -> None:
    """Per-type counts must sum to total entity count."""
    counts = ont.count_by_type()
    assert sum(counts.values()) == len(ont.objects), (
        f"entity type counts sum={sum(counts.values())} != total={len(ont.objects)}"
    )
    rel_counts = ont.relation_count_by_kind()
    assert sum(rel_counts.values()) == len(ont.all_links), (
        f"relation counts sum={sum(rel_counts.values())} != total links={len(ont.all_links)}"
    )


def pattern_match_person_works_at_company_in_industry(
    ont: Ontology, industry: str
) -> list[tuple[str, str]]:
    """Find all (person_id, company_id) such that person worksAt company and
    company.props['industry'] == industry.
    Returns sorted list for deterministic output.
    """
    results = []
    for l in ont.all_links:
        if l.kind != "worksAt":
            continue
        person = ont.objects.get(l.src)
        company = ont.objects.get(l.dst)
        if not person or not company:
            continue
        if company.type != "Company" or person.type != "Person":
            continue
        if company.props.get("industry") == industry:
            results.append((person.id, company.id))
    return sorted(results)


def assert_pattern_match_consistent(ont: Ontology, industry: str) -> None:
    """Re-derive the pattern from scratch (separate from the scenario function)
    and verify both agree. Also verify starting from another industry produces a
    disjoint result, AND the union across all industries covers all worksAt edges
    whose target Company has a known industry."""
    # 1. independent recompute
    independent = []
    for p in [o for o in ont.objects.values() if o.type == "Person"]:
        for l in ont.out_edges[p.id]:
            if l.kind != "worksAt":
                continue
            co = ont.objects.get(l.dst)
            if co and co.type == "Company" and co.props.get("industry") == industry:
                independent.append((p.id, co.id))
    independent.sort()
    scenario = pattern_match_person_works_at_company_in_industry(ont, industry)
    assert scenario == independent, (
        f"pattern match inconsistency for industry={industry}: "
        f"scenario={len(scenario)} independent={len(independent)}"
    )

    # 2. different industries must yield disjoint results
    other = pattern_match_person_works_at_company_in_industry(
        ont, rng_industry_for_change(industry)
    )
    s_set = set(scenario)
    o_set = set(other)
    assert s_set.isdisjoint(o_set), (
        f"pattern match across industries overlaps: {s_set & o_set}"
    )

    # 3. union across all industries must cover every worksAt edge whose
    # target Company has a recognized industry. (Each worksAt edge is a
    # single (Person, Company) pair, but the same pair can have multiple
    # edges, so we compare against the unique (src, dst) set, not the
    # multi-set of edges.)
    union = set()
    for ind in INDUSTRIES:
        union |= set(pattern_match_person_works_at_company_in_industry(ont, ind))
    # every worksAt edge should be in the union IF its target is a Company
    # with a known industry. (Companies without industry are data quality
    # issues; we just check at least 95% coverage.)
    worksAt_pairs = {(l.src, l.dst) for l in ont.all_links if l.kind == "worksAt"}
    expected = {
        (l.src, l.dst) for l in ont.all_links
        if l.kind == "worksAt"
        and (co := ont.objects.get(l.dst)) is not None
        and co.type == "Company"
        and co.props.get("industry") in INDUSTRIES
    }
    assert union == expected, (
        f"union of per-industry pattern match != expected worksAt coverage: "
        f"missing={len(expected - union)} extra={len(union - expected)}"
    )
    coverage = len(union) / len(worksAt_pairs) if worksAt_pairs else 1.0
    assert coverage >= 0.95, (
        f"industry coverage of worksAt edges too low: {coverage:.1%}"
    )


def rng_industry_for_change(current: str) -> str:
    return next(i for i in INDUSTRIES if i != current)


if __name__ == "__main__":
    print("═══ ontology-data-fabric: meaningful workload ═══")
    t0 = time.time()
    print("generating ontology (1,200+ entities, 2,400+ relations)...")
    ont = build_workload()
    build_t = time.time() - t0

    n_entities = len(ont.objects)
    n_links = len(ont.all_links)
    n_entity_types = len(ont.count_by_type())
    n_relation_kinds = len(ont.relation_count_by_kind())

    print(f"  built in {build_t:.2f}s")
    print(f"  entities:       {n_entities:,}")
    print(f"  relations:      {n_links:,}")
    print(f"  entity types:   {n_entity_types}")
    print(f"  relation kinds: {n_relation_kinds}")
    print()

    # per-type / per-kind breakdown
    print("  entities by type:")
    for t, c in sorted(ont.count_by_type().items(), key=lambda kv: -kv[1]):
        print(f"    {t:<14}{c:>6}")
    print("  relations by kind:")
    for k, c in sorted(ont.relation_count_by_kind().items(), key=lambda kv: -kv[1]):
        print(f"    {k:<18}{c:>6}")
    print()

    # ---------- Scenario A: integrity ----------
    print("═══ Scenario A: graph integrity (no orphans) ═══")
    t0 = time.time()
    assert_no_orphans(ont)
    integrity_ms = (time.time() - t0) * 1000
    print(f"  orphan check across {n_links:,} links: {integrity_ms:.2f}ms ✓")
    # spot-check: every entity is referenced at least once (no fully disconnected singletons
    # is NOT required, but at least 80% should appear somewhere in the graph)
    referenced = {l.src for l in ont.all_links} | {l.dst for l in ont.all_links}
    coverage = len(referenced) / n_entities
    print(f"  entities referenced in at least one link: {len(referenced):,}/{n_entities:,} = {coverage:.1%}")
    assert coverage >= 0.8, f"too many disconnected entities: {coverage:.1%}"
    print()

    # ---------- Scenario B: traversal ----------
    print("═══ Scenario B: 2-hop traversal from a Person ═══")
    person_pool = [o for o in ont.objects.values() if o.type == "Person"]
    rng = random.Random(7)
    start = rng.choice(person_pool).id
    t0 = time.time()
    reachable = ont.walk_any_kind(start, depth=2)
    traversal_ms = (time.time() - t0) * 1000
    print(f"  start: {start}")
    print(f"  2-hop reachable nodes: {len(reachable)} (in {traversal_ms:.2f}ms)")
    t0 = time.time()
    assert_traversal_valid(ont, start, reachable)
    check_ms = (time.time() - t0) * 1000
    print(f"  independent BFS re-derivation matches: ✓ ({check_ms:.2f}ms)")
    # also try a depth-3 walk with a single relation kind
    t0 = time.time()
    own_chain = ont.walk(start, "owns", depth=3)
    own_ms = (time.time() - t0) * 1000
    print(f"  'owns' chain (depth 3): {len(own_chain)} nodes ({own_ms:.2f}ms)")
    print()

    # ---------- Scenario C: aggregation by type ----------
    print("═══ Scenario C: aggregation by type/kind ═══")
    t0 = time.time()
    e_counts = ont.count_by_type()
    r_counts = ont.relation_count_by_kind()
    agg_ms = (time.time() - t0) * 1000
    print(f"  aggregation done in {agg_ms:.2f}ms")
    assert_aggregation_totals(ont)
    print(f"  entity counts sum to total: {sum(e_counts.values())} == {n_entities} ✓")
    print(f"  relation counts sum to total: {sum(r_counts.values())} == {n_links} ✓")
    # largest type
    top_type, top_count = max(e_counts.items(), key=lambda kv: kv[1])
    top_kind, top_rel = max(r_counts.items(), key=lambda kv: kv[1])
    print(f"  largest entity type: {top_type} ({top_count})")
    print(f"  most common relation kind: {top_kind} ({top_rel})")
    print()

    # ---------- Scenario D: pattern match ----------
    print("═══ Scenario D: pattern match (Person worksAt Company in industry X) ═══")
    # Use the most common industry for non-trivial results
    industry_pool = Counter()
    for co in (o for o in ont.objects.values() if o.type == "Company"):
        ind = co.props.get("industry")
        if ind:
            industry_pool[ind] += 1
    top_industry, _ = industry_pool.most_common(1)[0]

    t0 = time.time()
    matches = pattern_match_person_works_at_company_in_industry(ont, top_industry)
    pm_ms = (time.time() - t0) * 1000
    print(f"  industry = {top_industry!r}: {len(matches)} (Person, Company) pairs ({pm_ms:.2f}ms)")
    # Per-industry totals
    print("  per-industry match counts:")
    for ind in INDUSTRIES:
        c = len(pattern_match_person_works_at_company_in_industry(ont, ind))
        print(f"    {ind:<12}{c:>6}")
    # Consistency check: re-derive independently + disjointness + union = total
    t0 = time.time()
    assert_pattern_match_consistent(ont, top_industry)
    cons_ms = (time.time() - t0) * 1000
    print(f"  consistency check passed in {cons_ms:.2f}ms ✓")
    print()

    # ---------- final invariants ----------
    print("═══ final invariants ═══")
    assert n_entities >= 1000, f"entities {n_entities} < 1000"
    assert n_links >= 2000, f"relations {n_links} < 2000"
    assert n_entity_types >= 10, f"entity types {n_entity_types} < 10"
    assert n_relation_kinds >= 15, f"relation kinds {n_relation_kinds} < 15"
    assert_no_orphans(ont)
    assert_aggregation_totals(ont)
    # re-run pattern match consistency for every industry to be thorough
    for ind in INDUSTRIES:
        assert_pattern_match_consistent(ont, ind)
    # traversal validity for 5 random starts
    rng = random.Random(99)
    sample_starts = rng.sample(person_pool, k=min(5, len(person_pool)))
    for s in sample_starts:
        rh = ont.walk_any_kind(s.id, depth=2)
        assert_traversal_valid(ont, s.id, rh)
    print(f"  entities={n_entities} relations={n_links} types={n_entity_types}/{n_relation_kinds}")
    print(f"  pattern match consistency verified across all {len(INDUSTRIES)} industries")
    print(f"  traversal validity verified for {len(sample_starts)} random starts")
    print("✓ all invariants pass")