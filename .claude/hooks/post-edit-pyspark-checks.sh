#!/usr/bin/env bash
# .claude/hooks/post-edit-pyspark-checks.sh
#
# Runs after Claude edits a Python file. Lints, type-checks, and runs the
# narrow test suite for the layer touched. Failures are written to stderr;
# Claude sees them and can self-correct in the next turn.
#
# Exit 0 always — we want feedback, not blocking. (Blocking belongs in
# pre-tool hooks where the action hasn't happened yet.)

set -uo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')

# Only act on .py files inside the source tree
if [[ "$FILE_PATH" != *.py ]]; then exit 0; fi
if [[ "$FILE_PATH" != *src/* ]] && [[ "$FILE_PATH" != *tests/* ]] && [[ "$FILE_PATH" != *examples/* ]]; then
  exit 0
fi

ISSUES=()

# Lint
if command -v ruff >/dev/null 2>&1; then
  if ! ruff check "$FILE_PATH" >/tmp/ruff.out 2>&1; then
    ISSUES+=("ruff:" "$(cat /tmp/ruff.out)")
  fi
fi

# Type check
if command -v pyright >/dev/null 2>&1; then
  if ! pyright "$FILE_PATH" >/tmp/pyright.out 2>&1; then
    ISSUES+=("pyright:" "$(cat /tmp/pyright.out)")
  fi
fi

# Narrow tests: figure out which layer this file belongs to and run those
LAYER=""
if [[ "$FILE_PATH" == *src/bronze/* ]]; then LAYER="bronze";
elif [[ "$FILE_PATH" == *src/silver/* ]]; then LAYER="silver";
elif [[ "$FILE_PATH" == *src/gold/*   ]]; then LAYER="gold";
fi

if [[ -n "$LAYER" ]] && command -v pytest >/dev/null 2>&1; then
  if ! pytest -x --tb=line "tests/$LAYER/" >/tmp/pytest.out 2>&1; then
    ISSUES+=("pytest($LAYER):" "$(tail -30 /tmp/pytest.out)")
  fi
fi

if [[ ${#ISSUES[@]} -gt 0 ]]; then
  echo "post-edit checks reported issues for $FILE_PATH:" >&2
  printf '%s\n' "${ISSUES[@]}" >&2
fi

exit 0
