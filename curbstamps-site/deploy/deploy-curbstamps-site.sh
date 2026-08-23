#!/usr/bin/env bash
# Runs ON THE BOX, called by .github/workflows/deploy.yml's "Build and
# restart curbstamps-site" step, right after rsync has synced this directory
# to /home/ubuntu/curbstamps-site. Requires the one-time setup in
# docs/curbstamps/CURBSTAMPS_DEPLOYMENT.md (systemd unit installed, .env
# present) to already exist — this script builds and restarts, it doesn't
# provision a service from nothing.
set -euo pipefail
cd /home/ubuntu/curbstamps-site

npm ci
# Next.js reuses .next/cache across builds by default for incremental
# builds — that's exactly what makes ISR/static route output (including
# the homepage) survive indefinitely across deploys unless cleared here.
# Confirmed live: the homepage kept serving a stale cached render
# referencing an old creature asset version well after the underlying
# files had already been updated and redeployed.
rm -rf .next
npm run build
sudo systemctl restart curbstamps-site
sudo systemctl --no-pager status curbstamps-site
