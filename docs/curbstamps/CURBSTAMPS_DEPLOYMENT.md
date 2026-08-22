# Curb Stamps — Cloudflare + Oracle deployment

Status: **live**, as of 22 August 2026. This replaces an earlier version of
this doc written by a session with no Cloudflare/box access, which planned
around A-records + nginx + port 3100 for the storefront — none of which
matches how this box actually runs. What's below is the as-built record, from
a session that actually had SSH and Cloudflare access and did the work.

## What's actually running

Same Oracle box as shirtfaced (`161.33.31.74`), same Cloudflare Tunnel
(`be826f3d-e8a5-4e7c-94bb-d547079fa529`) — no nginx involved, exactly like
`shirtfaced.wtf`'s own admin/site/studio: cloudflared routes each hostname
straight to a local Next.js port, no reverse proxy in between.

| App | Port | systemd unit | Public hostname |
|---|---|---|---|
| `curbstamps-site` | **4100** | `curbstamps-site.service` | `curbstamps.com`, `www.curbstamps.com` |
| `curbstamps-admin` | `4300` | `curbstamps-admin.service` | `admin.curbstamps.com` |

Port note: `curbstamps-site/deploy/curbstamps-site.service` originally read
`3100` (an earlier session's plan, untested — it also would have relied on
`next start`'s default port with no `-p` flag, which resolves to `3000` and
collides with the live `shirtfaced-site`). Corrected to `4100` with an
explicit `-p` flag, matching the proven pattern the existing shirtfaced
systemd units already use.

## Cloudflare DNS (zone `curbstamps.com`)

| Type | Name | Value | Proxy |
|---|---|---|---|
| CNAME | `@` | `be826f3d-e8a5-4e7c-94bb-d547079fa529.cfargotunnel.com` | Proxied |
| CNAME | `www` | `be826f3d-e8a5-4e7c-94bb-d547079fa529.cfargotunnel.com` | Proxied |
| CNAME | `admin` | `be826f3d-e8a5-4e7c-94bb-d547079fa529.cfargotunnel.com` | Proxied |

CNAME-to-tunnel, not an A record to a raw IP — the box has nothing listening
on :80/:443 at all; cloudflared dials outbound. Same pattern as
`shirtfaced.wtf` in `docs/dns.md`. The two GoDaddy parking A-records the zone
was created with (and a self-referencing `www` CNAME) were deleted and
replaced with the above.

`/etc/cloudflared/config.yml` on the box has three new ingress rules (before
the `http_status:404` catch-all) routing the three hostnames to
`localhost:4100`/`localhost:4300`. `cloudflared` was restarted to pick them
up — a few seconds of shared downtime for every hostname on that tunnel
(shirtfaced.wtf, tradeninja.au, orveris.com, etc.), unavoidable since it's
one tunnel process for all of them.

SSL/TLS mode: should be **Full**, matching shirtfaced.wtf — not verified by
this session (the Cloudflare API token used was scoped to DNS edit only, by
design; zone-settings permission wasn't granted).

## One-time box setup (done)

- `curbstamps_shop` Postgres database + `curbstamps` role created on the
  box's existing Postgres instance (port 5432, same instance as
  `shirtfaced_shop`).
- `.env` files written on the box for both apps (never touched by rsync —
  both deploy scripts exclude `.env`) with generated `SESSION_SECRET`,
  `INTERNAL_API_KEY` (same value in both apps), `POD_WEBHOOK_SECRET`, and an
  `ADMIN_PASSWORD_HASH` generated with the app's own `hashPassword()`
  (scrypt) — real password given to the account owner directly, not stored
  in this repo. `ADMIN_EMAIL=cdunell@gmail.com`.
- Stripe keys and `PRINTFUL_API_KEY` left unset on purpose — see
  "Still open" below. `POD_PROVIDER=mock`.
- `curbstamps-admin`: `npm ci`, `drizzle-kit migrate`, `npm run seed` (36
  products across 12 creatures), `npm run build`.
- `curbstamps-site`: `npm ci`, `npm run build`.
- Systemd units installed from `curbstamps-admin/deploy/curbstamps-admin.service`
  and `curbstamps-site/deploy/curbstamps-site.service` (the corrected
  versions — see the port note above), enabled and started.

## Verified live (22 August 2026)

```
curl -I https://curbstamps.com          → 200
curl -I https://www.curbstamps.com      → 200
curl -I https://admin.curbstamps.com/login → 200
```

Homepage content confirmed by reading the actual rendered page (not just a
status code) — the mobile-first rebuild (Pick Your Weirdo / New Drop / Meet
the Curb Crew / Shop the Look / Weirdo Match / Made for Adventures / Parents
Corner / Join the Curb) is what's live, not the earlier placeholder hero.

## Still open

- Real Stripe keys and a real POD provider account — see
  `docs/curbstamps/CURB_STAMPS_SPEC.md` §4 and §8. `POD_PROVIDER=mock` and
  both Stripe env vars are unset, so checkout shows the honest
  "payment isn't connected" state and no real order can be placed yet.
- A children's-clothing compliance review and a legal review of
  Terms/Privacy — neither has happened; see `CURB_STAMPS_SPEC.md` §8.
- `.github/workflows/deploy.yml` now has the rsync/build/restart steps for
  both apps (additive, same pattern as shirtfaced's own) — they only fire on
  push to `main`, so nothing auto-deploys again until this branch merges and
  a future commit lands.
