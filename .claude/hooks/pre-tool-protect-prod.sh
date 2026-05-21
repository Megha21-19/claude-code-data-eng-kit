#!/usr/bin/env bash
# .claude/hooks/pre-tool-protect-prod.sh
#
# Blocks any tool call that would write to a prod path or run a prod-targeted
# Databricks command. This is the enforcement layer — CLAUDE.md is advisory,
# this script is the actual gate.
#
# Exit code 2 = block (Claude sees the message and cannot proceed with this call).
# Exit code 0 = allow.

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}')

block() {
  # Message on stderr; exit 2 surfaces it back to Claude.
  echo "BLOCKED by pre-tool-protect-prod: $1" >&2
  exit 2
}

case "$TOOL_NAME" in
  Write|Edit|MultiEdit)
    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // .path // empty')
    if [[ "$FILE_PATH" == *"/prod/"* ]] || [[ "$FILE_PATH" == */prod/* ]]; then
      block "write to prod path: $FILE_PATH. Propose a dev/ path or get human approval in chat first."
    fi
    ;;
  Bash)
    CMD=$(echo "$TOOL_INPUT" | jq -r '.command // empty')
    # Block any Databricks CLI that targets prod
    if echo "$CMD" | grep -qE -- '--target[= ]+prod|--env[= ]+prod|--profile[= ]+prod'; then
      block "Databricks command targets prod: $CMD"
    fi
    # Block destructive ops anywhere
    if echo "$CMD" | grep -qE 'dbutils\.fs\.rm|DROP +TABLE|TRUNCATE +TABLE|databricks +workspace +delete'; then
      block "destructive command not allowed from agent: $CMD"
    fi
    ;;
esac

exit 0
