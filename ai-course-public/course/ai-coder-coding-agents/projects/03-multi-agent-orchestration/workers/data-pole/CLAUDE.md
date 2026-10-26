# data-pole — CLAUDE.md

## What this pole does

Market data ingest. Reads vendor APIs (Yahoo Finance / IEX / Polygon in
the course's demo), normalizes to the shared `Quote` schema, caches on disk.

## What it must NOT do

- Make a trading decision.
- Call the broker. (That's `execution-pole`.)
- Modify another pole's data in the shared ledger.

## Inputs

- Vendor credentials in environment: `MARKET_DATA_API_KEY`.
- Symbolic args from orchestrator: `(trace_id, symbols)`.

## Outputs

One entry per symbol written to `shared/notes/ledger/<trace_id>.jsonl`:

```json
{
  "pole": "data-pole",
  "phase": "ingest",
  "trace_id": "...",
  "symbol": "AAPL",
  "quote": { "price": 191.04, "volume": 29834201, "ts": "..." },
  "warnings": []
}
```

If a quote is stale (>5 min behind `ts` of receipt), set
`warnings: ["stale"]` instead of dropping. The strategy-pole reads this
field to skip the symbol.

## Hard rule

**No data goes downstream unless schema-validated against
`contracts/quote.schema.json`.** The schema check is the cheapest defense
against a vendor API silently changing shape.