#!/usr/bin/env bash
#
# One-time setup for Shirtfaced Studio on the Oracle box. Idempotent: every step
# checks before it acts, so running it on each deploy is safe and it can be re-run
# after a partial failure.
#
# What it deliberately does NOT do:
#   - overwrite .env once it exists. The OpenAI key and the database password live
#     there and nowhere else, and CI must never be able to clobber them.
#   - touch studio/worlds. Studio writes canon there at runtime, so the box owns
#     that directory and the deploy rsync excludes it.
#
set -euo pipefail

ROOT=/home/ubuntu/shirtfaced-studio
ENV_FILE="$ROOT/.env"
DB_NAME=shirtfaced_studio
DB_USER=shirtfaced_studio

say() { printf '\n== %s\n' "$1"; }

say "Checking Python"
# Studio requires 3.12. Ubuntu 24.04 ships it; anything older needs it installed
# before this script can do anything useful, and guessing is worse than stopping.
PYTHON=$(command -v python3.12 || command -v python3)
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Studio needs Python 3.12 or newer. Found: $("$PYTHON" --version)" >&2
  echo "Install it (apt install python3.12 python3.12-venv) and re-run." >&2
  exit 1
fi
echo "Using $PYTHON ($("$PYTHON" --version))"

say "Ensuring the venv module and PostgreSQL are present"
NEEDED=()
"$PYTHON" -c 'import venv' 2>/dev/null || NEEDED+=("$(basename "$PYTHON")-venv")
command -v psql >/dev/null 2>&1 || NEEDED+=(postgresql)
if [ ${#NEEDED[@]} -gt 0 ]; then
  echo "Installing: ${NEEDED[*]}"
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${NEEDED[@]}"
fi
sudo systemctl enable --now postgresql

say "Ensuring the database role and database exist"
# A password is generated once and only ever read back out of .env, so re-running
# this script cannot silently change the credentials the service is using.
if [ -f "$ENV_FILE" ] && grep -q '^DATABASE_URL=' "$ENV_FILE"; then
  echo "DATABASE_URL already set; leaving the role and database alone."
else
  DB_PASSWORD=$(openssl rand -hex 24)
  if sudo -u postgres psql -tAc "select 1 from pg_roles where rolname='$DB_USER'" | grep -q 1; then
    sudo -u postgres psql -qc "alter role $DB_USER with login password '$DB_PASSWORD'"
  else
    sudo -u postgres psql -qc "create role $DB_USER with login password '$DB_PASSWORD'"
  fi
  if ! sudo -u postgres psql -tAc "select 1 from pg_database where datname='$DB_NAME'" | grep -q 1; then
    sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
  fi
  # The driver has to be named. Studio rejects a bare postgresql:// URL rather
  # than let SQLAlchemy silently pick psycopg2.
  NEW_DATABASE_URL="postgresql+psycopg://$DB_USER:$DB_PASSWORD@127.0.0.1:5432/$DB_NAME"
fi

say "Ensuring .env exists"
if [ ! -f "$ENV_FILE" ]; then
  # Written once. Later deploys leave it alone; the key is placed by the workflow
  # only when the file has no real one yet.
  cat > "$ENV_FILE" <<ENVEOF
# Written by bootstrap-studio.sh. Not synced from CI, and never overwritten.
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=gpt-5.5
OPENAI_REVIEW_MODEL=gpt-4o-mini
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_SIZE=1536x1024
OPENAI_IMAGE_QUALITY=high
OPENAI_TIMEOUT_SECONDS=300

DATABASE_URL=$NEW_DATABASE_URL
DB_SSLMODE=disable

WORLDS_ROOT=$ROOT/worlds
ASSETS_ROOT=$ROOT/assets
WEB_DIST_ROOT=$ROOT/web/dist

# Studio commits canon changes into this checkout. Nothing pushes them; that is
# a deliberate human step.
GIT_ENABLED=true

APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=false
ENVEOF
  chmod 600 "$ENV_FILE"
  echo "Wrote $ENV_FILE"
else
  echo "$ENV_FILE already exists; leaving it untouched."
fi

say "Checking the database URL names its driver"
# An earlier bootstrap wrote a bare postgresql:// URL, which Studio refuses at
# startup. .env is never replaced wholesale, so the repair is done in place.
if grep -q '^DATABASE_URL=postgresql://' "$ENV_FILE"; then
  sed -i 's|^DATABASE_URL=postgresql://|DATABASE_URL=postgresql+psycopg://|' "$ENV_FILE"
  echo "Rewrote DATABASE_URL to name the psycopg 3 driver."
else
  echo "Already correct."
fi

say "Ensuring the assets directory exists"
mkdir -p "$ROOT/assets"

say "Ensuring worlds/ is a git checkout Studio can commit into"
# Studio's git store commits canon documents after an approval. Without a repo
# here those commits fail and the change is flagged uncommitted -- the documents
# survive, but the history does not.
if [ ! -d "$ROOT/.git" ]; then
  git -C "$ROOT" init -q
  git -C "$ROOT" config user.email "studio@shirtfaced.wtf"
  git -C "$ROOT" config user.name "Shirtfaced Studio"
  git -C "$ROOT" add -A worlds 2>/dev/null || true
  git -C "$ROOT" commit -qm "Canon as deployed" 2>/dev/null || true
  echo "Initialised a local repository for canon history."
fi

say "Installing the systemd unit"
sudo cp "$ROOT/deploy/shirtfaced-studio.service" /etc/systemd/system/shirtfaced-studio.service
sudo systemctl daemon-reload
sudo systemctl enable shirtfaced-studio

say "Pointing admin at Studio"
# Admin calls Studio server-side over loopback. Without this the Prompts page
# falls back to STUDIO_URL, which is a public hostname that does not resolve.
ADMIN_ENV=/home/ubuntu/shirtfaced-admin/.env
if [ -f "$ADMIN_ENV" ] && ! grep -q '^STUDIO_API_URL=' "$ADMIN_ENV"; then
  echo 'STUDIO_API_URL=http://127.0.0.1:8000' >> "$ADMIN_ENV"
  echo "Added STUDIO_API_URL to $ADMIN_ENV"
  sudo systemctl restart shirtfaced-admin || true
else
  echo "STUDIO_API_URL already present, or admin is not installed here."
fi

say "Bootstrap complete"
