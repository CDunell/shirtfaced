#!/usr/bin/env bash
#
# Runs on the Oracle box on every deploy, after CI has synced the code.
# Bootstrap has already guaranteed the venv's prerequisites, the database, .env
# and the systemd unit.
#
set -euo pipefail

ROOT=/home/ubuntu/shirtfaced-studio
cd "$ROOT"

say() { printf '\n== %s\n' "$1"; }

say "Installing dependencies"
PYTHON=$(command -v python3.12 || command -v python3)
[ -d .venv ] || "$PYTHON" -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -e .

say "Ensuring database extensions"
PG_MAJOR=$(psql --version | grep -oE '[0-9]+' | head -1)
if [ ! -f "/usr/share/postgresql/$PG_MAJOR/extension/vector.control" ]; then
  echo "pgvector missing for PostgreSQL $PG_MAJOR; installing"
  sudo apt-get update -qq
  if ! sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      "postgresql-$PG_MAJOR-pgvector"; then
    echo "Not in the default archive; adding the PostgreSQL APT repository"
    sudo apt-get install -y -qq curl ca-certificates gnupg lsb-release
    sudo install -d /usr/share/postgresql-common/pgdg
    sudo curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
      https://www.postgresql.org/media/keys/ACCC4CF8.asc
    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc]" \
      "https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
      | sudo tee /etc/apt/sources.list.d/pgdg.list >/dev/null
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      "postgresql-$PG_MAJOR-pgvector"
  fi
fi
if [ ! -f "/usr/share/postgresql/$PG_MAJOR/extension/vector.control" ]; then
  echo "pgvector is still not installed for PostgreSQL $PG_MAJOR." >&2
  echo "The element archive migration cannot run without it." >&2
  exit 1
fi

set -a && . "$ROOT/.env" && set +a

DB_NAME=${DATABASE_URL##*/}
DB_NAME=${DB_NAME%%\?*}
sudo -u postgres psql -d "$DB_NAME" -qc 'CREATE EXTENSION IF NOT EXISTS vector'

say "Applying migrations"
./.venv/bin/alembic upgrade head

say "Importing worlds"
for world in worlds/*/; do
  slug=$(basename "$world")
  [ -f "$world/WORLD.md" ] || continue
  ./.venv/bin/python -m app.cli import-world "$slug"
done

say "Syncing the element archive"
./.venv/bin/python -m app.cli sync-archive

say "Checking Social render assets"
# Production Social rendering uses rasterized PNGs. SVGs remain alongside them as
# editable/source assets, but GO must not depend on browser SVG rasterisation.
SOCIAL_ROOT="$ROOT/public/social-assets/v3"
required_social_assets=(
  light-corner-mark-4x5.png
  dark-corner-mark-4x5.png
  adaptive-corner-mark-4x5.png
  light-feed-4x5.png
  dark-feed-4x5.png
  adaptive-feed-badge-4x5.png
  light-title-bug-9x16.png
  dark-title-bug-9x16.png
  light-reel-9x16.png
  dark-reel-9x16.png
  adaptive-reel-badge-9x16.png
)
for asset in "${required_social_assets[@]}"; do
  if [ ! -s "$SOCIAL_ROOT/$asset" ]; then
    echo "Missing rasterized Social render asset: $SOCIAL_ROOT/$asset" >&2
    exit 1
  fi
done

say "Building the interface"
if [ -d web ]; then
  ( cd web && npm install --silent && npm run build --silent )

  # SocialBench source names the canonical SVG overlays. Production swaps those
  # references to the rasterized PNG twins before the bundle is served. This keeps
  # source/editing assets vector while making canvas composition deterministic on
  # Android/WebView. A unique query string also prevents stale image-cache reuse.
  SOCIAL_ASSET_VERSION=$(date +%s)
  find web/dist -type f -name '*.js' -print0 | xargs -0 sed -i \
    -E "s#(/social-assets/v3/[^\"']+)\.svg#\1.png?v=${SOCIAL_ASSET_VERSION}#g"

  if grep -R -E -q "/social-assets/v3/[^\"']+\.svg" web/dist; then
    echo "Built Studio still contains a Social SVG runtime reference." >&2
    exit 1
  fi
  if ! grep -R -E -q "/social-assets/v3/[^\"']+\.png\?v=" web/dist; then
    echo "Built Studio contains no versioned Social PNG runtime references." >&2
    exit 1
  fi
fi

say "Restarting"
sudo systemctl restart shirtfaced-studio

say "Waiting for readiness"
PORT=${APP_PORT:-8010}
for attempt in $(seq 1 30); do
  if curl -fsS -m 5 "http://127.0.0.1:$PORT/ready" >/dev/null 2>&1; then
    echo "Studio is ready on 127.0.0.1:$PORT."
    exit 0
  fi
  sleep 2
done

echo "Studio did not become ready on port $PORT. Holding that port:" >&2
ss -ltnp "sport = :$PORT" 2>/dev/null >&2 || true
echo "Recent logs:" >&2
sudo journalctl -u shirtfaced-studio -n 40 --no-pager >&2
exit 1
