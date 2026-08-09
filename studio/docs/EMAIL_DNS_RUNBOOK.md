# Shirtfaced Email DNS Runbook

Status: target-state runbook; public DNS not yet changed
Domain: `shirtfaced.wtf`
Last updated: 2026-08-09

## Goal

Create authenticated, observable email sending without risking the storefront/root-domain configuration or inventing provider values before a provider is selected.

## Proposed namespace

| Purpose | Host | Notes |
| --- | --- | --- |
| Brand/site | `shirtfaced.wtf` | Existing root; do not disturb unrelated records. |
| Transactional mail | `mail.shirtfaced.wtf` | Proposed From/alignment namespace. |
| Marketing mail | `news.shirtfaced.wtf` | Proposed marketing From/alignment namespace. |
| Return path/bounces | Provider supplied under `bounce.*` | Exact record is provider-dependent. |
| Tracking links | `links.shirtfaced.wtf` | CNAME target is provider-dependent. |
| DMARC policy | `_dmarc.shirtfaced.wtf` | Organisational policy/reporting. |

Subdomains organise traffic and reputation signals; they are not magical reputation firewalls. Domain alignment and provider behaviour still matter.

## Before changing anything

1. Identify the authoritative DNS host for `shirtfaced.wtf`.
2. Export/screenshot the complete current DNS zone.
3. Record current MX, TXT, SPF, DKIM, DMARC and CNAME records.
4. Confirm whether any existing mailbox service uses the root domain.
5. Select the delivery provider(s) and obtain their exact verification/DKIM/return-path/tracking values.
6. Lower TTL only where the DNS host supports it and only if a planned cutover benefits from it.
7. Never replace an existing SPF record with a second SPF TXT record. Merge authorised senders into one SPF policy for that host.

## Required controls

### SPF

- Publish one SPF TXT record per sending host.
- Use only the provider's documented `include`/IP mechanism.
- Keep the SPF DNS lookup count within the protocol limit.
- Do not add a provider until it is actually used.

### DKIM

- Publish every selector exactly as issued by the selected provider.
- Prefer 2048-bit provider keys where supported.
- Keep marketing and transactional selectors distinct when the provider supports it.
- Rotate through the provider, not by manually editing key material in Git.

### DMARC

Start with monitoring while legitimate senders are inventoried, then tighten deliberately.

Initial target:

```text
_dmarc.shirtfaced.wtf TXT "v=DMARC1; p=none; rua=mailto:dmarc@shirtfaced.wtf; adkim=s; aspf=s; pct=100"
```

The reporting mailbox must exist or be handled before publication. Once all legitimate mail passes alignment and reports are clean, progress to `p=quarantine`, then `p=reject`. Do not jump to reject while unknown legitimate senders remain.

### Return path / bounce handling

Use the provider's custom return-path configuration so bounces align with Shirtfaced rather than a shared generic domain where supported. Exact DNS records are provider-issued.

### Tracking domain

Use `links.shirtfaced.wtf` (or provider-supported equivalent) rather than a generic provider tracking hostname. Only create the CNAME after obtaining the provider target.

### Mailboxes

At minimum reserve/route:

- `postmaster@shirtfaced.wtf`
- `abuse@shirtfaced.wtf`
- `dmarc@shirtfaced.wtf`
- a customer-facing reply address such as `hello@shirtfaced.wtf`

Do not use a no-reply address unless there is a concrete operational reason.

## Provider-neutral DNS manifest

The repository tracks expected record roles, never made-up provider targets:

```yaml
root_domain: shirtfaced.wtf
transactional_domain: mail.shirtfaced.wtf
marketing_domain: news.shirtfaced.wtf
tracking_domain: links.shirtfaced.wtf
records:
  spf_transactional: provider_required
  spf_marketing: provider_required
  dkim_transactional: provider_required
  dkim_marketing: provider_required
  return_path: provider_required
  tracking_cname: provider_required
  dmarc: planned
```

## Apply sequence

1. Add provider domain-verification records.
2. Add DKIM records.
3. Add/merge SPF for the exact sending hosts.
4. Configure custom return path and tracking domain.
5. Publish DMARC in monitor mode.
6. Verify all provider checks.
7. Send test messages to multiple mailbox providers.
8. Inspect raw headers for `spf=pass`, `dkim=pass` and `dmarc=pass` with expected alignment.
9. Confirm bounces and complaints are received by the application/provider webhook path.
10. Warm traffic naturally; do not dump an unengaged list into a new sending identity.

## Verification checklist

A DNS change is not complete because the provider UI shows a green tick. Confirm independently:

- authoritative DNS returns the intended record;
- no duplicate SPF record exists at the same host;
- DKIM selector resolves;
- DMARC record parses;
- From domain aligns under DMARC;
- return path is correct;
- tracking hostname resolves and uses HTTPS;
- test mail passes SPF/DKIM/DMARC;
- reply path reaches a monitored mailbox;
- unsubscribe works for marketing;
- hard bounce and complaint suppressions reach Shirtfaced state.

## Rollback

If mail authentication or existing mail breaks:

1. stop application/provider sends;
2. restore the pre-change DNS record set from the zone export;
3. remove only the newly introduced provider records;
4. verify existing MX/mail flow before retrying;
5. document the failure before the next attempt.

## Current execution status

The DNS architecture and apply procedure are defined. No public DNS records are claimed as changed by this repository work. Actual application requires verified access to the authoritative DNS host and exact provider-issued values.
