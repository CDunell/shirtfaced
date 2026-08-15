# SHIRTFACED HTML EMAIL SYSTEM

Production-ready standalone HTML email templates.

Built to match the brand visual system shown in the design concepts:
black header · cream paper (`#F3EFE5`) · acid lime (`#B9EC29`) · condensed display type · raw mates energy.

## Templates

| File | Purpose |
|------|---------|
| `html/01-welcome.html` | Welcome / onboarding |
| `html/02-drop-announcement.html` | New drop / collection launch |
| `html/03-back-in-stock.html` | Restock alert |
| `html/04-abandoned-cart.html` | Cart recovery |
| `html/05-order-confirmation.html` | Order confirmed |
| `html/06-shipping-confirmation.html` | Shipping + tracking |
| `html/07-thank-you.html` | Post-purchase thank you |
| `html/08-win-back.html` | Win-back (10% off – `COMEBACK10`) |
| `html/09-vip-early-access.html` | VIP / early access |
| `html/10-birthday.html` | Birthday (15% off – `BDAY15`) |

Matching plain-text versions live in `plain-text/`.

## Visual system

- **Colours**: black `#111111` / `#000000`, warm off-white `#F3EFE5`, acid lime `#B9EC29`
- **Typography**: email-safe condensed stack (`Impact / Haettenschweiler / Arial Black / Arial`)
- **Layout**: 600–640px desktop shell, single-column mobile, pure tables, Outlook-safe
- **No web fonts** in the emails (client support is unreliable). The custom `Shirtfaced` typeface lives in the main repo for the website.

## ESP placeholders

```
{{ primary_url }}
{{ unsubscribe_url }}
{{ current_year }}
{{ order_number }}
{{ order_date }}
{{ order_total }}
{{ shipping_name }}
{{ shipping_address }}
{{ order_status_url }}
{{ carrier_name }}
{{ tracking_number }}
{{ estimated_delivery }}
{{ tracking_url }}
```

## Image hosting

Current templates use placeholder images (`placehold.co`).  
Before sending, replace every `src` with absolute HTTPS URLs from your CDN / ESP asset library (lifestyle shots + product flats).

## Compatibility

- Table-based (no flex / grid)
- Hidden preheader text
- Apple Mail / Gmail / Outlook friendly
- Run through your ESP’s CSS inliner before send

## Brand rule

Keep the raw, unapologetic tone.  
Transactional emails stay cleaner.  
Campaign / drop emails can lean into the scrapbook / poster energy.

**GOOD MATES, GREAT TIMES, SHIRTFACED.**
