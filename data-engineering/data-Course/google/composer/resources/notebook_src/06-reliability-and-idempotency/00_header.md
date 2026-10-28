#! number: 06
#! title: Reliability & Idempotency
#! module: Module 2 · Reliability & Operations
#! lecture: Lecture 2.4

- Understand what *idempotent* means, precisely, and why retries are a design input
- Compare `WRITE_TRUNCATE` and `WRITE_APPEND` on a partitioned table
- Build **deterministic row identities** (`partition:order_id`) rather than arrival-time keys
- Demonstrate a real double-count and then prove the invariant that prevents it
- Make backfills safe by scoping writes to the partition being repaired
