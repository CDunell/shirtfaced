#!/usr/bin/env bash
#
# Reads an OpenAI key on stdin and writes it into Studio's .env, but only into an
# empty slot.
#
# Two rules, both learned the expensive way:
#   - stdin, never an argument, so the key is not in the box's process list.
#   - never replace a key that is already there. A deploy running without the
#     secret configured must not be able to blank a working key.
#
set -euo pipefail

ENV_FILE=/home/ubuntu/shirtfaced-studio/.env

read -r key
if [ -z "$key" ]; then
  echo "No key on stdin; nothing to do."
  exit 0
fi

if ! grep -q '^OPENAI_API_KEY=$' "$ENV_FILE"; then
  echo "A key is already set; left alone."
  exit 0
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
while IFS= read -r line; do
  if [ "$line" = "OPENAI_API_KEY=" ]; then
    printf 'OPENAI_API_KEY=%s\n' "$key"
  else
    printf '%s\n' "$line"
  fi
done < "$ENV_FILE" > "$tmp"

cat "$tmp" > "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo "Key placed."
