#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/home/ubuntu/shirtfaced-studio
ENV_FILE="$APP_DIR/.env"
read -r KEY

if [[ -z "$KEY" ]]; then
  echo "Refusing to write an empty GEMINI_API_KEY" >&2
  exit 1
fi

sudo install -o ubuntu -g ubuntu -m 600 /dev/null "$ENV_FILE.tmp"
if [[ -f "$ENV_FILE" ]]; then
  grep -v -E '^(GEMINI_API_KEY|GOOGLE_MEDIA_ENABLED)=' "$ENV_FILE" > "$ENV_FILE.tmp" || true
fi
printf 'GEMINI_API_KEY=%s\n' "$KEY" >> "$ENV_FILE.tmp"
printf 'GOOGLE_MEDIA_ENABLED=true\n' >> "$ENV_FILE.tmp"
mv "$ENV_FILE.tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo "Gemini key installed and Google media enabled."
