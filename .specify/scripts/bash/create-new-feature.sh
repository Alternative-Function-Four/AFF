#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "usage: $0 [--json] <feature-name>" >&2
  exit 1
fi
JSON=false
if [ "$1" = "--json" ]; then
  JSON=true
  shift
fi
NAME="$1"
SLUG="$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')"
LAST="$(ls -d .specify/specs/[0-9]* 2>/dev/null | sed -E 's#.*/([0-9]{3})-.*#\1#' | sort -V | tail -1 || echo 000)"
NEXT="$(printf '%03d' $((10#$LAST + 1)))"
BRANCH_NAME="${NEXT}-${SLUG}"
FEATURE_DIR=".specify/specs/${BRANCH_NAME}"
mkdir -p "$FEATURE_DIR"
SPEC_FILE="$FEATURE_DIR/spec.md"
cp .specify/templates/spec-template.md "$SPEC_FILE"
if [ "$JSON" = true ]; then
  printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s"}\n' "$BRANCH_NAME" "$(cd . && pwd)/$SPEC_FILE"
else
  echo "$BRANCH_NAME $SPEC_FILE"
fi
