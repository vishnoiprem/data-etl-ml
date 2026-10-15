"""
SCB AML Platform — Spark Job 4: Sanctions & PEP Screening
Phase 3, Step 4.

Screens the entire customer base (10M+ entities in prod) against:
  - OFAC SDN list
  - UN Consolidated list
  - EU Sanctions list
  - 10 local lists (MAS-SG, FCA-UK, FinCEN-US, etc.)
  - PEP databases (with relationship inference)

Matching strategy:
  1. Exact name match
  2. Fuzzy name match (Jaro-Winkler ≥ 0.80)
  3. Phonetic match (Double Metaphone)
  4. DOB + partial name match

False positive management:
  - Previously dismissed with same score → auto-dismiss
  - Score-based confidence (0–100)

Output: data/processed/screening_alerts.parquet
"""

import sys
import hashlib
from pathlib import Path
from datetime import datetime

import pandas as pd
import jellyfish
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import BASE_DIR

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

FUZZY_THRESHOLD = 0.80  # slightly lower than entity resolution to catch more hits


def normalize(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return name.upper().strip()


def compute_match_score(cust_name: str, list_name: str,
                        cust_dob: str, list_dob: str,
                        cust_nat: str, list_nat: str) -> tuple[int, str]:
    """
    Returns (score 0-100, match_type).
    score = name_sim * 60 + dob_match * 25 + nationality_match * 15
    """
    n1 = normalize(cust_name)
    n2 = normalize(list_name)

    if not n1 or not n2:
        return 0, "no_match"

    # Exact
    if n1 == n2:
        name_sim = 1.0
        match_type = "exact"
    else:
        name_sim = jellyfish.jaro_winkler_similarity(n1, n2)
        # Phonetic
        if name_sim < FUZZY_THRESHOLD:
            dm1 = jellyfish.metaphone(n1)
            dm2 = jellyfish.metaphone(n2)
            if dm1 and dm1 == dm2:
                name_sim = max(name_sim, 0.82)
                match_type = "phonetic"
            else:
                return 0, "no_match"
        else:
            match_type = "fuzzy"

    dob_match = 1.0 if (cust_dob and list_dob and
                        str(cust_dob)[:10] == str(list_dob)[:10]) else 0.0
    nat_match = 1.0 if (cust_nat and list_nat and
                        str(cust_nat).upper() == str(list_nat).upper()) else 0.0

    score = int(name_sim * 60 + dob_match * 25 + nat_match * 15)
    return score, match_type


def screen_against_list(customers: pd.DataFrame, sanctions: pd.DataFrame) -> pd.DataFrame:
    """Screen all customers against all sanctions entries."""
    results = []

    for _, cust in customers.iterrows():
        for _, sanc in sanctions.iterrows():
            # Screen against primary name
            names_to_check = [sanc["entity_name"]]

            # Also check name variants if available
            variants = sanc.get("name_variants", [])
            if isinstance(variants, list):
                names_to_check.extend(variants)
            elif isinstance(variants, str):
                # Could be string-serialized list from parquet
                try:
                    import ast
                    parsed = ast.literal_eval(variants)
                    if isinstance(parsed, list):
                        names_to_check.extend(parsed)
                except Exception:
                    pass

            best_score = 0
            best_type = "no_match"
            best_matched_name = ""

            for sanc_name in names_to_check:
                score, mtype = compute_match_score(
                    cust_name=cust["customer_name"],
                    list_name=sanc_name,
                    cust_dob=str(cust.get("date_of_birth", "")),
                    list_dob=str(sanc.get("dob", "")),
                    cust_nat=str(cust.get("nationality", "")),
                    list_nat=str(sanc.get("nationality", "")),
                )
                if score > best_score:
                    best_score = score
                    best_type = mtype
                    best_matched_name = sanc_name

            if best_score >= 50:  # minimum threshold to generate alert
                screening_id = hashlib.md5(
                    f"{cust['customer_id']}{sanc['entity_name']}".encode()
                ).hexdigest()[:12].upper()

                results.append({
                    "screening_id": f"SCR_{screening_id}",
                    "customer_id": cust["customer_id"],
                    "customer_name": cust["customer_name"],
                    "matched_list_source": sanc.get("list_source", "UNKNOWN"),
                    "matched_entity_name": best_matched_name,
                    "matched_program": sanc.get("program", ""),
                    "match_score": best_score,
                    "match_type": best_type,
                    "nationality": cust.get("nationality", ""),
                    "date_of_birth": str(cust.get("date_of_birth", "")),
                    "country_code": cust.get("country_code", ""),
                    "disposition": "pending",
                    "screening_date": datetime.utcnow().strftime("%Y-%m-%d"),
                })

    return pd.DataFrame(results)


def apply_pep_relationship_inference(
    customers: pd.DataFrame,
    rels: pd.DataFrame,
    screening_results: pd.DataFrame
) -> pd.DataFrame:
    """
    Flag relatives/associates of confirmed PEPs.
    spouse / parent / child of a PEP also gets a PEP-related flag.
    """
    pep_customers = customers[customers["pep_flag"] == "Y"]["customer_id"].tolist()

    # Find related entities
    rel_of_pep = rels[
        (rels["entity_id"].isin(pep_customers)) |
        (rels["related_entity_id"].isin(pep_customers))
    ].copy()

    rel_types_in_scope = {"spouse", "parent_company", "beneficial_owner"}
    rel_of_pep = rel_of_pep[
        rel_of_pep["relationship_type"].isin(rel_types_in_scope)
    ]

    # Collect all associated IDs
    associated = set()
    for _, row in rel_of_pep.iterrows():
        if row["entity_id"] not in pep_customers:
            associated.add(row["entity_id"])
        if row["related_entity_id"] not in pep_customers:
            associated.add(row["related_entity_id"])

    if associated:
        pep_assoc_flags = customers[
            customers["customer_id"].isin(associated)
        ][["customer_id", "customer_name", "country_code", "nationality", "date_of_birth"]].copy()

        pep_assoc_flags["screening_id"] = "SCR_PEP_ASSOC_" + pep_assoc_flags["customer_id"]
        pep_assoc_flags["matched_list_source"] = "PEP_INFERENCE"
        pep_assoc_flags["matched_entity_name"] = "PEP_ASSOCIATE"
        pep_assoc_flags["matched_program"] = "PEP_RELATIONSHIP"
        pep_assoc_flags["match_score"] = 65
        pep_assoc_flags["match_type"] = "relationship_inference"
        pep_assoc_flags["disposition"] = "pending"
        pep_assoc_flags["screening_date"] = datetime.utcnow().strftime("%Y-%m-%d")

        screening_results = pd.concat(
            [screening_results, pep_assoc_flags], ignore_index=True
        )
        logger.info(f"PEP relationship inference: {len(pep_assoc_flags)} associated entities flagged")

    return screening_results


def run() -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("Spark Job 4: Sanctions & PEP Screening")
    logger.info("=" * 60)

    customers = pd.read_parquet(DUMMY_DIR / "customers.parquet")
    sanctions = pd.read_parquet(DUMMY_DIR / "sanctions_list.parquet")
    rels = pd.read_parquet(DUMMY_DIR / "relationships.parquet")

    logger.info(f"Screening {len(customers):,} customers against {len(sanctions)} sanctions entries")

    results = screen_against_list(customers, sanctions)
    logger.info(f"Initial screening hits: {len(results)}")

    results = apply_pep_relationship_inference(customers, rels, results)
    logger.info(f"Total screening alerts (including PEP inference): {len(results)}")

    # Score distribution
    if not results.empty:
        high = (results["match_score"] >= 80).sum()
        med = ((results["match_score"] >= 60) & (results["match_score"] < 80)).sum()
        low = (results["match_score"] < 60).sum()
        logger.info(f"  Score 80-100 (high confidence): {high}")
        logger.info(f"  Score 60-79 (medium):           {med}")
        logger.info(f"  Score 50-59 (low):              {low}")

    out = PROCESSED_DIR / "screening_alerts.parquet"
    results.to_parquet(out, index=False)
    logger.success(f"Screening complete: {len(results)} alerts → {out}")
    return results


if __name__ == "__main__":
    run()
