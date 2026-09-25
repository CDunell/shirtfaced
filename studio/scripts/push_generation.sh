#!/usr/bin/env bash
# Push one locally-generated design image into Studio's review queue.
#
# Usage:
#   scripts/push_generation.sh <image_path> <tradition> <batch> <concept_text> <prompt_text>
#
# Runs from wherever the image was generated and downloaded -- a session
# driving a real ChatGPT/Gemini login, not the box itself. Copies the image
# plus the concept/prompt text up over SSH, then runs the same insert on
# the box that POST /api/design/generations would, so the row it creates is
# indistinguishable either way. Replaces the hand-typed multi-line python
# heredoc a batch run used to need per image.
#
# Requires SHIRTFACED_BOX_HOST (e.g. "ubuntu@<box-ip>") and, unless the key
# lives at the default path, SHIRTFACED_SSH_KEY. Neither is hardcoded here
# on purpose -- the box's address is exactly what deploy.yml keeps as a
# GitHub secret rather than committing, and this script holds to the same
# rule.
set -euo pipefail

if [ "$#" -ne 5 ]; then
  echo "Usage: $0 <image_path> <tradition> <batch> <concept_text> <prompt_text>" >&2
  exit 1
fi

IMAGE_PATH="$1"
TRADITION="$2"
BATCH="$3"
CONCEPT_TEXT="$4"
PROMPT_TEXT="$5"

if [ -z "${SHIRTFACED_BOX_HOST:-}" ]; then
  echo "SHIRTFACED_BOX_HOST is not set (e.g. export SHIRTFACED_BOX_HOST=ubuntu@<box-ip>)." >&2
  exit 1
fi

SSH_KEY="${SHIRTFACED_SSH_KEY:-$HOME/.ssh/shirtfaced_box}"
REMOTE_DIR="/home/ubuntu/shirtfaced-studio"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cp "$IMAGE_PATH" "$TMP/image.png"
printf '%s' "$CONCEPT_TEXT" > "$TMP/concept.txt"
printf '%s' "$PROMPT_TEXT" > "$TMP/prompt.txt"

REMOTE_TMP="/tmp/gen-$(date +%s)-$$"
ssh -i "$SSH_KEY" -o BatchMode=yes "$SHIRTFACED_BOX_HOST" "mkdir -p $REMOTE_TMP"
scp -i "$SSH_KEY" -o BatchMode=yes "$TMP"/image.png "$TMP"/concept.txt "$TMP"/prompt.txt \
  "$SHIRTFACED_BOX_HOST:$REMOTE_TMP/"

ssh -i "$SSH_KEY" -o BatchMode=yes "$SHIRTFACED_BOX_HOST" "
  set -e
  cd '$REMOTE_DIR'
  .venv/bin/python scripts/ingest_local_image.py \
    '$REMOTE_TMP/image.png' '$TRADITION' '$BATCH' '$REMOTE_TMP/concept.txt' '$REMOTE_TMP/prompt.txt'
  rm -rf '$REMOTE_TMP'
"
