#!/usr/bin/env bash
set -euo pipefail

GUARD_FILE="AI_GUARD_PATCH_STRICT.txt"

if [[ ! -f "$GUARD_FILE" ]]; then
  echo "ERROR: Guard file not found: $GUARD_FILE" >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  echo "Usage: ./ai_prompt.sh \"<your prompt here>\"" >&2
  exit 1
fi

USER_PROMPT="$*"

cat <<EOF
$(cat "$GUARD_FILE")

-----
PROMPT UTILISATEUR :
$USER_PROMPT
