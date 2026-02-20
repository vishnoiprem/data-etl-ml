"""
SCB AML Platform — Spark Job 1: Entity Resolution
Phase 3, Step 1 of the Spark Transformation Engine.

Purpose: Resolve the same real-world entity appearing across multiple
         countries / banking lines with different name spellings or
         script variations, and assign a single golden_entity_id.

Multi-pass approach:
  Pass 1 — Exact ID match (passport / national ID)
  Pass 2 — Fuzzy name match after transliteration (Jaro-Winkler ≥ 0.85)
  Pass 3 — Phonetic match (Double Metaphone)

Output: entity_master DataFrame with golden_entity_id column
        saved to data/processed/entity_master.parquet

Run: python job1_entity_resolution.py
"""

import sys
import hashlib
from pathlib import Path

import pandas as pd
import jellyfish
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import (
    DUMMY_DIR, JARO_WINKLER_THRESHOLD, BASE_DIR
)

DUMMY_DIR = Path(DUMMY_DIR)
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# TRANSLITERATION (simplified)
# ─────────────────────────────────────────────
ARABIC_LATIN_MAP = {
    "أ": "a", "ب": "b", "ت": "t", "ث": "th", "ج": "j",
    "ح": "h", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r",
    "ز": "z", "س": "s", "ش": "sh", "ص": "s", "ض": "d",
    "ط": "t", "ظ": "z", "ع": "a", "غ": "gh", "ف": "f",
    "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "و": "w", "ي": "y", "ة": "a", "ى": "a",
    "ا": "a", "لا": "la", "ء": "", "ئ": "y", "ؤ": "w",
    "ال": "al-", " ": " ",
}


def transliterate(text: str) -> str:
    """Basic Arabic → Latin transliteration. Real impl uses ICU4J / langdetect."""
    if not isinstance(text, str):
        return ""
    result = text
    for arabic, latin in ARABIC_LATIN_MAP.items():
        result = result.replace(arabic, latin)
    return result.strip()


def normalize_name(name: str) -> str:
    """Uppercase, strip, transliterate."""
    if not isinstance(name, str):
        return ""
    name = transliterate(name)
    return name.upper().strip()


# ─────────────────────────────────────────────
# SCORING FUNCTIONS
# ─────────────────────────────────────────────
def jaro_winkler_score(name1: str, name2: str) -> float:
    n1, n2 = normalize_name(name1), normalize_name(name2)
    if not n1 or not n2:
        return 0.0
    return jellyfish.jaro_winkler_similarity(n1, n2)


def phonetic_match(name1: str, name2: str) -> bool:
    n1, n2 = normalize_name(name1), normalize_name(name2)
    if not n1 or not n2:
        return False
    dm1 = jellyfish.metaphone(n1)
    dm2 = jellyfish.metaphone(n2)
    return dm1 == dm2 and bool(dm1)


def make_golden_id(customer_id: str) -> str:
    """Deterministic golden entity ID from canonical customer_id."""
    h = hashlib.sha256(customer_id.encode()).hexdigest()[:16].upper()
    return f"GEI_{h}"


