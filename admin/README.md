# Shirtfaced Admin

Server-rendered Next.js app for managing the shop's product catalog and
inventory, backed by Postgres. Separate from the storefront (`../src`), which
stays a static export — this app is the only thing in the repo that talks to
a database.

## Scope (v1)

- Products, colourways and per-size stock — full CRUD.
- Single admin login (one account, env-configured).
- A "Studio ↗" nav link out to Shirtfaced Studio, which has no deployed
  instance yet — the link is a placeholder (`STUDIO_URL` env var) until it
  does.

Site content management (About/Shipping/Returns copy) and order/customer
records are **not** built yet — the storefront still has no checkout/payment
integration to generate real orders from.

## Local development

Requires a Postgres instance. Point `SHOP_DATABASE_URL` at whatever you've
got — see `.env.example`.

```bash
npm install
cp .env.example .env   # then fill in the values below
npm run db:migrate     # creates products / product_colours / colour_stock
npm run seed            # imports ../src/lib/products.ts as a starting catalog
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

## Production (Oracle)

Deployed at `/root/shirtfaced-admin` on the Oracle box (same host as the
storefront's static files and the other services under `/root`), run via
systemd as `shirtfaced-admin.service`, bound to `127.0.0.1:4200` — **not**
yet exposed through nginx/a public domain. It uses its own Postgres role
(`shirtfaced_admin`) and database (`shirtfaced_shop`) on the box's existing
`main` Postgres cluster (port 5432), created specifically for this app —
nothing shared with the other apps on that box.

To redeploy after code changes:

```bash
# from admin/, package everything except node_modules/.next/.env
tar --exclude='node_modules' --exclude='.next' --exclude='.env' -czf /tmp/admin-deploy.tar.gz .
scp /tmp/admin-deploy.tar.gz ubuntu@<host>:/tmp/

# on the box (sudo):
cd /root/shirtfaced-admin
rm -rf src public *.ts *.mjs *.json 2>/dev/null  # or just re-extract over top
tar -xzf /tmp/admin-deploy.tar.gz -C /root/shirtfaced-admin
npm install   # only if package.json changed
npm run build
systemctl restart shirtfaced-admin
```

`.env` on the box has its own production credentials (different admin
password and session secret from local dev — rotate both before this is
ever exposed publicly, since they were generated during initial setup and
are known outside the account owner's password manager).

### Next steps

- Decide whether/how to expose this publicly (nginx site + subdomain, e.g.
  `admin.shirtfaced.wtf`, behind Cloudflare like the storefront) — deliberately
  left undone pending a decision, since it's currently only reachable via SSH
  tunnel or from other services on the box.
- Rotate the production admin password and `SESSION_SECRET` once a real
  password manager entry replaces the generated ones.
- When Studio gets a real deployment, point `STUDIO_URL` at it.
- Wire the storefront's build to read from this database instead of the
  static `src/lib/products.ts` array (today the two are only connected by
  the one-time `npm run seed` import — editing a product here does **not**
  update the live storefront).
