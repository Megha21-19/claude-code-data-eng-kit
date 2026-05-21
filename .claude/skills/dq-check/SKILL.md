---
name: dq-check
description: Add or run data-quality checks on a bronze, silver, or gold table — null rate, distinct count, referential integrity, distribution drift. Use when the user asks for data quality, DQ, validation, sanity checks, profiling, freshness, or drift detection on a table.
---

# dq-check

Use this skill when the user wants to add or run DQ on a table.

## When to invoke

Trigger phrases: "add DQ to X", "data quality for X", "validate X", "check X
for nulls / dupes / drift", "is X fresh", "profile X".

## DQ categories this kit supports

1. **Completeness** — null rate per column vs threshold.
2. **Uniqueness** — duplicate count on declared natural key.
3. **Referential** — foreign-key columns join cleanly to their dimension.
4. **Bounds** — numeric columns inside expected min/max.
5. **Freshness** — max `_ingested_at` within expected window.
6. **Drift** — distribution moves vs a recent baseline (PSI or KS).

## Where rules live

Rules are declarative YAML at `dq/<layer>_<table>.yml`. Example shape:

```yaml
table: silver.maintenance.workorders
natural_key: [workorder_id]
freshness:
  column: _ingested_at
  max_lag_hours: 26
completeness:
  - column: equipment_id
    max_null_rate: 0.0
  - column: status
    max_null_rate: 0.0
bounds:
  - column: cost_usd
    min: 0
    max: 1000000
referential:
  - column: equipment_id
    references: silver.assets.equipment.equipment_id
```

The DQ runner reads the YAML and emits a `dq.results` Delta table per run.

## Steps

1. Locate the rules file for the table. If absent, create one.
2. Add only rules that are *meaningful*. A null-rate check on a column that
   is naturally sparse is noise. Push back on the user if they ask for a
   blanket "check everything."
3. Run the DQ job:
   ```bash
   python -m dq.run --table silver.maintenance.workorders --env dev
   ```
4. Read the results from `dq.results` and summarize: passed / failed / warn.
5. If failures, propose remediation (a fix in the transform, a tightened
   schema, or a relaxed threshold — depending on the failure).

## What not to do

- Don't assert in pipeline code. DQ is observed, not enforced inline —
  otherwise a single bad row blows up a hourly job.
- Don't add drift checks on freshly built tables. Drift needs a baseline.
  Wait two weeks of stable runs.
- Don't write DQ logic that requires the prod warehouse. DQ runs in CI
  against dev fixtures too.
