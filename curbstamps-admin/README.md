# Curb Stamps — admin & backend

Order management and print-on-demand fulfilment backend for the Curb Stamps storefront
(`../curbstamps-site`). Same split as `shirtfaced`/`shirtfaced-admin`: this app owns the
database, `curbstamps-site` has none and reaches orders only through
`/api/internal/orders`.

Full spec: [`docs/curbstamps/CURB_STAMPS_SPEC.md`](../docs/curbstamps/CURB_STAMPS_SPEC.md).

## Running locally

```bash
npm install
cp .env.example .env       # fill in CURBSTAMPS_DATABASE_URL, SESSION_SECRET, INTERNAL_API_KEY
npm run db:generate         # generates SQL from src/db/schema.ts
npm run db:migrate          # applies it to CURBSTAMPS_DATABASE_URL
npm run seed                # seeds the 36 live products
npm run dev                 # runs on :4300
```

Set `ADMIN_EMAIL` / `ADMIN_PASSWORD_HASH` to sign in at `/login` in production — dev
mode skips the login gate (see `src/proxy.ts`), same as shirtfaced-admin.

## Print-on-demand

`src/lib/pod/` is a provider-agnostic interface (`PodProvider`) with two implementations:

- `mock-adapter.ts` — the default (`POD_PROVIDER=mock` or unset). Logs what a real
  provider would receive and fakes a lifecycle. Safe to run with zero vendor setup.
- `printful-adapter.ts` — a reference implementation against Printful's real order API.
  **Not wired up** — it needs a real `PRINTFUL_API_KEY` and a filled-in
  `SYNC_VARIANT_MAP` (Printful's per-colour/size product ids, from a Printful catalogue
  that doesn't exist yet) before `POD_PROVIDER=printful` does anything but throw. See
  that file's own comment and `docs/curbstamps/CURB_STAMPS_SPEC.md` §4.

An order calls into whichever provider `getPodProvider()` returns the moment it's marked
paid (`markOrderPaid` in `src/db/store-queries.ts`) — either by `POST /api/internal/orders/:id`
with `{"status":"paid"}` (curbstamps-site's Stripe webhook) or by staff clicking
"Mark paid & submit to POD" on an order.

`POST /api/pod/webhook` is where a real provider's fulfilment updates (in production,
shipped, tracking number) land — see that route's comment for the shared-secret auth and
generic payload shape.

## Orders

`/orders` lists everything; `/orders/:id` shows line items, shipping address, POD status
and tracking, with actions to mark paid (which also submits to POD), mark shipped, or
cancel (refunding via Stripe if a PaymentIntent exists).
