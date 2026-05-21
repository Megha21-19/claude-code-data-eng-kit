---
description: Pre-PR checklist for any pipeline change. Runs reviewer + cost-watchdog sub-agents, then summarizes.
argument-hint: "[optional: path or table name to focus on]"
---

# /ship-checklist

You are running the pre-PR checklist for this data-engineering repo. The user
is about to open a PR and wants a final sweep.

## Run these steps in order

1. **Diff sanity**. Run `git diff --stat origin/main...HEAD` and summarize
   what's changing (files, lines, layers touched).

2. **Spawn the `pipeline-reviewer` sub-agent** with the diff and the focused
   path/table from `$ARGUMENTS` if provided. Wait for it to return.

3. **Spawn the `cost-watchdog` sub-agent** in parallel with the diff. Wait
   for it to return.

4. **Run lint + tests locally**:
   - `ruff check .`
   - `pyright src/`
   - `pytest -x --tb=short`

5. **Schema fixtures** — for any table touched in the diff, verify the
   schema fixture in `tests/schema/` is up to date.

6. **DQ rules** — if a silver or gold table was touched, confirm a DQ rules
   file exists at `dq/<layer>_<table>.yml`.

## Output

A markdown summary with three sections:
- **Ready to ship** — green checks.
- **Fix before ship** — blocking issues (failing tests, missing fixtures,
  reviewer or watchdog flagged something critical).
- **Consider** — non-blocking suggestions from the sub-agents.

Do not open the PR. The human does that after reading your report.
