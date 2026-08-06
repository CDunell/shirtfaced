#!/usr/bin/env bash
#
# Adds studio.shirtfaced.wtf to the Cloudflare Tunnel's ingress.
#
# That config file is shared: it also serves tradeninja.au, orveris.com and
# cliniix. A bad edit takes those down, so this backs up first, validates the
# result with cloudflared itself, and restores the backup if validation fails.
# Idempotent -- running it twice is a no-op.
#
set -euo pipefail

CONFIG=/etc/cloudflared/config.yml
HOSTNAME=studio.shirtfaced.wtf
ENV_FILE=/home/ubuntu/shirtfaced-studio/.env

PORT=$(sed -n 's/^APP_PORT=//p' "$ENV_FILE" | head -1)
if [ -z "$PORT" ]; then
  echo "APP_PORT is not set in $ENV_FILE; refusing to guess." >&2
  exit 1
fi

if sudo grep -q "hostname: $HOSTNAME" "$CONFIG"; then
  echo "$HOSTNAME is already in the ingress. Nothing to do."
  exit 0
fi

BACKUP="$CONFIG.bak.$(date +%Y%m%d-%H%M%S)"
sudo cp "$CONFIG" "$BACKUP"
echo "Backed up to $BACKUP"

# The rule goes immediately before the catch-all. Ingress rules are evaluated in
# order and the catch-all matches everything, so anything after it is dead.
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
sudo awk -v host="$HOSTNAME" -v port="$PORT" '
  !done && /^[[:space:]]*-[[:space:]]*service:[[:space:]]*http_status:404/ {
    printf "  - hostname: %s\n    service: http://localhost:%s\n", host, port
    done = 1
  }
  { print }
  END { if (!done) exit 3 }
' "$CONFIG" > "$tmp" || {
  echo "No catch-all rule found in $CONFIG; refusing to guess where to insert." >&2
  exit 1
}

sudo cp "$tmp" "$CONFIG"

echo "Validating"
if ! sudo cloudflared tunnel ingress validate --config "$CONFIG"; then
  echo "Validation failed. Restoring $BACKUP and changing nothing." >&2
  sudo cp "$BACKUP" "$CONFIG"
  exit 1
fi

echo "Reloading cloudflared"
sudo systemctl restart cloudflared
sleep 3
if ! systemctl is-active --quiet cloudflared; then
  echo "cloudflared did not come back. Restoring $BACKUP." >&2
  sudo cp "$BACKUP" "$CONFIG"
  sudo systemctl restart cloudflared
  exit 1
fi

echo "Done. $HOSTNAME -> http://localhost:$PORT"
echo
echo "Still needed, and only doable in the Cloudflare dashboard:"
echo "  1. A proxied CNAME: studio -> \$TUNNEL_ID.cfargotunnel.com"
echo "  2. An Access policy over $HOSTNAME. Studio has no login of its own and"
echo "     its generate endpoint spends money, so until that policy exists the"
echo "     record above should not be created."
