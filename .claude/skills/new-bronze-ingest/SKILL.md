---
name: new-bronze-ingest
description: Scaffold a new bronze-layer ingest from a source feed into the lakehouse. Use when the user asks to add, ingest, onboard, or land a new data source / feed / table into bronze. Covers source discovery, schema definition, audit columns, quarantine, idempotency, and Asset Bundle wiring.
---

# new-bronze-ingest

Use this skill when the user wants to land a new data source into the bronze layer.

## When to invoke

Trigger phrases: "ingest the new X feed", "onboard the Y source", "add a bronze table for Z",
"land the W extract".

## Inputs to gather (ask, don't guess)

1. **Source** — what's producing the data? (S3 prefix, Kafka topic, JDBC, SFTP, REST API)
2. **Format** — Parquet, JSON, CSV, Avro, Delta, raw bytes?
3. **Cadence** — one-shot, hourly, daily, streaming?
4. **Volume** — rows/day order of magnitude, average row size
5. **Natural key** — what uniquely identifies a record?
6. **Schema source** — Schema Registry, sample file, vendor doc, none?
7. **Owner** — who do we page when this breaks?

If any of these are missing, stop and ask before writing code.

## Steps

1. Check naming. Confirm `bronze.<domain>.<table>` does not already exist
   (use the databricks-mini MCP `list_tables` if available).

2. Define schema explicitly in `src/bronze/<domain>/<table>/schema.py`.
   No inferred schemas in prod. Reserve audit columns: `_ingested_at`,
   `_source_file`, `_ingest_run_id`, `_ingested_date`.

3. Write the ingest job at `src/bronze/<domain>/<table>/ingest.py`.
   - Append-only.
   - Schema enforced on read; rejected rows go to `bronze.<domain>.<table>_quarantine`.
   - Partition by `_ingested_date`.
   - Idempotent: if the job re-runs on the same source files, output is unchanged.

4. Tests at `tests/bronze/<domain>/test_<table>.py`:
   - Schema contract test (compare against checked-in schema fixture).
   - Smoke test reading 10 sample rows.
   - Idempotency test: run twice, assert row count unchanged.

5. Wire into Asset Bundle (`databricks.yml`) as a job named
   `bronze_<domain>_<table>_<cadence>`.

6. Reference `examples/bronze_ingest_example.py` for the canonical shape.

## What not to do

- Do not transform data in bronze. No casting, no renaming, no derived columns
  beyond the audit four.
- Do not silently drop rows. Quarantine them.
- Do not skip the schema fixture file. It's how we detect upstream drift.
- Do not write to prod. The pre-tool hook will block you anyway — propose
  the dev path.
