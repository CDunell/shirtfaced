# SHIRTFACED — BRAND VOICE

**Status:** Canon.
**Promoted from:** Hot List item 1 (`docs/shirtfaced-audit.md`, Area 4), seeded by
`docs/SESSION_HANDOVER_2026-08-07.md` §1–2.
**Date:** 7 August 2026.

This is the document that holds consistency while design content changes. Nothing
else in the repo does that job.

---

## 0. Scope & authority

This document is canon for anything written or spoken: taglines, captions, product
and service copy, social, email. It sits alongside `UNIVERSE_PREMISE.md` and
`WORLD.md`, but it is not gated by the planner's `PLANNING_CANON_HEADINGS`
allowlist — that mechanism governs image generation only. There is currently no
code enforcement of this document. It is enforced by review, the same way it was
enforced before it existed: by someone reading the copy and knowing what's wrong
with it. §9 flags what code enforcement would take.

Australian English throughout, in this document and everything it governs.

---

## 1. The word

**Shirtfaced is a verb and a state, not an identity.**

- "I got shirtfaced." "I want to get shirtfaced." "We all get shirtfaced together."
- It sits in the Australian lexicon alongside shitfaced, munted, written off, off
  your chops, maggoted, cooked, legless, blind.
- **There is no tribe noun, and none is needed.** A noun is an identity claim the
  wearer has to defend. A verb is just Saturday. Lower social risk, wider entry.
- **The unit is the group.** Nobody gets shirtfaced alone. This is why group
  custom orders are a core commercial mechanic, not a side channel.
- **The boundary is the occasion, not the demographic.** The swappable token is
  the night — the trip, the wedding, the buck's, the grand final — not a suburb
  or an age bracket.

### The critical widening

**Shirtfaced means *that level of good time*, not *that many drinks*.**

Consequences:

- Addressable occasions expand from piss-ups to every big night.
- The sober mate, the pregnant mate, the driver are all still in the photo and
  still shirtfaced. Nobody is excluded from their own night.
- Wearability rises sharply. A garment reading *drunk* gets worn twice a year.
  One reading *we had the best night* gets worn on a Wednesday. Worn garments
  are the distribution channel.
- The pun survives intact — the audience supplies the original meaning for free.
  The edge is obtained without being owned.

**Protection clause:** this only holds if imagery does not drag it back.
Schooners and staggering collapse the word to *drunk* and the range is lost.
Visual language sits on **aftermath and affection** — the group shot at the end,
the bad chips, shoes off, sunrise, the mate asleep in a plastic chair. Everyone
laughing at something that happened, not at the drinking that may or may not
have caused it. This is `WORLD.md`'s job to hold in photography; it's this
document's job to hold in words.

---

## 2. Two voices, one brand

Shirtfaced does not have one tone of voice. It has two, doing two different
jobs, and the failure mode this document exists to prevent is letting them blur
into each other.

### Identity voice — the lifestyle attitude

**Where it's used:** the hero tagline, campaign and marketing copy, social
captions, and the emotional register of World photography (what a scene *feels*
like, and what a character in it would say).

**Character:** sincere, within its own hyperbole. Warm, escalating, groups over
individuals. This is the brand talking about what a good night is. It does not
undercut itself — that's the other voice's job.

`WORLD.md`'s emotional tone — *"Fuck yeah." "One more." "We'll work it out."
"Who's driving?"* — is this voice's character-dialogue register: not things the
brand says to a customer, but the feeling a scene is built to carry. The
tagline grammar in §3 is this voice's copywriting register: what the brand says
to an audience.

### Storefront voice — the retail joke

**Where it's used:** product names and blurbs, and all service copy — shipping,
returns, size guide, about, contact, account, footer.

**Character:** dry, deadpan, self-aware. It plays regret and bad decisions for
laughs rather than disclaiming them. It is willing to take the piss out of the
brand and the customer in equal measure. This voice is already live and already
consistent — it just hadn't been named as canon. It stays exactly as it is:

> "Thirty days. Unworn, unwashed, tags on. **We won't ask why.**"
> "Not because we're precious — we just can't resell it and won't pretend
> otherwise."
> "nice shirt. shame about your choices."
> "we promise fewer emails than your ex."

### The line between them

Identity voice states what Shirtfaced believes about a good night. Storefront
voice is the brand's own retail employee, in on the joke, selling you a shirt
while gently taking the piss. One is not a lesser version of the other — they
have different jobs and different audiences-in-the-moment. A shipping page
written in Identity voice reads try-hard. A tagline written in Storefront voice
reads like it doesn't believe in itself.

---

## 3. Tagline grammar (Identity voice)

> `<beat one>, <beat two>, shirtfaced`

Reference form: **Good mates, great times, shirtfaced.**

The payoff word is the brand's own name, not a disclaimer. The escalation does
the moral positioning: the mates come first, shirtfaced is the consequence, not
the goal. Nothing sells intoxication; it sells the night, after the fact.
Because the third beat is always the brand, every shirt and every caption signs
itself.

### Starting library

From the working session that produced this document — a bank, not a fixed
set, and open to more in the same shape:

