# shirtfaced — Email Visual Direction Handover

## Status
LOCKED WORKING DIRECTION — 2026-08-10

This document records the decisions from the current visual exploration so the next session continues from the established direction rather than restarting or converging on one repeated template.

## Identity rules — immutable

- Customer-facing brand name is always lowercase: `shirtfaced`.
- When functioning as the brand mark/logo, the wordmark MUST use the official wordmark + official dripping X-eyes smiley lockup.
- The wordmark MUST NOT appear alone as a substitute logo.
- Plain `shirtfaced` without the smiley is allowed only inside sentence copy or as an intentional text treatment.
- Never redraw, reinterpret or invent the smiley. Use the actual repository identity asset.
- Use the established Shirtfaced custom type system/assets from the repository. Do not substitute generic streetwear typography where the real font can be used.

## Email colour system

- Emails are NOT dark-mode compositions.
- Primary body/canvas is light / off-white.
- Dark/black header and footer are part of the approved email framing system.
- Lime is accent only.
- Lime must not become the dominant field, default background, or automatic highlight on every element.
- Black, off-white and photography do the heavy lifting; lime punctuates.

## Structural direction

There is no single universal Shirtfaced email template.

Email families should be visibly different compositions held together by the immutable identity system. Do not make one layout and swap headlines/products.

Approved principle:

`same bastard underneath; different clothes.`

Examples of intentionally different families:

- Welcome — editorial introduction / brand-world entry.
- Drop announcement — campaign-led, high-impact, photography or art dominant.
- Back in stock — product-led and immediate.
- Abandoned cart — sparse/direct, can be product or moment led.
- Order confirmation — deliberately utilitarian/receipt-like while still Shirtfaced.
- Shipping — dispatch/tracking/docket language.
- Post-purchase — human/photographic, less transactional.
- VIP/early access — invitation or access-pass logic.
- Win-back — concept-led rather than a generic discount card.

## Photography

Do not allow one hero image, one bloke, one night market, one pub scene, or one lighting condition to become the email identity.

Photography should draw from the broader Shirtfaced world and campaign engine: nightlife, daylight, beach, 4WD, parties, BBQs, footy, festivals, servo stops, kick-ons, dawn, suburban and other ordinary Australian social moments as appropriate to the campaign.

The photograph must remain good enough to share even without the product.

Product is naturally present where useful; it does not need to be the subject of every image.

## Anti-convergence rule for email

Before producing the next email, compare it to the previous three visual explorations across:

- layout architecture;
- hero geometry;
- photography setting;
- light/time of day;
- typography scale and position;
- product density;
- texture/treatment;
- CTA architecture;
- amount/location of lime;
- footer treatment.

If the proposed email substantially repeats the previous composition, reject it before rendering and change the mechanics.

A successful previous email creates a repetition penalty, not a formula.

Reference `docs/design/MECHANICAL_ANTI_CONVERGENCE_GATE.md` and `docs/SHIRTFACED_CREATIVE_BRAIN.md` for the broader principle.

## What was approved in the exploration

The user approved the overall direction once the emails moved to:

- light/off-white email bodies;
- dark header and footer;
- strong editorial composition;
- actual Shirtfaced identity language;
- documentary/lifestyle photography;
- restrained lime accent;
- larger individual email studies rather than contact sheets.

The user explicitly rejected:

- dark-mode emails;
- lime-dominant emails;
- uppercase SHIRTFACED wordmarks;
- wordmark used as a standalone logo without the smiley;
- invented/reinterpreted smileys or mascots;
- repeated identical email layouts;
- repeated identical hero photography;
- generic grunge/streetwear cosplay presented as brand identity;
- ten postage-stamp templates on one board when individual designs need judging.

## Important caveat about exploratory renders

Generated visual concepts are references for composition only unless they use verified repository assets. Image generation has repeatedly invented garment graphics, product names, slogans, smileys and typography. None of those inventions become brand assets or product truth by appearing in a concept render.

When converting concepts to HTML, source real logos, fonts, products, photography and copy from the repository/content system.

## Next-session instruction

Continue ONE EMAIL AT A TIME at useful viewing size.

Do not begin by making another welcome/drop layout.

Pick the next lifecycle email and deliberately choose a composition unlike the previous examples. Use the actual repo identity assets and established font. Keep the dark header/footer + light body framing, but vary everything else that is not locked.

The immediate next exploration should preferably move away from the repeated nightlife/collage treatment — e.g. a daylight or non-nightlife Shirtfaced world, a highly typographic utility treatment, or another medium that passes the anti-convergence gate.

After the visual families are approved, translate them into robust HTML email components with email-client-safe fallbacks rather than treating the generated images as implementation assets.
