# Project conventions

This is a PySpark / Databricks lakehouse repo using a medallion architecture
(bronze → silver → gold). Read this on every session.

## Non-negotiables

- **Never write to paths matching `**/prod/**`** without explicit human approval
  in chat. The pre-tool hook will block it; do not try to route around it.
- **No `dbutils.fs.rm`, no `DROP TABLE`, no `TRUNCATE`** in any code you author.
  If a destructive op is genuinely required, propose it in chat; a human runs it.
- **Idempotency is required** in every job. Re-running yesterday's job must
  produce yesterday's output, not a duplicate.
- **No secrets in code.** Use `dbutils.secrets.get(scope, key)` or env vars.

## What "good" looks like here

- PySpark over pandas for anything that touches Delta tables.
- Delta merge with explicit `whenMatchedUpdateAll` / `whenNotMatchedInsertAll`,
  not blind overwrites.
- Bronze keeps raw shape; silver applies schema; gold is read-optimized.
- Tests live in `tests/`, mirror the source tree, and run in CI on every PR.

## When in doubt

- For PySpark idioms, see `.claude/rules/pyspark.md` (auto-loads in `src/**/*.py`).
- For medallion structure, see `.claude/rules/medallion.md`.
- For repeatable workflows, check available skills: `new-bronze-ingest`,
  `promote-to-silver`, `dq-check`, `prompt-eval`.
- Before opening a PR, run `/ship-checklist`.

## Tooling

- Python 3.11, PySpark 3.5, Delta 3.x.
- `ruff` for lint, `pyright` for types, `pytest` for tests.
- CI is Azure DevOps Pipelines (`azure-pipelines.yml` at repo root).
- Databricks runs are orchestrated via Asset Bundles (`databricks.yml`).
