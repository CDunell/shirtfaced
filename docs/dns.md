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
| CNAME | `admin` | `be826f3d-e8a5-4e7c-94bb-d547079fa529.cfargotunnel.com` | Proxied |
| CNAME | `studio` | `be826f3d-e8a5-4e7c-94bb-d547079fa529.cfargotunnel.com` | Proxied |
| TXT | `@` | `v=spf1 include:amazonses.com include:_spf.mx.cloudflare.net ~all` | — |
| TXT | `_dmarc` | `v=DMARC1; p=reject;` | — |
| MX | `@` | `route1/2/3.mx.cloudflare.net` (Cloudflare Email Routing) | — |

**Mail is live and DMARC is at full strength** (confirmed 22 August 2026 via
public DNS lookup — `nslookup`, no credentials needed — and by three real
order-confirmation emails actually arriving). SPF authorises Amazon SES,
which is Resend's underlying sender — Resend's domain verification was
completed for real, not just planned. MX routes inbound through Cloudflare
Email Routing, so `hello@shirtfaced.wtf` receives mail (owner-confirmed).
DMARC held at the mid-changeover `p=quarantine` setting through three
successful real sends, then was moved to `p=reject` the same day — the
resting state, not temporary any more. This section previously described
the pre-Resend blocked state (`v=spf1 -all`, no MX) — that was stale; this
repo's docs had not been updated to match what was actually configured on
the box/Cloudflare dashboard.

`admin` was added by hand and is live (confirmed 2026-08-06 — `/login` serves,
every other path redirects to it). Same tunnel; `/etc/cloudflared/config.yml`
routes `admin.shirtfaced.wtf` → `localhost:4200`, the shirtfaced-admin service.

It had to be added in the dashboard rather than by the box, because the tunnel's
own credential there is scoped to a different zone (`tradeninja.au`) and cannot
provision records in this one. That constraint still applies to any future record.

**`studio` is not yet added** (2026-08-06) — the tunnel ingress is live
(`studio.shirtfaced.wtf` → `localhost:8010`, the shirtfaced-studio service),
so the record is the only missing piece. Same manual-add constraint as `admin`.

⚠️ **Create the Access policy before the record.** Studio has no login of its
own and its generate endpoint bills OpenAI, so the moment that CNAME resolves
without a policy in front, anyone who finds the hostname can spend money. Zero
Trust → Access → Applications → self-hosted, domain `studio.shirtfaced.wtf`,
one policy: Allow, Include → Emails → the owner's address.

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

## Done — was "MUST DO before checkout goes live"

This was written when SPF was `v=spf1 -all` and would have rejected every
order-confirmation email outright. Resend's sending-domain verification has
since been completed for real (see the Records table above) — the SPF
include, the wildcard null-DKIM removal, and the DMARC relax to
`p=quarantine` all happened. Confirmed working, not just configured: three
real orders have gone through checkout and their confirmation emails
actually arrived. DMARC was then moved to `p=reject` (22 August 2026),
closing out the whole plan — nothing left open in this section.
