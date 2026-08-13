# SHIRTFACED — The Shirtfaced Shout

Status: Future ownership mechanic  
Date: 13 August 2026  
Scope: Low-friction recurring ownership ritual for customers

---

# 1. Concept

Every eligible SHIRTFACED order includes a unique SHOUT number.

Example:

`SHOUT #00481`

At a defined cadence, SHIRTFACED publishes one number. The owner of that number receives a defined reward.

The default reward concept is the next eligible product/drop at no charge, but the exact reward must be commercially and legally approved before launch.

---

# 2. Why it exists

The mechanic should:

- make ownership persist beyond checkout
- create a reason to retain packaging/order inserts
- give existing customers a recurring reason to check the brand
- create early-number provenance without fake exclusivity
- work nationally
- require effectively zero effort from the customer

This is not a lottery-style mechanic to be improvised casually. Promotion law, terms, accounting and fulfilment must be checked before implementation.

---

# 3. Customer experience

## At fulfilment

Customer receives a physical or digital SHOUT number.

Example insert:

`SHOUT #00481`

Optional supporting line:

`KEEP THIS.`

Do not overexplain on the card if the website/order email already contains the rules.

## At draw/publication

SHIRTFACED publishes:

`THIS WEEK'S SHOUT: #00481`

The customer follows the published claim process.

---

# 4. System requirements

Before launch, define:

- unique number generation
- order-to-number mapping
- duplicate prevention
- customer lookup
- eligibility rules
- claim verification
- claim deadline
- reward type
- stock treatment
- refund/return interaction
- cancellation handling
- privacy treatment
- terms and conditions
- Australian trade-promotion legal review if required

The mapping must be internal and auditable.

---

# 5. Suggested data model

Minimum fields:

- `shout_number`
- `order_id`
- `customer_id`
- `issued_at`
- `order_status`
- `eligible`
- `selected_at`
- `claimed_at`
- `reward_id`
- `fulfilment_status`

Do not expose customer identity publicly by default.

---

# 6. Cadence

Do not begin with a weekly promise unless operational capacity and legal treatment are confirmed.

Recommended rollout:

## Phase 1 — pilot

- issue numbers to a small defined order cohort
- run one controlled SHOUT event
- validate claim and fulfilment process

## Phase 2 — recurring

Only after the pilot works:

- define a stable cadence
- automate number assignment
- automate customer verification where practical
- integrate publication scheduling into the marketing engine

---

# 7. Creative extensions

Only after the base mechanic proves understandable:

- Gary's Shout
- number-ending event, e.g. all eligible numbers ending in a specified suffix
- first-customer anniversary call-back
- historic low-number stories
- product-specific SHOUT rounds

Do not constantly change the mechanic. Recognition depends on a stable core rule.

---

# 8. Measurement

Track:

- percentage of issued numbers successfully mapped
- claim completion rate
- repeat site visits from existing customers where measurable
- direct traffic around SHOUT publication
- customer posts showing numbers
- support burden
- cost per reward
- repeat purchase behaviour among numbered customers

---

# 9. Go / no-go gate

Do not launch until:

- real order volume exists
- fulfilment can reliably issue unique numbers
- legal/promotion treatment is confirmed
- claim process is tested end-to-end
- reward economics are acceptable
- customer-service handling is documented

This is a customer-stage mechanic, not a zero-audience launch tactic.
