# Pre-go-live checklist

Everything here must be settled **before** the store takes a real payment.

Two categories: claims that are currently invented and need real numbers, and
technical work that will silently break things if skipped.

---

## 1. Copy that is fabricated

None of the following was supplied — it was written to fill out the design and
reads as fact. All of it needs checking against reality or removing.

Country-of-origin claims were already corrected (designed in Australia, printed
anywhere). These are what's left.

| Claim | Where | Status |
|---|---|---|
| Standard shipping $11.70, 2–6 business days | `src/lib/checkout-pricing.ts` (charged), `src/app/shipping/page.tsx` (shown) | **real** — Australia Post Parcel Post, own packaging, ≤500g, 1 July 2026 published rate. No small-business discount below $50+/4wks spend, so retail-counter price is what's actually paid |
| Express shipping $15.20, 1–3 business days | same | **real** — AusPost Express Post, same conditions as above |
| Free shipping over $100 | `src/lib/products.ts` (`FREE_SHIPPING_THRESHOLD`), cart, checkout | **real** — owner-set 21 August 2026 |
| New Zealand flat $21.60, 4–7 days | `src/app/shipping/page.tsx` | **real** — AusPost Standard international, own packaging, 251–500g. Sendle (the usual cheaper AU small-business alternative) ceased Australian operations January 2026 and was ruled out for that reason |
| Same-day dispatch before 2pm AEST | `src/app/shipping/page.tsx` | removed, but re-check before re-adding |
| 30-day returns window, prepaid label, 5-day refund timing | `src/app/returns/page.tsx` | **resolved by removal** — the returns policy was reworked to no change-of-mind returns (owner decision); none of these day-count promises exist in the current copy any more, so there's nothing left here to verify |
| Recycled mailers, no plastic filler | `src/app/shipping/page.tsx` | invented |
| 240gsm / 230gsm combed cotton, garment-dyed | `src/app/about/page.tsx`, `src/lib/products.ts`, `src/components/BuyPanel.tsx` | **mostly real** — corrected to the locked 220gsm (AS Colour 5026, main range) / 207gsm (Comfort Colors 1717, washed line) figures from `GARMENT_BLANK_STRATEGY.md` in the generic About/product-feature copy and the two washed-line demo products. Any *other* individual product description not yet checked against its actual blank may still be wrong |
| Size chart measurements (chest/length per size) | `src/lib/products.ts` (`SIZE_CHART`), `/size-guide` | invented |
| "Started in 2026" | `src/app/about/page.tsx` | invented |
| Product descriptions (fit, weight, print detail) | `src/lib/products.ts` | invented |
| `hello@shirtfaced.wtf` | `src/app/contact/page.tsx` | **resolved** — owner confirmed reading real mail there, 22 August 2026 |

**Ratings and review counts were removed entirely** (2026-08-03) rather than
left as placeholders — invented ratings on a live store are a misleading-conduct
problem, not a copy one. The `rating`/`reviews` fields are gone from the `Product`
type as well, so nothing can render them by accident. Add them back only when
they're backed by real reviews.

---

## 2. Mail records — done

Resend's sending-domain verification is live (confirmed via public DNS
lookup and, better, three real order-confirmation emails actually arriving
— see `docs/dns.md`). SPF authorises Amazon SES (Resend's sender), MX routes
inbound through Cloudflare Email Routing. One step left from the original
plan: DMARC is still `p=quarantine` for the changeover and should return to
`p=reject` once alignment's held for a few more real sends.

---

## 3. Payment

Done. Checkout has no card fields of its own — card data goes straight into
Stripe's own PaymentElement (`src/app/checkout/PaymentStep.tsx`), never
through our inputs. Server-side pricing, a real PaymentIntent, and the order
webhook are all wired (see the `feat(checkout): wire real Stripe payment...`
commit) and confirmed working end to end by real test orders.

---

## 4. Catalogue gaps

- Five products still render fallback artwork instead of photography:
  No Regrets, Handle With Care, Mentally On Annual Leave, Offline Since Birth,
  Emotional Support Beverage. Drop shots into `public/products`, run
  `node scripts/optimise-images.mjs`, add the path to the colourway.
- Tanks, hoodies, hats and accessories are navigation entries with no stock
  behind them — either stock them or remove the filters.
- No light-background logo variant (the wordmark is white).

---

## 5. Legal pages

`/terms`, `/privacy` and `/returns` all exist and reference Australian
Consumer Law properly — this section's original claim that none of them
existed was itself stale by the time anyone re-checked it.

The one real gap — no legal entity named anywhere — is now closed. The
operating entity is **BM Media, ABN 34 538 203 506** (owner-supplied,
21 August 2026), trading as shirtfaced. Named on `/terms` ("Who you're
dealing with") and `/privacy` ("Your rights").

Still open: **`hello@shirtfaced.wtf` is referenced everywhere as the contact
address but the mailbox doesn't exist yet.** Nothing above fixes that.
