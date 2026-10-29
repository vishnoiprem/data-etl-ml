# Delta Lake example (PySpark)
from delta.tables import DeltaTable

# Step 1: Add column (nullable)
spark.sql("""
    ALTER TABLE users
    ADD COLUMNS (is_active BOOLEAN)
""")

# Step 2: Backfill using MERGE or UPDATE
spark.sql("""
    UPDATE users
    SET is_active = TRUE
    WHERE is_active IS NULL
""")

# Step 3: Verify
assert spark.table("users").filter("is_active IS NULL").count() == 0

# Step 4: Commit schema change
spark.sql("ALTER TABLE users ALTER COLUMN is_active TYPE BOOLEAN NOT NULL")