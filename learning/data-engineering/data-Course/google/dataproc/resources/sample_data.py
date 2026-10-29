"""
sample_data.py — generates the synthetic datasets used across the course.

Everything here is DETERMINISTIC: the same seed always produces the
same data. That matters for teaching, because a student can compare
their pipeline output against a known-correct answer.

The datasets deliberately include DIRTY ROWS — null prices, unparseable
dates, duplicate keys, negative quantities, malformed ICD-10 codes.
A pipeline that only ever sees clean data is a pipeline that has never
been tested.

Usage:
    # Write everything to a local directory
    python resources/sample_data.py --output-dir=./sample_data --seed=42

    # Custom row counts
    python resources/sample_data.py --output-dir=./sample_data \
        --seed=42 --retail-rows=5000 --claims-rows=2000

    # Use it as a library
    from sample_data import make_retail_sales, make_healthcare_claims
    sales = make_retail_sales(n=100, seed=42)
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import random
from typing import Any

# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------

PRODUCT_CATEGORIES = [
    ("Electronics", "Electronics"),
    ("Home & Kitchen", "Home"),
    ("Apparel", "Apparel"),
    ("Sports & Outdoors", "Sports"),
    ("Beauty", "Beauty"),
    ("Toys", "Toys"),
    ("Grocery", "Grocery"),
    ("Office", "Office"),
]

BRANDS = [
    "Aurora", "Brightline", "Cobalt", "Driftwood", "Everest",
    "Foundry", "Granite", "Harbor", "Indigo", "Juniper",
]

REGIONS = [
    ("R01", "Northeast"),
    ("R02", "Southeast"),
    ("R03", "Midwest"),
    ("R04", "Southwest"),
    ("R05", "West"),
]

CITIES = [
    ("Boston", "MA", "R01"), ("Portland", "ME", "R01"),
    ("Atlanta", "GA", "R02"), ("Miami", "FL", "R02"),
    ("Chicago", "IL", "R03"), ("Detroit", "MI", "R03"),
    ("Austin", "TX", "R04"), ("Phoenix", "AZ", "R04"),
    ("Seattle", "WA", "R05"), ("Denver", "CO", "R05"),
]

STORE_FORMATS = ["Supermarket", "Hypermarket", "Convenience", "Department"]

PAYMENT_METHODS = ["CREDIT_CARD", "DEBIT_CARD", "CASH", "MOBILE_WALLET", "GIFT_CARD"]

ORDER_STATUSES = ["COMPLETED"] * 18 + ["CANCELLED", "REFUNDED", "PENDING"]

PROMO_CODES = ["SAVE10", "SAVE20", "BOGUS", "FREESHIP", "WELCOME15", None]

PROVIDER_TYPES = ["PRIMARY_CARE", "SPECIALIST", "HOSPITAL", "HOME_HEALTH"]
PROVIDER_TYPE_WEIGHTS = [0.40, 0.35, 0.15, 0.10]

# A representative slice of the ICD-10-CM code space.
ICD10_CODES = [
    ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine", "4"),
    ("E11.65", "Type 2 diabetes mellitus with hyperglycemia", "Endocrine", "4"),
    ("I10", "Essential (primary) hypertension", "Circulatory", "9"),
    ("I25.10", "Coronary artery disease", "Circulatory", "9"),
    ("J45.909", "Unspecified asthma, uncomplicated", "Respiratory", "16"),
    ("J44.1", "COPD with (acute) exacerbation", "Respiratory", "16"),
    ("M54.50", "Low back pain, unspecified", "Musculoskeletal", "13"),
    ("M54.16", "Radiculopathy, lumbar region", "Musculoskeletal", "13"),
    ("F41.1", "Generalized anxiety disorder", "Mental", "5"),
    ("F32.9", "Major depressive disorder, single episode, unspecified", "Mental", "5"),
    ("Z00.00", "General adult medical exam without abnormal findings", "Factors", "21"),
    ("Z23", "Encounter for immunization", "Factors", "21"),
    ("R51.9", "Headache, unspecified", "Symptoms", "18"),
    ("R10.9", "Unspecified abdominal pain", "Symptoms", "18"),
    ("N39.0", "Urinary incontinence", "Genitourinary", "14"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis", "Digestive", "13"),
    ("G43.909", "Migraine, unspecified, not intractable", "Neurology", "8"),
    ("S06.0X0A", "Concussion without loss of consciousness", "Injury", "19"),
]

# ICD-10 codes that are structurally INVALID — used for the dirty rows.
# Each one fails the course's ICD10_REGEX
# (^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$) for a different reason,
# so the validation rules are exercised in several directions.
MALFORMED_ICD10 = [
    "A1.2",        # only 1 digit after the letter
    "12345",       # starts with a digit
    "E11.9x",      # lowercase letter after the decimal
    "XYZ.99",      # three letters before the decimal
    "E1.9",        # only 1 digit before the decimal
    "",            # empty string
    "E11.99999",   # 5 characters after the decimal
    "U07.1",       # 'U' is reserved in the first position
]

DENIAL_CODES = [
    (None, None),
    ("CO-16", "Missing or invalid diagnosis code"),
    ("CO-18", "Duplicate claim"),
    ("CO-29", "Service not covered on this date"),
    ("CO-197", "Prior authorization required"),
    ("CO-16", "Missing or invalid diagnosis code"),
]

# The date the sample data is centred on. Fixed, so the data is
# deterministic across runs and machines.
DATA_END_DATE = datetime.date(2026, 10, 27)
DATA_START_DATE = datetime.date(2026, 9, 1)


# --------------------------------------------------------------------------
# Retail — dimensions
# --------------------------------------------------------------------------


def make_retail_dims(seed: int = 42) -> dict[str, list[dict[str, Any]]]:
    """Generate the retail product and store dimensions.

    Args:
        seed: The random seed. The same seed always yields the same
            dimensions.

    Returns:
        A dict with "products" and "stores" keys, each a list of row
        dicts.
    """
    rng = random.Random(seed)

    products: list[dict[str, Any]] = []
    for i in range(1, 61):
        category_id, category_name = rng.choice(PRODUCT_CATEGORIES)
        products.append(
            {
                "product_id": f"P{i:05d}",
                "name": f"{rng.choice(BRANDS)} {category_name} Item {i:03d}",
                "category": category_name,
                "brand": rng.choice(BRANDS),
                "cost": round(rng.uniform(2.0, 180.0), 2),
            }
        )

    stores: list[dict[str, Any]] = []
    for i in range(1, 13):
        city, state, region_id = rng.choice(CITIES)
        region_name = dict(REGIONS)[region_id]
        stores.append(
            {
                "store_id": f"S{i:03d}",
                "name": f"{city} {rng.choice(STORE_FORMATS)} #{i:02d}",
                "city": city,
                "state": state,
                "region": region_name,
                "sq_ft": rng.randrange(4_000, 120_000, 500),
            }
        )

    return {"products": products, "stores": stores}


# --------------------------------------------------------------------------
# Retail — transactions
# --------------------------------------------------------------------------


def make_retail_sales(n: int = 1000, seed: int = 42) -> list[dict[str, Any]]:
    """Generate POS transactions, including deliberately dirty rows.

    The dirty rows are the point of this function. The course pipeline
    must handle:

        - NULL unit_price
        - An unparseable order timestamp
        - Duplicate order_id values (a source replay)
        - Negative quantity
        - A missing store_id or product_id

    Args:
        n: The approximate number of rows to generate. A handful of
            extra dirty rows are added on top.
        seed: The random seed.

    Returns:
        A list of transaction dicts. Every row has the same keys.
    """
    rng = random.Random(seed)
    dims = make_retail_dims(seed=seed)
    products = dims["products"]
    stores = dims["stores"]

    span_days = (DATA_END_DATE - DATA_START_DATE).days + 1

    rows: list[dict[str, Any]] = []
    for i in range(n):
        product = rng.choice(products)
        store = rng.choice(stores)

        order_date = DATA_START_DATE + datetime.timedelta(days=rng.randrange(span_days))
        order_ts = datetime.datetime.combine(
            order_date,
            datetime.time(rng.randrange(7, 22), rng.randrange(0, 60), rng.randrange(0, 60)),
            tzinfo=datetime.timezone.utc,
        )

        quantity = rng.choices(
            [1, 2, 3, 4, 5, 10],
            weights=[45, 25, 15, 8, 5, 2],
        )[0]
        unit_price = round(rng.uniform(3.0, 450.0), 2)
        discount = round(unit_price * quantity * rng.choice([0.0, 0.0, 0.0, 0.05, 0.10, 0.20]), 2)

        rows.append(
            {
                "order_id": f"ORD-{i:06d}",
                "store_id": store["store_id"],
                "product_id": product["product_id"],
                "order_timestamp": order_ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "quantity": quantity,
                "unit_price": unit_price,
                "discount": discount,
                "payment_method": rng.choice(PAYMENT_METHODS),
                "promo_code": rng.choice(PROMO_CODES),
                "status": rng.choice(ORDER_STATUSES),
                "source_file": f"pos_orders_{order_date.isoformat()}.csv",
            }
        )

    # ---- Dirty rows -----------------------------------------------------

    # 1. A null unit_price — the price column is missing entirely.
    if rows:
        dirty = dict(rows[0])
        dirty["order_id"] = "ORD-DIRTY-NULL-PRICE"
        dirty["unit_price"] = None
        dirty["status"] = "COMPLETED"
        rows.append(dirty)

    # 2. An unparseable timestamp — a source format change.
    if len(rows) > 5:
        dirty = dict(rows[5])
        dirty["order_id"] = "ORD-DIRTY-BAD-DATE"
        dirty["order_timestamp"] = "15/10/2026 14:22:00"
        dirty["status"] = "COMPLETED"
        rows.append(dirty)

    # 3. A negative quantity — a sign error at the scanner.
    if len(rows) > 10:
        dirty = dict(rows[10])
        dirty["order_id"] = "ORD-DIRTY-NEG-QTY"
        dirty["quantity"] = -abs(dirty["quantity"])
        dirty["status"] = "COMPLETED"
        rows.append(dirty)

    # 4. Duplicate order_ids — the source replayed two records.
    for idx in (20, 21):
        if len(rows) > idx:
            duplicate = dict(rows[idx])
            duplicate["order_id"] = rows[0]["order_id"]
            duplicate["source_file"] = "pos_orders_replay.csv"
            rows.append(duplicate)

    # 5. A missing store_id — a referential integrity break.
    if len(rows) > 30:
        dirty = dict(rows[30])
        dirty["order_id"] = "ORD-DIRTY-NO-STORE"
        dirty["store_id"] = None
        dirty["status"] = "COMPLETED"
        rows.append(dirty)

    # 6. A missing product_id — another referential integrity break.
    if len(rows) > 40:
        dirty = dict(rows[40])
        dirty["order_id"] = "ORD-DIRTY-NO-PRODUCT"
        dirty["product_id"] = None
        dirty["status"] = "COMPLETED"
        rows.append(dirty)

    return rows


# --------------------------------------------------------------------------
# Healthcare — dimensions
# --------------------------------------------------------------------------


def make_healthcare_dims(seed: int = 7) -> dict[str, list[dict[str, Any]]]:
    """Generate the healthcare provider and diagnosis dimensions.

    Args:
        seed: The random seed.

    Returns:
        A dict with "providers" and "diagnoses" keys.
    """
    rng = random.Random(seed)

    providers: list[dict[str, Any]] = []
    for i in range(1, 26):
        provider_type = rng.choices(
            PROVIDER_TYPES,
            weights=PROVIDER_TYPE_WEIGHTS,
        )[0]
        city, state, _ = rng.choice(CITIES)
        contract_start = DATA_START_DATE - datetime.timedelta(days=rng.randrange(365, 2200))
        contract_end = (
            contract_start + datetime.timedelta(days=rng.randrange(730, 2500))
            if rng.random() < 0.8
            else None
        )
        providers.append(
            {
                "provider_npi": f"{rng.randrange(1000000000, 9999999999)}",
                "provider_name": f"{city} {provider_type.title().replace('_', ' ')} Group {i:02d}",
                "provider_type": provider_type,
                "tax_id": f"{rng.randrange(10**11, 10**12)}",
                "city": city,
                "state": state,
                "contract_start": contract_start.isoformat(),
                "contract_end": contract_end.isoformat() if contract_end else None,
                "is_active": bool(contract_end and contract_end > DATA_END_DATE)
                or contract_end is None,
            }
        )

    diagnoses: list[dict[str, Any]] = []
    for code, description, category, chapter in ICD10_CODES:
        diagnoses.append(
            {
                "icd10_code": code,
                "description": description,
                "category": category,
                "chapter": chapter,
                "is_valid": True,
            }
        )

    return {"providers": providers, "diagnoses": diagnoses}


# --------------------------------------------------------------------------
# Healthcare — claims
# --------------------------------------------------------------------------


def make_healthcare_claims(
    n: int = 800,
    seed: int = 7,
) -> list[dict[str, Any]]:
    """Generate nested healthcare claims, including dirty rows.

    Each claim is a dict with a `dx` array (the nested diagnosis list)
    AND a `diagnosis_payload` field holding that array as a
    JSON-encoded string. The duplication is deliberate: the nested form
    is what a JSON feed looks like, and the encoded-string form is what
    the healthcare case study's bronze table actually stores. The
    pipeline has to parse the string and explode the array.

    Dirty rows include:
        - A non-numeric or negative claim_amount
        - A service date in the future
        - A malformed ICD-10 code
        - A missing provider NPI
        - A claim whose diagnosis array is empty

    Args:
        n: The approximate number of claims to generate.
        seed: The random seed.

    Returns:
        A list of claim dicts.
    """
    rng = random.Random(seed)
    dims = make_healthcare_dims(seed=seed)
    providers = dims["providers"]
    diagnoses = dims["diagnoses"]

    span_days = (DATA_END_DATE - DATA_START_DATE).days + 1

    claims: list[dict[str, Any]] = []
    for i in range(n):
        provider = rng.choice(providers)
        service_date = DATA_START_DATE + datetime.timedelta(days=rng.randrange(span_days))
        submitted_at = datetime.datetime.combine(
            service_date + datetime.timedelta(days=rng.randrange(0, 30)),
            datetime.time(rng.randrange(8, 18), rng.randrange(0, 60)),
            tzinfo=datetime.timezone.utc,
        )

        dx_count = rng.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
        dx_codes = [rng.choice(diagnoses)["icd10_code"] for _ in range(dx_count)]

        amount = round(
            rng.choice(
                [
                    rng.uniform(50, 500),
                    rng.uniform(500, 5000),
                    rng.uniform(5000, 50000),
                ]
            ),
            2,
        )

        denial_code, denial_reason = rng.choice(DENIAL_CODES)

        dx_array = [
            {"code": code, "description": _describe_code(code, diagnoses)}
            for code in dx_codes
        ]

        claims.append(
            {
                "claim_id": f"CLM-{i:06d}",
                "member_id": f"MEM-{rng.randrange(100000, 999999)}",
                "provider_npi": provider["provider_npi"],
                "service_date": service_date.isoformat(),
                "submitted_at": submitted_at.strftime("%Y-%m-%dT%H:%M:%S"),
                "claim_amount": amount,
                "dx": dx_array,
                "diagnosis_payload": json.dumps(dx_array),
                "procedure_codes": [f"PROC{rng.randrange(10000, 99999)}" for _ in range(rng.randrange(0, 3))],
                "denial_code": denial_code,
                "denial_reason": denial_reason,
                "source_file": f"claims_{service_date.isoformat()}.ndjson",
            }
        )

    # ---- Dirty rows -----------------------------------------------------

    # 1. A non-numeric amount.
    if claims:
        dirty = dict(claims[0])
        dirty["claim_id"] = "CLM-DIRTY-AMOUNT"
        dirty["claim_amount"] = "NOT_A_NUMBER"
        claims.append(dirty)

    # 2. A future service date.
    if len(claims) > 3:
        dirty = dict(claims[3])
        dirty["claim_id"] = "CLM-DIRTY-FUTURE"
        dirty["service_date"] = (DATA_END_DATE + datetime.timedelta(days=45)).isoformat()
        claims.append(dirty)

    # 3. A malformed ICD-10 code.
    if len(claims) > 7:
        dirty = dict(claims[7])
        dirty["claim_id"] = "CLM-DIRTY-ICD"
        bad_code = rng.choice([c for c in MALFORMED_ICD10 if c])
        dirty["dx"] = [{"code": bad_code, "description": "Malformed code"}]
        dirty["diagnosis_payload"] = json.dumps(dirty["dx"])
        claims.append(dirty)

    # 4. A missing provider NPI.
    if len(claims) > 11:
        dirty = dict(claims[11])
        dirty["claim_id"] = "CLM-DIRTY-NO-NPI"
        dirty["provider_npi"] = None
        claims.append(dirty)

    # 5. An empty diagnosis array.
    if len(claims) > 15:
        dirty = dict(claims[15])
        dirty["claim_id"] = "CLM-DIRTY-NO-DX"
        dirty["dx"] = []
        dirty["diagnosis_payload"] = json.dumps([])
        claims.append(dirty)

    # 6. A negative amount.
    if len(claims) > 19:
        dirty = dict(claims[19])
        dirty["claim_id"] = "CLM-DIRTY-NEGATIVE"
        dirty["claim_amount"] = -250.00
        claims.append(dirty)

    return claims


def _describe_code(code: str, diagnoses: list[dict[str, Any]]) -> str:
    """Look up the description for an ICD-10 code."""
    for row in diagnoses:
        if row["icd10_code"] == code:
            return str(row["description"])
    return "Unknown diagnosis code"


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------


def _write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    """Write a list of dicts to a CSV file."""
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            handle.write("")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: str, rows: list[dict[str, Any]]) -> None:
    """Write a list of dicts to a JSON Lines file."""
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str))
            handle.write("\n")


def _write_nested_json(path: str, rows: list[dict[str, Any]]) -> None:
    """Write a list of dicts to a pretty-printed JSON array."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, default=str)