# ─────────────────────────────────────────────
# PASS 1: EXACT ID MATCH
# ─────────────────────────────────────────────
def pass1_exact_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign the same golden_entity_id to all records sharing an id_number
    (across any country). This handles: same passport, same national ID.
    """
    logger.info("Pass 1: Exact ID match across countries")
    # Ignore 'N/A' or null IDs
    valid = df[df["id_number"].notna() & (df["id_number"] != "None")].copy()

    # Map id_number → earliest customer_id as canonical
    id_canonical = (
        valid.sort_values("country_code")
             .groupby("id_number")["customer_id"]
             .first()
             .to_dict()
    )

    def _golden(row):
        canon = id_canonical.get(row["id_number"])
        return make_golden_id(canon) if canon else make_golden_id(row["customer_id"])

    df["golden_entity_id"] = df.apply(_golden, axis=1)
    logger.info(f"  After Pass 1: {df['golden_entity_id'].nunique():,} unique golden IDs")
    return df


# ─────────────────────────────────────────────
# PASS 2: FUZZY NAME MATCH
# ─────────────────────────────────────────────
def pass2_fuzzy_name(df: pd.DataFrame) -> pd.DataFrame:
    """
    For records that still have unique golden IDs (no ID match),
    group by (nationality, DOB) and apply Jaro-Winkler on the name.
    Threshold: 0.85
    """
    logger.info("Pass 2: Fuzzy name match (Jaro-Winkler ≥ 0.85)")

    # Only attempt within same (nationality, dob) bucket to reduce combinations
    buckets = df.groupby(["nationality", "date_of_birth"])

    merge_map = {}  # golden_id → canonical_golden_id
    match_count = 0

    for (nat, dob), group in buckets:
        if len(group) < 2:
            continue
        rows = group.to_dict("records")
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                score = jaro_winkler_score(a["customer_name"], b["customer_name"])
                if score >= JARO_WINKLER_THRESHOLD:
                    # Merge b → a's golden ID
                    canonical = min(a["golden_entity_id"], b["golden_entity_id"])
                    merge_map[a["golden_entity_id"]] = canonical
                    merge_map[b["golden_entity_id"]] = canonical
                    match_count += 1

    def resolve(gid):
        seen = set()
        while gid in merge_map and gid not in seen:
            seen.add(gid)
            gid = merge_map[gid]
        return gid

    df["golden_entity_id"] = df["golden_entity_id"].apply(resolve)
    logger.info(f"  Pass 2 merged {match_count} pairs → {df['golden_entity_id'].nunique():,} golden IDs")
    return df


# ─────────────────────────────────────────────
# PASS 3: PHONETIC MATCH
# ─────────────────────────────────────────────
def pass3_phonetic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Final pass: phonetic match within nationality bucket.
    Catches 'Chen' / 'Chan', 'Mohammed' / 'Muhammad', etc.
    """
    logger.info("Pass 3: Phonetic match (Double Metaphone)")

    merge_map = {}
    match_count = 0

    # Group by nationality only (DOB may differ due to data quality)
    buckets = df.groupby("nationality")
    for nat, group in buckets:
        if len(group) < 2:
            continue
        rows = group.to_dict("records")
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                if phonetic_match(a["customer_name"], b["customer_name"]):
                    # Additional check: same DOB decade (rough)
                    dob_a = str(a.get("date_of_birth", ""))[:4]
                    dob_b = str(b.get("date_of_birth", ""))[:4]
                    if dob_a and dob_b and abs(int(dob_a) - int(dob_b)) <= 5:
                        canonical = min(a["golden_entity_id"], b["golden_entity_id"])
                        merge_map[a["golden_entity_id"]] = canonical
                        merge_map[b["golden_entity_id"]] = canonical
                        match_count += 1

    def resolve(gid):
        seen = set()
        while gid in merge_map and gid not in seen:
            seen.add(gid)
            gid = merge_map[gid]
        return gid

    df["golden_entity_id"] = df["golden_entity_id"].apply(resolve)
    logger.info(f"  Pass 3 merged {match_count} pairs → {df['golden_entity_id'].nunique():,} golden IDs")
    return df


# ─────────────────────────────────────────────
# BUILD ENTITY MASTER
# ─────────────────────────────────────────────
def build_entity_master(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse all per-country customer records into a single
    entity_master row per golden_entity_id.
    """
    logger.info("Building entity_master table...")

    def agg_variants(names):
        return list(set(str(n) for n in names if isinstance(n, str) and n != "None"))

    master = (
        df.sort_values("risk_rating",
                       key=lambda s: s.map({"high": 0, "medium": 1, "low": 2}).fillna(3))
          .groupby("golden_entity_id")
          .agg(
              entity_id=("customer_id", "first"),
              customer_name=("customer_name", "first"),
              name_local_script=("name_local_script", "first"),
              name_variants=("customer_name", agg_variants),
              date_of_birth=("date_of_birth", "first"),
              nationality=("nationality", "first"),
              id_type=("id_type", "first"),
              id_number=("id_number", "first"),
              risk_score=("risk_rating",
                          lambda s: 80 if (s == "high").any()
                          else 50 if (s == "medium").any() else 20),
              pep_flag=("pep_flag",
                        lambda s: "Y" if (s == "Y").any() else "N"),
              pep_grade=("pep_grade", lambda s: next(
                  (v for v in s if isinstance(v, str) and v not in ("None", "")), None
              )),
              country_codes=("country_code", lambda s: list(s.unique())),
              source_count=("customer_id", "count"),
          )
          .reset_index()
    )

    out = PROCESSED_DIR / "entity_master.parquet"
    master.to_parquet(out, index=False)
    logger.success(f"entity_master: {len(master):,} entities → {out}")
    return master


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run():
    logger.info("=" * 60)
    logger.info("Spark Job 1: Entity Resolution")
    logger.info("=" * 60)

    df = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    logger.info(f"Input: {len(df):,} customer records across {df['country_code'].nunique()} countries")

    df = pass1_exact_id(df)
    df = pass2_fuzzy_name(df)
    df = pass3_phonetic(df)

    master = build_entity_master(df)

    # Save enriched customer table (with golden_entity_id)
    enriched_path = PROCESSED_DIR / "customers_enriched.parquet"
    df.to_parquet(enriched_path, index=False)

    # Stats
    exact_hits = df[df["golden_entity_id"].duplicated(keep=False)]["golden_entity_id"].nunique()
    logger.info(f"\nEntity Resolution Summary:")
    logger.info(f"  Input records   : {len(df):,}")
    logger.info(f"  Unique entities : {master['golden_entity_id'].nunique():,}")
    logger.info(f"  Cross-country links: {exact_hits:,} entities with 2+ records")

    return master


if __name__ == "__main__":
    run()
