---
name: promote-to-silver
description: Promote a bronze table to a silver table — typed, conformed, deduped, with SCD2 history when applicable. Use when the user asks to promote, conform, clean, type-cast, dedupe, or build silver from an existing bronze table.
---

# promote-to-silver

Use this skill when the user wants to build (or rebuild) a silver table from an
existing bronze table.

## When to invoke

Trigger phrases: "promote bronze.X to silver", "build the silver table for X",
"conform X to silver", "dedupe and type-cast X".

## Pre-checks

1. Confirm the bronze source exists and has recent successful runs
   (use `databricks-mini` MCP `get_job_runs` if available).
2. Confirm the silver target name. Convention: `silver.<domain>.<table>`,
   snake_case, English, canonical names.
3. Identify the natural key. Required.
4. Identify whether this is Type 1 (overwrite latest) or Type 2 (history-tracked).
   Default Type 2 unless the user downgrades it explicitly.

## Steps

1. **Schema mapping**. Create `src/silver/<domain>/<table>/schema.py` with the
   canonical schema and a `BRONZE_TO_SILVER_MAP` dict documenting every rename
   and type coercion. No magic renames — they're audited.

2. **Transform job** at `src/silver/<domain>/<table>/transform.py`:
   - Read latest bronze partition.
   - Apply renames and casts. Fail loudly on cast errors (do not coalesce to null).
   - Deduplicate on natural key, keeping the latest by `_ingested_at`.
   - For SCD2: compute `effective_from`, `effective_to`, `is_current`.
   - Merge into silver target with explicit conditions.

3. **Tests** at `tests/silver/<domain>/test_<table>.py`:
   - Unit test the transform on a small fixture.
   - SCD2 history test: insert a row, modify it, assert two versions exist
     and only one has `is_current=true`.
   - Type contract test against the silver schema fixture.

4. **DQ rules** registered in `dq/silver_<table>.yml`:
   - Natural key not null, not duplicated.
   - Required columns not null.
   - Reasonable bounds on numeric columns (min/max).
   - Run via the `dq-check` skill, not inline assertions.

5. Wire into Asset Bundle as `silver_<domain>_<table>_<cadence>`,
   with the bronze job as a task dependency.

## Reference

See `examples/silver_transform_example.py` for the canonical shape.

## What not to do

- Don't dedupe by `dropDuplicates()` without ordering. You'll get
  non-deterministic results.
- Don't cast with `try_cast` to "be safe". Bad data should be visible.
- Don't write to gold from silver code. Layer separation is enforced by
  module boundaries; respect it.
