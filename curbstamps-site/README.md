# Curb Stamps — storefront

Kids apparel storefront for Curb Stamps: 12 creatures live today (of 60 planned), each as
a tee, a hoodie and a cap. Same architecture split as `shirtfaced`/`shirtfaced-admin`: this
app has no direct database access — it calls `curbstamps-admin`'s `/api/internal/orders`
to create and update orders, and Stripe directly to take payment.

Full spec: [`docs/curbstamps/CURB_STAMPS_SPEC.md`](../docs/curbstamps/CURB_STAMPS_SPEC.md).

## Running locally

```bash
npm install
cp .env.example .env   # fill in Stripe test keys + ADMIN_API_URL/ADMIN_INTERNAL_API_KEY
npm run dev
```

Runs on port 3000 by default. Start `curbstamps-admin` alongside it (see its own README) —
checkout needs it to create orders, even with Stripe unconfigured the app runs fine and
shows the shop/cart honestly without a working checkout.

## Catalog

The catalog (`src/lib/products.ts`, `src/lib/creatures.ts`) is static for v1 — no database
sync. Once product data needs editing without a code deploy (new creature, price change,
new colourway), follow shirtfaced's pattern: move the catalog into curbstamps-admin's
database and add a `scripts/sync-products.mjs` step, exactly as `src/lib/
products-data.generated.ts` does in the shirtfaced storefront.

## Product art

`public/creatures/*-logo.png` are transparent-background line-art lockups generated from
the supplied logo sheets. `src/components/GarmentArt.tsx` composites them onto a flat
illustrated garment shape — there's no real product photography yet. Swap that component
for real photos once samples exist; nothing else needs to change.
