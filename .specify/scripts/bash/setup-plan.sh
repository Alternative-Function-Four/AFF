#!/usr/bin/env bash
set -euo pipefail
FEATURE_DIR="$(ls -d .specify/specs/[0-9]* 2>/dev/null | sort -V | tail -1 || true)"
if [ -z "$FEATURE_DIR" ]; then
  echo '{"FEATURE_SPEC":"","IMPL_PLAN":"","SPECS_DIR":"","BRANCH":""}'
  exit 0
fi
SPEC="$FEATURE_DIR/spec.md"
PLAN="$FEATURE_DIR/plan.md"
if [ ! -f "$PLAN" ]; then
  cp .specify/templates/plan-template.md "$PLAN"
fi
BRANCH="$(basename "$FEATURE_DIR")"
printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' "$(cd . && pwd)/$SPEC" "$(cd . && pwd)/$PLAN" "$(cd . && pwd)/$FEATURE_DIR" "$BRANCH"
