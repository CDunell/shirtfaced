# Shirtfaced

T-shirt storefront for **shirtfaced.wtf**. Next.js (App Router) + Tailwind CSS,
built as a static export.

Product catalog is static data in `src/lib/products.ts`. The cart is
client-side only (React context backed by `localStorage`, see
`src/lib/cart-context.tsx`) — there is no checkout/payment integration yet.

## Develop

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Build

```bash
npm run build
```

Emits a static site to `out/`. Deploys as-is to Cloudflare Pages, Netlify,
Vercel, or any static host — no server runtime required.

## Structure

- `src/app/page.tsx` — home page / product grid
- `src/app/products/[slug]/page.tsx` — product detail + add to cart
- `src/app/cart/page.tsx` — cart page
- `src/app/checkout/page.tsx` — checkout (no card fields by design)
- `src/lib/products.ts` — product catalog
- `src/lib/cart-context.tsx` — cart state

## Before go-live

**Read [docs/pre-golive.md](docs/pre-golive.md).** Shipping rates, returns
windows, fabric weights, size measurements and product descriptions are
currently invented placeholder copy and need real figures before launch.

## Next steps

- Wire up real checkout (e.g. Stripe Checkout or Shopify) — **read
  [docs/dns.md](docs/dns.md) first**: SPF is currently `-all` (nothing may send)
  and there is a wildcard null-DKIM record. Both MUST be changed before a
  payment provider sends receipts, or every confirmation email is rejected.
- Photograph the five products still on fallback artwork (see docs/pre-golive.md)
- Persist products in a CMS/DB instead of the static array
- Bump Next past 16.2.12 to clear the transitive postcss/sharp advisories
  (do **not** run `npm audit fix --force` — it downgrades to next@9)
