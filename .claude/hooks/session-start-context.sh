#!/usr/bin/env bash
# .claude/hooks/session-start-context.sh
#
# Runs once at session start. Injects useful project context that the model
# would otherwise have to fish for: current branch, recent commits, dirty files,
# and a one-line CI status if available.
#
# Returns a JSON object with `additionalContext` — Claude Code wraps it in a
# system reminder and inserts it into the conversation.

set -uo pipefail

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
COMMITS=$(git log --oneline -5 2>/dev/null || echo "no git history")
DIRTY=$(git status --porcelain 2>/dev/null | head -10)

CONTEXT=$(cat <<EOF
Project: claude-code-data-eng-kit
Branch: $BRANCH

Recent commits:
$COMMITS

Uncommitted files (truncated):
${DIRTY:-(clean)}

Reminder: this repo follows medallion conventions. See CLAUDE.md and .claude/rules/
before writing PySpark. Run /ship-checklist before opening a PR.
EOF
)

# Hook output schema: print a JSON object on stdout.
jq -n --arg ctx "$CONTEXT" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx
  }
}'

exit 0
