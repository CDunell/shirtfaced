# Curb Stamps — Spec

Kids apparel brand and storefront, built as a sibling to Shirtfaced in this repo but
otherwise independent of it. This document is the map: what Curb Stamps is, what's built,
what's stubbed, and what's still a decision rather than code.

Curb Stamps does **not** go through Shirtfaced Studio (System A/B/C in the root
`CLAUDE.md`). It has no design-generation pipeline, no world canon, no review scorecard.
Artwork is supplied directly; this spec and the two new apps it describes are the whole
of Curb Stamps' engineering surface.

## 1. What it is

A kids clothing label — tees, hoodies, headwear, toddler to teen — built around a growing
cast of small illustrated creatures. 60 creatures are planned; **12 have finished artwork
and are live in the catalog today** (see §3). Each creature is a character with a name and
a one-line personality, not just a print — the brand is "a little universe of little
guys," closer to a sticker-book than a streetwear drop.

Tone: friendly, a little dry, never twee. Screen-printed, not vinyl. Made to be handed
down, not outgrown in one wash.

## 2. What's built

Two new sibling Next.js apps, alongside `src/` (Shirtfaced's own storefront) and `admin/`:

| App | Path | Role |
|---|---|---|
| Storefront | `curbstamps-site/` | Public shop — catalog, cart, checkout, About/FAQ/Terms/etc. |
| Backend | `curbstamps-admin/` | Orders database, Stripe refunds, POD fulfilment, staff order dashboard |

This mirrors `src/` + `admin/`'s own split deliberately: the storefront has **no direct
database access**, and reaches orders only through `curbstamps-admin`'s
`/api/internal/orders` routes, authenticated with a shared secret
(`INTERNAL_API_KEY` / `ADMIN_INTERNAL_API_KEY`). Two independent Next.js apps, two
independent `package.json`s, no monorepo tooling — consistent with how this repo already
runs (`admin/` was added the same way, alongside `src/`; see the investigation in this
project's history for why no `apps/*` workspace layout was introduced instead).

Both apps: **run and typecheck and lint clean** (`npm run build`, `npm run lint`,
`tsc --noEmit`), and `curbstamps-admin`'s Drizzle schema generates a real migration
(`src/db/migrations/0000_*.sql`). Neither has been run against a live Postgres instance,
a live Stripe account, or a live POD provider — see §8 for exactly what that leaves open.

### 2.1 Storefront (`curbstamps-site/`)

- Static catalog (`src/lib/creatures.ts`, `src/lib/products.ts`) — 12 creatures × 3
  categories (tee/hoodie/cap) = 36 products. No database sync for v1; see §7.
- Cart (`localStorage`, same pattern as Shirtfaced's `cart-context.tsx`).
- Checkout: contact → address → shipping method → Stripe `PaymentElement`. No discount
  codes in v1 (see §7).
- `api/create-payment-intent` and `api/stripe-webhook` — same shape as Shirtfaced's own,
  minus the ad-attribution plumbing (Meta/TikTok server-side events) — not needed until
  Curb Stamps runs paid acquisition.
- Full page set: Home, Shop (with category filter), Product detail, Cart, Checkout (+
  success), About, FAQ, Terms, Privacy, Shipping, Returns, Size Guide, Contact.
- Product art: `public/creatures/*-logo.png` — transparent-background line-art lockups,
  generated from the supplied logo sheets (black backgrounds keyed out to alpha). No real
  garment photography exists, so `components/GarmentArt.tsx` renders an honest flat
  illustration (a thick-outline garment silhouette + the creature print composited on
  top) instead of faking a product photo. Swap that one component for real photography
  once samples exist — nothing else needs to change.
- New design tokens in `globals.css` — cream/paper base, one accent colour per creature,
  rounded "Baloo 2" display type — distinct from Shirtfaced's ink-black/lime system on
  purpose (see §3).

### 2.2 Backend (`curbstamps-admin/`)

- Postgres via Drizzle ORM, **its own database** (`curbstamps_shop`, see §5) — not a
  schema bolted onto `shirtfaced_shop` or `shirtfaced_studio`.
- Schema: `products`, `customers`, `orders`, `orderItems`. No stock/colour tables —
  fulfilment is print-on-demand, so there's no physical inventory to count (a genuine
  simplification versus Shirtfaced's schema, not a shortcut).
- `/api/internal/orders` (POST create, GET/PATCH by id) — same contract as
  `admin/src/app/api/internal/orders`, so the storefront's payment-intent and webhook
  routes are near copies of Shirtfaced's own.
- `/api/pod/webhook` — inbound fulfilment status updates from a real POD provider (§4).
- Session-cookie login (`scrypt` password hash + HMAC-signed cookie), gated off in dev,
  enforced in production — same mechanism as `admin/src/lib/session.ts`.
- `/orders` (list) and `/orders/:id` (detail) — status, shipping address, POD status and
  tracking, with actions to mark paid (which also submits to POD), mark shipped, or
  cancel (refunding via Stripe if a PaymentIntent exists).
- No content-management UI (About/FAQ copy lives in the storefront's own source, not a
  database) and no discount codes — both are Shirtfaced-admin features not reproduced
  here yet; see §7.

## 3. The creatures

12 live today, of a planned 60:

| Creature | Animal | Accent |
|---|---|---|
| Blip | Caterpillar | Grass `#7ed957` |
| Twig | Stick insect | Sky `#3ec6e0` |
| Murk | Eel | Teal `#2c9e8f` |
| Squib | Platypus | Butter `#ffc93c` |
| Plod | Tortoise | Moss `#8a9a5b` |
| Grub | Caterpillar | Coral `#ff6f5e` |
| Grit | Bandicoot | Clay `#c96f4a` |
| Bub | Dugong | Powder `#a7c4e0` |
| Claw | Crab | Tomato `#ff5757` |
| Dreg | Little devil | Grape `#9b6bd6` |
| Lod | Slug | Lilac `#c9a7e0` |
| Snu | Shrew | Sand `#e0b98a` |

Each ships as a tee ($34.95), hoodie ($64.95) and cap ($29.95), in Jet Black, Natural and
its own signature accent colour. **Prices are placeholders** — set from a rough sense of
kids-apparel market pricing, not a real cost-plus calculation; revisit once a POD
provider's per-unit cost is known (§4).

Adding creature #13 onward: land the artwork as a transparent PNG in
`curbstamps-site/public/creatures/{slug}-logo.png`, add one entry to `CREATURES` in both
`curbstamps-site/src/lib/creatures.ts` **and** `curbstamps-admin/src/db/seed.ts` (kept in
sync by hand for now, see §7), and re-run `npm run seed` in `curbstamps-admin`. No code
changes needed beyond that — the product grid, cart, checkout and admin dashboard all
derive from the creature list.

## 4. Print-on-demand — what's real, what's a stub

**No POD vendor account exists yet.** This was an explicit scope decision (see the
project's Q&A): build the integration point generically now, wire up a real vendor once
one's chosen. That leaves three pieces:

1. **`curbstamps-admin/src/lib/pod/types.ts`** — the `PodProvider` interface
   (`createOrder`, `getOrderStatus`). Nothing else in the app talks to a vendor's API
   shape directly; everything calls this.
2. **`mock-adapter.ts`** — the default (`POD_PROVIDER` unset or `mock`). Logs what a real
   provider would receive and fakes a lifecycle. This is what runs today, and it's
   enough to exercise checkout → paid → "in production" end to end without a vendor.
3. **`printful-adapter.ts`** — a **reference implementation**, not a working
   integration. It calls Printful's real Orders API
   (`POST/GET https://api.printful.com/orders`) with the right shape, but:
   - `SYNC_VARIANT_MAP` (which maps this catalog's slug/colour/size to Printful's own
     per-variant ids) is **empty** — it can only be filled in once a Printful account
     exists and the 36 products above are built there as "sync products" against real
     blanks (kids tee/hoodie/cap SKUs — Shirtfaced's own blank research in
     `docs/production/GARMENT_BLANK_STRATEGY.md` and
     `docs/production/POD_FULFILMENT_RESEARCH.md` is adult-garment-specific and doesn't
     directly apply to kids sizing; a fresh blank decision is needed for Curb Stamps).
   - `confirm: false` is hardcoded — real orders land as Printful drafts needing manual
     confirmation until the integration is trusted enough to flip that.
   - Untested against a real Printful account — there isn't one.

**To go live with real fulfilment:** pick a vendor (Printful and Printify both do
kids-sized blanks; this hasn't been evaluated — do it before committing), open an
account, build the 36 products in the vendor's dashboard against real kids blanks, fill
in `SYNC_VARIANT_MAP`, set `POD_PROVIDER=printful` (or write a new adapter file for
whichever vendor was actually chosen — Printify's API shape differs and would need its
own adapter following the same `PodProvider` interface), and set the vendor's webhook to
POST fulfilment updates to `/api/pod/webhook` with the shared `POD_WEBHOOK_SECRET` header
(exact header/signing scheme depends on the vendor — adjust `verifyPodWebhook` in that
route to match their real mechanism).

## 5. Data model

`curbstamps-admin` owns a new, standalone Postgres database — **not** a new schema
inside `shirtfaced_shop`, and **not** anything in `shirtfaced_studio`. Naming it
`curbstamps_shop` (on the same Postgres instance as the other two is fine operationally;
it's a separate `CREATE DATABASE`, not shared tables) keeps the same clean separation
Shirtfaced already has between its own shop and Studio.

```
products      — slug, creature, category, name, price, art, colours (jsonb), sizes (text[])
customers     — email (unique), name
orders        — orderSeq (human reference), customerId, status, totals, shippingAddress,
                stripePaymentIntentId, podProvider/podOrderId/podStatus, tracking fields
order_items   — orderId, productId (nullable snapshot), productName, colourName, size, qty, price
```

`status` lifecycle: `pending → paid → in_production → shipped`, or `cancelled` at any
point before `shipped`. `paid` is set by Stripe's webhook (never the client);
`in_production`/`shipped` are meant to be driven by the POD provider's own webhook once
one exists, not typed in by staff (though staff *can* override by hand today, since no
real webhook exists yet to do it for them).

## 6. Payments

Stripe, in test mode until real keys are supplied — same "honest unconfigured state"
pattern as Shirtfaced's own checkout: with `STRIPE_SECRET_KEY` unset, the checkout page
shows a plain "payment isn't connected" message instead of a broken card form. No
discount codes, no ad-attribution server events (Meta/TikTok Conversions API) — both
exist in Shirtfaced's checkout and were deliberately left out of v1 here (§7).

## 7. Explicitly out of scope for v1 (and why)

Cut to keep the first build shippable, not because they're wrong ideas:

- **Discount codes.** Shirtfaced admin has a full `discounts` table + redemption flow;
  Curb Stamps doesn't. Add by porting that table + `redeemDiscountByCode` pattern
  verbatim once needed.
- **Database-driven content.** About/FAQ/Terms copy is hardcoded in
  `curbstamps-site/src/app/*/page.tsx`, not editable from `curbstamps-admin` the way
  Shirtfaced's `aboutContent`/`faqContent` tables are. Fine while one person edits copy
  by committing code; revisit once non-technical staff need to change it.
- **Catalog sync from the database.** The 36 products are a static TypeScript file, not
  synced from `curbstamps-admin`'s `products` table the way Shirtfaced's storefront syncs
  from `admin` at build time (`scripts/sync-products.mjs`). Fine at 36 SKUs across 12
  creatures; once new creatures ship often enough that a code deploy per creature is
  annoying, port that sync script.
- **Real garment photography.** See §2.1 — `GarmentArt.tsx` is an honest placeholder.
- **International shipping.** Australia-only shipping methods, same restriction
  Shirtfaced currently ships under.
- **Ad-attribution / analytics.** No GA4/Meta/TikTok pixels wired up yet.
- **Monorepo tooling.** Two independent `package.json`s and lockfiles, matching how
  `admin/` sits alongside `src/` today. Worth revisiting only if Curb Stamps and
  Shirtfaced start sharing real code (a components package, a shared design-token
  system) rather than just conventions.

## 8. What's needed before this can take a real order

In rough order:

1. **A real Postgres database** — provision `curbstamps_shop`, run
   `cd curbstamps-admin && npm run db:migrate && npm run seed`.
2. **Stripe** — a real (or test-mode-for-now) Stripe account; set
   `STRIPE_SECRET_KEY`/`NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` in both apps and
   `STRIPE_WEBHOOK_SECRET` in the storefront once a webhook endpoint is registered in the
   Stripe dashboard pointing at `curbstamps-site`'s `/api/stripe-webhook`.
3. **`INTERNAL_API_KEY`** — one shared secret, set identically as
   `INTERNAL_API_KEY` in `curbstamps-admin/.env` and `ADMIN_INTERNAL_API_KEY` in
   `curbstamps-site/.env`.
4. **A POD decision** — see §4. Blocks real fulfilment, not the ability to take payment
   (orders will sit in `paid` with a note that POD submission failed, visible in the
   admin order list, until this is wired up).
5. **A children's clothing compliance check.** This spec included one safety detail
   already acted on — no drawstrings on toddler-size (2T–4T) hoodies, per AS/NZS 1249 —
   but a proper compliance review (labelling requirements, care-label wording, any
   mandatory standard beyond drawstrings) hasn't been done and should happen before
   selling real garments to children, not assumed from this document.
6. **A legal review of Terms and Privacy** — both pages are explicitly flagged in-app as
   placeholder drafts, not reviewed against the Australian Consumer Law / Australian
   Privacy Principles.
7. **Deployment.** Neither app has been deployed. `.github/workflows/deploy.yml` is a
   complex, single-purpose pipeline for the existing three apps (`shirtfaced-site`,
   `shirtfaced-admin`, `shirtfaced-studio`) with box-side scripts that aren't tracked in
   this repo — extending it to a fourth and fifth app is a real but separate piece of
   work, deliberately not done as part of this build (editing shared production CI isn't
   something to do speculatively). The shape to follow: add
   `curbstamps-site`/`curbstamps-admin` rsync steps to `deploy.yml` mirroring the
   existing ones, write `deploy-curbstamps-site.sh`/`deploy-curbstamps-admin.sh` on the
   Oracle box (following whatever the existing untracked `deploy-admin.sh`/
   `deploy-site.sh` do — likely `npm ci && npm run build` + a systemd restart), pick
   ports (this spec uses `4300` for `curbstamps-admin` locally, matching
   `shirtfaced-admin`'s convention of a non-3000 port; `curbstamps-site` defaults to
   `3000` like `shirtfaced` — both need distinct ports or hosts on the real box since all
   apps share one server), and add an nginx/reverse-proxy entry per new subdomain
   (e.g. `shop.curbstamps.com.au`, `admin.curbstamps.com.au`).

## 9. Roadmap (not built)

- Creatures #13–60, as art is finished.
- Real POD vendor integration (§4).
- Real product photography, replacing `GarmentArt.tsx`.
- Discount codes, database-driven content, catalog DB sync (§7) once volume justifies
  the extra moving parts.
- Wholesale/bulk ordering (mentioned on the Contact page as a stated intent, no workflow
  built for it).
- Gift cards, size-exchange self-service, subscription/"new creature every month" club —
  none evaluated, all plausible for a kids collectibles-adjacent brand.

## 10. File map

```
curbstamps-site/            storefront (Next.js, no DB access)
  src/lib/creatures.ts       the 12 (of 60) creatures — name, animal, blurb, accent colour
  src/lib/products.ts        36 SKUs derived from creatures × {tee, hoodie, cap}
  src/lib/cart-context.tsx   localStorage cart
  src/lib/checkout-pricing.ts server-trusted pricing (shipping methods, free-shipping threshold)
  src/components/GarmentArt.tsx  placeholder product art — swap for real photos later
  src/app/api/create-payment-intent, api/stripe-webhook   talk to curbstamps-admin + Stripe
  src/app/{about,faq,terms,privacy,shipping,returns,size-guide,contact}  static content pages

curbstamps-admin/           backend (Next.js + Drizzle + Postgres, owns the database)
  src/db/schema.ts           products, customers, orders, order_items
  src/db/store-queries.ts    order lifecycle, incl. the POD submission call on markOrderPaid
  src/lib/pod/               provider-agnostic POD interface + mock/Printful adapters
  src/app/api/internal/orders   what curbstamps-site's checkout calls
  src/app/api/pod/webhook    inbound fulfilment updates from a real POD provider
  src/app/{login,orders}    staff-facing order dashboard

docs/curbstamps/CURB_STAMPS_SPEC.md   this document
```
