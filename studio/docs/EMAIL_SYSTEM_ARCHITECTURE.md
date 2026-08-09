# Shirtfaced Email System Architecture

Status: implementation baseline
Owner: Shirtfaced
Last updated: 2026-08-09

## Purpose

Email is a first-class Shirtfaced publishing channel alongside Social and the storefront. The system must support customer lifecycle messages, marketing campaigns and future Marketing Engine decisions without handing ownership of customer state to an email vendor.

The provider is an execution adapter. Shirtfaced remains the source of truth for contacts, consent, suppressions, lifecycle events, message intent and delivery history.

## Principles

1. Transactional and marketing intent are separate.
2. Marketing email is never sent without current consent and a clear unsubscribe path.
3. Hard bounces, complaints and global suppressions stop delivery immediately.
4. Consent history is append-only. Current eligibility is derived from the history plus suppression state.
5. Production must never report fake delivery success.
6. Provider credentials and provider-issued DNS values are environment/configuration data, never committed secrets.
7. Human approval remains the gate for campaign creative and broadcasts. Event-triggered transactional messages may execute automatically once their template is approved.
8. The future Marketing Engine may recommend audience, timing, campaign and cadence, but must use the same eligibility and delivery contracts.

## Channel separation

### Transactional

Examples: order confirmation, payment/refund, fulfilment, shipping, delivery, cancellation and account/security messages if accounts are introduced.

Transactional delivery does not depend on marketing opt-in. It is still blocked by addresses known to be undeliverable or unsafe to send to.

### Marketing

Examples: signup/welcome, pre-drop, drop live, restock, browse/cart/checkout recovery, post-purchase merchandising, win-back and one-off broadcasts.

Marketing delivery requires current marketing consent and no applicable suppression.

## Data model

### EmailContact

Canonical, normalised address with optional display name and customer reference. Address comparison is case-insensitive through normalisation before persistence.

### EmailConsentEvent

Append-only event recording subscription or unsubscription, purpose, source and occurrence time. Sources include storefront signup, checkout, account preference, import, admin and provider webhook.

### EmailSuppression

Durable block with reason and scope. Reasons include unsubscribe, hard bounce, complaint, manual and legal. Global suppressions block all discretionary delivery; marketing suppressions block marketing only.

### EmailMessage

One rendered delivery intent. Stores purpose, template key, subject, rendered HTML/text, adapter, state, external provider ID, attempts and delivery receipt. This is the audit record for what Shirtfaced attempted to send.

## Eligibility

Marketing is eligible only when all are true:

- a contact exists;
- the latest marketing consent event is `subscribed`;
- there is no active marketing or global suppression;
- the address has not been hard-bounced or complained.

Transactional is eligible when there is no global delivery suppression caused by hard bounce, complaint or an explicit operational block. A marketing unsubscribe alone does not block a legitimate transactional message.

## Adapter boundary

`EmailAdapter` exposes a small send contract and returns a durable receipt. Initial modes are:

- `disabled`: production-safe default; refuses delivery;
- `local`: writes a deterministic preview artifact for development/testing only;
- future provider adapters: Resend, Amazon SES, Postmark or another selected provider.

No provider-specific contact list becomes canonical state.

## Email Studio

Phase 1 adds an Email bench to Studio with:

- DNS/readiness plan;
- template catalogue;
- purpose visibility;
- sample payload entry;
- HTML/text preview;
- eligibility check;
- local test delivery when explicitly enabled.

Later phases add contact inspection, campaign review, audience preview, scheduling and delivery analytics.

## Marketing Engine hooks

The future Marketing Engine may emit an `EmailRecommendation` containing:

- campaign/drop reference;
- lifecycle trigger;
- audience/segment reference;
- template key;
- proposed subject/preheader;
- recommended send time;
- priority and expiry;
- rationale and source signals.

The engine cannot bypass consent, suppressions, approved-template status or human campaign approval.

## Event inputs

Expected upstream events include:

- subscriber.created / subscriber.updated;
- product.viewed;
- cart.updated;
- checkout.started / checkout.abandoned;
- order.created / paid / fulfilled / shipped / delivered / cancelled / refunded;
- product.restocked / stock.low;
- drop.announced / drop.live / drop.ending;
- campaign.approved;
- social.published;
- customer.inactive.

Event ingestion is idempotent. Email automation consumes events; it does not rewrite their source systems.

## Phases

### Phase 1 — foundation

DNS runbook and manifest, contact/consent/suppression/message persistence, adapter boundary, disabled/local adapters, preview API and Email Studio bench.

### Phase 2 — storefront capture

Signup endpoints/forms, double-opt-in policy decision, preference centre, unsubscribe endpoint, checkout consent capture and provider webhook ingestion.

### Phase 3 — transactional

Approved transactional templates and commerce event wiring.

### Phase 4 — lifecycle marketing

Welcome, recovery, drop, restock, post-purchase and win-back automations with review gates.

### Phase 5 — orchestration

Marketing Engine recommendations, campaign calendar coordination across Email/Social/site, performance ingestion and sales feedback.

## Out of scope for Phase 1

- choosing a provider by guesswork;
- changing public DNS without verified DNS-host access;
- creating social/email accounts;
- importing bought lists;
- autonomous campaign sending;
- secrets in Git.
