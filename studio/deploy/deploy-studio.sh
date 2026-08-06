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

say "Applying migrations"
# A controlled release step, not something the application does at startup: a
# failed migration must stop the deploy rather than crash-loop the service.
set -a && . "$ROOT/.env" && set +a
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
for attempt in $(seq 1 30); do
  if curl -fsS -m 5 http://127.0.0.1:8000/ready >/dev/null 2>&1; then
    echo "Studio is ready."
    exit 0
  fi
  sleep 2
done

echo "Studio did not become ready. Recent logs:" >&2
sudo journalctl -u shirtfaced-studio -n 40 --no-pager >&2
exit 1
