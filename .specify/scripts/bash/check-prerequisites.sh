#!/usr/bin/env bash
set -euo pipefail
FEATURE_DIR="$(ls -d .specify/specs/[0-9]* 2>/dev/null | sort -V | tail -1 || true)"
if [ -z "$FEATURE_DIR" ]; then
  echo '{"FEATURE_DIR":"","AVAILABLE_DOCS":[]}'
  exit 0
fi
DOCS=()
for file in spec.md plan.md data-model.md tasks.md; do
  if [ -f "$FEATURE_DIR/$file" ]; then
    DOCS+=("\"$file\"")
  fi
done
printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":[%s]}\n' "$FEATURE_DIR" "$(IFS=,; echo "${DOCS[*]}")"