Good mates, great times, shirtfaced · Long lunch, no dinner · Two carloads, one
esky · Nan's 80th · Someone's cousin's boat · Everyone said early night · Ferry
there, taxi home · Grand final, either way · Wedding, wake, whatever · Sunrise,
servo pie · Best mate's wedding, worst speech · Shoes in hand · Group chat's
still going · Bali, day three · Nobody knows whose ute this is · Christmas with
the outlaws · Meant to be there for one · Someone's turning 30 again · Melbourne
Cup, Tuesday · Backyard, borrowed chairs · Camping, technically · Six mates, one
tent · Fishing trip, no fish · Bucks in a bus · Wrong pub, right crowd · Twenty
year reunion · Golf day, front nine only · Missed the last train · Uncle's on
the karaoke · Barefoot by nine · Whole street's here now · Nobody's got a
charger

---

## 4. Retired

**"Bad decisions" is retired as an Identity-voice payoff.** The demo-era hero
frames are retired in full:

- `src/lib/taglines.ts` — `GOOD TIMES. / <rotating> / ZERO REGRETS.`
- `src/app/layout.tsx` — `Good times. Bad decisions. Zero regrets.`

Neither was a deliberate voice decision — the site was built as a demo before
any voice canon existed, so retiring them breaks no prior commitment. **"Zero
regrets" is retired as the Identity-voice payoff position specifically:** the
brand's stance is not to disclaim consequence, it's to name itself. This does
not ban the word "regret" from existing anywhere — Storefront voice keeps
joking with it exactly as it already does ("most regrets retained," "shame
about your choices"). The retirement applies to what closes a tagline, not to
the vocabulary generally.

**Flag, not a fix:** `good-times-bad-decisions-tee`
(`src/lib/products-data.generated.ts`) is named after the retired phrase. This
is demo/placeholder catalog data, not a real design — per
`docs/shirtfaced-audit.md` 2.1, no design has ever been run through the
review system, so nothing commercial hangs off this name. It doesn't need
sign-off, just doesn't need fixing by hand either: the file is generated from
the admin Postgres database (`scripts/sync-products.mjs`), so the retirement
takes effect whenever the demo catalog is replaced with real products, not by
editing the generated file directly.

---

## 5. What we never do

Inherited from `studio/docs/stage-2/CHANNEL_TRANSLATION.md` §4, for Identity
voice wherever it writes a caption:

- Never explain the joke.
- Never force slang.
- Morning-after content stays optimistic — quiet kitchens, early light, coffee
  — never misery or humiliation.

Storefront voice already keeps its own version of this rule, stated in its own
words on the live about page — cited here as evidence this voice already knows
what it is:

> "No countdown timers telling you four people are looking at this right now.
> No fake scarcity. No inventing an origin story we can't back up."

---

## 6. Voice by surface

| Surface | Voice |
|---|---|
| Hero tagline, site `<title>`/OG/meta | Identity |
| World photography emotional tone, character feeling | Identity (dialogue register) |
| Social captions, campaign copy | Identity |
| Product names & blurbs | Storefront |
| Shipping, returns, size guide, about, contact, account | Storefront |
| Footer, newsletter opt-in, other flourishes | Storefront |

---

## 7. Worked example

Same fact — a shipping delay — in both voices:

- **Identity:** doesn't apply. Identity voice doesn't do operational
  announcements; that's not its job.
- **Storefront:** "Running a bit behind — the courier, not us. Tracking's below,
  we'll chase it if it stalls."

If a line could plausibly be either, it's Storefront. Identity voice only
covers the narrow surfaces in §6.

---

## 8. Provenance

- `docs/SESSION_HANDOVER_2026-08-07.md` §1 (the word) and §2 (tagline grammar)
  — working conclusions, now promoted.
- `docs/shirtfaced-audit.md` Area 4 — the gap this document closes.
- `docs/research/SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md` §10, "Identity /
  Display / Information voice," is a **typographic** hierarchy — which
  typeface does which job on a garment. It is unrelated to this document
  despite the shared word. Do not merge them.

---

## 9. Migration note — `taglines.ts` should derive from this document

Not done here; flagged for a separate pass.

- `taglines.ts` currently hand-authors both the words and a per-line `size`
  measured against the exact string via `scripts/tune-taglines.mjs`. A
  canon-authored line list would still need to flow through that same tuning
  step — tuning stays code, wording moves to canon.
- Photo pairing per line is an art-direction decision, not something this
  document should dictate. Derivation likely means canon owns the words only;
  tuning and photo-pairing stay hand-authored downstream, referencing canon
  lines by id.
- `layout.tsx`'s static title/OG copy currently hardcodes its own line,
  independently of `taglines.ts` — which is exactly how it drifted out of
  sync with the rotation's own stated rules. It needs to pull from the same
  canonical source as the hero rotation, not maintain a third copy.
- The six existing rotating lines (`BAD INFLUENCES`, `COMPLETE CHAOS`, etc.)
  don't map onto the new grammar's two free beats plus fixed word — this is a
  content rewrite, not a relabelling. The bank in §3 is the replacement
  material.
