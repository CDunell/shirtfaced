# Curb Stamps — deploy handover

For a session that actually has what this one doesn't: SSH access to the
Oracle box and/or Cloudflare dashboard/API access. Everything code-side is
already built and pushed; what's left is infrastructure that needs real
credentials this cloud session was never going to have.

Repo: `CDunell/shirtfaced`, branch `claude/curb-stamps-kids-shop-sas8gu`.

## What's already done (in the repo, on that branch)

- `curbstamps-site/` — the storefront (Next.js). Builds, lints, typechecks
  clean.
- `curbstamps-admin/` — orders/backend (Next.js + Postgres/Drizzle + Stripe
  refunds + a print-on-demand interface with a working mock adapter).
- `.github/workflows/deploy.yml` — already has sync/build/restart steps for
  both apps, additive to the existing shirtfaced-site/shirtfaced-admin/
  shirtfaced-studio steps. Only runs on push to `main` — this branch hasn't
  been merged, so nothing has deployed yet.
- `curbstamps-admin/deploy/` and `curbstamps-site/deploy/` — box-side deploy
  scripts and systemd unit files, versioned so they arrive via rsync (no
  manual file creation needed on the box for these two files specifically).
- `docs/curbstamps/CURBSTAMPS_DEPLOYMENT.md` — the full runbook this handover
  summarizes. Read that for the exact commands; this file is the checklist.
- `docs/curbstamps/CURB_STAMPS_SPEC.md` — full product/architecture spec.

## What the real session needs to actually have

- SSH access to the Oracle Cloud box shirtfaced already runs on (the
  `ORACLE_DEPLOY_KEY` / `ORACLE_HOST` this repo's GitHub Actions already use
  — or the box's IP and a key with `ubuntu@` access some other way).
- Cloudflare access for the `curbstamps.com` zone (dashboard login, or an
  API token scoped to that zone's DNS).

## Task list, in order

1. **Get the box's real IP.** Either from the Cloudflare dashboard
   (`shirtfaced.wtf` zone → DNS → the `A` record for `@`) or the Oracle
   Cloud console (Compute → Instances → public IP). Confirm with the human
   first whether curbstamps goes on this same box or a new one — this
   whole handover assumes the same box.

2. **Add Cloudflare DNS for `curbstamps.com`:**

   | Type | Name | Content | Proxy |
   |---|---|---|---|
   | A | `@` | `<box IP>` | Proxied |
   | A | `www` | `<box IP>` | Proxied |
   | A | `admin` | `<box IP>` | Proxied (or DNS-only, human's call) |

3. **SSH in and run the one-time setup** — exact commands in
   `docs/curbstamps/CURBSTAMPS_DEPLOYMENT.md` §2: create the
   `curbstamps_shop` Postgres database (separate from `shirtfaced_shop` and
   `shirtfaced_studio`), create `.env` files on the box for both apps from
   their `.env.example` (Stripe keys, `SESSION_SECRET`, `INTERNAL_API_KEY` —
   same value in both apps' `.env` — `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH`),
   install the systemd units from each app's `deploy/` directory, first
   build, enable + start both services.

4. **Reverse proxy** — nginx server blocks for `curbstamps.com`/
   `www.curbstamps.com` → `127.0.0.1:3100` and `admin.curbstamps.com` →
   `127.0.0.1:4300`. Exact config in the deployment doc §3. Match whatever
   the box already uses in front of shirtfaced's own apps if it isn't nginx.

5. **Merge `claude/curb-stamps-kids-shop-sas8gu` to `main`** (once the
   human's happy with it) so the new deploy.yml steps actually start firing
   on push.

6. **Verify:** `curl -I https://curbstamps.com` and
   `curl -I https://admin.curbstamps.com/login` both return 200 (or a
   redirect to `/login` for admin).

## Real decisions still open (not infra, needs the human)

- Which POD provider (Printful/Printify/Prodigi/Gooten — see
  `CURB_STAMPS_SPEC.md` §4 and the pricing research earlier in this
  project's history). `POD_PROVIDER` defaults to a mock adapter until this
  is decided and `PRINTFUL_API_KEY` (or a new adapter) is wired in.
- Real Stripe keys (test vs live).
- The homepage's final visual design — being built on a separate track on
  top of this same branch; don't let infrastructure work block on it, they're
  independent.