def write_local(
    data_dir: str,
    seed: int = 42,
    retail_rows: int = 1000,
    claims_rows: int = 800,
) -> dict[str, str]:
    """Write every sample dataset to a local directory.

    Creates the following layout:

        data_dir/
        ├── pos/
        │   ├── pos_orders.csv          # the transactions
        │   ├── product_master.csv      # the product dimension
        │   └── store_master.csv        # the store dimension
        ├── claims/
        │   ├── claims.ndjson           # the claims, one JSON per line
        │   ├── claims.json             # the same claims, pretty-printed
        │   ├── provider_master.csv     # the provider dimension
        │   └── diagnosis_master.csv    # the ICD-10 reference

    Args:
        data_dir: The output directory. Created if it does not exist.
        seed: The random seed.
        retail_rows: The number of retail transactions to generate.
        claims_rows: The number of healthcare claims to generate.

    Returns:
        A dict mapping the dataset name to the file path written.
    """
    pos_dir = os.path.join(data_dir, "pos")
    claims_dir = os.path.join(data_dir, "claims")
    os.makedirs(pos_dir, exist_ok=True)
    os.makedirs(claims_dir, exist_ok=True)

    written: dict[str, str] = {}

    # --- Retail ---
    retail_dims = make_retail_dims(seed=seed)
    sales = make_retail_sales(n=retail_rows, seed=seed)

    path = os.path.join(pos_dir, "pos_orders.csv")
    _write_csv(path, sales)
    written["retail_sales"] = path

    path = os.path.join(pos_dir, "product_master.csv")
    _write_csv(path, retail_dims["products"])
    written["retail_products"] = path

    path = os.path.join(pos_dir, "store_master.csv")
    _write_csv(path, retail_dims["stores"])
    written["retail_stores"] = path

    # --- Healthcare ---
    health_dims = make_healthcare_dims(seed=seed)
    claims = make_healthcare_claims(n=claims_rows, seed=seed)

    path = os.path.join(claims_dir, "claims.ndjson")
    _write_json(path, claims)
    written["healthcare_claims"] = path

    path = os.path.join(claims_dir, "claims.json")
    _write_nested_json(path, claims)
    written["healthcare_claims_json"] = path

    path = os.path.join(claims_dir, "provider_master.csv")
    _write_csv(path, health_dims["providers"])
    written["healthcare_providers"] = path

    path = os.path.join(claims_dir, "diagnosis_master.csv")
    _write_csv(path, health_dims["diagnoses"])
    written["healthcare_diagnoses"] = path

    return written


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Generate the synthetic datasets used across the Dataproc course."
    )
    parser.add_argument(
        "--output-dir",
        default="./sample_data",
        help="Directory to write the datasets into (default: ./sample_data).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed. The same seed always produces the same data (default: 42).",
    )
    parser.add_argument(
        "--retail-rows",
        type=int,
        default=1000,
        help="Number of retail transactions to generate (default: 1000).",
    )
    parser.add_argument(
        "--claims-rows",
        type=int,
        default=800,
        help="Number of healthcare claims to generate (default: 800).",
    )
    args = parser.parse_args()

    written = write_local(
        data_dir=args.output_dir,
        seed=args.seed,
        retail_rows=args.retail_rows,
        claims_rows=args.claims_rows,
    )

    print(f"Sample data written to {os.path.abspath(args.output_dir)}")
    print(f"Seed: {args.seed}")
    print()
    for name, path in written.items():
        size_kb = os.path.getsize(path) / 1024
        print(f"  {name:24} {path}  ({size_kb:,.1f} KB)")


if __name__ == "__main__":
    main()
