---
description: Bronze / silver / gold conventions for this lakehouse. Loads when editing files under src/bronze, src/silver, src/gold.
globs:
  - "src/bronze/**"
  - "src/silver/**"
  - "src/gold/**"
---

# Medallion conventions

## Bronze — raw, append-only, no transforms

- Mirrors source byte-for-byte where possible (preserve raw column names,
  raw types where reasonable).
- Stored as Delta. Append-only writes (`mode("append")`).
- Always includes audit columns: `_ingested_at` (timestamp),
  `_source_file` (string), `_ingest_run_id` (string).
- Partitioned by ingest date (`_ingested_date`), not source date.
- Schema is enforced on read; bad rows go to a `*_quarantine` table, not
  silently dropped.

## Silver — typed, deduped, conformed

- Schema is renamed to canonical conventions (snake_case, English names).
- Types are coerced (strings → timestamps, numerics).
- Deduplication on natural key with a `_silver_loaded_at` for lineage.
- Slowly-changing dimensions: Type 2 unless explicitly downgraded.
- Joins to reference data happen here, not in bronze and not in gold.

## Gold — query-optimized, denormalized

- One table per analytical use case. No "general purpose" gold tables.
- Aggregated grain documented in table comment.
- Z-ORDER on the columns the downstream BI tool filters by.
- Refreshed by merge on the grain key, not full overwrite, unless the
  upstream silver is itself a full refresh.

## Naming

- Catalogs: `bronze`, `silver`, `gold` (or `<env>_bronze` etc. in non-prod).
- Schemas: domain (e.g. `silver.maintenance`, `gold.operations`).
- Tables: singular noun (`equipment`, not `equipments`), snake_case.
- Job names: `<layer>_<schema>_<table>_<frequency>`, e.g.
  `bronze_maintenance_workorders_hourly`.

## Promotion gates

Bronze → silver requires:
- Schema contract test passes (`tests/schema/test_<table>.py`).
- Row count delta is within expected bounds (DQ rule, not assertion).

Silver → gold requires:
- All silver inputs have a current run with status SUCCESS.
- Reference data freshness check passes.
