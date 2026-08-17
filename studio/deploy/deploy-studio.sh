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

say "Importing complete worlds"
for world in worlds/*/; do
  slug=$(basename "$world")
  missing=()
  for document in WORLD.md CONTINUITY.md SHOTLIST.md; do
    [ -f "$world/$document" ] || missing+=("$document")
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    echo "Skipping draft world $slug; missing: ${missing[*]}"
    continue
  fi
  ./.venv/bin/python -m app.cli import-world "$slug"
done

say "Importing the cast into the Visual Asset Library"
# Idempotent, and identified by the SHA of the bytes: a re-run re-links what is
# already there. var/ is excluded from the deploy rsync, so this reads whatever
# cast the box itself holds, not whatever was in the repository.
if [ -d var/cast ]; then
  ./.venv/bin/python -m app.cli ingest-cast
else
  echo "No var/cast on this host; skipping."
fi

say "Syncing the element archive"
./.venv/bin/python -m app.cli sync-archive

say "Importing design concepts"
if [ -f docs/design/TSHIRT_CONCEPT_LIBRARY.md ]; then
  ./.venv/bin/python -m app.cli import-design-concepts docs/design/TSHIRT_CONCEPT_LIBRARY.md
else
  echo "No concept library synced; skipping."
fi

say "Checking Social render assets"
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
  SOCIAL_ASSET_VERSION=$(date +%s)
  sed -i -E \
    "s#(/social-assets/v3/[^\"'\x60]+)\.svg#\1.png?v=${SOCIAL_ASSET_VERSION}#g" \
    web/src/components/SocialBench.tsx

  if grep -E -q "/social-assets/v3/[^\"'\x60]+\.svg" web/src/components/SocialBench.tsx; then
    echo "SocialBench still contains a Social SVG runtime reference before build." >&2
    exit 1
  fi
  if ! grep -E -q "/social-assets/v3/.*\.png\?v=" web/src/components/SocialBench.tsx; then
    echo "SocialBench contains no versioned Social PNG runtime references before build." >&2
    exit 1
  fi

  ( cd web && npm install --silent && npm run build --silent )
fi

mkdir -p /home/ubuntu/shirtfaced-research/vintage-agents \
  /home/ubuntu/shirtfaced-research/vintage-agent-outbox \
  /home/ubuntu/shirtfaced-research/vintage-ebay-images

# Collectors import Playwright from this directory. Stop them before npm touches
# node_modules; replacing dependencies under a live worker corrupts its runtime.
enabled_vintage_agents=()
for agent_id in 1 2 3 4; do
  agent_dir="/home/ubuntu/shirtfaced-research/vintage-agents/agent-$agent_id"
  [ -f "$agent_dir/enabled" ] || continue
  enabled_vintage_agents+=("$agent_id")
  pid=$(python3 -c "import json; print(json.load(open('$agent_dir/pid.json')).get('pid',''))" 2>/dev/null || true)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  fi
done
vintage_recovery_marker=/home/ubuntu/shirtfaced-research/vintage-agents/.sold-evidence-html-v4
if [ ! -f "$vintage_recovery_marker" ]; then
  # The broken runtime marked the original pool attempted without collecting a
  # record. Run every shard once on the repaired runtime to recover that work.
  enabled_vintage_agents=(1 2 3 4)
fi

say "Installing vintage agent Chromium runtime"
if [ -d "$ROOT/worker_scripts" ]; then
  (
    cd "$ROOT/worker_scripts"
    npm install --silent
    node -e "import('playwright').then(p => { if (!p.chromium) process.exit(1) })"
    sudo npx playwright install-deps chromium >/dev/null
    npx playwright install chromium >/dev/null
  )
fi

say "Installing Social publisher timer"
sudo install -m 0644 "$ROOT/deploy/shirtfaced-social-publisher.service" /etc/systemd/system/shirtfaced-social-publisher.service
sudo install -m 0644 "$ROOT/deploy/shirtfaced-social-publisher.timer" /etc/systemd/system/shirtfaced-social-publisher.timer
sudo systemctl daemon-reload
sudo systemctl enable --now shirtfaced-social-publisher.timer

say "Restarting"
sudo systemctl restart shirtfaced-studio

say "Waiting for readiness"
PORT=${APP_PORT:-8010}
for attempt in $(seq 1 30); do
  if curl -fsS -m 5 "http://127.0.0.1:$PORT/ready" >/dev/null 2>&1; then
    echo "Studio is ready on 127.0.0.1:$PORT."
    for agent_id in "${enabled_vintage_agents[@]}"; do
      ./.venv/bin/python -c \
        "from app.services.vintage_agents import set_enabled; set_enabled($agent_id, True)"
      echo "Restarted vintage Agent $agent_id on the current worker script."
    done
    touch "$vintage_recovery_marker"
    exit 0
  fi
  sleep 2
done

echo "Studio did not become ready on port $PORT. Holding that port:" >&2
ss -ltnp "sport = :$PORT" 2>/dev/null >&2 || true
echo "Recent logs:" >&2
sudo journalctl -u shirtfaced-studio -n 40 --no-pager >&2
exit 1
