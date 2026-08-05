# Shirtfaced Admin

Server-rendered Next.js app for managing the shop's product catalog,
inventory, and site page copy, backed by Postgres. Separate from the
storefront (`../src`), which stays a static export — this app is the only
thing in the repo that talks to a database directly at runtime.

Live at **admin.shirtfaced.wtf**.

## Scope (v1)

- Products, colourways and per-size stock — full CRUD.
- Site content for About, Shipping (incl. rates), Returns, Contact, Size
  guide (incl. the measurements table), Home, Account, More, and the
  per-product feature list — distinct named fields per page, not a generic
  blob. See `src/db/schema.ts` for exactly what's covered; a few things are
  deliberately left out (hero taglines, collection tile images, the More
  page's link list) because they're either tied to specific photo assets
  admin doesn't manage or are fixed navigation, not copy.
- Single admin login (one account, env-configured).
- A "Studio ↗" nav link out to Shirtfaced Studio, which has no deployed
  instance yet — the link is a placeholder (`STUDIO_URL` env var) until it
  does.

Order/customer records are **not** built — the storefront still has no
checkout/payment integration to generate real orders from.

## Local development

Requires a Postgres instance. Point `SHOP_DATABASE_URL` at whatever you've
got — see `.env.example`.

```bash
npm install
cp .env.example .env    # then fill in the values below
npm run db:migrate      # creates all tables
npm run seed             # imports ../src/lib/products.ts as a starting catalog
npm run seed:content     # imports the storefront's current hardcoded page copy
npm run dev
```

### Env vars

| Var                    | Purpose                                                             |
| ----------------------- | -------------------------------------------------------------------- |
| `SHOP_DATABASE_URL`     | Postgres connection string. **Not** `DATABASE_URL` — see below.     |
| `ADMIN_EMAIL`           | The one admin account's email.                                      |
| `ADMIN_PASSWORD_HASH`   | scrypt hash — generate with a one-off `tsx` script using `hashPassword` from `src/lib/password.ts`. |
| `SESSION_SECRET`        | 32+ random bytes (hex), signs the session cookie.                   |
| `STUDIO_URL`            | Where the "Studio" nav link points.                                  |
| `STUDIO_API_URL`        | Where the Prompts page calls Studio server-side. Falls back to `STUDIO_URL`. |

**Why `SHOP_DATABASE_URL` and not `DATABASE_URL`:** on a shared dev machine
with other projects, a generic env var name is a real collision risk — an
unrelated project's `DATABASE_URL` can already be set at the OS level, and
neither `dotenv` nor Next's own env loader override a variable that's already
in `process.env`. That happened during this app's own build: migrations
silently ran against a different project's database until this was caught
and the tables were dropped from it. Keep the name specific.

### Database schema

Product → many Colourways → many (size, quantity) stock rows. Sizes are
S/M/L/XL/XXL, matching the storefront's `SizeKey`. Editing a product rewrites
all of its colourways and stock rows in one transaction — there's no
diffing, so colourway IDs aren't stable across edits.

Site content is 9 singleton tables (`about_content`, `shipping_content`,
etc.) — always exactly one row (`id = 1`), no create/delete, only edit.

## Production (Oracle)

Deployed at `/home/ubuntu/shirtfaced-admin` on the Oracle box (same host as
the storefront's static files and the other services there), run via
systemd as `shirtfaced-admin.service` on port 4200, reverse-proxied through
the account's existing Cloudflare Tunnel at `admin.shirtfaced.wtf`. It uses
its own Postgres role (`shirtfaced_admin`) and database (`shirtfaced_shop`)
on the box's existing `main` Postgres cluster (port 5432), created
specifically for this app — nothing shared with the other apps on that box.

**Deploys automatically on every push to `main`** — see the root
[README's "Deploying" section](../README.md#deploying) for how the GitHub
Actions workflow and the box's `deploy-admin.sh` fit together.

`.env` on the box has its own production credentials (different admin
password and session secret from local dev).

### Next steps

- Rotate the production admin password and `SESSION_SECRET` before/at
  go-live — the current ones were generated during initial setup and are
  known outside the account owner's password manager.
- When Studio gets a real deployment, point `STUDIO_URL` at it.
