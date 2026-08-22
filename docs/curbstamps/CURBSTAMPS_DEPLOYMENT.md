# Curb Stamps — Cloudflare + Oracle deployment

What's automated, what's a one-time manual step, and exactly what to run for
each. I have no Cloudflare account access and no SSH access to the Oracle
box in this session — nothing here could be executed directly; it's staged
so the manual part is copy-paste, not figured out from scratch.

## What's already done (this branch)

- `.github/workflows/deploy.yml` — new steps added (additive only, nothing
  existing touched) that rsync `curbstamps-admin/` and `curbstamps-site/` to
  the box and run their deploy scripts, same pattern as the existing
  shirtfaced-admin/shirtfaced-site steps. Only fires on push to `main`, same
  as everything else in that workflow — inert until this branch merges.
- `curbstamps-admin/deploy/deploy-curbstamps-admin.sh` and
  `curbstamps-site/deploy/deploy-curbstamps-site.sh` — the box-side
  build+restart scripts, versioned here (unlike `deploy-admin.sh` /
  `deploy-site.sh`, which exist only on the box) so they arrive automatically
  via rsync — no manual file creation on the box needed for these two.
- `curbstamps-admin/deploy/curbstamps-admin.service` and
  `curbstamps-site/deploy/curbstamps-site.service` — systemd unit files,
  reference copies to install once (§2 below).
- Ports fixed to avoid colliding with the existing shirtfaced apps on the
  same box: **curbstamps-site → 3100**, **curbstamps-admin → 4300**
  (shirtfaced-site runs on 3000, shirtfaced-admin on 4200).

## What I need from you before any of this goes live

1. **Same Oracle box as shirtfaced, or a new one?** Everything below assumes
   the same box (simplest — one server, one deploy key, already paid for).
2. **The box's IP address.** It's a GitHub Actions secret (`ORACLE_HOST`)
   I can't read from here. `shirtfaced.wtf` itself resolves to Cloudflare's
   proxy IPs, not the real origin, so I can't discover it by looking the
   domain up either.
3. Once I have that IP, either:
   - **You add the Cloudflare DNS records yourself** — takes about 2 minutes,
     exact records in §1 below, or
   - **You give me a Cloudflare API token** scoped to the `curbstamps.com`
     zone (Zone → DNS → Edit permission is enough) and I'll create the
     records directly via Cloudflare's API. Your call — sharing a scoped
     token here is a real decision, not something to default into.

## 1. Cloudflare DNS records

Once `curbstamps.com` is added as a site in Cloudflare (nameservers pointed
there — presumably already done since you said it's "secured" and ready to
route through Cloudflare):

| Type | Name | Content | Proxy status |
|---|---|---|---|
| A | `@` | `<ORACLE_HOST IP>` | Proxied (orange cloud) |
| A | `www` | `<ORACLE_HOST IP>` | Proxied |
| A | `admin` | `<ORACLE_HOST IP>` | Proxied |

Proxied (not "DNS only") matches how `shirtfaced.wtf` is already set up —
Cloudflare terminates TLS and fronts the box, same as today. If you'd rather
the admin subdomain skip Cloudflare's proxy entirely (direct-only, no CDN/
WAF in front of the staff order dashboard), set that one row to "DNS only"
instead — a legitimate choice, not required either way.

No CNAME needed for `www` — an A record pointing at the same IP is simpler
than a flattened CNAME-at-apex setup and is what Cloudflare recommends for
this exact case.

## 2. One-time box setup (SSH in, run once)

Assuming the same Oracle box as shirtfaced, as `ubuntu`:

```bash
# 1. Create the app directories (rsync creates these on first deploy too,
#    but the systemd units and .env need to exist before the first deploy
#    tries to start the service).
mkdir -p /home/ubuntu/curbstamps-admin /home/ubuntu/curbstamps-site

# 2. Postgres: create curbstamps' own database, separate from
#    shirtfaced_shop and shirtfaced_studio (same instance is fine).
sudo -u postgres psql -c "CREATE DATABASE curbstamps_shop;"
sudo -u postgres psql -c "CREATE USER curbstamps WITH PASSWORD '<choose one>';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE curbstamps_shop TO curbstamps;"

# 3. .env files — rsync excludes .env, so these are never overwritten by a
#    deploy. Fill in real values per curbstamps-admin/.env.example and
#    curbstamps-site/.env.example (Stripe keys, SESSION_SECRET,
#    INTERNAL_API_KEY — same value in both — ADMIN_EMAIL/PASSWORD_HASH, etc).
nano /home/ubuntu/curbstamps-admin/.env
nano /home/ubuntu/curbstamps-site/.env
# curbstamps-site's ADMIN_API_URL should be http://localhost:4300 in
# production (same box, no need to go through the public domain).

# 4. First deploy needs the code on the box before systemd can start it —
#    either trigger the GitHub Actions workflow once first (it rsyncs but
#    the service enable/start below still needs doing once), or rsync by
#    hand right now:
#      rsync -az curbstamps-admin/ ubuntu@<host>:/home/ubuntu/curbstamps-admin/
#      rsync -az curbstamps-site/ ubuntu@<host>:/home/ubuntu/curbstamps-site/

# 5. Install the systemd units (copied from the repo, already on the box
#    after the rsync above).
sudo cp /home/ubuntu/curbstamps-admin/deploy/curbstamps-admin.service /etc/systemd/system/
sudo cp /home/ubuntu/curbstamps-site/deploy/curbstamps-site.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable curbstamps-admin curbstamps-site

# 6. Build once by hand, then start (subsequent deploys do this automatically).
cd /home/ubuntu/curbstamps-admin && npm ci && npm run build
cd /home/ubuntu/curbstamps-site && npm ci && npm run build
sudo systemctl start curbstamps-admin curbstamps-site
sudo systemctl status curbstamps-admin curbstamps-site
```

## 3. Reverse proxy (nginx)

Assuming the box already runs nginx in front of shirtfaced's apps (typical
for a Cloudflare-proxied Oracle Cloud VM) — add two server blocks. If the
box uses something else (Caddy, a different setup) the shape is the same,
just different config syntax.

```nginx
server {
    listen 80;
    server_name curbstamps.com www.curbstamps.com;
    location / {
        proxy_pass http://127.0.0.1:3100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name admin.curbstamps.com;
    location / {
        proxy_pass http://127.0.0.1:4300;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

TLS: with Cloudflare in "Proxied" mode, Cloudflare terminates TLS to the
visitor and can talk plain HTTP to the origin (Flexible mode) or HTTPS (Full
mode, needs a cert on the box — e.g. `certbot --nginx`, or Cloudflare's own
origin certificate, free, 15-year validity, purpose-built for exactly this).
Full (or Full Strict) is the safer choice if the box already has a
mechanism for it from the shirtfaced setup — reuse whatever that is.

## 4. Verifying it's live

```bash
curl -I https://curbstamps.com
curl -I https://admin.curbstamps.com/login
```

Both should return `200` (or `307`/`302` to `/login` for admin, if not yet
signed in) once DNS has propagated (usually under 5 minutes through
Cloudflare) and both systemd services are running.

## Still open after this

- Real Stripe keys, POD provider account, and the `.env` values that go with
  them — see `docs/curbstamps/CURB_STAMPS_SPEC.md` §8.
- The visual homepage rebuild is in progress on a separate track — this
  document is only about getting *something* reachable at the domain, not
  about what it looks like once it's there.
