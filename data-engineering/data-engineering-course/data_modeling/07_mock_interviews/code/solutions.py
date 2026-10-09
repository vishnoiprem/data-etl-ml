"""Solutions to the M07 practice problems.

Three end-to-end star schemas with sample data, in
working SQLite:

  * Library management (Lesson 34) — `build_library`.
  * Hospital patient records (Lesson 35) — `build_hospital`.
  * Hotel booking (Lesson 36) — `build_hotel`.

Each function returns the list of tables it created,
so the tests can inspect them.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

from typing import List

from common import Column, QueryRunner, Table


# ---- Library management -------------------------------------------------


def build_library(q: QueryRunner) -> List[str]:
    """Library management star schema.

    Central fact: `fact_loans`, grain = one row per
    loan (checkout-to-return cycle). Dimensions: book,
    patron (SCD 2), branch, date (role-played).
    """
    dim_book = Table("dim_book", [
        Column("book_key", "INTEGER", primary_key=True),
        Column("isbn", "TEXT", nullable=False),
        Column("title", "TEXT", nullable=False),
        Column("author", "TEXT", nullable=False),
        Column("genre", "TEXT"),
    ])
    dim_patron = Table("dim_patron", [
        Column("patron_key", "INTEGER", primary_key=True),
        Column("patron_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("patron_type", "TEXT", nullable=False),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_branch = Table("dim_branch", [
        Column("branch_key", "INTEGER", primary_key=True),
        Column("branch_id", "INTEGER", nullable=False),
        Column("branch_name", "TEXT", nullable=False),
        Column("city", "TEXT", nullable=False),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])
    fact = Table("fact_loans", [
        Column("loan_key", "INTEGER", primary_key=True),
        Column("book_key", "INTEGER", nullable=False,
               references="dim_book(book_key)"),
        Column("patron_key", "INTEGER", nullable=False,
               references="dim_patron(patron_key)"),
        Column("branch_key", "INTEGER", nullable=False,
               references="dim_branch(branch_key)"),
        Column("checkout_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("due_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("return_date_key", "INTEGER",
               references="dim_date(date_key)"),
        Column("loan_duration_days", "INTEGER"),
        Column("days_overdue", "INTEGER"),
        Column("fine_amount", "REAL", nullable=False, default="0"),
    ])
    tables = [dim_book, dim_patron, dim_branch, dim_date, fact]
    for t in tables:
        q.execute(t.to_ddl())

    # Books.
    q.executemany(
        "INSERT INTO dim_book VALUES (?,?,?,?,?)",
        [
            (1, "ISBN-001", "1984", "Orwell", "Dystopia"),
            (2, "ISBN-002", "Dune", "Herbert", "SciFi"),
            (3, "ISBN-003", "Foundation", "Asimov", "SciFi"),
            (4, "ISBN-004", "Beloved", "Morrison", "Fiction"),
        ],
    )
    # Patron SCD 2 — patron 1 was student in Q1, adult in Q2.
    q.executemany(
        "INSERT INTO dim_patron VALUES (?,?,?,?,?,?,?)",
        [
            (1, 101, "Alice", "student", 20240101, 20240630, 0),
            (2, 101, "Alice", "adult",   20240701, None,     1),
            (3, 102, "Bob",   "adult",   20240101, None,     1),
            (4, 103, "Carol", "senior",  20240101, None,     1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_branch VALUES (?,?,?,?)",
        [
            (1, 1, "Downtown", "Springfield"),
            (2, 2, "Eastside", "Springfield"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240115, "2024-01-15", 1, 2024),
            (20240201, "2024-02-01", 2, 2024),
            (20240301, "2024-03-01", 3, 2024),
            (20240401, "2024-04-01", 4, 2024),
        ],
    )
    # Loans.  Alice (student version) borrows 1984 in Jan,
    # returns late.  Bob borrows Dune in Feb, returns on time.
    #  Carol borrows Foundation in Mar, still out.
    q.executemany(
        "INSERT INTO fact_loans VALUES "
        "(?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 20240115, 20240215, 20240301,
             46, 15, 7.5),
            (2, 2, 3, 1, 20240201, 20240301, 20240228,
             27, 0,  0.0),
            (3, 3, 4, 2, 20240301, 20240401, None,
             None, None, 0.0),
        ],
    )
    return [t.name for t in tables]


# ---- Hospital patient records -------------------------------------------


def build_hospital(q: QueryRunner) -> List[str]:
    """Hospital patient records.

    Two fact tables: `fact_admissions` (accumulating
    snapshot, one row per admission) and
    `fact_procedures` (transactional, one row per
    procedure). Tokenized patient dim.
    """
    dim_patient = Table("dim_patient", [
        Column("patient_key", "INTEGER", primary_key=True),
        Column("patient_id", "INTEGER", nullable=False),
        Column("age_band", "TEXT", nullable=False),
        Column("gender", "TEXT", nullable=False),
        Column("insurance_type", "TEXT", nullable=False),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_ward = Table("dim_ward", [
        Column("ward_key", "INTEGER", primary_key=True),
        Column("ward_id", "INTEGER", nullable=False),
        Column("ward_name", "TEXT", nullable=False),
        Column("ward_type", "TEXT"),
    ])
    dim_surgeon = Table("dim_surgeon", [
        Column("surgeon_key", "INTEGER", primary_key=True),
        Column("surgeon_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("specialty", "TEXT"),
    ])
    dim_procedure_code = Table("dim_procedure_code", [
        Column("procedure_code_key", "INTEGER", primary_key=True),
        Column("cpt_code", "TEXT", nullable=False),
        Column("description", "TEXT", nullable=False),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])

    # Tokenized patient mapping (the "natural" id lives
    # behind restricted access).
    patient_token_map = Table("patient_token_map", [
        Column("patient_key", "INTEGER", primary_key=True,
               references="dim_patient(patient_key)"),
        Column("patient_id", "INTEGER", nullable=False),
    ])

    # Accumulating snapshot fact for admissions.
    fact_admissions = Table("fact_admissions", [
        Column("admission_key", "INTEGER", primary_key=True),
        Column("patient_key", "INTEGER", nullable=False,
               references="dim_patient(patient_key)"),
        Column("ward_key", "INTEGER", nullable=False,
               references="dim_ward(ward_key)"),
        Column("admit_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("discharge_date_key", "INTEGER",
               references="dim_date(date_key)"),
        Column("los_days", "INTEGER"),
        Column("procedure_count", "INTEGER", nullable=False,
               default="0"),
        Column("total_charges", "REAL", nullable=False, default="0"),
    ])
    # Transactional fact for procedures.
    fact_procedures = Table("fact_procedures", [
        Column("procedure_fact_key", "INTEGER", primary_key=True),
        Column("admission_key", "INTEGER", nullable=False,
               references="fact_admissions(admission_key)"),
        Column("patient_key", "INTEGER", nullable=False,
               references="dim_patient(patient_key)"),
        Column("surgeon_key", "INTEGER", nullable=False,
               references="dim_surgeon(surgeon_key)"),
        Column("procedure_code_key", "INTEGER", nullable=False,
               references="dim_procedure_code(procedure_code_key)"),
        Column("procedure_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("duration_min", "INTEGER"),
        Column("complication_flag", "INTEGER", nullable=False,
               default="0"),
    ])
    tables = [
        dim_patient, dim_ward, dim_surgeon, dim_procedure_code,
        dim_date, patient_token_map,
        fact_admissions, fact_procedures,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_patient VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1001, "30-39", "F", "private", 20240101, 20240630, 0),
            (2, 1001, "30-39", "F", "medicare", 20240701, None,     1),
            (3, 1002, "60-69", "M", "medicare", 20240101, None,     1),
        ],
    )
    q.executemany(
        "INSERT INTO patient_token_map VALUES (?,?)",
        [(1, 1001), (2, 1001), (3, 1002)],
    )
    q.executemany(
        "INSERT INTO dim_ward VALUES (?,?,?,?)",
        [
            (1, 1, "ICU",        "intensive"),
            (2, 2, "Med-Surg",   "general"),
            (3, 3, "Maternity",  "obstetric"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_surgeon VALUES (?,?,?,?)",
        [
            (1, 201, "Dr. Smith", "cardiac"),
            (2, 202, "Dr. Jones", "ortho"),
            (3, 203, "Dr. Lee",   "general"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_procedure_code VALUES (?,?,?)",
        [
            (1, "CPT-001", "CABG"),
            (2, "CPT-002", "Knee replacement"),
            (3, "CPT-003", "Appendectomy"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240101, "2024-01-01"),
            (20240105, "2024-01-05"),
            (20240110, "2024-01-10"),
            (20240115, "2024-01-15"),
            (20240120, "2024-01-20"),
        ],
    )
    # Admissions.  Patient 1 admitted Jan 1, discharged
    # Jan 10 (LOS = 9 days), 1 procedure.  Patient 3 admitted
    # Jan 5, discharged Jan 15 (LOS = 10 days), 1 procedure
    # with complication.
    q.executemany(
        "INSERT INTO fact_admissions VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 20240101, 20240110, 9,  1, 50000.0),
            (2, 3, 2, 20240105, 20240115, 10, 1, 12000.0),
        ],
    )
    q.executemany(
        "INSERT INTO fact_procedures VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 20240105, 240, 0),
            (2, 2, 3, 3, 3, 20240108,  60, 1),
        ],
    )
    return [t.name for t in tables]


# ---- Hotel booking ------------------------------------------------------


def build_hotel(q: QueryRunner) -> List[str]:
    """Hotel booking star schema.

    Central fact: `fact_reservations`, grain = one row
    per reservation (accumulating snapshot with
    milestones: book, check-in, check-out, cancel).
    Plus `fact_room_nights` periodic snapshot for
    occupancy reporting.
    """
    dim_guest = Table("dim_guest", [
        Column("guest_key", "INTEGER", primary_key=True),
        Column("guest_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("loyalty_tier", "TEXT", nullable=False),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_hotel = Table("dim_hotel", [
        Column("hotel_key", "INTEGER", primary_key=True),
        Column("hotel_id", "INTEGER", nullable=False),
        Column("hotel_name", "TEXT", nullable=False),
        Column("city", "TEXT", nullable=False),
        Column("star_rating", "INTEGER"),
    ])
    dim_room_type = Table("dim_room_type", [
        Column("room_type_key", "INTEGER", primary_key=True),
        Column("room_type_id", "INTEGER", nullable=False),
        Column("type_name", "TEXT", nullable=False),
        Column("max_occupancy", "INTEGER"),
    ])
    dim_channel = Table("dim_channel", [
        Column("channel_key", "INTEGER", primary_key=True),
        Column("channel_name", "TEXT", nullable=False),
        Column("channel_category", "TEXT"),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])
    fact_reservations = Table("fact_reservations", [
        Column("reservation_key", "INTEGER", primary_key=True),
        Column("guest_key", "INTEGER", nullable=False,
               references="dim_guest(guest_key)"),
        Column("hotel_key", "INTEGER", nullable=False,
               references="dim_hotel(hotel_key)"),
        Column("room_type_key", "INTEGER", nullable=False,
               references="dim_room_type(room_type_key)"),
        Column("channel_key", "INTEGER", nullable=False,
               references="dim_channel(channel_key)"),
        Column("book_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("check_in_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("check_out_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("cancel_date_key", "INTEGER",
               references="dim_date(date_key)"),
        Column("num_nights", "INTEGER", nullable=False),
        Column("num_rooms", "INTEGER", nullable=False, default="1"),
        Column("total_room_revenue", "REAL", nullable=False),
        Column("total_fb_revenue", "REAL", nullable=False, default="0"),
        Column("cancellation_lead_days", "INTEGER"),
    ])
    fact_room_nights = Table("fact_room_nights", [
        Column("room_night_key", "INTEGER", primary_key=True),
        Column("hotel_key", "INTEGER", nullable=False,
               references="dim_hotel(hotel_key)"),
        Column("room_type_key", "INTEGER", nullable=False,
               references="dim_room_type(room_type_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("occupied_flag", "INTEGER", nullable=False, default="0"),
        Column("rate_charged", "REAL", nullable=False, default="0"),
        Column("was_cancelled", "INTEGER", nullable=False, default="0"),
    ])
    tables = [
        dim_guest, dim_hotel, dim_room_type, dim_channel, dim_date,
        fact_reservations, fact_room_nights,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_guest VALUES (?,?,?,?,?,?,?)",
        [
            (1, 501, "Alice", "silver", 20240101, 20240630, 0),
            (2, 501, "Alice", "gold",   20240701, None,     1),
            (3, 502, "Bob",   "silver", 20240101, None,     1),
            (4, 503, "Carol", "platinum", 20240101, None, 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_hotel VALUES (?,?,?,?,?)",
        [
            (1, 100, "Grand Plaza",  "NYC",   5),
            (2, 200, "Sea Breeze",   "Miami", 4),
        ],
    )
    q.executemany(
        "INSERT INTO dim_room_type VALUES (?,?,?,?)",
        [
            (1, 1, "Standard", 2),
            (2, 2, "Suite",    4),
        ],
    )
    q.executemany(
        "INSERT INTO dim_channel VALUES (?,?,?)",
        [
            (1, "Direct",   "direct"),
            (2, "Expedia",  "OTA"),
            (3, "Booking",  "OTA"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240105, "2024-01-05", 1, 2024),
            (20240110, "2024-01-10", 1, 2024),
            (20240115, "2024-01-15", 1, 2024),
            (20240120, "2024-01-20", 1, 2024),
            (20240125, "2024-01-25", 1, 2024),
        ],
    )
    # Reservations.
    #  Res 1: Alice (silver) books 5 nights, checks in 15, out 20.
    #   1000/night.  Total = 5000.
    #  Res 2: Bob books 5 nights (10-15), 200/night, then
    #   cancels 1 day before.  Cancelled.
    #  Res 3: Carol books 5 nights (20-25), suite, 500/night.
    q.executemany(
        "INSERT INTO fact_reservations VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 20240105, 20240115, 20240120, None,
             5, 1, 5000.0, 200.0, None),
            (2, 3, 1, 1, 2, 20240105, 20240110, 20240115, 20240109,
             5, 1, 1000.0,   0.0, 6),
            (3, 4, 2, 2, 1, 20240110, 20240120, 20240125, None,
             5, 1, 2500.0,   0.0, None),
        ],
    )
    # Room nights — exploded per-night.  Res 1 occupies
    # standard rooms 15–20.  Res 2 was cancelled, so rooms
    # are *not* occupied (was_cancelled = 1).  Res 3
    # occupies suites 20–25.
    nights = []
    nights.append((1, 1, 1, 20240115, 1, 1000.0, 0))
    nights.append((2, 1, 1, 20240116, 1, 1000.0, 0))
    nights.append((3, 1, 1, 20240117, 1, 1000.0, 0))
    nights.append((4, 1, 1, 20240118, 1, 1000.0, 0))
    nights.append((5, 1, 1, 20240119, 1, 1000.0, 0))
    nights.append((6, 1, 1, 20240110, 0,    0.0, 1))
    nights.append((7, 1, 1, 20240111, 0,    0.0, 1))
    nights.append((8, 1, 1, 20240112, 0,    0.0, 1))
    nights.append((9, 1, 1, 20240113, 0,    0.0, 1))
    nights.append((10, 1, 1, 20240114, 0,   0.0, 1))
    nights.append((11, 2, 2, 20240120, 1,  500.0, 0))
    nights.append((12, 2, 2, 20240121, 1,  500.0, 0))
    nights.append((13, 2, 2, 20240122, 1,  500.0, 0))
    nights.append((14, 2, 2, 20240123, 1,  500.0, 0))
    nights.append((15, 2, 2, 20240124, 1,  500.0, 0))
    q.executemany(
        "INSERT INTO fact_room_nights VALUES "
        "(?,?,?,?,?,?,?)", nights
    )
    return [t.name for t in tables]


# ---- demo ----------------------------------------------------------------


if __name__ == "__main__":
    print("Building M07 practice schemas...\n")
    for name, fn in [
        ("library",  build_library),
        ("hospital", build_hospital),
        ("hotel",    build_hotel),
    ]:
        with QueryRunner(":memory:") as q:
            tables = fn(q)
            print(f"[{name}]  tables: {tables}")
            for tn in tables:
                if tn.startswith("fact_"):
                    rows = q.query_all(f"SELECT * FROM {tn}")
                    print(f"   {tn}: {len(rows)} rows")
        print()
