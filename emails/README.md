# SHIRTFACED HTML EMAIL SYSTEM

Production-oriented standalone HTML email templates built around the **Gig Poster** core system, with **Aftermath** as the cinematic photo-led variant.

## Included

- `html/01-welcome.html`
- `html/02-new-drop.html`
- `html/03-order-confirmation.html`
- `html/04-shipping-confirmation.html`
- `html/05-restock-promo.html`
- `html/06-aftermath-campaign.html`
- Matching plain-text versions in `plain-text/`
- Demo brand/reference assets in `assets/`

## Visual system

Core palette: black `#111111`, warm off-white `#F3EFE5`, acid lime `#C8FF1A`. Controlled accents: coral `#FF5F56`, electric blue `#5D7CFF`, burnt orange `#D9792B`. Typography uses email-safe `Arial Black / Impact / Arial` fallbacks so the layouts do not depend on webfont support.

## ESP variables

Replace the moustache-style placeholders with your ESP syntax:

- `{{ primary_url }}`
- `{{ unsubscribe_url }}`
- `{{ current_year }}`
- `{{ order_number }}`
- `{{ order_date }}`
- `{{ order_total }}`
- `{{ shipping_name }}`
- `{{ shipping_address }}`
- `{{ order_status_url }}`
- `{{ carrier_name }}`
- `{{ tracking_number }}`
- `{{ estimated_delivery }}`
- `{{ tracking_url }}`

## Image hosting

The included HTML uses relative demo paths such as `../assets/hero-01.png`. Before sending, upload campaign images to your CDN/ESP and replace each `src` with an absolute HTTPS URL.

## Compatibility

- 640px desktop email shell
- responsive single-column mobile fallback
- table-based layout
- no CSS grid/flex dependencies
- Outlook-safe typography fallback
- hidden preheader text
- Apple Mail / Gmail / Outlook-friendly structure

## Recommended production step

Run the final HTML through your ESP's CSS inliner/minifier before send. These templates already keep critical styling simple and email-safe, but inlining remains the safest production path for older Outlook clients.

## Brand rule

**Gig Poster** is the default system for welcome, launches, promos, order and shipping. **Aftermath** is the premium image-first variant. Keep Pub Wall / scrapbook treatments out of transactional emails.
