# DNS — shirtfaced.wtf

Authoritative record of what is configured and why. Update this file whenever a
record changes.

## Where it's hosted

- Registrar: **GoDaddy**
- DNS: **Cloudflare** (zone `shirtfaced.wtf`, nameservers `joel` / `nancy.ns.cloudflare.com`)
- Origin: **Oracle** `161.33.31.74`, reached only via Cloudflare Tunnel
  `be826f3d-e8a5-4e7c-94bb-d547079fa529` — the box has **nothing on :80/:443**,
  nginx listens on `:4173` and cloudflared dials outbound.

`shirtfaced.au` is also registered but stalled behind auDA identity validation.
Oracle's nginx `server_name` and the tunnel ingress already cover it, so it will
work with no config change if it ever completes.

## Records

| Type | Name | Value | Proxy |
|---|---|---|---|
| CNAME | `@` | `be826f3d-e8a5-4e7c-94bb-d547079fa529.cfargotunnel.com` | Proxied |
| CNAME | `www` | `be826f3d-e8a5-4e7c-94bb-d547079fa529.cfargotunnel.com` | Proxied |
| TXT | `@` | `v=spf1 -all` | — |
| TXT | `_dmarc` | `v=DMARC1; p=quarantine;` | — |

SSL/TLS mode: **Full**.

### Why the mail records look like this

The domain sends no email, so the posture is "reject everything":

- `v=spf1 -all` — no host is authorised to send as this domain.
- `p=quarantine` while an outbound sender is being chosen. Goes back to
  `p=reject` once mail is confirmed DKIM-aligned.
- The wildcard `*._domainkey` null-key record was REMOVED 2026-08-02: it
  revokes every selector and would block any real sending provider's DKIM.

**No `rua=`** on the DMARC record: reports to an address on another domain
require that domain to publish `shirtfaced.wtf._report._dmarc.<their-domain>`.
We can't add records to gmail.com, so compliant receivers would silently drop
the reports. A `rua=` pointing at Gmail would be decorative, not functional.

**No null MX** (`MX 0 .`): it would refuse inbound mail, and `support@` /
`orders@shirtfaced.wtf` is a near-certainty for a storefront. SPF + DMARC already
stop spoofing without booby-trapping future inbound. When inbound is wanted, use
**Cloudflare Email Routing** — `orveris.com` already runs that way.

## ⚠️ MUST DO before checkout goes live

`v=spf1 -all` means **nothing** may send as this domain. That is correct today
and **wrong the moment a payment provider starts sending on our behalf** —
order confirmations and receipts will be rejected outright, not just spam-filed.

Before enabling Stripe Checkout or Shopify:

1. Run the provider's sending-domain verification flow. It issues the exact
   records to add — typically an SPF `include:` plus one or more DKIM CNAMEs.
   Take the values from that flow; do not guess them.
2. Replace the SPF record with `v=spf1 <provider include> -all`.
3. Remove the wildcard `*._domainkey` null-DKIM record, or it will override the
   provider's real DKIM selector and every signature will fail.
4. Temporarily relax DMARC to `v=DMARC1; p=quarantine;` during the changeover,
   then return it to `p=reject` once mail is confirmed delivering and aligned.

Step 3 is the one that bites — the wildcard null key is deliberately hostile to
all selectors, including legitimate ones.
