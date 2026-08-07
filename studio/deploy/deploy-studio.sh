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
# A migration that needs an extension cannot install it: CREATE EXTENSION only
# loads a package that is already on disk, so an absent one fails the migration
# and stops the deploy. That is what happened when the element archive first
# went out, and provisioning belongs here rather than inside a migration.
#
# Idempotent, and keyed off the server's own PostgreSQL major version rather
# than a pinned one, so an upgrade of the box does not silently skip this.
PG_MAJOR=$(psql --version | grep -oE '[0-9]+' | head -1)
if [ ! -f "/usr/share/postgresql/$PG_MAJOR/extension/vector.control" ]; then
  echo "pgvector missing for PostgreSQL $PG_MAJOR; installing"
  sudo apt-get update -qq
  if ! sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      "postgresql-$PG_MAJOR-pgvector"; then
    # Older Ubuntu releases do not carry pgvector in the default archive. The
    # PostgreSQL project's own repository does, for every supported major.
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
# Fail here with a readable message rather than inside alembic's traceback.
if [ ! -f "/usr/share/postgresql/$PG_MAJOR/extension/vector.control" ]; then
  echo "pgvector is still not installed for PostgreSQL $PG_MAJOR." >&2
  echo "The element archive migration cannot run without it." >&2
  exit 1
fi

set -a && . "$ROOT/.env" && set +a

# CREATE EXTENSION requires superuser, and the application role deliberately is
# not one. So the extension is enabled here, as postgres, and the migration only
# uses it -- which is the right split anyway: provisioning is a deploy concern
# and schema is a migration concern.
DB_NAME=${DATABASE_URL##*/}
DB_NAME=${DB_NAME%%\?*}
sudo -u postgres psql -d "$DB_NAME" -qc 'CREATE EXTENSION IF NOT EXISTS vector'

say "Applying migrations"
# A controlled release step, not something the application does at startup: a
# failed migration must stop the deploy rather than crash-loop the service.
./.venv/bin/alembic upgrade head

say "Importing worlds"
# Idempotent, and it is what makes a world visible to the API at all. Only the
# directories that are actually present are imported.
for world in worlds/*/; do
  slug=$(basename "$world")
  [ -f "$world/WORLD.md" ] || continue
  ./.venv/bin/python -m app.cli import-world "$slug"
done

say "Building the interface"
if [ -d web ]; then
  ( cd web && npm install --silent && npm run build --silent )
fi

say "Restarting"
sudo systemctl restart shirtfaced-studio

say "Waiting for readiness"
# /ready fails when the database is unreachable, migrations are missing, world
# files are unreadable or assets are not writable -- so a green here means the
# deploy actually works, not merely that a process started.
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
