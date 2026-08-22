#!/usr/bin/env bash
# Runs ON THE BOX, called by .github/workflows/deploy.yml's "Build and
# restart curbstamps-admin app" step, right after rsync has synced this
# directory to /home/ubuntu/curbstamps-admin. Requires the one-time setup in
# docs/curbstamps/CURBSTAMPS_DEPLOYMENT.md (systemd unit installed, .env
# present) to already exist — this script builds and restarts, it doesn't
# provision a service from nothing.
set -euo pipefail
cd /home/ubuntu/curbstamps-admin

npm ci
npm run build
sudo systemctl restart curbstamps-admin
sudo systemctl --no-pager status curbstamps-admin
