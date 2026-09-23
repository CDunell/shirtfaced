# SHIRTFACED — Agency Services Arm

Status: APPROVED DIRECTION — a separate entity, kept distinct from the Shirtfaced brand
Date: 20 August 2026

## Governance

Only decisions explicitly approved by the project owner are project rules.
Assistant-generated sequencing, naming, pricing and vertical priorities are proposals
unless explicitly approved. Documentation does not convert a recommendation into policy.

### Approved directive

Stand up a client design/production services business, run separately from Shirtfaced,
using Studio's existing design-generation and compositing pipeline to do paid creative
and merch-production work for outside clients.

## Scope statement

This document governs a client-services business that sits outside Systems A, B and C
in `CLAUDE.md`. It does not govern the Shirtfaced universe, product design, or
Shirtfaced's own channel/campaign work — none of those systems' rules apply to work
produced under this arm, because that work is published under a client's brand, not
Shirtfaced's. Equally, nothing in this document overrides `POSITIONING.md`,
`BRAND_VOICE.md`, or the product design constitution — this arm does not touch them,
and they do not touch it.

## Why it exists

- **Runway.** Client revenue lands before Shirtfaced has any customers of its own
  (`src/app/checkout/page.tsx` has no payment processor wired up yet — see the
  storefront's current state). It funds Shirtfaced's own launch spend instead of that
  spend needing to come out of pocket with no income against it.
- **Audience access without brand cost.** Client venues (breweries, clubs, gyms,
  podcasts) already hold physical/social audiences that overlap with Shirtfaced's
  target register. The arm doesn't expose those audiences to the Shirtfaced brand —
  it exposes the people running the arm to venues and relationships that make a later,
  separate Shirtfaced pitch (stockist, collab, pop-up) easier and warmer.
- **Cheap pattern-testing.** Every client brief tests what original, non-logo-slapping
  illustration work actually sells, on someone else's print run and someone else's risk.
- **Distribution relationships.** A client that trusts the arm's design work is a warm
  lead for a future Shirtfaced stockist conversation — a separate, later pitch, not an
  automatic consequence of the services relationship.

## Structural rule: kept separate, deliberately

- Separate trading name — not yet chosen (open decision).
- Separate site/portfolio; no shared visual identity with Shirtfaced.
- Separate social presence.
- No mention of "Shirtfaced" in any client-facing material.
- The connection between the two stays internal only. This is not a "house of brands"
  visible-cross-promotion model — the whole point of separation is to avoid diluting
  or confusing the universe/character brand. If visible cross-promotion is wanted
  instead, that is a different, later structural decision, not a variant of this one.

## Build state

- `agency/index.html` — draft one-page site (MAAS pitch, pricing model, verticals,
  contact). Standalone static HTML, no dependency on the Shirtfaced Next.js app —
  deliberate, so the two can never accidentally share a build or a deploy.
- `agency/PITCH_ONE_PAGER.md` — printable/emailable version of the same pitch, plus a
  first-contact email draft.
- Both use the placeholder trading name **Second Pour Studio** — proposed, not decided.
  Search-check and confirm before it touches anything client-facing.
- `hello@secondpourstudio.example` in both files is a placeholder mailbox — it does not
  exist and must be replaced once a real domain is registered.

## Candidate service model: Merch-as-a-Service (MAAS)

Researched precedent, not Shirtfaced-specific invention: brewery-merch agencies
(Brewery Branding Co, Bout It Merch, the Beer Fans marketplace) run design, production,
fulfilment and storefront for venues at no upfront cost or inventory risk to the venue,
taking a share of sales instead.

- Breweries typically allocate 8–14% of marketing budget to merch; a well-run quarterly
  merch store can net a venue roughly $25k in revenue (industry reporting, not a
  Shirtfaced projection).
- Best-selling categories in that research: black tees, stubby holders, cooler bags,
  beach towels — stubby holders and coolers overlap directly with Shirtfaced's own
  drinkware line, so the product knowledge transfers even though the brand doesn't.
- The recurring complaint from industry sources is generic "logo-slapping" merch that
  nobody wears twice. Every incumbent vendor found in this space is a logo-print shop,
  not a design studio. Original character/illustration work — the thing Studio's
  pipeline is built for — is a real differentiator against that incumbent set, not a
  marketing claim.

## Candidate client verticals (idea bank — not approved specifics)

- Breweries, pubs, bottle shops
- Local sports clubs (footy, cricket, netball) — supporter merch
- Podcasts with an Australian-humour audience
- Gyms, boxing, CrossFit

Selection of a first vertical is an open decision.

## Open decisions (still require owner approval)

- Trading name and legal structure (second trading name off the same ABN vs a separate
  entity)
- Pricing/revenue model (flat fee vs revenue share vs full no-upfront MAAS)
- Which vertical to approach first
- Whether Studio's design-generation and compositing pipeline is reused as-is for
  client work, or forked so client work and Shirtfaced's own corpus/pipeline changes
  can't cross-contaminate each other
- Whether any output from client work is permitted to inform Shirtfaced's own design
  corpus, or must stay fully partitioned

No assistant recommendation in this document becomes a project rule by being written
down. The core directive — build this as a separate arm — is approved; everything
under "candidate" and "open decisions" above is not.
