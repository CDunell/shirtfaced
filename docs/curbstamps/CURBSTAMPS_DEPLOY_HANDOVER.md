# Curb Stamps — deploy handover

For a session that actually has what this cloud session doesn't: outbound network access
to `api.printify.com` (this sandbox's egress policy blocks it outright — confirmed via
`$HTTPS_PROXY/__agentproxy/status`, a `403 policy denial`, not a transient failure), and/or
SSH access to the Oracle box. The site and admin backend are both live already — this is
about finishing real POD fulfilment, not getting something on the internet.

Repo: `CDunell/shirtfaced`, branch `claude/curb-stamps-kids-shop-sas8gu`
(already merged to `main` once via PR #11 — check whether this branch has new commits
since that need merging again before assuming `main` is current).

## Current state (see docs/curbstamps/CURBSTAMPS_DEPLOYMENT.md for the full as-built record)

**Live**: `curbstamps.com`, `www.curbstamps.com`, `admin.curbstamps.com` — Cloudflare
Tunnel to the same Oracle box as shirtfaced, `curbstamps-site` on port 4100,
`curbstamps-admin` on port 4300, both systemd services. No nginx, no A-records — it's all
CNAME-to-tunnel, same pattern as shirtfaced.wtf.

**Checkout works end-to-end against a mock POD provider** — Stripe isn't configured
either (`POD_PROVIDER=mock`, both Stripe env vars unset on the box), so no real order can
be placed yet, but the flow (cart → real per-destination shipping quote →
payment-isn't-connected message) is real, tested code, not a stub UI.

**POD provider decided: Printify.** `curbstamps-admin/src/lib/pod/printify-adapter.ts`
is a real implementation against Printify's documented v1 API. It's inert until:

## The actual next task: wire up the real Printify account

**A live Printify personal access token exists** — the account owner has it (scopes:
shops.manage/read, catalog.read, orders.read/write, products.read/write, webhooks.read/
write, uploads.read/write, print_providers.read, user.info). It has NOT been entered
anywhere in this repo or on the box yet — this cloud session received it in chat but
could not use it (network block above), and never wrote it to disk anywhere persistent.
Get it from the account owner directly, don't assume it's stored anywhere.

With real network access to `api.printify.com`, in order:

1. `GET /v1/shops.json` with `Authorization: Bearer <token>` → get the real numeric
   `shop_id`. If no shop exists yet, one needs creating first (Printify's own
   onboarding, or `shops.manage` scope covers creating one via API).
2. Browse the catalog (`catalog.read` scope — `GET /v1/catalog/blueprints.json`, then
   `/v1/catalog/blueprints/{id}/print_providers.json` and `.../variants.json`) for:
   - **Gildan 5000B** (youth tee) and **Gildan 18500B** (youth hoodie) — both confirmed
     to exist in Printify's catalogue, referenced in `CURB_STAMPS_SPEC.md` §4.
   - A kids cap blank — not picked yet, needs a decision here.
   - Pick print providers that actually offer these blueprints with reasonable
     shipping to Australia (this store's home base) and internationally.
3. Create the 36 products (12 creatures × tee/hoodie/cap) in Printify — either through
   their dashboard by hand, or via `products.write`/`uploads.write` (upload the artwork
   from `curbstamps-site/public/creatures/*-logo.png` / `*-logo-dark.png`, then create a
   product per creature/category referencing the right blueprint + print provider +
   variant list).
4. Fill in `SYNC_VARIANT_MAP` in `printify-adapter.ts` — maps this app's own
   `slug/colourName/size` (e.g. `"blip-tee"` / `"Jet Black"` / `"M (10/12)"`) to
   Printify's `(product_id, variant_id)` pairs from step 3. This part is safe to commit
   — it's catalogue ids, not a secret.
5. On the box: set `PRINTIFY_API_KEY=<token>`, `PRINTIFY_SHOP_ID=<from step 1>`,
   `POD_PROVIDER=printify` in `/home/ubuntu/curbstamps-admin/.env`, restart
   `curbstamps-admin.service`.
6. Set up Printify's webhook (their dashboard, or `webhooks.write`) to POST fulfilment
   updates to `https://admin.curbstamps.com/api/pod/webhook` — confirm Printify's real
   payload/signing scheme against `verifyPodWebhook` in that route file and adjust it;
   it was written generically, never matched against a real Printify webhook payload.
7. Place one real test order end-to-end (real Stripe test-mode key first — see below —
   then a real Printify order) before calling this done.

## Also still open

- **Stripe**: no keys set anywhere yet, test or live. Needed before step 7 above can
  even happen — a Printify order without a paid order behind it isn't a real test.
- **A kids cap blank decision** (step 2 above) — not evaluated at all yet.
- **A children's-clothing compliance review and legal review of Terms/Privacy** — see
  `CURB_STAMPS_SPEC.md` §8, neither has happened.

## Security note

The Printify token was pasted directly into this session's chat. Treat it as exposed to
whoever/whatever can read that transcript. If that's a concern, rotate it in Printify's
dashboard (Settings → Connections) once the real setup above is done, and hand the new
one only to whichever session/person actually applies it on the box.
