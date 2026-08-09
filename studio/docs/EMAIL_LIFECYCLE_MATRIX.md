# Shirtfaced Email Lifecycle / Event Matrix

Status: implementation baseline
Last updated: 2026-08-09

| Flow | Trigger | Purpose | Audience rule | Human gate | Stop / exit condition | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| Signup confirmation / welcome | marketing consent recorded | Marketing | Current marketing consent, no suppression | Template approved once | Unsubscribe/suppress | 2/4 |
| Drop teaser | drop approved for launch | Marketing | Eligible subscribed segment | Campaign approval | Drop cancelled/expired | 4 |
| Drop live | drop goes live | Marketing | Eligible subscribed segment | Campaign approval | Drop ends / sold out | 4 |
| Restock | stock becomes available | Marketing | Eligible interested/subscribed customers | Campaign approval/policy | Stock unavailable | 4 |
| Low stock | stock threshold signal | Marketing | Eligible segment only | Campaign approval/policy | Stock unavailable/threshold stale | 4 |
| Browse recovery | qualifying product view without purchase | Marketing | Consent + configured inactivity window | Automation/template approval | Purchase/unsubscribe/expiry | 4 |
| Cart recovery | cart abandoned | Marketing | Consent + cart still actionable | Automation/template approval | Purchase/cart cleared/unsubscribe/expiry | 4 |
| Checkout recovery | checkout abandoned | Marketing | Consent + checkout still actionable | Automation/template approval | Purchase/unsubscribe/expiry | 4 |
| Order confirmation | order created/paid | Transactional | Order recipient; deliverable address | Template approved once | Sent/cancelled as appropriate | 3 |
| Refund | refund recorded | Transactional | Order recipient | Template approved once | Sent | 3 |
| Fulfilment | fulfilment created | Transactional | Order recipient | Template approved once | Superseded/cancelled | 3 |
| Shipped | shipment event | Transactional | Order recipient | Template approved once | Sent | 3 |
| Delivered | delivery event | Transactional | Order recipient | Template approved once | Sent | 3 |
| Cancellation | order cancelled | Transactional | Order recipient | Template approved once | Sent | 3 |
| Post-purchase | delivery + delay | Marketing | Consent + eligible purchase | Automation/template approval | Refund/unsubscribe/expiry | 4 |
| Cross-sell | purchase/profile signal | Marketing | Consent + frequency cap | Campaign/automation approval | Unsubscribe/expiry | 4 |
| Win-back | inactivity threshold | Marketing | Consent + frequency cap | Automation/template approval | Activity/purchase/unsubscribe | 4 |
| Broadcast | manually created campaign | Marketing | Approved eligible segment | Every campaign | Cancelled/sent | 4 |

## Frequency and conflict rules

Transactional messages are not delayed to satisfy marketing cadence. Marketing automations and broadcasts share a future frequency-cap service so a customer is not hammered because multiple triggers fire together.

Campaign/drop priority can override a lower-priority marketing recommendation, but never consent/suppression rules. Manual schedules are treated as locked unless the owner changes them.

## Event contract requirements

Every consumed event must carry a stable idempotency key, occurrence timestamp, event type and source reference. Commerce events should carry order/customer/product references, not duplicated authoritative order state.

The Email system records what it consumed and what action it derived. Replaying the same event must not duplicate a message intent.

## Marketing Engine boundary

The future Marketing Engine may decide that a flow should run, choose a segment and recommend timing. Email remains responsible for final eligibility, approved template version, frequency limits, suppression and delivery state.
